from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.app.db.database import get_db
from backend.app.schemas.schemas import ScheduleGenerateRequest, ScheduleGenerateResponse, StudySessionResponse
from backend.app.services.scheduling_service import SchedulingService
from backend.app.services.session_service import SessionService

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/generate", response_model=ScheduleGenerateResponse)
def generate_schedule(req: ScheduleGenerateRequest, db: Session = Depends(get_db)):
    return SchedulingService.generate_schedule(db, req)


@router.get("", response_model=List[StudySessionResponse])
def get_schedules(
    start: Optional[datetime] = Query(None, description="Start date/time"),
    end: Optional[datetime] = Query(None, description="End date/time"),
    db: Session = Depends(get_db)
):
    return SessionService.list_sessions(db=db, start_time=start, end_time=end)
