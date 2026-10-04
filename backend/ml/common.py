"""Shared paths and checks for local CSV outputs."""

from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / "data"
PROCESSED = DATA / "processed"
OUTPUT = DATA / "output"
MODELS = BACKEND / "models"
IDENTITY = ["intersection_id", "intersection_name", "latitude", "longitude"]
FEATURES = ["last_year", "avg_2yr"]
YEARS = [2018, 2019, 2020, 2021, 2022]
# Approximate Metro Vancouver plausibility rectangle, not an official boundary.
BOUNDS = (-123.5, 49.0, -122.3, 49.6)


def coordinate_mask(frame):
    lat = pd.to_numeric(frame["latitude"], errors="coerce")
    lon = pd.to_numeric(frame["longitude"], errors="coerce")
    west, south, east, north = BOUNDS
    return (np.isfinite(lat) & np.isfinite(lon)
            & lat.between(-90, 90) & lon.between(-180, 180)
            & lat.between(south, north) & lon.between(west, east))


def validate_identity(frame):
    if frame.empty:
        raise ValueError("No geographically identifiable intersections remain")
    for column in IDENTITY[:2]:
        values = frame[column].astype("string")
        if values.isna().any() or values.str.strip().eq("").any():
            raise ValueError(f"Missing {column}")
    if not coordinate_mask(frame).all():
        raise ValueError("Invalid, reversed or implausible WGS84 coordinates")
    if frame[IDENTITY].drop_duplicates().duplicated("intersection_id").any():
        raise ValueError("Conflicting name or coordinates for an intersection ID")


def validate_predictions(frame):
    validate_identity(frame)
    if frame.duplicated(["intersection_id", "prediction_year"]).any():
        raise ValueError("Duplicate intersection-year prediction")
    for column in ["predicted_crashes", "actual_crashes"]:
        values = pd.to_numeric(frame[column], errors="coerce")
        if not (np.isfinite(values) & values.ge(0)).all():
            raise ValueError(f"Invalid {column}")


def save_csv(frame, path):
    """Never allow an output to replace one of the three source datasets."""
    path = Path(path).resolve()
    if path in { (DATA / name).resolve() for name in
                 ["icbc_clean.csv", "intersections.csv", "icbc_review.csv"] }:
        raise ValueError("Cannot overwrite an existing cleaned dataset")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")
