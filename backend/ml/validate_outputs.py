"""Read exports back and check source identity, history, predictions and CMFs."""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from .common import DATA, FEATURES, IDENTITY, MODELS, OUTPUT, PROCESSED, validate_identity, validate_predictions
from .prepare_data import make_features, prepare_data
from .simulate import validate_scenarios
from .train_model import select_method


def main():
    evaluation = json.loads((OUTPUT / "evaluation.json").read_text())
    expected_hashes = evaluation["preparation"]["input_sha256"]
    for name, digest in expected_hashes.items():
        if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Source changed since preparation: {name}; rerun the pipeline")
    records = pd.read_csv(DATA / "icbc_clean.csv", dtype={"intersection_id": "string"})
    source_lookup = pd.read_csv(DATA / "intersections.csv", dtype={"intersection_id": "string"})
    expected_annual, expected_lookup, _, _ = prepare_data(records, source_lookup)
    lookup = pd.read_csv(PROCESSED / "intersection_lookup.csv", dtype={"intersection_id": "string"})
    annual = pd.read_csv(PROCESSED / "intersection_year.csv", dtype={"intersection_id": "string"})
    features = pd.read_csv(PROCESSED / "ml_features.csv", dtype={"intersection_id": "string"})
    predictions = pd.read_csv(OUTPUT / "predictions_2022.csv", dtype={"intersection_id": "string"})
    scenarios = pd.read_csv(OUTPUT / "roundabout_scenarios_2022.csv", dtype={"intersection_id": "string"})
    pd.testing.assert_frame_equal(lookup, expected_lookup.reset_index(drop=True), check_dtype=False)
    pd.testing.assert_frame_equal(annual, expected_annual, check_dtype=False)
    pd.testing.assert_frame_equal(features, make_features(annual), check_dtype=False)
    validate_predictions(predictions)
    validate_scenarios(scenarios, predictions)
    for frame in [annual, features, predictions, scenarios]:
        validate_identity(frame)
        joined = frame.merge(lookup[IDENTITY], on="intersection_id", how="left",
                             validate="many_to_one", suffixes=("", "_lookup"))
        for column in IDENTITY[1:]:
            if not joined[column].eq(joined[column + "_lookup"]).all():
                raise ValueError(f"Export differs from canonical {column}")
    method = evaluation["selected_prediction_method"]
    if method != select_method(evaluation["validation_mae"]):
        raise ValueError("Method was not selected by validation MAE")
    if evaluation["saved_model_training_target_years"] != [2020, 2021]:
        raise ValueError("Historical model must exclude 2022 targets")
    test = features.loc[features.year.eq(2022)].set_index("intersection_id")
    if set(test.index) != set(predictions.intersection_id):
        raise ValueError("Prediction cohort differs from eligible test cohort")
    ordered = test.loc[predictions.intersection_id]
    if not predictions.prediction_year.eq(2022).all() or not predictions.prediction_method.eq(method).all():
        raise ValueError("Incorrect exported year or method")
    if not predictions.model_version.eq(evaluation["model_version"]).all():
        raise ValueError("Incorrect exported version")
    model = joblib.load(MODELS / "crash_model.joblib")
    history = features.loc[features.year.isin([2020, 2021])]
    np.testing.assert_allclose(model[0].mean_, history[FEATURES].mean())
    expected = model.predict(ordered[FEATURES]) if method == "poisson" else ordered[method].to_numpy()
    np.testing.assert_allclose(predictions.predicted_crashes, expected, rtol=1e-10)
    np.testing.assert_array_equal(predictions.actual_crashes, ordered.crash_count)
    if len(scenarios) != 4 * len(predictions):
        raise ValueError("Expected four hypothetical conversions per intersection")
    report = {"checks_passed": ["input SHA256 unchanged", "annual source aggregation",
                                "canonical identity and geography", "historical feature lags",
                                "validation-based selection", "saved scaler training years",
                                "saved predictions and actual counts", "scenario uniqueness and CMF arithmetic"],
              "intersections": len(predictions), "annual_rows": len(annual),
              "feature_rows": len(features), "scenario_rows": len(scenarios),
              "input_sha256": expected_hashes}
    (OUTPUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
