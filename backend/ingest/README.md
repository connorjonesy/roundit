# Processing ICBC Data

From the project root:

```bash
source .venv-ingest/bin/activate
python -m pip install -r backend/requirements-ingest.txt
python backend/ingest/clean_icbc.py
```

icbc_clean.csv:
* general intersection data

intersections.csv:
* combining all details into one row per intersection

icbc_reviews.csv:
* entries that have some missing information or not within bounds. Excluded from intersection data. We can look at these later. 
