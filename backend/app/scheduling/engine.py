from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Tuple
from backend.app.scheduling.rules import calculate_task_score
from backend.app.scheduling.candidate_slots import generate_candidate_slots_for_horizon
from backend.app.scheduling.constraints import (
    check_task_deadline_constraint,
    check_earliest_start_constraint,
    check_daily_limit_constraint,
    check_collision_constraint,
    is_overlapping
)


def generate_rule_based_schedule(
    tasks: List[Any],
    availability_windows: List[Any],
    preference: Any,
    existing_sessions: List[Any],
    start_date: date,
    horizon_days: int = 7,
    reference_time: datetime = None
) -> Dict[str, Any]:
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    pref_session = getattr(preference, "preferred_session_minutes", 45)
    pref_break = getattr(preference, "break_duration_minutes", 15)
    max_daily = getattr(preference, "maximum_daily_study_minutes", 240)

    # Calculate initial daily totals from existing non-skipped sessions within the horizon
    daily_totals: Dict[date, int] = {}
    for s in existing_sessions:
        if getattr(s, "status", "Scheduled") != "Skipped":
            s_start = s.start_at if s.start_at.tzinfo is not None else s.start_at.replace(tzinfo=timezone.utc)
            s_end = s.end_at if s.end_at.tzinfo is not None else s.end_at.replace(tzinfo=timezone.utc)
            s_date = s_start.date()
            dur = int((s_end - s_start).total_seconds() / 60)
            daily_totals[s_date] = daily_totals.get(s_date, 0) + dur

    # Sort tasks descending by rule-based score
    scored_tasks = []
    for t in tasks:
        # Check if already completed
        if getattr(t, "status", "Pending") == "Completed":
            continue
        score = calculate_task_score(t, reference_time)
        scored_tasks.append((score, t))

    # Higher score first (more urgent, higher priority)
    scored_tasks.sort(key=lambda x: x[0], reverse=True)

    # Generate candidate slots using preferred session duration
    candidate_slots = generate_candidate_slots_for_horizon(
        start_date=start_date,
        horizon_days=horizon_days,
        availability_windows=availability_windows,
        session_duration_minutes=pref_session,
        break_duration_minutes=pref_break,
        reference_time=reference_time
    )

    planned_sessions: List[Dict[str, Any]] = []
    unscheduled_tasks: List[Dict[str, Any]] = []
    all_sessions_tracker = list(existing_sessions)

    for score, task in scored_tasks:
        est_duration = getattr(task, "estimated_duration_minutes", 60)
        
        # Calculate how much time this task still needs
        completed_duration = sum(
            int((s.end_at - s.start_at).total_seconds() / 60)
            for s in existing_sessions
            if getattr(s, "task_id") == task.id and getattr(s, "status") == "Completed"
        )
        remaining_duration = max(0, est_duration - completed_duration)
        if remaining_duration <= 0:
            continue

        # Split remaining duration into chunks up to pref_session
        chunks = []
        rem = remaining_duration
        while rem > 0:
            if rem <= pref_session:
                # If very small remainder (e.g. < 15 mins) and we already have a chunk, merge if reasonable
                if rem < 15 and chunks:
                    chunks[-1] += rem
                else:
                    chunks.append(rem)
                rem = 0
            else:
                chunks.append(pref_session)
                rem -= pref_session

        task_fully_scheduled = True
        failed_reason = ""

        task_allocated_sessions = []
        for chunk_minutes in chunks:
            slot_found = False
            for i, (c_start, c_end) in enumerate(candidate_slots):
                actual_end = c_start + timedelta(minutes=chunk_minutes)
                s_date = c_start.date()

                # 1. Earliest start check
                ok, reason = check_earliest_start_constraint(c_start, task)
                if not ok:
                    continue

                # 2. Deadline check
                ok, reason = check_task_deadline_constraint(actual_end, task)
                if not ok:
                    # Candidate slot is past deadline
                    continue

                # 3. Daily limit check
                ok, reason = check_daily_limit_constraint(s_date, chunk_minutes, daily_totals, max_daily)
                if not ok:
                    continue

                # 4. Collision check
                ok, reason = check_collision_constraint(c_start, actual_end, all_sessions_tracker, buffer_minutes=pref_break)
                if not ok:
                    continue

                # Feasible slot found!
                slot_found = True
                new_session = {
                    "task_id": task.id,
                    "start_at": c_start,
                    "end_at": actual_end,
                    "status": "Scheduled",
                    "task_title": task.title,
                    "subject_name": task.subject.name if getattr(task, "subject", None) else "",
                    "subject_color": task.subject.color if getattr(task, "subject", None) else "#3B82F6",
                }
                task_allocated_sessions.append(new_session)

                # Update daily total
                daily_totals[s_date] = daily_totals.get(s_date, 0) + chunk_minutes

                # Add dummy session to collision tracker
                class SessionStub:
                    def __init__(self, s, e, tid):
                        self.start_at = s
                        self.end_at = e
                        self.task_id = tid
                        self.status = "Scheduled"

                all_sessions_tracker.append(SessionStub(c_start, actual_end, task.id))

                # Remove used slot from candidate slots
                candidate_slots.pop(i)
                break

            if not slot_found:
                task_fully_scheduled = False
                failed_reason = f"No available slots before deadline ({task.due_at.strftime('%Y-%m-%d %H:%M')}) or daily study limits reached."
                break

        if task_fully_scheduled:
            planned_sessions.extend(task_allocated_sessions)
        else:
            # Report as unscheduled
            unscheduled_tasks.append({
                "task_id": task.id,
                "title": task.title,
                "reason": failed_reason
            })

    total_minutes = sum(int((s["end_at"] - s["start_at"]).total_seconds() / 60) for s in planned_sessions)
    return {
        "sessions_created": planned_sessions,
        "unscheduled_tasks": unscheduled_tasks,
        "total_slots_used_minutes": total_minutes,
        "message": f"Successfully generated {len(planned_sessions)} sessions ({total_minutes} mins)."
    }
