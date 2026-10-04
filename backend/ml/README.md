# Local collision prediction experiment

Run everything from the repository root. This pipeline reads the existing local
CSVs; it does not download Kaggle data, read `.env`, connect to a database, run
FastAPI, modify the frontend, or deploy anything. Inputs are never overwritten.

## Run

Python 3.12 was used for the recorded results. Use the existing ingest environment,
or create a local environment first:

```bash
python3 -m venv .venv-ingest  # only if you do not already have it
source .venv-ingest/bin/activate
python -m pip install -r backend/requirements-ml.txt

python -m backend.ml.prepare_data
python -m backend.ml.train_model
python -m backend.ml.simulate
python -m backend.ml.validate_outputs
python -m pytest backend/tests -q
```

The first three commands regenerate only the new processed files, output files
and historical evaluation model. Training also exports the held-out predictions.
All processing and tests run offline once the dependencies are installed. The
existing ingest dependencies remain separate because this experiment does not
need Kaggle, a database driver or server dependencies.

For one explicit hypothetical assessment using an already saved prediction:

```bash
python -m backend.ml.simulate \
  --intersection-id 4ea8441d-794c-550b-b939-9339d61e66f6 \
  --control-type signalized \
  --roundabout-type single-lane
```

The single-intersection command prints the assessment without replacing the full
scenario export. `simulate_intersection()` is also available as a Python function.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `common.py` | Local paths, geographic checks, prediction validation, safe CSV writing |
| `prepare_data.py` | Exact geographic joins, diagnostics, annual aggregation, lag features |
| `train_model.py` | Chronological evaluation, baseline selection, saving the fitted pipeline |
| `roundabout.py` | Four documented urban CMFs and validated arithmetic |
| `simulate.py` | Retrieve predictions, generate explicit hypothetical scenarios, validate exports |
| `validate_outputs.py` | Read exports back; verify source hashes, identity, counts, history and scenarios |
| `../tests/` | Synthetic, local tests for joins, geography, leakage, evaluation and CMFs |

The simple constants at the top of each module control paths, features, experiment
years, geographic bounds, model parameters, version and CMFs. Functions operate
on DataFrames or numbers; there is no server, database abstraction or scheduler.

## Source data and geography

`backend/data/icbc_clean.csv` has 131,153 records with `year`, `crash_count`,
`municipality`, `road_a`, `road_b`, `latitude`, `longitude` and other collision
fields. A row carries a collision **count**, sometimes greater than one. Annual
counts are the sum of `crash_count`, not the number of rows. Similar-looking source
rows are not deduplicated because that could remove legitimate collisions.

`backend/data/intersections.csv` contains 5,540 canonical intersection summaries
with municipality, street pair, coordinates, period and all-years collision totals.
Only identity and geography are used from it; its aggregate totals are never ML
features or training targets. Neither CSV currently supplies an intersection ID
or verified traffic-control type.

The matching key is the **exact municipality plus sorted canonical street pair**
already produced by the cleaner. No fuzzy matching, name-only matching, or external
geocoding is performed. UUID5 identifiers are assigned once at preparation from
that complete key. They stay stable across reordered inputs and repeated runs.
`intersection_lookup.csv` records the mapping to the existing application data.
If canonical IDs later exist, they are preserved; if both inputs share
`intersection_id`, that ID is used for the join and the street/municipality identity
must still agree. Renaming a street can change a generated ID; preserve the mapping
when establishing permanent application/database IDs. These IDs are not claimed
to be existing database primary keys.

Lookup identity must be unique: duplicated IDs/ambiguous keys are rejected rather
than arbitrarily choosing a row. A `many_to_one` join cannot multiply observations.
Source coordinates must be valid and within 100 metres of the existing canonical
point. A conflicting observation excludes the entire intersection so its annual
counts are not silently reduced. Names/coordinates stay constant throughout.
Canonical coordinates are retained exactly rather than averaging source points.

The source geographic degree columns are reused as WGS84/EPSG:4326, consistent
with the existing map export; no projected coordinates or reprojection are used.
Values must be finite, within global latitude/longitude ranges, and within an
approximate Metro Vancouver rectangle: longitude -123.5 to -122.3, latitude 49.0
to 49.6. This is a plausibility check, not an official boundary or independent
survey of the supplied coordinates. The current cleaner has already restricted
the supplied data to Vancouver. Decimal precision is preserved in CSV exports.
MapLibre should construct **`[longitude, latitude]`**.

There must be observed records for **every year 2018–2022**. Missing years are not
filled with zero; reporting conventions have not been established to justify that.
Missing/invalid names, geography, counts and incomplete histories are logged in
`unmatched_intersections.csv`. It includes history exclusions as well as geographic
failures, with a `reason` column. Ambiguous or conflicting records never appear in
the main exports. Invalid fractional/negative source counts are rejected.

## Features and evaluation

Each intersection gets one annual row, sorted by ID then year. `groupby()` and
`shift()` produce only `last_year` and `avg_2yr`. Consecutive calendar-year checks
prevent accidentally treating a gap as last year's observation. IDs, names and
coordinates are metadata, never model inputs. After two years of history, target
years are 2020, 2021 and 2022.

1. Fit `StandardScaler` followed by `PoissonRegressor(alpha=1.0, max_iter=1000)`
   on targets from 2020. Evaluate it and both baselines on 2021.
2. Select the lowest validation MAE; prefer a baseline on an exact tie.
3. Fit a new pipeline using 2020 and 2021 target rows. Evaluate all methods once
   on 2022, and export predictions from the already selected method.

The scaler is fitted inside each pipeline using only that pipeline's training
rows. The 2022 features use 2020 and 2021 collision counts, never 2022 targets.
No final all-data refit is created. The saved Poisson pipeline is the historical
evaluation model even when a baseline supplies the exported predictions; therefore
calling its `predict()` directly does not reproduce baseline-selected exports.
`evaluation.json` records the chosen method, version, feature names, training years,
package versions, MAE, evaluated cohort and preparation statistics/input hashes.

Recorded results on the supplied files:

| Method | Validation 2021 MAE | Test 2022 MAE |
| --- | ---: | ---: |
| Poisson regression | 6.7685 | 7.5648 |
| Last-year baseline | **3.2933** | 3.5675 |
| Two-year baseline | 3.3464 | 3.4675 |

The last-year baseline is selected because it wins on **validation**, even though
the two-year baseline has lower test error. Test results do not change selection.
MAE is the average absolute error measured in annual collisions. The saved model
has 3,750 training rows (1,875 intersections times two target years).

Test errors are also reported for low/high prior-year collision groups, using a
cutoff of 7 derived from training history. The selected baseline's MAE is 2.2266
for the low group (1,156 intersections) and 5.7232 for the high group (719).

## Outputs

| Path under `backend/` | Contents |
| --- | --- |
| `data/processed/intersection_lookup.csv` | Stable IDs mapped to original municipality, roads, name and canonical coordinates |
| `data/processed/intersection_year.csv` | 9,375 observed annual rows, five per eligible intersection |
| `data/processed/ml_features.csv` | 5,625 rows with identifying geography, target counts and two historical features |
| `data/output/predictions_2022.csv` | 1,875 unique intersection/year predictions, actual counts, method and version |
| `data/output/roundabout_scenarios_2022.csv` | 7,500 scenarios: four explicit hypothetical assumptions per intersection |
| `data/output/unmatched_intersections.csv` | Records needing review or lacking complete histories, with reasons |
| `data/output/preparation.json` | Match/eligibility counts, diagnostic counts, CRS and source fingerprints |
| `data/output/evaluation.json` | Model/method metadata and actual evaluation results |
| `data/output/validation.json` | Results of the independent check of files read back from disk |
| `models/crash_model.joblib` | Fitted historical Poisson evaluation pipeline; no 2022 target refit |

All 5,540 source intersections matched canonical geographic coordinates. None
were excluded for geographic issues in this run. **1,875** have all five observed
years and enter the experiment; **3,665** lack complete histories and are excluded.
The exported scenario key is `(intersection_id, prediction_year, control_type,
roundabout_type)`. Four scenarios refer to one intersection, not four intersections.

## CMFs and interpretation

The factors were checked against the B.C. government's
[Collision Modification Factors for British Columbia (2008)](https://www2.gov.bc.ca/assets/gov/driving-and-transportation/transportation-infrastructure/engineering-standards-and-guidelines/traffic-engineering-and-safety/highway-safety/cmfs_for_bc_2008.pdf),
Exhibits 6.2–6.3, printed pages 99–100 (PDF pages 109–110). They concern urban
intersections and **all collisions combined**:

| Assumed existing control | Assumed roundabout | CMF |
| --- | --- | ---: |
| signalized | single-lane | 0.71 |
| signalized | multi-lane | 0.83 |
| stop-controlled | one-lane | 0.76 |
| stop-controlled | two-lane | 0.89 |

`expected_after = predicted_crashes * cmf`, `collisions_prevented = predicted_crashes
- expected_after`, and `reduction_percent = (1 - cmf) * 100`. Fractional counts are
expected values and are not rounded to integers. Each scenario includes its CMF
source and exhibit as well as the prediction's stable identity/geography.

No verified control field exists in these inputs. Every exported scenario is
explicitly `hypothetical`; controls are never inferred from collision totals.
The cited pages do not distinguish all-way-stop applicability, so a specific
`all-way-stop` input is rejected. A generic stop-controlled hypothetical assumption
does not verify applicability to a particular intersection. Before introducing
verified-input scenarios, supply documented urban control information and verify
that the chosen configuration satisfies the underlying treatment evidence.
Do not apply these total-collision factors separately to injury, cyclist or
pedestrian collisions or interpret four assumptions as one recommendation.

Example: **BOUNDARY RD & GRANDVIEW HWY, VANCOUVER**, ID
`4ea8441d-794c-550b-b939-9339d61e66f6`, latitude **49.258209**, longitude
**-123.023636**. The selected historical method predicts **200** collisions in
2022; the actual count is **204**. Assuming a signalized-to-single-lane conversion
gives **142** expected after, **58** prevented and **29%** reduction. This is an
explicit assumption, not verification of that intersection's traffic controls.

The cohort and canonical locations were curated retrospectively from all five
years. That eligibility/geographic selection can favor consistently reported
intersections; it is not a prospective deployment evaluation. COVID-era traffic
changes, lack of traffic exposure/road design features and only five source years
limit generalization. No uncertainty intervals, causal conversion study, or
construction/land-use/cost analysis is supplied. These are held-out **2022**
predictions, not validated forecasts for **2026**. Expected collision counts and
CMFs do not prove a roundabout should be built or establish feasibility.

The implementation's tests run entirely on synthetic local fixtures and include
source aggregation, stable IDs, municipal name collisions, join uniqueness,
conflicting/missing/reversed coordinates, missing years, feature leakage, scaler
training, validation selection, persistence, valid outputs and all four CMFs.
The recorded run passed **35 tests**. Joblib issued one local CPU-detection warning
and used the logical-core count; training and tests completed successfully.
