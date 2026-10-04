#holds our pydantic models
#Something like dis
from typing import Literal
from pydantic import BaseModel

# ---------- Map dots: GET /intersections ----------

class IntersectionProps(BaseModel):
    id: int
    name: str | None = None
    score: float | None = None   # roundabout_score, used to color/size the dot

class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]   # (lng, lat)

class IntersectionFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: IntersectionProps

class IntersectionCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[IntersectionFeature]

# ---------- Report: GET /intersections/{id} ----------

class Metrics(BaseModel):
    # PLACEHOLDERS: rename/replace to match whatever your ingest script writes
    roundabout_score: float | None = None      # 0-100 overall benefit
    crash_count: int | None = None
    injury_crash_count: int | None = None
    avg_daily_traffic: int | None = None
    est_delay_reduction_pct: float | None = None
    est_crash_reduction_pct: float | None = None

class IntersectionReport(BaseModel):
    id: int
    name: str | None = None
    lat: float
    lng: float
    street_count: int
    metrics: Metrics
