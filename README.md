# Roundit

#### Has this ever happened to you?

lorem ipsum


#### BUILD & DEV

### Dev environemnt

* serve the backend with uvicorn: `uvicorn main:app --reload`

* serve the frontend with vite: `npm run dev`

INGEST is run locally, not part of our deployment, ingest requirements are local only 

# requirements-ingest.txt

osmnx: pulls in geopandas, shapely, networkx, numpy, and pyproj

pandas: for loading and joining crash, traffic, or other CSV datasets onto intersections

psycopg[binary]: writes to postgres

python-dotenv: lets the ingest scripts read the same .env as the API

requests: pulling datasets from http source

To Ingest that crap locally, use a virtual environment

```
python3 -m venv .venv-ingest
source .venv-ingest/bin/activate
pip install -r requirements-ingest.txt
```

### PROD

* render backend

* frontend: `npm run build`


