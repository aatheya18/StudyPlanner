from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.models.entities import Task, Subject, StudySession
from backend.app.schemas.schemas import TaskCreate, TaskUpdate, TaskResponse
from backend.app.services.profile_service import ProfileService


class TaskService:
    @staticmethod
    def _to_response(task: Task, db: Session) -> TaskResponse:
        sched_mins = 0
        comp_mins = 0
        for s in task.sessions:
            dur = int((s.end_at - s.start_at).total_seconds() / 60)
            if s.status != "Skipped":
                sched_mins += dur
            if s.status == "Completed":
                comp_mins += (s.actual_duration_minutes if s.actual_duration_minutes is not None else dur)

        return TaskResponse(
            id=task.id,
            profile_id=task.profile_id,
            subject_id=task.subject_id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            due_at=task.due_at,
            earliest_start_at=task.earliest_start_at,
            estimated_duration_minutes=task.estimated_duration_minutes,
            priority=task.priority,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
            subject_name=task.subject.name if task.subject else None,
            subject_color=task.subject.color if task.subject else "#3B82F6",
            scheduled_duration_minutes=sched_mins,
            completed_duration_minutes=comp_mins
        )

    @staticmethod
    def list_tasks(
        db: Session,
        subject_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "due_at",  # due_at, priority, estimated_duration, created_at
        sort_order: Optional[str] = "asc"
    ) -> List[TaskResponse]:
        profile = ProfileService.get_or_create_profile(db)
        query = db.query(Task).filter(Task.profile_id == profile.id)

        if subject_id is not None:
            query = query.filter(Task.subject_id == subject_id)
        if status_filter:
            query = query.filter(Task.status == status_filter)
        if priority_filter:
            query = query.filter(Task.priority == priority_filter)
        if search:
            s_term = f"%{search}%"
            query = query.filter(or_(Task.title.ilike(s_term), Task.description.ilike(s_term)))

        # Sorting
        order_fn = desc if sort_order.lower() == "desc" else asc
        if sort_by == "priority":
            # Priority string sorting order: High > Medium > Low
            query = query.order_by(order_fn(Task.priority))
        elif sort_by == "estimated_duration":
            query = query.order_by(order_fn(Task.estimated_duration_minutes))
        elif sort_by == "created_at":
            query = query.order_by(order_fn(Task.created_at))
        else:
            query = query.order_by(order_fn(Task.due_at))

        tasks = query.all()
        return [TaskService._to_response(t, db) for t in tasks]

    @staticmethod
    def get_task(db: Session, task_id: int) -> Task:
        profile = ProfileService.get_or_create_profile(db)
        task = db.query(Task).filter(Task.id == task_id, Task.profile_id == profile.id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found.")
        return task

    @staticmethod
    def create_task(db: Session, data: TaskCreate) -> TaskResponse:
        profile = ProfileService.get_or_create_profile(db)
        # Verify subject belongs to profile
        subject = db.query(Subject).filter(Subject.id == data.subject_id, Subject.profile_id == profile.id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {data.subject_id} does not exist."
            )

        task = Task(
            profile_id=profile.id,
            subject_id=data.subject_id,
            title=data.title.strip(),
            description=data.description,
            task_type=data.task_type,
            due_at=data.due_at,
            earliest_start_at=data.earliest_start_at,
            estimated_duration_minutes=data.estimated_duration_minutes,
            priority=data.priority,
            status=data.status
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return TaskService._to_response(task, db)

    @staticmethod
    def update_task(db: Session, task_id: int, data: TaskUpdate) -> TaskResponse:
        task = TaskService.get_task(db, task_id)

        if data.subject_id is not None:
            subject = db.query(Subject).filter(
                Subject.id == data.subject_id,
                Subject.profile_id == task.profile_id
            ).first()
            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject with ID {data.subject_id} does not exist."
                )
            task.subject_id = data.subject_id

        if data.title is not None:
            task.title = data.title.strip()
        if data.description is not None:
            task.description = data.description
        if data.task_type is not None:
            task.task_type = data.task_type
        if data.due_at is not None:
            task.due_at = data.due_at
        if data.earliest_start_at is not None:
            task.earliest_start_at = data.earliest_start_at
        if data.estimated_duration_minutes is not None:
            task.estimated_duration_minutes = data.estimated_duration_minutes
        if data.priority is not None:
            task.priority = data.priority
        if data.status is not None:
            task.status = data.status

        # Validate date relationship
        if task.earliest_start_at and task.due_at and task.earliest_start_at > task.due_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Earliest start date cannot be after due date."
            )

        db.commit()
        db.refresh(task)
        return TaskService._to_response(task, db)

    @staticmethod
    def delete_task(db: Session, task_id: int) -> None:
        task = TaskService.get_task(db, task_id)
        db.delete(task)
        db.commit()
