import joblib
import numpy as np
import pandas as pd
import pytest

from backend.ml.common import FEATURES, validate_predictions
from backend.ml.prepare_data import make_features, prepare_data
from backend.ml.train_model import scores, select_method, split_years, train_and_evaluate


def test_metrics_and_validation_selection():
    assert scores([2, 6], {"last_year": np.array([1, 3]), "avg_2yr": np.array([2, 6])}) == {"last_year": 2, "avg_2yr": 0}
    assert select_method({"poisson": 2, "last_year": 1, "avg_2yr": 3}) == "last_year"
    assert select_method({"poisson": 1, "last_year": 2, "avg_2yr": 3}) == "poisson"
    assert select_method({"poisson": 1, "last_year": 1, "avg_2yr": 1}) == "last_year"


def test_chronological_fit_and_saved_model(source_data, tmp_path):
    annual, _, _, _ = prepare_data(*source_data)
    features = make_features(annual)
    training, validation, test = split_years(features)
    assert set(training.year) == {2020}
    assert set(validation.year) == {2021}
    assert set(test.year) == {2022}
    model, predictions, metadata = train_and_evaluate(features)
    validate_predictions(predictions)
    assert set(metadata["validation_mae"]) == {"poisson", "last_year", "avg_2yr"}
    assert metadata["selected_prediction_method"] == select_method(metadata["validation_mae"])
    assert metadata["saved_model_training_target_years"] == [2020, 2021]
    np.testing.assert_allclose(model[0].mean_, pd.concat([training, validation])[FEATURES].mean())
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    np.testing.assert_allclose(joblib.load(path).predict(test[FEATURES]), model.predict(test[FEATURES]))
    changed = features.copy()
    changed.loc[changed.year.eq(2022), "crash_count"] = 999999
    second_model, second_predictions, second_metadata = train_and_evaluate(changed)
    np.testing.assert_allclose(predictions.predicted_crashes, second_predictions.predicted_crashes)
    np.testing.assert_allclose(model[-1].coef_, second_model[-1].coef_)
    assert metadata["selected_prediction_method"] == second_metadata["selected_prediction_method"]
    assert metadata["test_mae"] != second_metadata["test_mae"]


def test_invalid_prediction_coordinates_and_counts(source_data):
    annual, _, _, _ = prepare_data(*source_data)
    _, predictions, _ = train_and_evaluate(make_features(annual))
    for column, value in [("predicted_crashes", -1), ("predicted_crashes", np.inf), ("latitude", -123.1)]:
        bad = predictions.copy()
        bad.loc[bad.index[0], column] = value
        with pytest.raises(ValueError):
            validate_predictions(bad)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_predictions(pd.concat([predictions, predictions.iloc[[0]]]))
