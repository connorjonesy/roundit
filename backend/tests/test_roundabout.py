import numpy as np
import pytest

from backend.ml.prepare_data import make_features, prepare_data
from backend.ml.roundabout import assess_roundabout
from backend.ml.simulate import generate_scenarios, simulate_intersection, validate_scenarios
from backend.ml.train_model import train_and_evaluate


@pytest.mark.parametrize("control,design,after,prevented", [
    ("signalized", "single-lane", 14.2, 5.8),
    ("signalized", "multi-lane", 16.6, 3.4),
    ("stop-controlled", "one-lane", 15.2, 4.8),
    ("stop-controlled", "two-lane", 17.8, 2.2),
])
def test_verified_factors(control, design, after, prevented):
    assessment = assess_roundabout(20, control, design)
    assert assessment["expected_after"] == pytest.approx(after)
    assert assessment["collisions_prevented"] == pytest.approx(prevented)
    assert assessment["reduction_percent"] == pytest.approx(prevented / 20 * 100)
    assert assessment["cmf_source"].endswith("cmfs_for_bc_2008.pdf")


@pytest.mark.parametrize("count", [-1, np.nan, np.inf, True, "20", None])
def test_invalid_count(count):
    with pytest.raises(ValueError):
        assess_roundabout(count, "signalized", "single-lane")


@pytest.mark.parametrize("control,design", [
    ("all-way-stop", "one-lane"), ("unknown", "single-lane"),
    ("signalized", "two-lane"), ("stop-controlled", "multi-lane"), (None, "single-lane"),
])
def test_unsupported_conversion(control, design):
    with pytest.raises(ValueError):
        assess_roundabout(20, control, design)


def test_scenario_identity_uniqueness_and_saved_prediction(source_data):
    annual, _, _, _ = prepare_data(*source_data)
    _, predictions, _ = train_and_evaluate(make_features(annual))
    scenarios = generate_scenarios(predictions)
    assert len(scenarios) == 4 * len(predictions)
    assert set(scenarios.scenario_type) == {"hypothetical"}
    row = predictions.iloc[0]
    single = simulate_intersection(predictions, row.intersection_id, "signalized", "single-lane")
    assert single["latitude"] == row.latitude
    assert single["longitude"] == row.longitude
    assert single["intersection_name"] == row.intersection_name
    assert single["expected_after"] == pytest.approx(row.predicted_crashes * .71)
    with pytest.raises(ValueError):
        simulate_intersection(predictions, "missing-id", "signalized", "single-lane")
    scenarios.loc[0, "latitude"] += .001
    with pytest.raises(ValueError):
        validate_scenarios(scenarios, predictions)


def test_zero_fractional_counts():
    assert assess_roundabout(0, "signalized", "single-lane")["expected_after"] == 0
    assert assess_roundabout(1.5, "signalized", "single-lane")["expected_after"] == pytest.approx(1.065)
