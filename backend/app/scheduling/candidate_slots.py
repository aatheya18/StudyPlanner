from datetime import datetime, date, time, timedelta, timezone
from typing import List, Tuple, Dict, Any


def generate_candidate_slots_for_horizon(
    start_date: date,
    horizon_days: int,
    availability_windows: List[Any],
    session_duration_minutes: int,
    break_duration_minutes: int,
    reference_time: datetime
) -> List[Tuple[datetime, datetime]]:
    """
    Generates contiguous time intervals of length session_duration_minutes
    that fall strictly within active availability windows, spaced by break_duration_minutes,
    starting strictly after reference_time.
    """
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    # Map day_of_week -> list of active windows
    window_map: Dict[int, List[Any]] = {}
    for w in availability_windows:
        if getattr(w, "is_active", True):
            dow = getattr(w, "day_of_week")
            window_map.setdefault(dow, []).append(w)

    slots: List[Tuple[datetime, datetime]] = []

    for d in range(horizon_days):
        current_date = start_date + timedelta(days=d)
        dow = current_date.weekday()  # Monday=0, Sunday=6
        day_windows = window_map.get(dow, [])

        for win in day_windows:
            start_parts = [int(p) for p in win.start_time.split(":")]
            end_parts = [int(p) for p in win.end_time.split(":")]

            win_start = datetime.combine(
                current_date,
                time(start_parts[0], start_parts[1]),
                tzinfo=timezone.utc
            )
            win_end = datetime.combine(
                current_date,
                time(end_parts[0], end_parts[1]),
                tzinfo=timezone.utc
            )

            current_cursor = win_start
            # Ensure slot does not start in the past
            if current_cursor < reference_time:
                # advance cursor to nearest 15-minute mark after reference_time
                minutes_past = (reference_time - current_cursor).total_seconds() / 60.0
                if minutes_past > 0:
                    advance_steps = int(minutes_past // 15) + 1
                    current_cursor = current_cursor + timedelta(minutes=advance_steps * 15)

            step = timedelta(minutes=session_duration_minutes + break_duration_minutes)
            slot_len = timedelta(minutes=session_duration_minutes)

            while current_cursor + slot_len <= win_end:
                slot_start = current_cursor
                slot_end = current_cursor + slot_len
                if slot_start >= reference_time:
                    slots.append((slot_start, slot_end))
                current_cursor += step

    return slots
