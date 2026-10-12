from sqlalchemy.orm import Session
from datetime import datetime, date, timezone
from typing import Optional
from backend.app.models.entities import Task, StudySession, AvailabilityWindow, StudyPreference
from backend.app.schemas.schemas import ScheduleGenerateRequest, ScheduleGenerateResponse, StudySessionResponse, UnscheduledTaskInfo
from backend.app.scheduling.engine import generate_rule_based_schedule
from backend.app.services.profile_service import ProfileService


class SchedulingService:
    @staticmethod
    def generate_schedule(db: Session, req: ScheduleGenerateRequest) -> ScheduleGenerateResponse:
        profile = ProfileService.get_or_create_profile(db)
        pref = ProfileService.get_preferences(db)
        avail = ProfileService.get_availability_windows(db)

        now_utc = datetime.now(timezone.utc)
        start_date = req.start_date if req.start_date else now_utc.date()

        # If clear_existing_scheduled is True, clear upcoming sessions with status 'Scheduled'
        if req.clear_existing_scheduled:
            task_ids = [t.id for t in db.query(Task.id).filter(Task.profile_id == profile.id).all()]
            if task_ids:
                db.query(StudySession).filter(
                    StudySession.task_id.in_(task_ids),
                    StudySession.status == "Scheduled",
                    StudySession.start_at >= now_utc
                ).delete(synchronize_session=False)
                db.commit()

        # Retrieve incomplete tasks
        tasks = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"])
        ).all()

        # Retrieve any currently preserved sessions
        existing_sessions = db.query(StudySession).join(Task).filter(
            Task.profile_id == profile.id
        ).all()

        result = generate_rule_based_schedule(
            tasks=tasks,
            availability_windows=avail,
            preference=pref,
            existing_sessions=existing_sessions,
            start_date=start_date,
            horizon_days=req.horizon_days,
            reference_time=now_utc
        )

        # Persist generated sessions
        created_responses = []
        for s_data in result["sessions_created"]:
            session = StudySession(
                task_id=s_data["task_id"],
                start_at=s_data["start_at"],
                end_at=s_data["end_at"],
                status="Scheduled"
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            created_responses.append(StudySessionResponse(
                id=session.id,
                task_id=session.task_id,
                start_at=session.start_at,
                end_at=session.end_at,
                status=session.status,
                actual_duration_minutes=None,
                created_at=session.created_at,
                updated_at=session.updated_at,
                task_title=s_data["task_title"],
                subject_name=s_data["subject_name"],
                subject_color=s_data["subject_color"]
            ))

        unscheduled_list = [
            UnscheduledTaskInfo(
                task_id=u["task_id"],
                title=u["title"],
                reason=u["reason"]
            )
            for u in result["unscheduled_tasks"]
        ]

        return ScheduleGenerateResponse(
            sessions_created=created_responses,
            unscheduled_tasks=unscheduled_list,
            total_slots_used_minutes=result["total_slots_used_minutes"],
            message=result["message"]
        )
