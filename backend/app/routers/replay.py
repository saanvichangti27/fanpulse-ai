from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...ingestion.replay import ReplayController
from ...ingestion import service as ingestion_service

router = APIRouter()
replay_ctrl = ReplayController()


class ReplayControlRequest(BaseModel):
    action: str                      # "start" | "stop"
    match_id: str
    file: str = "replay_dev_fixture.json"
    speed: Optional[float] = 1.0


@router.post("/replay/control")
async def replay_control(req: ReplayControlRequest):
    if ingestion_service.INGESTION_QUEUE is None:
        raise HTTPException(status_code=503, detail="Ingestion service not started yet")
    if req.action == "start":
        replay_ctrl.start(req.match_id, req.file, req.speed, ingestion_service.INGESTION_QUEUE)
    elif req.action == "stop":
        replay_ctrl.stop(req.match_id)
    else:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR: action must be start|stop")
    return {"accepted": True}
