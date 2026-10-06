"""Clean ICBC data and export British Columbia intersection CSVs."""

import argparse
from pathlib import Path

import kagglehub
import numpy as np
import pandas as pd

DATASET = "tcashion/icbc-vehicle-crash-dataset/versions/2"
# Approximate British Columbia extent, used to reject invalid out-of-province
# coordinates while retaining municipalities throughout the province.
STUDY_BOUNDS = (-139.1, 48.2, -114.0, 60.1)
YES = {"YES", "Y", "TRUE", "1"}
NO = {"NO", "N", "FALSE", "0"}
UNKNOWN_NAMES = {"", "UNKNOWN", "NOT AVAILABLE", "N/A", "NA", "NULL"}
GROUP_COLUMNS = ["municipality", "road_a", "road_b"]
ALIASES = {
    "municipality": ["municipality_name_ifnull", "municipality_name", "city"],
    "street": ["street_full_name_ifnull", "street_full_name", "on_street"],
    "cross_street": ["cross_street_full_name", "at_street"],
    "year": ["date_of_loss_year", "crash_year"],
    "crash_count": ["total_crashes"],
    "pedestrian_flag": ["pedestrian_involved"],
    "cyclist_flag": ["cyclist_involved"],
    "latitude": ["lat"], "longitude": ["lon", "lng"],
}


def normalize_headers(columns):
    return (columns.str.strip().str.lower()
            .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_"))


def load_crash_data(csv_file):
    """Detect encoding/delimiter without silently skipping malformed records."""
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        for sep in ("\t", ",", ";"):
            try:
                sample = pd.read_csv(csv_file, sep=sep, encoding=encoding, nrows=5)
            except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeError):
                continue
            columns = set(normalize_headers(sample.columns))
            if "intersection_crash" in columns and columns & {"municipality", *ALIASES["municipality"]}:
                return pd.read_csv(csv_file, sep=sep, encoding=encoding,
                                   dtype="string", keep_default_na=False, low_memory=False)
    raise ValueError(f"Could not parse crash dataset: {csv_file}")


def distance_m(lat, lng, target_lat, target_lng):
    lat, lng, target_lat, target_lng = map(np.radians, (lat, lng, target_lat, target_lng))
    a = (np.sin((lat - target_lat) / 2) ** 2
         + np.cos(lat) * np.cos(target_lat) * np.sin((lng - target_lng) / 2) ** 2)
    return 2 * 6_371_008.8 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def clean_data(raw, max_distance_m=100, max_year=None):
    """Return cleaned records, intersection summaries, and records needing review."""
    if not np.isfinite(max_distance_m) or max_distance_m <= 0:
        raise ValueError("max_distance_m must be finite and positive")
    max_year = max_year if max_year is not None else pd.Timestamp.today().year
    data = raw.copy().reset_index(drop=True)
    data.columns = normalize_headers(data.columns)
    if data.columns.duplicated().any():
        raise ValueError("Source headers collide after normalization")
    for name, alternatives in ALIASES.items():
        source = next((col for col in [name, *alternatives] if col in data), None)
        if source is None:
            raise ValueError(f"Missing {name}. Available columns: {list(data.columns)}")
        data = data.rename(columns={source: name})
    if missing := [col for col in ["intersection_crash", "crash_severity"] if col not in data]:
        raise ValueError(f"Missing columns: {missing}")

    # Keep only relevant fields, without hashes, provenance columns, or invented IDs.
    data = data[[*ALIASES, "intersection_crash", "crash_severity"]].copy()
    for col in ["municipality", "street", "cross_street", "crash_severity"]:
        data[col] = data[col].astype("string").str.strip().str.upper()
    flags = {**dict.fromkeys(YES, "yes"), **dict.fromkeys(NO, "no")}
    for col in ["intersection_crash", "pedestrian_flag", "cyclist_flag"]:
        data[col] = data[col].astype("string").str.strip().str.upper().map(flags).fillna("unknown")
    # Unknown intersection flags are retained for review.
    data = data.loc[data["intersection_crash"].ne("no")].copy()
    for col in ["street", "cross_street"]:
        data[col] = (data[col].str.replace(r"\s+", " ", regex=True)
                     .str.replace(r"[.,]", "", regex=True))
    for col in ["year", "crash_count", "latitude", "longitude"]:
        data[col] = pd.to_numeric(data[col], errors="coerce").astype("float64")
    first = data["street"] <= data["cross_street"]
    data["road_a"] = data["street"].where(first, data["cross_street"])
    data["road_b"] = data["cross_street"].where(first, data["street"])
    reasons = pd.Series("", index=data.index, dtype="string")

    def flag(mask, reason):
        mask = mask.fillna(False)
        reasons.loc[mask] = reasons.loc[mask] + reason + ";"

    flag(data["intersection_crash"].eq("unknown"), "unknown_intersection_flag")
    flag(data["street"].isna() | data["cross_street"].isna()
         | data["street"].isin(UNKNOWN_NAMES) | data["cross_street"].isin(UNKNOWN_NAMES),
         "unresolved_street_name")
    flag(data["street"].eq(data["cross_street"]), "identical_street_names")
    flag(~(data["year"].between(1990, max_year) & data["year"].mod(1).eq(0)), "invalid_year")
    flag(~(np.isfinite(data["crash_count"]) & data["crash_count"].gt(0)
           & data["crash_count"].mod(1).eq(0)), "invalid_crash_count")
    valid_coords = data["latitude"].between(-90, 90) & data["longitude"].between(-180, 180)
    flag(~valid_coords, "invalid_coordinate")
    west, south, east, north = STUDY_BOUNDS
    in_bounds = data["latitude"].between(south, north) & data["longitude"].between(west, east)
    flag(valid_coords & ~in_bounds, "outside_study_bounds")

    locations = []
    for names, group in data.loc[reasons.eq("")].groupby(GROUP_COLUMNS, sort=True):
        # Select an observed coordinate pair near the median; do not invent a point.
        points = group[["latitude", "longitude"]].drop_duplicates().sort_values(["latitude", "longitude"])
        lat, lng = points["latitude"].to_numpy(), points["longitude"].to_numpy()
        chosen = int(np.argmin(distance_m(lat, lng, group["latitude"].median(), group["longitude"].median())))
        spread = float(distance_m(lat, lng, lat[chosen], lng[chosen]).max())
        if spread > max_distance_m:
            reasons.loc[group.index] = "dispersed_intersection_locations;"
        else:
            locations.append(dict(zip(GROUP_COLUMNS, names)) | {
                "latitude": float(lat[chosen]), "longitude": float(lng[chosen]),
                "max_distance_m": spread})

    cleaned = data.loc[reasons.eq("")].copy()
    cleaned[["year", "crash_count"]] = cleaned[["year", "crash_count"]].astype("int64")
    cleaned["crash_severity"] = cleaned["crash_severity"].replace("", "UNKNOWN").fillna("UNKNOWN")
    for kind in ["pedestrian", "cyclist"]:
        cleaned[f"{kind}_crashes"] = cleaned["crash_count"].where(cleaned[f"{kind}_flag"].eq("yes"), 0)
    summary = cleaned.groupby(GROUP_COLUMNS, as_index=False).agg(
        total_crashes=("crash_count", "sum"), pedestrian_crashes=("pedestrian_crashes", "sum"),
        cyclist_crashes=("cyclist_crashes", "sum"),
        period_start_year=("year", "min"), period_end_year=("year", "max"))
    summary = summary.merge(pd.DataFrame(locations, columns=[*GROUP_COLUMNS, "latitude", "longitude", "max_distance_m"]),
                            on=GROUP_COLUMNS, validate="one_to_one")
    summary["shared_coordinate"] = summary.duplicated(["latitude", "longitude"], keep=False)
    review = data.loc[reasons.ne("")].copy()
    review["review_reasons"] = reasons.loc[review.index].str.rstrip(";")
    if len(data) != len(cleaned) + len(review) or int(cleaned.crash_count.sum()) != int(summary.total_crashes.sum()):
        raise ValueError("Row or crash-count reconciliation failed")
    return cleaned, summary, review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Read a local source CSV instead of downloading")
    parser.add_argument("--output-dir", type=Path, default=Path("backend/data"))
    parser.add_argument("--max-distance-m", type=float, default=100)
    args = parser.parse_args()
    csv_file = args.csv
    if csv_file is None:
        folder = Path(kagglehub.dataset_download(DATASET))
        files = list(folder.rglob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found in {folder}")
        csv_file = max(files, key=lambda file: file.stat().st_size)
    raw = load_crash_data(csv_file)
    print(f"Read {len(raw):,} source records", flush=True)
    cleaned, summary, review = clean_data(raw, max_distance_m=args.max_distance_m)
    if cleaned.empty:
        raise ValueError("No accepted records; refusing to overwrite existing outputs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output_dir / "icbc_clean.csv", index=False)
    summary.to_csv(args.output_dir / "intersections.csv", index=False)
    review.to_csv(args.output_dir / "icbc_review.csv", index=False)
    print(f"Saved {len(cleaned):,} records, {len(summary):,} intersections, "
          f"and {len(review):,} review records to {args.output_dir}")


if __name__ == "__main__":
    main()
