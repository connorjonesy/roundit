#Example
import os
import osmnx as ox
import psycopg
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

load_dotenv()  # reads DATABASE_URL from .env
DATABASE_URL = os.environ["DATABASE_URL"]

# 1. Build intersections with OSMnx
G = ox.graph_from_place("Vancouver, British Columbia, Canada", network_type="drive")
G = ox.project_graph(G)
G = ox.consolidate_intersections(G, tolerance=15, rebuild_graph=True, dead_ends=False)
G = ox.project_graph(G, to_crs="EPSG:4326")
nodes, edges = ox.graph_to_gdfs(G)

nodes = nodes[nodes["street_count"] >= 3]

# 2. Build rows to insert
rows = []
for node_id, n in nodes.iterrows():
    name = None  # fill in from edges later (see note below)
    rows.append((name, int(n["street_count"]), float(n["x"]), float(n["y"]), Jsonb({})))

# 3. Write to Postgres
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE intersections RESTART IDENTITY")  # makes the script re-runnable
        cur.executemany(
            """
            INSERT INTO intersections (name, street_count, geom, metrics)
            VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
            """,
            rows,
        )
    conn.commit()

print(f"Inserted {len(rows)} intersections")
