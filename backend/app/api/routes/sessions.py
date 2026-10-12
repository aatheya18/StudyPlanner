from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.app.db.database import get_db
from backend.app.schemas.schemas import StudySessionUpdate, StudySessionResponse, StudySessionCompleteRequest
from backend.app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[StudySessionResponse])
def list_sessions(
    start: Optional[datetime] = Query(None, description="Filter start date/time (inclusive)"),
    end: Optional[datetime] = Query(None, description="Filter end date/time (inclusive)"),
    task_id: Optional[int] = Query(None, description="Filter by task"),
    status: Optional[str] = Query(None, description="Filter by session status"),
    db: Session = Depends(get_db)
):
    return SessionService.list_sessions(
        db=db,
        start_time=start,
        end_time=end,
        task_id=task_id,
        status_filter=status
    )


@router.get("/{session_id}", response_model=StudySessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = SessionService.get_session(db, session_id)
    return SessionService._to_response(session)


@router.put("/{session_id}", response_model=StudySessionResponse)
def update_session(session_id: int, data: StudySessionUpdate, db: Session = Depends(get_db)):
    return SessionService.update_session(db, session_id, data)


@router.post("/{session_id}/complete", response_model=StudySessionResponse)
def complete_session(session_id: int, req: StudySessionCompleteRequest, db: Session = Depends(get_db)):
    return SessionService.complete_session(db, session_id, req)


@router.post("/{session_id}/skip", response_model=StudySessionResponse)
def skip_session(session_id: int, db: Session = Depends(get_db)):
    return SessionService.skip_session(db, session_id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    SessionService.delete_session(db, session_id)
    return None
