import pytest

from backend.ml.prepare_data import make_features, prepare_data


def test_lags_are_per_intersection_and_use_only_history(source_data):
    annual, _, _, _ = prepare_data(*source_data)
    features = make_features(annual)
    assert len(features) == 6
    for intersection_id, group in annual.groupby("intersection_id"):
        counts = group.set_index("year").crash_count
        for row in features.loc[features.intersection_id.eq(intersection_id)].itertuples():
            assert row.last_year == counts[row.year - 1]
            assert row.avg_2yr == (counts[row.year - 1] + counts[row.year - 2]) / 2
    changed = annual.copy()
    changed.loc[changed.year.eq(2022), "crash_count"] = 9999
    assert make_features(changed)[["last_year", "avg_2yr"]].equals(features[["last_year", "avg_2yr"]])


def test_gaps_not_treated_as_previous_year(source_data):
    annual, _, _, _ = prepare_data(*source_data)
    annual = annual.loc[annual.year.ne(2020)]
    assert make_features(annual).empty


def test_duplicate_observations_rejected(source_data):
    annual, _, _, _ = prepare_data(*source_data)
    import pandas as pd
    with pytest.raises(ValueError, match="Duplicate"):
        make_features(pd.concat([annual, annual.iloc[[0]]]))
