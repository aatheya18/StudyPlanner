from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from backend.app.models.entities import Subject, Task
from backend.app.schemas.schemas import SubjectCreate, SubjectUpdate, SubjectResponse
from backend.app.services.profile_service import ProfileService


class SubjectService:
    @staticmethod
    def list_subjects(db: Session) -> List[SubjectResponse]:
        profile = ProfileService.get_or_create_profile(db)
        subjects = db.query(Subject).filter(Subject.profile_id == profile.id).order_by(Subject.name.asc()).all()
        result = []
        for s in subjects:
            task_cnt = db.query(Task).filter(Task.subject_id == s.id).count()
            resp = SubjectResponse(
                id=s.id,
                profile_id=s.profile_id,
                name=s.name,
                description=s.description,
                color=s.color,
                created_at=s.created_at,
                updated_at=s.updated_at,
                task_count=task_cnt
            )
            result.append(resp)
        return result

    @staticmethod
    def get_subject(db: Session, subject_id: int) -> Subject:
        profile = ProfileService.get_or_create_profile(db)
        subject = db.query(Subject).filter(Subject.id == subject_id, Subject.profile_id == profile.id).first()
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subject with ID {subject_id} not found.")
        return subject

    @staticmethod
    def create_subject(db: Session, data: SubjectCreate) -> SubjectResponse:
        profile = ProfileService.get_or_create_profile(db)
        # Check duplicate name
        existing = db.query(Subject).filter(
            Subject.profile_id == profile.id,
            Subject.name == data.name.strip()
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with name '{data.name}' already exists."
            )

        subject = Subject(
            profile_id=profile.id,
            name=data.name.strip(),
            description=data.description,
            color=data.color or "#3B82F6"
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return SubjectResponse(
            id=subject.id,
            profile_id=subject.profile_id,
            name=subject.name,
            description=subject.description,
            color=subject.color,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
            task_count=0
        )

    @staticmethod
    def update_subject(db: Session, subject_id: int, data: SubjectUpdate) -> SubjectResponse:
        subject = SubjectService.get_subject(db, subject_id)
        if data.name is not None and data.name.strip() != subject.name:
            # Check duplicate
            dup = db.query(Subject).filter(
                Subject.profile_id == subject.profile_id,
                Subject.name == data.name.strip(),
                Subject.id != subject_id
            ).first()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another subject with name '{data.name}' already exists."
                )
            subject.name = data.name.strip()

        if data.description is not None:
            subject.description = data.description
        if data.color is not None:
            subject.color = data.color

        db.commit()
        db.refresh(subject)
        task_cnt = db.query(Task).filter(Task.subject_id == subject.id).count()
        return SubjectResponse(
            id=subject.id,
            profile_id=subject.profile_id,
            name=subject.name,
            description=subject.description,
            color=subject.color,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
            task_count=task_cnt
        )

    @staticmethod
    def delete_subject(db: Session, subject_id: int, force: bool = False) -> None:
        subject = SubjectService.get_subject(db, subject_id)
        task_cnt = db.query(Task).filter(Task.subject_id == subject_id).count()
        if task_cnt > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete subject '{subject.name}' because it has {task_cnt} associated task(s). Delete or reassign tasks first."
            )
        db.delete(subject)
        db.commit()
