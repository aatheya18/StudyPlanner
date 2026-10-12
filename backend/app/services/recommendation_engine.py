from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Tuple
from backend.app.scheduling.candidate_slots import generate_candidate_slots_for_horizon
from backend.app.scheduling.constraints import (
    check_task_deadline_constraint,
    check_earliest_start_constraint,
    check_daily_limit_constraint,
    check_collision_constraint
)
from backend.app.ml.predict import ModelPredictor


class RecommendationEngine:
    def __init__(self, predictor: ModelPredictor = None):
        self.predictor = predictor or ModelPredictor()

    def generate_recommendations(
        self,
        tasks: List[Any],
        availability_windows: List[Any],
        preference: Any,
        existing_sessions: List[Any],
        start_date: date,
        horizon_days: int = 5,
        max_recommendations_per_task: int = 2,
        reference_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Pure recommendation logic:
        1. Identifies feasible candidate slots within the student's availability windows.
        2. Filters strictly with hard constraints (no overlaps, before deadline, within daily limit).
        3. Evaluates suitability using the ML ModelPredictor.
        4. Ranks candidates descending by ML suitability score.
        5. Returns top recommendations with explanations.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        elif reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        pref_session = getattr(preference, "preferred_session_minutes", 45)
        pref_break = getattr(preference, "break_duration_minutes", 15)
        max_daily = getattr(preference, "maximum_daily_study_minutes", 240)

        # Existing daily totals
        daily_totals: Dict[date, int] = {}
        for s in existing_sessions:
            if getattr(s, "status", "Scheduled") != "Skipped":
                s_start = s.start_at if s.start_at.tzinfo is not None else s.start_at.replace(tzinfo=timezone.utc)
                s_end = s.end_at if s.end_at.tzinfo is not None else s.end_at.replace(tzinfo=timezone.utc)
                s_date = s_start.date()
                dur = int((s_end - s_start).total_seconds() / 60)
                daily_totals[s_date] = daily_totals.get(s_date, 0) + dur

        # Candidate slots strictly within student availability
        candidate_slots = generate_candidate_slots_for_horizon(
            start_date=start_date,
            horizon_days=horizon_days,
            availability_windows=availability_windows,
            session_duration_minutes=pref_session,
            break_duration_minutes=pref_break,
            reference_time=reference_time
        )

        all_recommendations: List[Dict[str, Any]] = []

        for task in tasks:
            if getattr(task, "status", "Pending") == "Completed":
                continue

            scored_candidates = []

            for c_start, c_end in candidate_slots:
                s_date = c_start.date()
                curr_workload = daily_totals.get(s_date, 0)

                # Hard constraints verification (Hard constraints MUST take precedence over ML scores)
                ok, _ = check_earliest_start_constraint(c_start, task)
                if not ok:
                    continue

                ok, _ = check_task_deadline_constraint(c_end, task)
                if not ok:
                    continue

                ok, _ = check_daily_limit_constraint(s_date, pref_session, daily_totals, max_daily)
                if not ok:
                    continue

                ok, _ = check_collision_constraint(c_start, c_end, existing_sessions, buffer_minutes=0)
                if not ok:
                    continue

                # Score with ML model
                score, explanation = self.predictor.predict_candidate_slot(
                    task=task,
                    slot_start=c_start,
                    slot_end=c_end,
                    daily_workload_minutes=curr_workload,
                    reference_time=reference_time
                )

                scored_candidates.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "subject_name": task.subject.name if getattr(task, "subject", None) else "",
                    "subject_color": task.subject.color if getattr(task, "subject", None) else "#3B82F6",
                    "recommended_start_at": c_start,
                    "recommended_end_at": c_end,
                    "suitability_score": score,
                    "model_version": self.predictor.metadata.get("model_version", "v1.0"),
                    "explanation": explanation
                })

            # Sort candidate slots by ML suitability score descending
            scored_candidates.sort(key=lambda x: x["suitability_score"], reverse=True)

            # Pick top candidates for this task
            chosen = scored_candidates[:max_recommendations_per_task]
            all_recommendations.extend(chosen)

        # Sort all recommendations across tasks by suitability score
        all_recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
        return all_recommendations
