from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from backend.app.models.entities import (
    StudentProfile,
    StudyPreference,
    AvailabilityWindow,
    Subject,
    Task
)
from backend.app.db.database import Base, engine


def init_db(db: Session):
    Base.metadata.create_all(bind=engine)

    profile = db.query(StudentProfile).first()
    if not profile:
        profile = StudentProfile(
            display_name="Alex Morgan",
            timezone="UTC"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Create preferences
        pref = StudyPreference(
            profile_id=profile.id,
            preferred_session_minutes=45,
            break_duration_minutes=15,
            maximum_daily_study_minutes=240
        )
        db.add(pref)

        # Create default availability windows (Mon to Sun: 09:00 to 18:00)
        for day in range(7):
            window = AvailabilityWindow(
                profile_id=profile.id,
                day_of_week=day,
                start_time="09:00",
                end_time="18:00",
                is_active=True
            )
            db.add(window)

        # Create sample subjects
        math_subj = Subject(
            profile_id=profile.id,
            name="Advanced Mathematics",
            description="Calculus, Linear Algebra, and Discrete Math",
            color="#3B82F6"
        )
        cs_subj = Subject(
            profile_id=profile.id,
            name="Computer Science",
            description="Data Structures, Algorithms, and Software Engineering",
            color="#10B981"
        )
        phys_subj = Subject(
            profile_id=profile.id,
            name="Physics",
            description="Mechanics, Electromagnetism, and Quantum Basics",
            color="#F59E0B"
        )
        db.add_all([math_subj, cs_subj, phys_subj])
        db.commit()
        db.refresh(math_subj)
        db.refresh(cs_subj)
        db.refresh(phys_subj)

        # Create sample tasks
        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                profile_id=profile.id,
                subject_id=math_subj.id,
                title="Calculus Problem Set 3",
                description="Complete problems 1 through 15 on multivariable derivatives",
                task_type="assignment",
                due_at=now + timedelta(days=2, hours=4),
                estimated_duration_minutes=90,
                priority="High",
                status="Pending"
            ),
            Task(
                profile_id=profile.id,
                subject_id=cs_subj.id,
                title="Implement Dijkstra Algorithm",
                description="Write clean Python implementation with priority queue and unit tests",
                task_type="practice",
                due_at=now + timedelta(days=3, hours=2),
                estimated_duration_minutes=120,
                priority="High",
                status="Pending"
            ),
            Task(
                profile_id=profile.id,
                subject_id=phys_subj.id,
                title="Read Chapter 4: Thermodynamics",
                description="Study heat cycles and entropy equations for quiz",
                task_type="reading",
                due_at=now + timedelta(days=4),
                estimated_duration_minutes=60,
                priority="Medium",
                status="Pending"
            ),
            Task(
                profile_id=profile.id,
                subject_id=cs_subj.id,
                title="Software Project Tut Review",
                description="Prepare architectural design diagrams and component review",
                task_type="revision",
                due_at=now + timedelta(days=5),
                estimated_duration_minutes=90,
                priority="Low",
                status="Pending"
            ),
        ]
        db.add_all(tasks)
        db.commit()

    return profile
