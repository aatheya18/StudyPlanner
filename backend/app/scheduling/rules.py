from datetime import datetime, timezone
from typing import Any


def calculate_task_score(task: Any, reference_time: datetime) -> float:
    """
    Deterministic rule-based scoring system:
    - Task priority weight (High: 40, Medium: 25, Low: 10)
    - Deadline urgency score (exponential decay / step score based on hours remaining)
    - Duration factor (prioritizing longer tasks slightly earlier so they fit)
    """
    # 1. Priority weight
    priority_map = {
        "High": 40.0,
        "Medium": 25.0,
        "Low": 10.0
    }
    p_score = priority_map.get(task.priority, 20.0)

    # 2. Urgency score
    if task.due_at.tzinfo is None:
        due_at = task.due_at.replace(tzinfo=timezone.utc)
    else:
        due_at = task.due_at

    if reference_time.tzinfo is None:
        ref_time = reference_time.replace(tzinfo=timezone.utc)
    else:
        ref_time = reference_time

    hours_remaining = (due_at - ref_time).total_seconds() / 3600.0

    if hours_remaining <= 0:
        # Overdue
        urgency_score = 100.0
    elif hours_remaining <= 24:
        urgency_score = 60.0
    elif hours_remaining <= 48:
        urgency_score = 40.0
    elif hours_remaining <= 72:
        urgency_score = 25.0
    elif hours_remaining <= 168:  # 1 week
        urgency_score = 15.0
    else:
        urgency_score = max(0.0, 10.0 - (hours_remaining / 168.0))

    # 3. Duration factor
    duration_minutes = getattr(task, "estimated_duration_minutes", 60)
    duration_factor = min(15.0, (duration_minutes / 60.0) * 3.0)

    total_score = p_score + urgency_score + duration_factor
    return total_score
