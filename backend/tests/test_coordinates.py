import numpy as np
import pandas as pd
import pytest

from backend.ml.common import DATA, save_csv, validate_identity
from backend.ml.prepare_data import prepare_data


def test_counts_and_distinct_municipalities(source_data):
    records, lookup = source_data
    annual, canonical, diagnostics, report = prepare_data(records, lookup)
    assert len(annual) == 10
    assert canonical.intersection_id.nunique() == 2
    assert annual.crash_count.sum() == records.crash_count.sum()
    vancouver = canonical.loc[canonical.municipality.eq("VANCOUVER")].iloc[0]
    rows = annual.loc[annual.intersection_id.eq(vancouver.intersection_id)]
    assert rows.crash_count.tolist() == [3, 4, 5, 6, 7]
    assert rows.latitude.eq(49.25).all()
    assert rows.longitude.eq(-123.1).all()
    assert report["intersections_matched_to_coordinates"] == 2
    assert diagnostics.empty


def test_stable_ids_reordered_inputs_and_preserved_ids(source_data):
    records, lookup = source_data
    _, canonical, _, _ = prepare_data(records, lookup)
    _, reordered, _, _ = prepare_data(records.iloc[::-1], lookup.iloc[::-1])
    assert canonical.set_index("municipality").intersection_id.to_dict() == reordered.set_index("municipality").intersection_id.to_dict()
    lookup["intersection_id"] = ["existing-001", "existing-002"]
    annual, _, _, _ = prepare_data(records, lookup)
    assert set(annual.intersection_id) == {"existing-001", "existing-002"}
    records = records.merge(lookup[["municipality", "intersection_id"]], on="municipality", validate="many_to_one")
    annual, _, _, _ = prepare_data(records, lookup)
    assert set(annual.intersection_id) == {"existing-001", "existing-002"}


@pytest.mark.parametrize("problem,reason", [
    ("missing", "invalid_canonical_coordinates"),
    ("reversed", "invalid_canonical_coordinates"),
    ("far", "source_identity_or_coordinates_disagree"),
    ("duplicate", "ambiguous_or_duplicate_canonical_identity"),
    ("negative", "invalid_year_or_collision_count"),
    ("missing_name", "missing_identity"),
])
def test_unresolved_intersection_excluded_entirely(source_data, problem, reason):
    records, lookup = source_data
    if problem == "missing":
        lookup.loc[0, "latitude"] = np.nan
    elif problem == "reversed":
        lookup.loc[0, ["latitude", "longitude"]] = [-123.1, 49.25]
    elif problem == "far":
        records.loc[0, "latitude"] = 49.3
    elif problem == "duplicate":
        lookup = pd.concat([lookup, lookup.iloc[[0]]], ignore_index=True)
    elif problem == "negative":
        records.loc[0, "crash_count"] = -1
    elif problem == "missing_name":
        lookup.loc[0, "municipality"] = pd.NA
    annual, _, diagnostic, report = prepare_data(records, lookup)
    assert annual.intersection_id.nunique() == 1
    assert reason in set(diagnostic.reason)
    assert report["intersections_in_experiment"] == 1


def test_missing_year_never_filled_with_zero(source_data):
    records, lookup = source_data
    records = records.loc[~(records.municipality.eq("VANCOUVER") & records.year.eq(2020))]
    annual, _, diagnostic, report = prepare_data(records, lookup)
    assert annual.intersection_id.nunique() == 1
    assert report["intersections_matched_to_coordinates"] == 2
    assert "incomplete_2018_2022_observations_no_zero_fill" in set(diagnostic.reason)


def test_duplicate_shared_id_and_wrong_shared_identity(source_data):
    records, lookup = source_data
    lookup["intersection_id"] = ["one", "two"]
    records = records.merge(lookup[["municipality", "intersection_id"]], on="municipality")
    records.loc[0, "municipality"] = "WRONG CITY"
    annual, _, diagnostic, _ = prepare_data(records, lookup)
    assert set(annual.intersection_id) == {"two"}
    assert "source_identity_or_coordinates_disagree" in set(diagnostic.reason)
    lookup.loc[1, "intersection_id"] = "one"
    with pytest.raises(ValueError, match="No geographically"):
        prepare_data(records, lookup)


def test_coordinate_conflict_and_source_protection(source_data):
    records, lookup = source_data
    annual, _, _, _ = prepare_data(records, lookup)
    annual.loc[annual.index[0], "latitude"] += .001
    with pytest.raises(ValueError, match="Conflicting"):
        validate_identity(annual)
    with pytest.raises(ValueError, match="overwrite"):
        save_csv(annual, DATA / "icbc_clean.csv")


def test_canonical_coordinate_not_averaged(source_data):
    records, lookup = source_data
    records.loc[0, "latitude"] += .0001
    annual, canonical, _, _ = prepare_data(records, lookup)
    intersection_id = canonical.loc[canonical.municipality.eq("VANCOUVER"), "intersection_id"].iloc[0]
    assert annual.loc[annual.intersection_id.eq(intersection_id), "latitude"].eq(49.25).all()
