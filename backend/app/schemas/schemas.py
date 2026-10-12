from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# --- Profile & Preferences ---
class StudentProfileBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)


class StudentProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)


class StudentProfileResponse(StudentProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailabilityWindowBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format, e.g. 09:00")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format, e.g. 17:00")
    is_active: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_time_order(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be strictly after start_time")
        return v


class AvailabilityWindowCreate(AvailabilityWindowBase):
    pass


class AvailabilityWindowResponse(AvailabilityWindowBase):
    id: int
    profile_id: int

    class Config:
        from_attributes = True


class StudyPreferenceBase(BaseModel):
    preferred_session_minutes: int = Field(default=45, gt=0, le=240)
    break_duration_minutes: int = Field(default=15, ge=0, le=120)
    maximum_daily_study_minutes: int = Field(default=240, gt=0, le=960)


class StudyPreferenceUpdate(BaseModel):
    preferred_session_minutes: Optional[int] = Field(None, gt=0, le=240)
    break_duration_minutes: Optional[int] = Field(None, ge=0, le=120)
    maximum_daily_study_minutes: Optional[int] = Field(None, gt=0, le=960)


class StudyPreferenceResponse(StudyPreferenceBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Subject ---
class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#3B82F6", max_length=20)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)


class SubjectResponse(SubjectBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Task ---
class TaskBase(BaseModel):
    subject_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str = Field(default="assignment", description="assignment, revision, reading, practice")
    due_at: datetime
    earliest_start_at: Optional[datetime] = None
    estimated_duration_minutes: int = Field(..., gt=0, le=10000, description="Estimated duration in minutes")
    priority: str = Field(default="Medium", description="Low, Medium, High")
    status: str = Field(default="Pending", description="Pending, In Progress, Completed")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v not in ["Low", "Medium", "High"]:
            raise ValueError("priority must be one of: Low, Medium, High")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["Pending", "In Progress", "Completed"]:
            raise ValueError("status must be one of: Pending, In Progress, Completed")
        return v

    @field_validator("earliest_start_at")
    @classmethod
    def validate_dates(cls, v, info):
        if v and "due_at" in info.data and v > info.data["due_at"]:
            raise ValueError("earliest_start_at cannot be after due_at")
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    subject_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: Optional[str] = None
    due_at: Optional[datetime] = None
    earliest_start_at: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = Field(None, gt=0, le=10000)
    priority: Optional[str] = None
    status: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ["Low", "Medium", "High"]:
            raise ValueError("priority must be one of: Low, Medium, High")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ["Pending", "In Progress, Completed"]:
            raise ValueError("status must be one of: Pending, In Progress, Completed")
        return v


class TaskResponse(TaskBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    scheduled_duration_minutes: Optional[int] = 0
    completed_duration_minutes: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Study Session ---
class StudySessionBase(BaseModel):
    task_id: int
    start_at: datetime
    end_at: datetime
    status: str = Field(default="Scheduled", description="Scheduled, Completed, Skipped")
    actual_duration_minutes: Optional[int] = Field(None, ge=0)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["Scheduled", "Completed", "Skipped"]:
            raise ValueError("status must be one of: Scheduled, Completed, Skipped")
        return v

    @field_validator("end_at")
    @classmethod
    def validate_end_at(cls, v, info):
        if "start_at" in info.data and v <= info.data["start_at"]:
            raise ValueError("end_at must be strictly after start_at")
        return v


class StudySessionCreate(StudySessionBase):
    pass


class StudySessionUpdate(BaseModel):
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[str] = None
    actual_duration_minutes: Optional[int] = Field(None, ge=0)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ["Scheduled", "Completed", "Skipped"]:
            raise ValueError("status must be one of: Scheduled, Completed, Skipped")
        return v


class StudySessionCompleteRequest(BaseModel):
    actual_duration_minutes: Optional[int] = Field(None, ge=0)
    mark_task_completed: bool = False


class StudySessionResponse(StudySessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    task_title: Optional[str] = None
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None

    class Config:
        from_attributes = True


# --- Rule-Based Scheduling ---
class ScheduleGenerateRequest(BaseModel):
    start_date: Optional[date] = None
    horizon_days: int = Field(default=7, ge=1, le=30)
    clear_existing_scheduled: bool = Field(default=True, description="Clear future uncompleted sessions before generating")


class UnscheduledTaskInfo(BaseModel):
    task_id: int
    title: str
    reason: str


class ScheduleGenerateResponse(BaseModel):
    sessions_created: List[StudySessionResponse]
    unscheduled_tasks: List[UnscheduledTaskInfo]
    total_slots_used_minutes: int
    message: str


# --- Dashboard ---
class WeeklyProgressPoint(BaseModel):
    day: str
    date: str
    planned_minutes: int
    completed_minutes: int


class DashboardSummaryResponse(BaseModel):
    today_sessions: List[StudySessionResponse]
    tasks_due_soon: List[TaskResponse]
    overdue_tasks: List[TaskResponse]
    pending_tasks_count: int
    completed_tasks_count: int
    total_planned_minutes: int
    total_completed_minutes: int
    weekly_progress: List[WeeklyProgressPoint]


# --- Reminders ---
class ReminderItem(BaseModel):
    id: str
    type: str  # "upcoming_session", "approaching_deadline", "overdue_task"
    title: str
    message: str
    due_or_start_at: datetime
    urgency: str  # "high", "medium", "low"
    entity_id: int


class RemindersResponse(BaseModel):
    reminders: List[ReminderItem]
    count: int


# --- AI Recommendations ---
class RecommendationGenerateRequest(BaseModel):
    horizon_days: int = Field(default=5, ge=1, le=14)
    candidate_slots_per_task: int = Field(default=3, ge=1, le=10)


class RecommendationResponse(BaseModel):
    id: int
    task_id: int
    task_title: str
    subject_name: str
    subject_color: str
    recommended_start_at: datetime
    recommended_end_at: datetime
    suitability_score: Optional[float] = None
    model_version: str
    explanation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationFeedbackRequest(BaseModel):
    note: Optional[str] = None


class ModelStatusResponse(BaseModel):
    model_loaded: bool
    model_version: str
    model_type: str
    status_detail: str
    training_sample_count: Optional[int] = None
    test_accuracy: Optional[float] = None
    test_f1: Optional[float] = None
    test_roc_auc: Optional[float] = None
