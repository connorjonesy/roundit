-- keep this as close to kaggle dataset as possible!!!

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS crashes (
  id SERIAL PRIMARY KEY,
  -- your Kaggle columns here: date, severity, crash_type, street names, etc.
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  geom GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS crashes_geom_idx ON crashes USING GIST (geom);
