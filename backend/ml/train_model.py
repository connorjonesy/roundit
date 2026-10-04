"""Chronological evaluation against two historical baselines."""

import json

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .common import FEATURES, IDENTITY, MODELS, OUTPUT, PROCESSED, save_csv, validate_identity, validate_predictions

VERSION = "roundit-historical-v1"
METHODS = ["poisson", "last_year", "avg_2yr"]


def new_model():
    return make_pipeline(StandardScaler(), PoissonRegressor(alpha=1.0, max_iter=1000))


def split_years(features):
    validate_identity(features)
    if features.duplicated(["intersection_id", "year"]).any():
        raise ValueError("Duplicate feature observation")
    if set(features.year) != {2020, 2021, 2022}:
        raise ValueError("Expected feature targets 2020, 2021 and 2022")
    numeric = features[[*FEATURES, "crash_count"]].to_numpy(dtype=float)
    if not (np.isfinite(numeric) & (numeric >= 0)).all():
        raise ValueError("Features and targets must be finite and non-negative")
    splits = [features.loc[features.year.eq(year)].sort_values("intersection_id").copy()
              for year in [2020, 2021, 2022]]
    if not (set(splits[0].intersection_id) == set(splits[1].intersection_id) == set(splits[2].intersection_id)):
        raise ValueError("Each split must contain the same complete intersection cohort")
    return splits


def predict_methods(model, rows):
    predictions = {"poisson": model.predict(rows[FEATURES]),
                   "last_year": rows.last_year.to_numpy(),
                   "avg_2yr": rows.avg_2yr.to_numpy()}
    for values in predictions.values():
        if not (np.isfinite(values) & (values >= 0)).all():
            raise ValueError("Non-finite or negative prediction")
    return predictions


def scores(actual, predictions):
    return {name: float(mean_absolute_error(actual, values)) for name, values in predictions.items()}


def select_method(validation_scores):
    # Prefer a simple baseline on an exact tie; selection never reads test scores.
    return min(["last_year", "avg_2yr", "poisson"], key=lambda method: validation_scores[method])


def train_and_evaluate(features):
    training, validation, test = split_years(features)
    validation_model = new_model().fit(training[FEATURES], training.crash_count)
    validation_mae = scores(validation.crash_count, predict_methods(validation_model, validation))
    selected = select_method(validation_mae)
    historical_training = pd.concat([training, validation], ignore_index=True)
    # Test targets remain untouched until this pipeline has been fitted and chosen.
    evaluation_model = new_model().fit(historical_training[FEATURES], historical_training.crash_count)
    test_predictions = predict_methods(evaluation_model, test)
    test_mae = scores(test.crash_count, test_predictions)
    predictions = test[IDENTITY].copy()
    predictions["prediction_year"] = 2022
    predictions["predicted_crashes"] = test_predictions[selected]
    predictions["actual_crashes"] = test.crash_count.to_numpy()
    predictions["prediction_method"] = selected
    predictions["model_version"] = VERSION
    validate_predictions(predictions)
    # The cutoff uses training observations only, rather than the final targets.
    cutoff = float(training.last_year.median())
    strata = {}
    for label, mask in [("low", test.last_year <= cutoff), ("high", test.last_year > cutoff)]:
        strata[label] = {"intersections": int(mask.sum()),
                         "mae": scores(test.crash_count[mask], {k: v[mask.to_numpy()] for k, v in test_predictions.items()}) if mask.any() else {}}
    metadata = {
        "model_version": VERSION, "model_class": "StandardScaler + PoissonRegressor(alpha=1.0, max_iter=1000)",
        "package_versions": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__,
                             "numpy": np.__version__, "joblib": joblib.__version__},
        "feature_names": FEATURES, "selected_prediction_method": selected,
        "selection_rule": "lowest validation MAE; prefer baseline on exact ties",
        "validation_training_target_years": [2020], "validation_target_year": 2021,
        "saved_model_training_target_years": [2020, 2021], "test_target_year": 2022,
        "history_years": [2018, 2019, 2020, 2021],
        "validation_mae": validation_mae, "test_mae": test_mae,
        "intersections_evaluated": len(test), "training_observations": len(historical_training),
        "test_strata_previous_year_cutoff": cutoff, "test_strata": strata,
        "saved_model_role": "historical evaluation pipeline; not refitted on 2022 targets",
        "forecast_scope": "held-out historical 2022 predictions, not validated 2026 forecasts",
    }
    return evaluation_model, predictions, metadata


def main():
    features = pd.read_csv(PROCESSED / "ml_features.csv", dtype={"intersection_id": "string"})
    model, predictions, metadata = train_and_evaluate(features)
    preparation = OUTPUT / "preparation.json"
    if preparation.exists():
        metadata["preparation"] = json.loads(preparation.read_text())
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS / "crash_model.joblib")
    save_csv(predictions, OUTPUT / "predictions_2022.csv")
    (OUTPUT / "evaluation.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    print(f"{'Method':<15} {'Validation MAE':>16} {'Test MAE':>12}")
    for method in METHODS:
        print(f"{method:<15} {metadata['validation_mae'][method]:>16.4f} {metadata['test_mae'][method]:>12.4f}")
    print(f"Selected using validation: {metadata['selected_prediction_method']} ({len(predictions):,} intersections)")


if __name__ == "__main__":
    main()
