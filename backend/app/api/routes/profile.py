from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.database import get_db
from backend.app.schemas.schemas import (
    StudentProfileResponse,
    StudentProfileUpdate,
    StudyPreferenceResponse,
    StudyPreferenceUpdate,
    AvailabilityWindowResponse,
    AvailabilityWindowCreate
)
from backend.app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/profile", response_model=StudentProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    return ProfileService.get_or_create_profile(db)


@router.put("/profile", response_model=StudentProfileResponse)
def update_profile(data: StudentProfileUpdate, db: Session = Depends(get_db)):
    return ProfileService.update_profile(db, data)


@router.get("/preferences", response_model=StudyPreferenceResponse)
def get_preferences(db: Session = Depends(get_db)):
    return ProfileService.get_preferences(db)


@router.put("/preferences", response_model=StudyPreferenceResponse)
def update_preferences(data: StudyPreferenceUpdate, db: Session = Depends(get_db)):
    return ProfileService.update_preferences(db, data)


@router.get("/availability", response_model=List[AvailabilityWindowResponse])
def get_availability(db: Session = Depends(get_db)):
    return ProfileService.get_availability_windows(db)


@router.put("/availability", response_model=List[AvailabilityWindowResponse])
def update_availability(windows: List[AvailabilityWindowCreate], db: Session = Depends(get_db)):
    return ProfileService.update_availability_windows(db, windows)
