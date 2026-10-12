from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.schemas import RemindersResponse
from backend.app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=RemindersResponse)
def get_reminders(db: Session = Depends(get_db)):
    return ReminderService.get_reminders(db)
