import pandas as pd
import pytest


@pytest.fixture
def source_data():
    lookup = pd.DataFrame([
        {"municipality": "VANCOUVER", "road_a": "A ST", "road_b": "B ST", "latitude": 49.25, "longitude": -123.1},
        {"municipality": "BURNABY", "road_a": "A ST", "road_b": "B ST", "latitude": 49.26, "longitude": -122.95},
    ])
    rows = []
    for i, place in enumerate(lookup.to_dict("records")):
        for year in range(2018, 2023):
            # Two rows with unequal counts: aggregation must sum, not count rows.
            for count in [year - 2017 + i * 10, 2]:
                rows.append({**place, "year": year, "crash_count": count})
    return pd.DataFrame(rows), lookup
