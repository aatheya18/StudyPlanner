from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple


def is_overlapping(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
    buffer_minutes: int = 0
) -> bool:
    """
    Checks if interval A overlaps interval B, with optional buffer around B.
    """
    from datetime import timedelta
    buf = timedelta(minutes=buffer_minutes)
    return max(start_a, start_b - buf) < min(end_a, end_b + buf)


def check_task_deadline_constraint(slot_end: datetime, task: Any) -> Tuple[bool, str]:
    due_at = task.due_at if task.due_at.tzinfo is not None else task.due_at.replace(tzinfo=timezone.utc)
    s_end = slot_end if slot_end.tzinfo is not None else slot_end.replace(tzinfo=timezone.utc)

    if s_end > due_at:
        return False, f"Slot ends at {s_end.isoformat()} which is after task deadline {due_at.isoformat()}"
    return True, ""


def check_earliest_start_constraint(slot_start: datetime, task: Any) -> Tuple[bool, str]:
    if task.earliest_start_at is not None:
        earliest = task.earliest_start_at if task.earliest_start_at.tzinfo is not None else task.earliest_start_at.replace(tzinfo=timezone.utc)
        s_start = slot_start if slot_start.tzinfo is not None else slot_start.replace(tzinfo=timezone.utc)
        if s_start < earliest:
            return False, f"Slot starts before task's earliest start time {earliest.isoformat()}"
    return True, ""


def check_daily_limit_constraint(
    slot_date: date,
    slot_minutes: int,
    daily_totals: Dict[date, int],
    max_daily_minutes: int
) -> Tuple[bool, str]:
    current_total = daily_totals.get(slot_date, 0)
    if current_total + slot_minutes > max_daily_minutes:
        return False, f"Daily study limit ({max_daily_minutes} mins) exceeded for {slot_date} (currently {current_total} mins)"
    return True, ""


def check_collision_constraint(
    slot_start: datetime,
    slot_end: datetime,
    existing_sessions: List[Any],
    buffer_minutes: int = 0
) -> Tuple[bool, str]:
    s_start = slot_start if slot_start.tzinfo is not None else slot_start.replace(tzinfo=timezone.utc)
    s_end = slot_end if slot_end.tzinfo is not None else slot_end.replace(tzinfo=timezone.utc)

    for s in existing_sessions:
        os_start = s.start_at if s.start_at.tzinfo is not None else s.start_at.replace(tzinfo=timezone.utc)
        os_end = s.end_at if s.end_at.tzinfo is not None else s.end_at.replace(tzinfo=timezone.utc)
        if is_overlapping(s_start, s_end, os_start, os_end, buffer_minutes):
            return False, f"Slot overlaps with existing session from {os_start.isoformat()} to {os_end.isoformat()}"
    return True, ""
