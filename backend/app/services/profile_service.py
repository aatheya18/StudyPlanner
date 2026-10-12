from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from backend.app.models.entities import StudentProfile, StudyPreference, AvailabilityWindow
from backend.app.schemas.schemas import (
    StudentProfileUpdate,
    StudyPreferenceUpdate,
    AvailabilityWindowCreate
)


class ProfileService:
    @staticmethod
    def get_or_create_profile(db: Session) -> StudentProfile:
        profile = db.query(StudentProfile).first()
        if not profile:
            from backend.app.db.init_db import init_db
            profile = init_db(db)
        return profile

    @staticmethod
    def update_profile(db: Session, update_data: StudentProfileUpdate) -> StudentProfile:
        profile = ProfileService.get_or_create_profile(db)
        if update_data.display_name is not None:
            profile.display_name = update_data.display_name
        if update_data.timezone is not None:
            profile.timezone = update_data.timezone
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_preferences(db: Session) -> StudyPreference:
        profile = ProfileService.get_or_create_profile(db)
        pref = db.query(StudyPreference).filter(StudyPreference.profile_id == profile.id).first()
        if not pref:
            pref = StudyPreference(
                profile_id=profile.id,
                preferred_session_minutes=45,
                break_duration_minutes=15,
                maximum_daily_study_minutes=240
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(db: Session, update_data: StudyPreferenceUpdate) -> StudyPreference:
        pref = ProfileService.get_preferences(db)
        if update_data.preferred_session_minutes is not None:
            pref.preferred_session_minutes = update_data.preferred_session_minutes
        if update_data.break_duration_minutes is not None:
            pref.break_duration_minutes = update_data.break_duration_minutes
        if update_data.maximum_daily_study_minutes is not None:
            pref.maximum_daily_study_minutes = update_data.maximum_daily_study_minutes
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def get_availability_windows(db: Session) -> List[AvailabilityWindow]:
        profile = ProfileService.get_or_create_profile(db)
        windows = db.query(AvailabilityWindow).filter(
            AvailabilityWindow.profile_id == profile.id
        ).order_by(AvailabilityWindow.day_of_week.asc(), AvailabilityWindow.start_time.asc()).all()
        return windows

    @staticmethod
    def update_availability_windows(db: Session, windows_data: List[AvailabilityWindowCreate]) -> List[AvailabilityWindow]:
        profile = ProfileService.get_or_create_profile(db)
        # Clear existing and replace
        db.query(AvailabilityWindow).filter(AvailabilityWindow.profile_id == profile.id).delete()
        new_windows = []
        for w in windows_data:
            window = AvailabilityWindow(
                profile_id=profile.id,
                day_of_week=w.day_of_week,
                start_time=w.start_time,
                end_time=w.end_time,
                is_active=w.is_active
            )
            db.add(window)
            new_windows.append(window)
        db.commit()
        return ProfileService.get_availability_windows(db)
