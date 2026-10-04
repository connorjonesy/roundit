"""Join canonical geography, aggregate observed years, and create lag features."""

import json
import hashlib
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pandas as pd

from .common import DATA, IDENTITY, OUTPUT, PROCESSED, YEARS, coordinate_mask, save_csv, validate_identity

KEY = ["municipality", "road_a", "road_b"]


def distance_m(lat, lon, canonical_lat, canonical_lon):
    lat, lon, canonical_lat, canonical_lon = map(
        np.radians, (lat, lon, canonical_lat, canonical_lon))
    a = (np.sin((lat - canonical_lat) / 2) ** 2
         + np.cos(lat) * np.cos(canonical_lat) * np.sin((lon - canonical_lon) / 2) ** 2)
    return 2 * 6371008.8 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def prepare_data(records, lookup):
    """Return annual rows, canonical lookup, diagnostics and inclusion counts.

    Source counts are summed, never counted as rows or deduplicated. Exact
    municipality/street-pair keys are used only when no shared ID exists.
    Ambiguous lookup entries and disagreements over 100 m exclude the entire
    intersection. No missing year is interpreted as zero.
    """
    records, lookup = records.copy(), lookup.copy()
    for frame in [records, lookup]:
        for column in KEY:
            if column not in frame:
                raise ValueError(f"Missing matching column: {column}")
            frame[column] = frame[column].astype("string").str.strip()
        # These are already canonical road names from the cleaner; no fuzzy matching.
        roads = np.sort(frame[["road_a", "road_b"]].fillna("").to_numpy(), axis=1)
        frame[["road_a", "road_b"]] = roads
    shared_id = "intersection_id" in records and "intersection_id" in lookup
    if "intersection_id" not in lookup:
        lookup["intersection_id"] = [str(uuid5(NAMESPACE_URL, "roundit:" + json.dumps([None if pd.isna(v) else v for v in key])))
                                     for key in lookup[KEY].itertuples(index=False, name=None)]
    lookup["intersection_id"] = lookup["intersection_id"].astype("string")
    if shared_id:
        records["intersection_id"] = records["intersection_id"].astype("string")
    if "intersection_name" not in lookup:
        lookup["intersection_name"] = (lookup["road_a"] + " & " + lookup["road_b"]
                                       + ", " + lookup["municipality"])
    join_key = ["intersection_id"] if shared_id else KEY
    diagnostics = []

    def diagnose(frame, mask, reason):
        bad = frame.loc[mask].copy()
        if not bad.empty:
            bad["reason"] = reason
            diagnostics.append(bad)

    invalid_key = lookup[KEY].isna().any(axis=1) | lookup[KEY].eq("").any(axis=1)
    invalid_id = lookup["intersection_id"].isna() | lookup["intersection_id"].str.strip().eq("")
    ambiguous = lookup.duplicated(join_key, keep=False) | lookup.duplicated("intersection_id", keep=False)
    invalid_geo = ~coordinate_mask(lookup)
    invalid_name = lookup["intersection_name"].isna() | lookup["intersection_name"].astype("string").str.strip().eq("")
    diagnose(lookup, invalid_key | invalid_id | invalid_name, "missing_identity")
    diagnose(lookup, ambiguous, "ambiguous_or_duplicate_canonical_identity")
    diagnose(lookup, invalid_geo, "invalid_canonical_coordinates")
    canonical = lookup.loc[~(invalid_key | invalid_id | invalid_name | ambiguous | invalid_geo),
                           list(dict.fromkeys(KEY + IDENTITY))].copy()
    for col in ["latitude", "longitude"]:
        canonical[col] = pd.to_numeric(canonical[col], errors="raise")
    # Drop an unshared source ID so the canonical identity remains authoritative.
    if not shared_id:
        records = records.drop(columns=["intersection_id"], errors="ignore")
    records = records.drop(columns=["intersection_name"], errors="ignore")
    merged = records.merge(canonical, on=join_key, how="left", suffixes=("_source", ""),
                           validate="many_to_one", indicator=True)
    if len(merged) != len(records):
        raise ValueError("Geographic join changed the observation count")
    unmatched = merged["_merge"].ne("both")
    diagnose(merged, unmatched, "unmatched_or_rejected_canonical_intersection")
    merged = merged.loc[~unmatched].copy()
    conflict = pd.Series(False, index=merged.index)
    if shared_id:
        for column in KEY:
            conflict |= ~merged[column + "_source"].eq(merged[column]).fillna(False)
    if "latitude_source" in merged and "longitude_source" in merged:
        source = merged.rename(columns={"latitude": "canonical_lat", "longitude": "canonical_lon",
                                        "latitude_source": "latitude", "longitude_source": "longitude"})
        lat = pd.to_numeric(source["latitude"], errors="coerce")
        lon = pd.to_numeric(source["longitude"], errors="coerce")
        conflict |= ~coordinate_mask(source) | distance_m(lat, lon, merged.latitude, merged.longitude).gt(100)
    elif "latitude_source" in merged or "longitude_source" in merged:
        raise ValueError("Source coordinates must have both latitude and longitude")
    diagnose(merged, conflict, "source_identity_or_coordinates_disagree")
    bad_ids = set(merged.loc[conflict, "intersection_id"])
    geo_matched = set(merged["intersection_id"]) - bad_ids
    for column in ["year", "crash_count"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    invalid = (~merged.year.isin(YEARS) | ~np.isfinite(merged.crash_count)
               | merged.crash_count.lt(0) | merged.crash_count.mod(1).ne(0))
    diagnose(merged, invalid, "invalid_year_or_collision_count")
    bad_ids |= set(merged.loc[invalid, "intersection_id"])
    usable = merged.loc[~merged.intersection_id.isin(bad_ids)].copy()
    annual = usable.groupby(IDENTITY + ["year"], as_index=False, dropna=False).crash_count.sum()
    coverage = annual.groupby("intersection_id").year.agg(set)
    complete_ids = set(coverage.index[coverage.map(lambda years: years == set(YEARS))])
    incomplete = canonical.intersection_id.isin(set(coverage.index) - complete_ids)
    diagnose(canonical, incomplete, "incomplete_2018_2022_observations_no_zero_fill")
    diagnose(canonical, ~canonical.intersection_id.isin(set(merged.intersection_id)), "no_source_observations")
    annual = annual.loc[annual.intersection_id.isin(complete_ids)].sort_values(["intersection_id", "year"]).reset_index(drop=True)
    annual["year"] = annual.year.astype(int)
    validate_identity(annual)
    if annual.duplicated(["intersection_id", "year"]).any():
        raise ValueError("Duplicate annual observation")
    report = {
        "source_collision_rows": len(records), "canonical_intersection_rows": len(lookup),
        "intersections_matched_to_coordinates": len(geo_matched),
        "canonical_intersections_excluded_geography": len(lookup) - len(geo_matched),
        "intersections_in_experiment": len(complete_ids),
        "intersections_excluded_from_experiment": len(lookup) - len(complete_ids),
        "geographically_matched_intersections_excluded_incomplete_or_invalid": len(geo_matched) - len(complete_ids),
        "unmatched_collision_rows": int(unmatched.sum()),
        "coordinate_crs": "EPSG:4326", "id_strategy": "shared_source_id" if shared_id else "canonical_id_or_uuid5_exact_municipality_street_pair",
    }
    diagnostic = pd.concat(diagnostics, ignore_index=True, sort=False) if diagnostics else pd.DataFrame(columns=KEY + IDENTITY + ["reason"])
    report["diagnostic_rows_by_reason"] = diagnostic.reason.value_counts().to_dict()
    return annual, canonical, diagnostic, report


def make_features(annual):
    validate_identity(annual)
    if annual.duplicated(["intersection_id", "year"]).any():
        raise ValueError("Duplicate intersection-year")
    data = annual.sort_values(["intersection_id", "year"]).copy()
    group = data.groupby("intersection_id")
    data["last_year"] = group.crash_count.shift(1)
    data["avg_2yr"] = (data.last_year + group.crash_count.shift(2)) / 2
    # Shifting rows alone would incorrectly bridge missing years.
    consecutive = group.year.shift(1).eq(data.year - 1) & group.year.shift(2).eq(data.year - 2)
    return data.loc[consecutive].dropna(subset=["last_year", "avg_2yr"]).reset_index(drop=True)


def main():
    records = pd.read_csv(DATA / "icbc_clean.csv", dtype={"intersection_id": "string"})
    lookup = pd.read_csv(DATA / "intersections.csv", dtype={"intersection_id": "string"})
    annual, canonical, diagnostics, report = prepare_data(records, lookup)
    report["input_sha256"] = {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest()
                              for name in ["icbc_clean.csv", "intersections.csv"]}
    save_csv(annual, PROCESSED / "intersection_year.csv")
    save_csv(canonical, PROCESSED / "intersection_lookup.csv")
    save_csv(make_features(annual), PROCESSED / "ml_features.csv")
    save_csv(diagnostics, OUTPUT / "unmatched_intersections.csv")
    (OUTPUT / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
