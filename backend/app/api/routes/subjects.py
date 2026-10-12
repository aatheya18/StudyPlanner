from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.database import get_db
from backend.app.schemas.schemas import SubjectCreate, SubjectUpdate, SubjectResponse
from backend.app.services.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return SubjectService.list_subjects(db)


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    return SubjectService.create_subject(db, data)


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subj = SubjectService.get_subject(db, subject_id)
    from backend.app.models.entities import Task
    task_cnt = db.query(Task).filter(Task.subject_id == subj.id).count()
    return SubjectResponse(
        id=subj.id,
        profile_id=subj.profile_id,
        name=subj.name,
        description=subj.description,
        color=subj.color,
        created_at=subj.created_at,
        updated_at=subj.updated_at,
        task_count=task_cnt
    )


@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db)):
    return SubjectService.update_subject(db, subject_id, data)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    force: bool = Query(False, description="Force delete if tasks exist"),
    db: Session = Depends(get_db)
):
    SubjectService.delete_subject(db, subject_id, force=force)
    return None
