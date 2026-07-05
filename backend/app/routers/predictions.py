from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...contracts import AudienceForecast
from ..stubs_intelligence import get_audience_forecast_stub

router = APIRouter()

class ReforecastRequest(BaseModel):
    match_id: str

@router.get("/matches/{match_id}/forecast", response_model=AudienceForecast)
def get_forecast(match_id: str):
    return get_audience_forecast_stub(match_id)

@router.post("/forecast/reforecast", response_model=AudienceForecast)
def reforecast(req: ReforecastRequest):
    return get_audience_forecast_stub(req.match_id)
