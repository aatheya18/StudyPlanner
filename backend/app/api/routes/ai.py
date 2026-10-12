from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.db.database import get_db
from backend.app.schemas.schemas import (
    RecommendationGenerateRequest,
    RecommendationResponse,
    RecommendationFeedbackRequest,
    ModelStatusResponse,
    StudySessionResponse
)
from backend.app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/recommendations/generate", response_model=List[RecommendationResponse])
def generate_recommendations(req: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    return RecommendationService.generate_recommendations(db, req)


@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    status: Optional[str] = Query("Pending", description="Filter by status (Pending, Accepted, Rejected)"),
    db: Session = Depends(get_db)
):
    return RecommendationService.list_recommendations(db, status_filter=status)


@router.post("/recommendations/{recommendation_id}/accept", response_model=StudySessionResponse)
def accept_recommendation(
    recommendation_id: int,
    feedback: Optional[RecommendationFeedbackRequest] = None,
    db: Session = Depends(get_db)
):
    return RecommendationService.accept_recommendation(db, recommendation_id, feedback)


@router.post("/recommendations/{recommendation_id}/reject", status_code=status.HTTP_200_OK)
def reject_recommendation(
    recommendation_id: int,
    feedback: Optional[RecommendationFeedbackRequest] = None,
    db: Session = Depends(get_db)
):
    RecommendationService.reject_recommendation(db, recommendation_id, feedback)
    return {"message": "Recommendation rejected successfully."}


@router.get("/status", response_model=ModelStatusResponse)
def get_ai_status():
    return RecommendationService.get_model_status()
