"""Convert the cleaned intersection summaries to MapLibre GeoJSON (stdlib only)."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'backend/data/intersections.csv'
OUTPUT = ROOT / 'frontend/public/data/intersections.geojson'


def export():
    if not SOURCE.exists():
        raise SystemExit('Missing backend/data/intersections.csv. Run backend/ingest/clean_icbc.py first.')
    features = []
    with SOURCE.open(newline='', encoding='utf-8') as source:
        for number, row in enumerate(csv.DictReader(source), start=2):
            try:
                lng, lat = float(row['longitude']), float(row['latitude'])
                if not (math.isfinite(lng) and math.isfinite(lat) and -180 <= lng <= 180 and -90 <= lat <= 90):
                    raise ValueError('invalid coordinates')
                counts = {key: int(row[key]) for key in ['total_crashes', 'pedestrian_crashes', 'cyclist_crashes']}
                if counts['total_crashes'] <= 0 or any(value < 0 or value > counts['total_crashes'] for value in counts.values()):
                    raise ValueError('invalid crash counts')
                start, end = int(row['period_start_year']), int(row['period_end_year'])
                if start > end:
                    raise ValueError('invalid reporting period')
                properties = dict(counts, name=f"{row['road_a']} & {row['road_b']}",
                                  municipality=row['municipality'], period_start_year=start,
                                  period_end_year=end, shared_coordinate=row['shared_coordinate'].lower() == 'true')
                features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [lng, lat]},
                                 'properties': properties})
            except (KeyError, ValueError) as error:
                raise SystemExit(f'Invalid intersection CSV row {number}: {error}') from error
    if not features:
        raise SystemExit('No intersection summaries to export.')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({'type': 'FeatureCollection', 'features': features},
                                 indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'Exported {len(features):,} intersection points to {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    export()
