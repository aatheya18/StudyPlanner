import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    CheckConstraint,
    Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(100), nullable=False, default="Student")
    timezone = Column(String(50), nullable=False, default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    subjects = relationship("Subject", back_populates="profile", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="profile", cascade="all, delete-orphan")
    availability_windows = relationship("AvailabilityWindow", back_populates="profile", cascade="all, delete-orphan")
    preference = relationship("StudyPreference", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=False, default="#3B82F6")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("StudentProfile", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", passive_deletes="all")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False, default="assignment")  # assignment, revision, reading, practice
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    earliest_start_at = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=False)
    priority = Column(String(20), nullable=False, default="Medium")  # Low, Medium, High
    status = Column(String(20), nullable=False, default="Pending")    # Pending, In Progress, Completed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("estimated_duration_minutes > 0", name="check_positive_duration"),
        CheckConstraint("priority IN ('Low', 'Medium', 'High')", name="check_valid_priority"),
        CheckConstraint("status IN ('Pending', 'In Progress', 'Completed')", name="check_valid_status"),
    )

    profile = relationship("StudentProfile", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")
    sessions = relationship("StudySession", back_populates="task", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="task", cascade="all, delete-orphan")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="Scheduled")  # Scheduled, Completed, Skipped
    actual_duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('Scheduled', 'Completed', 'Skipped')", name="check_valid_session_status"),
        CheckConstraint("end_at > start_at", name="check_session_time_order"),
    )

    task = relationship("Task", back_populates="sessions")


class AvailabilityWindow(Base):
    __tablename__ = "availability_windows"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, ..., 6=Sunday
    start_time = Column(String(5), nullable=False)  # "HH:MM" e.g. "09:00"
    end_time = Column(String(5), nullable=False)    # "HH:MM" e.g. "17:00"
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="check_valid_day_of_week"),
    )

    profile = relationship("StudentProfile", back_populates="availability_windows")


class StudyPreference(Base):
    __tablename__ = "study_preferences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    preferred_session_minutes = Column(Integer, nullable=False, default=45)
    break_duration_minutes = Column(Integer, nullable=False, default=15)
    maximum_daily_study_minutes = Column(Integer, nullable=False, default=240)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("preferred_session_minutes > 0", name="check_positive_pref_session"),
        CheckConstraint("break_duration_minutes >= 0", name="check_non_negative_break"),
        CheckConstraint("maximum_daily_study_minutes > 0", name="check_positive_daily_limit"),
    )

    profile = relationship("StudentProfile", back_populates="preference")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    recommended_start_at = Column(DateTime(timezone=True), nullable=False)
    recommended_end_at = Column(DateTime(timezone=True), nullable=False)
    suitability_score = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=False, default="v1.0")
    explanation = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Accepted, Rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('Pending', 'Accepted', 'Rejected')", name="check_valid_rec_status"),
    )

    task = relationship("Task", back_populates="recommendations")
    feedback = relationship("RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # accept, reject
    feedback_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("action IN ('accept', 'reject')", name="check_valid_feedback_action"),
    )

    recommendation = relationship("Recommendation", back_populates="feedback")
