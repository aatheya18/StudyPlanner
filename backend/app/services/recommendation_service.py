from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import List, Optional
from backend.app.models.entities import (
    Task,
    StudySession,
    Recommendation,
    RecommendationFeedback
)
from backend.app.schemas.schemas import (
    RecommendationGenerateRequest,
    RecommendationResponse,
    RecommendationFeedbackRequest,
    ModelStatusResponse,
    StudySessionResponse
)
from backend.app.services.recommendation_engine import RecommendationEngine
from backend.app.services.profile_service import ProfileService
from backend.app.scheduling.constraints import (
    check_task_deadline_constraint,
    check_collision_constraint,
    check_daily_limit_constraint
)


class RecommendationService:
    _engine = RecommendationEngine()

    @staticmethod
    def _to_response(rec: Recommendation) -> RecommendationResponse:
        return RecommendationResponse(
            id=rec.id,
            task_id=rec.task_id,
            task_title=rec.task.title if rec.task else "",
            subject_name=rec.task.subject.name if rec.task and rec.task.subject else "",
            subject_color=rec.task.subject.color if rec.task and rec.task.subject else "#3B82F6",
            recommended_start_at=rec.recommended_start_at,
            recommended_end_at=rec.recommended_end_at,
            suitability_score=rec.suitability_score,
            model_version=rec.model_version,
            explanation=rec.explanation,
            status=rec.status,
            created_at=rec.created_at
        )

    @staticmethod
    def generate_recommendations(
        db: Session,
        req: RecommendationGenerateRequest
    ) -> List[RecommendationResponse]:
        profile = ProfileService.get_or_create_profile(db)
        pref = ProfileService.get_preferences(db)
        avail = ProfileService.get_availability_windows(db)

        now_utc = datetime.now(timezone.utc)

        # Incomplete tasks
        tasks = db.query(Task).filter(
            Task.profile_id == profile.id,
            Task.status.in_(["Pending", "In Progress"])
        ).all()

        existing_sessions = db.query(StudySession).join(Task).filter(
            Task.profile_id == profile.id
        ).all()

        rec_data_list = RecommendationService._engine.generate_recommendations(
            tasks=tasks,
            availability_windows=avail,
            preference=pref,
            existing_sessions=existing_sessions,
            start_date=now_utc.date(),
            horizon_days=req.horizon_days,
            max_recommendations_per_task=req.candidate_slots_per_task,
            reference_time=now_utc
        )

        # Clear existing unaccepted/pending recommendations
        task_ids = [t.id for t in db.query(Task.id).filter(Task.profile_id == profile.id).all()]
        if task_ids:
            db.query(Recommendation).filter(
                Recommendation.task_id.in_(task_ids),
                Recommendation.status == "Pending"
            ).delete(synchronize_session=False)
            db.commit()

        created_recs = []
        for r in rec_data_list:
            rec = Recommendation(
                task_id=r["task_id"],
                recommended_start_at=r["recommended_start_at"],
                recommended_end_at=r["recommended_end_at"],
                suitability_score=r["suitability_score"],
                model_version=r["model_version"],
                explanation=r["explanation"],
                status="Pending"
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            created_recs.append(RecommendationService._to_response(rec))

        return created_recs

    @staticmethod
    def list_recommendations(db: Session, status_filter: Optional[str] = "Pending") -> List[RecommendationResponse]:
        profile = ProfileService.get_or_create_profile(db)
        query = db.query(Recommendation).join(Task).filter(Task.profile_id == profile.id)
        if status_filter:
            query = query.filter(Recommendation.status == status_filter)
        recs = query.order_by(Recommendation.suitability_score.desc().nullslast()).all()
        return [RecommendationService._to_response(r) for r in recs]

    @staticmethod
    def accept_recommendation(
        db: Session,
        recommendation_id: int,
        feedback: Optional[RecommendationFeedbackRequest] = None
    ) -> StudySessionResponse:
        profile = ProfileService.get_or_create_profile(db)
        rec = db.query(Recommendation).join(Task).filter(
            Recommendation.id == recommendation_id,
            Task.profile_id == profile.id
        ).first()

        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation {recommendation_id} not found.")

        if rec.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recommendation is already {rec.status}."
            )

        task = rec.task
        if task.status == "Completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task has already been completed."
            )

        # Revalidate hard constraints at time of acceptance
        now_utc = datetime.now(timezone.utc)
        rec_start = rec.recommended_start_at if rec.recommended_start_at.tzinfo is not None else rec.recommended_start_at.replace(tzinfo=timezone.utc)
        if rec_start < now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This recommended slot is now in the past."
            )

        ok, reason = check_task_deadline_constraint(rec.recommended_end_at, task)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

        existing_sessions = db.query(StudySession).filter(
            StudySession.status != "Skipped"
        ).all()
        ok, reason = check_collision_constraint(rec.recommended_start_at, rec.recommended_end_at, existing_sessions)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot accept recommendation: {reason}"
            )

        # Create session
        new_session = StudySession(
            task_id=task.id,
            start_at=rec.recommended_start_at,
            end_at=rec.recommended_end_at,
            status="Scheduled"
        )
        db.add(new_session)

        # Update recommendation status
        rec.status = "Accepted"

        # Record feedback
        fb = RecommendationFeedback(
            recommendation_id=rec.id,
            action="accept",
            feedback_note=feedback.note if feedback else None
        )
        db.add(fb)

        db.commit()
        db.refresh(new_session)

        return StudySessionResponse(
            id=new_session.id,
            task_id=new_session.task_id,
            start_at=new_session.start_at,
            end_at=new_session.end_at,
            status=new_session.status,
            actual_duration_minutes=None,
            created_at=new_session.created_at,
            updated_at=new_session.updated_at,
            task_title=task.title,
            subject_name=task.subject.name if task.subject else None,
            subject_color=task.subject.color if task.subject else "#3B82F6"
        )

    @staticmethod
    def reject_recommendation(
        db: Session,
        recommendation_id: int,
        feedback: Optional[RecommendationFeedbackRequest] = None
    ) -> None:
        profile = ProfileService.get_or_create_profile(db)
        rec = db.query(Recommendation).join(Task).filter(
            Recommendation.id == recommendation_id,
            Task.profile_id == profile.id
        ).first()

        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation {recommendation_id} not found.")

        if rec.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recommendation is already {rec.status}."
            )

        rec.status = "Rejected"

        fb = RecommendationFeedback(
            recommendation_id=rec.id,
            action="reject",
            feedback_note=feedback.note if feedback else None
        )
        db.add(fb)
        db.commit()

    @staticmethod
    def get_model_status() -> ModelStatusResponse:
        predictor = RecommendationService._engine.predictor
        meta = predictor.metadata
        eval_metrics = meta.get("evaluation_metrics", {})
        return ModelStatusResponse(
            model_loaded=predictor.loaded,
            model_version=meta.get("model_version", "v1.0"),
            model_type=predictor.model_type,
            status_detail="Active and evaluating candidate slots" if predictor.loaded else "Running in graceful heuristic demo mode",
            training_sample_count=meta.get("train_samples"),
            test_accuracy=eval_metrics.get("accuracy"),
            test_f1=eval_metrics.get("f1"),
            test_roc_auc=eval_metrics.get("roc_auc")
        )
