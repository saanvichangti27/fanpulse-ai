from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ReplayControlRequest(BaseModel):
    action: str
    match_id: str
    file: str
    speed: Optional[float] = 1.0

@router.post("/replay/control")
def replay_control(req: ReplayControlRequest):
    # This will call W1's ReplayController
    return {"accepted": True}
