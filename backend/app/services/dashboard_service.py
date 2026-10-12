from sqlalchemy.orm import Session
from datetime import datetime, date, time, timedelta, timezone
from typing import List
from backend.app.models.entities import Task, StudySession
from backend.app.schemas.schemas import DashboardSummaryResponse, WeeklyProgressPoint
from backend.app.services.task_service import TaskService
from backend.app.services.session_service import SessionService
from backend.app.services.profile_service import ProfileService


class DashboardService:
    @staticmethod
    def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
        profile = ProfileService.get_or_create_profile(db)
        now_utc = datetime.now(timezone.utc)
        today_date = now_utc.date()

        # 1. Today's sessions
        today_start = datetime.combine(today_date, time.min, tzinfo=timezone.utc)
        today_end = datetime.combine(today_date, time.max, tzinfo=timezone.utc)

        today_sessions = SessionService.list_sessions(
            db=db,
            start_time=today_start,
            end_time=today_end
        )

        # 2. Tasks due soon (within next 3 days)
        three_days_later = now_utc + timedelta(days=3)
        due_soon_db = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"]),
            Task.due_at >= now_utc,
            Task.due_at <= three_days_later
        ).order_by(Task.due_at.asc()).all()
        tasks_due_soon = [TaskService._to_response(t, db) for t in due_soon_db]

        # 3. Overdue tasks
        overdue_db = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"]),
            Task.due_at < now_utc
        ).order_by(Task.due_at.asc()).all()
        overdue_tasks = [TaskService._to_response(t, db) for t in overdue_db]

        # 4. Counts
        pending_count = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"])
        ).count()
        completed_count = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status == "Completed"
        ).count()

        # 5. Total planned & completed study minutes
        all_sessions = db.query(StudySession).join(Task).filter(
            Task.profile_id == profile.id
        ).all()

        total_planned_minutes = 0
        total_completed_minutes = 0
        for s in all_sessions:
            dur = int((s.end_at - s.start_at).total_seconds() / 60)
            if s.status != "Skipped":
                total_planned_minutes += dur
            if s.status == "Completed":
                total_completed_minutes += (s.actual_duration_minutes if s.actual_duration_minutes is not None else dur)

        # 6. Weekly progress (last 3 days, today, next 3 days = 7 days total)
        weekly_progress: List[WeeklyProgressPoint] = []
        for offset in range(-3, 4):
            day_d = today_date + timedelta(days=offset)
            d_start = datetime.combine(day_d, time.min, tzinfo=timezone.utc)
            d_end = datetime.combine(day_d, time.max, tzinfo=timezone.utc)

            day_sessions = []
            for s in all_sessions:
                s_st = s.start_at if s.start_at.tzinfo is not None else s.start_at.replace(tzinfo=timezone.utc)
                if d_start <= s_st <= d_end:
                    day_sessions.append(s)

            p_mins = sum(
                int((s.end_at - s.start_at).total_seconds() / 60)
                for s in day_sessions if s.status != "Skipped"
            )
            c_mins = sum(
                (s.actual_duration_minutes if s.actual_duration_minutes is not None else int((s.end_at - s.start_at).total_seconds() / 60))
                for s in day_sessions if s.status == "Completed"
            )

            weekly_progress.append(WeeklyProgressPoint(
                day=day_d.strftime("%a"),
                date=day_d.strftime("%Y-%m-%d"),
                planned_minutes=p_mins,
                completed_minutes=c_mins
            ))

        return DashboardSummaryResponse(
            today_sessions=today_sessions,
            tasks_due_soon=tasks_due_soon,
            overdue_tasks=overdue_tasks,
            pending_tasks_count=pending_count,
            completed_tasks_count=completed_count,
            total_planned_minutes=total_planned_minutes,
            total_completed_minutes=total_completed_minutes,
            weekly_progress=weekly_progress
        )
