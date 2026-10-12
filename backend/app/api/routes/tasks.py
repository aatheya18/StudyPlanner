from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.db.database import get_db
from backend.app.schemas.schemas import TaskCreate, TaskUpdate, TaskResponse
from backend.app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    status: Optional[str] = Query(None, description="Filter by status (Pending, In Progress, Completed)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Low, Medium, High)"),
    search: Optional[str] = Query(None, description="Search task title and description"),
    sort_by: Optional[str] = Query("due_at", description="Sort by due_at, priority, estimated_duration, created_at"),
    sort_order: Optional[str] = Query("asc", description="Sort order asc or desc"),
    db: Session = Depends(get_db)
):
    return TaskService.list_tasks(
        db=db,
        subject_id=subject_id,
        status_filter=status,
        priority_filter=priority,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    return TaskService.create_task(db, data)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = TaskService.get_task(db, task_id)
    return TaskService._to_response(task, db)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    return TaskService.update_task(db, task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    TaskService.delete_task(db, task_id)
    return None
