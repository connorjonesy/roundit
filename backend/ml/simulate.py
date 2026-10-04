"""Attach explicit hypothetical conversions to saved historical predictions."""

import argparse

import numpy as np
import pandas as pd

from .common import OUTPUT, save_csv, validate_identity, validate_predictions
from .roundabout import CMFS, assess_roundabout

SCENARIO_KEY = ["intersection_id", "prediction_year", "control_type", "roundabout_type"]


def simulate_intersection(predictions, intersection_id, control_type, roundabout_type, prediction_year=2022):
    """Retrieve exactly one saved prediction and apply an explicit assumption."""
    validate_predictions(predictions)
    found = predictions.loc[predictions.intersection_id.eq(intersection_id)
                            & predictions.prediction_year.eq(prediction_year)]
    if len(found) != 1:
        raise ValueError("Expected one saved prediction for that intersection/year")
    prediction = found.iloc[0].to_dict()
    prediction.pop("actual_crashes", None)
    return {**prediction, "control_type": control_type, "roundabout_type": roundabout_type,
            **assess_roundabout(prediction["predicted_crashes"], control_type, roundabout_type),
            "scenario_type": "hypothetical"}


def validate_scenarios(scenarios, predictions):
    validate_identity(scenarios)
    validate_predictions(predictions)
    if scenarios.duplicated(SCENARIO_KEY).any():
        raise ValueError("Duplicate conversion scenario")
    comparison = scenarios.merge(predictions, on=["intersection_id", "prediction_year"],
                                  how="left", suffixes=("", "_prediction"), validate="many_to_one", indicator=True)
    if comparison._merge.ne("both").any():
        raise ValueError("Scenario has no corresponding saved prediction")
    for column in ["intersection_name", "latitude", "longitude", "predicted_crashes", "prediction_method", "model_version"]:
        if not comparison[column].eq(comparison[column + "_prediction"]).all():
            raise ValueError(f"Scenario changed prediction {column}")
    for row in scenarios.to_dict("records"):
        expected = assess_roundabout(row["predicted_crashes"], row["control_type"], row["roundabout_type"])
        for column in ["cmf", "expected_after", "collisions_prevented", "reduction_percent"]:
            if not np.isfinite(row[column]) or not np.isclose(row[column], expected[column], rtol=1e-10, atol=1e-10):
                raise ValueError(f"Invalid scenario calculation: {column}")
        if row["scenario_type"] != "hypothetical":
            raise ValueError("This source has no verified control types; scenarios must be hypothetical")


def generate_scenarios(predictions):
    validate_predictions(predictions)
    # No controls exist in the supplied files. Never infer them from crash totals.
    rows = []
    for prediction in predictions.to_dict("records"):
        prediction.pop("actual_crashes", None)
        for control, design in CMFS:
            rows.append({**prediction, "control_type": control, "roundabout_type": design,
                         **assess_roundabout(prediction["predicted_crashes"], control, design),
                         "scenario_type": "hypothetical"})
    scenarios = pd.DataFrame(rows)
    validate_scenarios(scenarios, predictions)
    return scenarios


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intersection-id", help="Optional single-intersection demonstration")
    parser.add_argument("--control-type", choices=["signalized", "stop-controlled"])
    parser.add_argument("--roundabout-type", choices=["single-lane", "multi-lane", "one-lane", "two-lane"])
    args = parser.parse_args()
    predictions = pd.read_csv(OUTPUT / "predictions_2022.csv", dtype={"intersection_id": "string"})
    if args.intersection_id:
        if not args.control_type or not args.roundabout_type:
            parser.error("Single-intersection scenario requires --control-type and --roundabout-type")
        print(simulate_intersection(predictions, args.intersection_id, args.control_type, args.roundabout_type))
        return
    if args.control_type or args.roundabout_type:
        parser.error("Supply --intersection-id for a single scenario")
    scenarios = generate_scenarios(predictions)
    save_csv(scenarios, OUTPUT / "roundabout_scenarios_2022.csv")
    print(f"Exported {len(scenarios):,} hypothetical scenarios for {predictions.intersection_id.nunique():,} intersections")


if __name__ == "__main__":
    main()
