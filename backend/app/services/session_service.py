from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.models.entities import StudySession, Task
from backend.app.schemas.schemas import StudySessionUpdate, StudySessionResponse, StudySessionCompleteRequest
from backend.app.scheduling.constraints import is_overlapping
from backend.app.services.profile_service import ProfileService


class SessionService:
    @staticmethod
    def _to_response(s: StudySession) -> StudySessionResponse:
        return StudySessionResponse(
            id=s.id,
            task_id=s.task_id,
            start_at=s.start_at,
            end_at=s.end_at,
            status=s.status,
            actual_duration_minutes=s.actual_duration_minutes,
            created_at=s.created_at,
            updated_at=s.updated_at,
            task_title=s.task.title if s.task else None,
            subject_name=s.task.subject.name if s.task and s.task.subject else None,
            subject_color=s.task.subject.color if s.task and s.task.subject else "#3B82F6"
        )

    @staticmethod
    def list_sessions(
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        task_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[StudySessionResponse]:
        profile = ProfileService.get_or_create_profile(db)
        query = db.query(StudySession).join(Task).filter(Task.profile_id == profile.id)

        if task_id is not None:
            query = query.filter(StudySession.task_id == task_id)
        if status_filter:
            query = query.filter(StudySession.status == status_filter)
        if start_time:
            query = query.filter(StudySession.end_at >= start_time)
        if end_time:
            query = query.filter(StudySession.start_at <= end_time)

        sessions = query.order_by(StudySession.start_at.asc()).all()
        return [SessionService._to_response(s) for s in sessions]

    @staticmethod
    def get_session(db: Session, session_id: int) -> StudySession:
        profile = ProfileService.get_or_create_profile(db)
        session = db.query(StudySession).join(Task).filter(
            StudySession.id == session_id,
            Task.profile_id == profile.id
        ).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Study session with ID {session_id} not found.")
        return session

    @staticmethod
    def update_session(db: Session, session_id: int, data: StudySessionUpdate) -> StudySessionResponse:
        session = SessionService.get_session(db, session_id)

        new_start = data.start_at if data.start_at is not None else session.start_at
        new_end = data.end_at if data.end_at is not None else session.end_at

        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session end time must be after start time."
            )

        # Check deadline
        task = session.task
        task_due = task.due_at if task.due_at.tzinfo is not None else task.due_at.replace(tzinfo=timezone.utc)
        check_end = new_end if new_end.tzinfo is not None else new_end.replace(tzinfo=timezone.utc)
        if check_end > task_due:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session cannot be scheduled after task deadline {task_due.isoformat()}."
            )

        # Check collision with other sessions
        other_sessions = db.query(StudySession).filter(
            StudySession.id != session.id,
            StudySession.status != "Skipped"
        ).all()
        for os in other_sessions:
            os_start = os.start_at if os.start_at.tzinfo is not None else os.start_at.replace(tzinfo=timezone.utc)
            os_end = os.end_at if os.end_at.tzinfo is not None else os.end_at.replace(tzinfo=timezone.utc)
            check_start = new_start if new_start.tzinfo is not None else new_start.replace(tzinfo=timezone.utc)
            if is_overlapping(check_start, check_end, os_start, os_end):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session overlaps with another session ({os_start.strftime('%Y-%m-%d %H:%M')} - {os_end.strftime('%H:%M')})."
                )

        session.start_at = new_start
        session.end_at = new_end
        if data.status is not None:
            session.status = data.status
        if data.actual_duration_minutes is not None:
            session.actual_duration_minutes = data.actual_duration_minutes

        db.commit()
        db.refresh(session)
        return SessionService._to_response(session)

    @staticmethod
    def complete_session(db: Session, session_id: int, req: StudySessionCompleteRequest) -> StudySessionResponse:
        session = SessionService.get_session(db, session_id)
        session.status = "Completed"
        if req.actual_duration_minutes is not None:
            session.actual_duration_minutes = req.actual_duration_minutes
        else:
            session.actual_duration_minutes = int((session.end_at - session.start_at).total_seconds() / 60)

        # Update task status if explicitly requested or if all task sessions are completed
        task = session.task
        if req.mark_task_completed:
            task.status = "Completed"
        elif task.status == "Pending":
            task.status = "In Progress"

        db.commit()
        db.refresh(session)
        return SessionService._to_response(session)

    @staticmethod
    def skip_session(db: Session, session_id: int) -> StudySessionResponse:
        session = SessionService.get_session(db, session_id)
        session.status = "Skipped"
        db.commit()
        db.refresh(session)
        return SessionService._to_response(session)

    @staticmethod
    def delete_session(db: Session, session_id: int) -> None:
        session = SessionService.get_session(db, session_id)
        db.delete(session)
        db.commit()
