from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.ingestion.replay import ReplayController
import backend.ingestion.service as ingestion_service

router = APIRouter()
replay_ctrl = ReplayController()

class ReplayControlRequest(BaseModel):
    action: str
    match_id: str
    file: str
    speed: Optional[float] = 1.0

@router.post("/replay/control")
async def replay_control(req: ReplayControlRequest):
    if req.action == "start":
        replay_ctrl.start(req.match_id, req.file, req.speed, ingestion_service.INGESTION_QUEUE)
    elif req.action == "stop":
        replay_ctrl.stop(req.match_id)
    return {"accepted": True}
