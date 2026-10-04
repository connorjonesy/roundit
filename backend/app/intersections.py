#example
from fastapi import APIRouter, HTTPException, Request
from schemas import IntersectionCollection, IntersectionReport
##^^ our pydantic models


router = APIRouter(prefix="/intersections", tags=["intersections"])

#not real yuet
@router.get("/{intersection_id}")
async def get_intersection(intersection_id: int, request: Request):
    row = await request.app.state.pool.fetchrow(
        "SELECT id, name, ST_Y(geom) AS lat, ST_X(geom) AS lng, street_count, metrics "
        "FROM intersections WHERE id = $1", intersection_id
    )
    if not row:
        raise HTTPException(404, "Intersection not found")
    return dict(row)
