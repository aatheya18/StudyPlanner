from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
from backend.app.models.entities import Task, StudySession
from backend.app.schemas.schemas import ReminderItem, RemindersResponse
from backend.app.services.profile_service import ProfileService


class ReminderService:
    @staticmethod
    def get_reminders(db: Session) -> RemindersResponse:
        profile = ProfileService.get_or_create_profile(db)
        now_utc = datetime.now(timezone.utc)
        items: List[ReminderItem] = []

        # 1. Upcoming scheduled sessions (within next 4 hours)
        upcoming_window = now_utc + timedelta(hours=4)
        sessions = db.query(StudySession).join(Task).filter(
            Task.profile_id == profile.id,
            StudySession.status == "Scheduled",
            StudySession.start_at >= now_utc,
            StudySession.start_at <= upcoming_window
        ).order_by(StudySession.start_at.asc()).all()

        for s in sessions:
            diff_mins = int((s.start_at - now_utc).total_seconds() / 60)
            items.append(ReminderItem(
                id=f"session-{s.id}",
                type="upcoming_session",
                title=f"Study Session: {s.task.title}",
                message=f"Starts in {diff_mins} minutes ({s.start_at.strftime('%H:%M')}).",
                due_or_start_at=s.start_at,
                urgency="high" if diff_mins <= 30 else "medium",
                entity_id=s.id
            ))

        # 2. Approaching deadlines (due within next 24 hours)
        next_24h = now_utc + timedelta(hours=24)
        due_soon_tasks = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"]),
            Task.due_at >= now_utc,
            Task.due_at <= next_24h
        ).order_by(Task.due_at.asc()).all()

        for t in due_soon_tasks:
            hours_left = max(0, int((t.due_at - now_utc).total_seconds() / 3600))
            items.append(ReminderItem(
                id=f"deadline-{t.id}",
                type="approaching_deadline",
                title=f"Deadline Approaching: {t.title}",
                message=f"Due in ~{hours_left} hours ({t.due_at.strftime('%b %d, %H:%M')}).",
                due_or_start_at=t.due_at,
                urgency="high" if hours_left <= 6 else "medium",
                entity_id=t.id
            ))

        # 3. Overdue tasks
        overdue_tasks = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"]),
            Task.due_at < now_utc
        ).order_by(Task.due_at.asc()).all()

        for t in overdue_tasks:
            hours_overdue = int((now_utc - t.due_at).total_seconds() / 3600)
            items.append(ReminderItem(
                id=f"overdue-{t.id}",
                type="overdue_task",
                title=f"Overdue Task: {t.title}",
                message=f"Task was due {hours_overdue} hours ago ({t.due_at.strftime('%b %d, %H:%M')}).",
                due_or_start_at=t.due_at,
                urgency="high",
                entity_id=t.id
            ))

        return RemindersResponse(reminders=items, count=len(items))
