"""
ML-Assisted Study Plan Generator Module for Meticul.

Urgency Scoring Explanation:

1. Urgency is determined using three primary features for each pending task:
   - Deadline Proximity: Inverse logarithm of hours remaining until deadline.
     Fewer hours remaining results in exponentially higher urgency.
   - Workload Pressure: Ratio of task duration (hours) to remaining time (hours).
     High duration with little time remaining indicates severe crunch.
   - Priority Weight: Explicit user priority (High=3.0, Medium=2.0, Low=1.0).
   - Task Type Multiplier: Assignments (1.1x) vs Revision (1.0x).

2. scikit-learn's MinMaxScaler normalizes these features across pending tasks
   into [0, 1] bounds. A calibrated linear scoring model computes the composite
   Urgency Score:
     Score = 0.40 * norm_deadline_prox + 0.35 * norm_workload_pressure + 0.25 * norm_priority

3. Scheduling Strategy:
   - Tasks are prioritized by (Urgency Score DESC, Due Date ASC).
   - Each task is broken into chunks <= session_length (e.g., 45m).
   - Sequential sessions are separated by break_length (e.g., 15m).
   - Normal mode respects relaxed limits: <= 3 tasks/day and <= daily_duration_cap (e.g., 240m).
   - Tight deadline detection: if remaining relaxed capacity before any task's deadline
     is insufficient, the daily cap and task-count limit are exceeded up to the day's full window.
   - Never schedules past a task's deadline. If any chunk cannot fit before the deadline,
     the task is flagged as "is_at_risk = True".
"""

from datetime import datetime, date, time, timedelta
import math
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def parse_iso_datetime(dt_str: str) -> datetime:
    """Safely parses an ISO datetime string."""
    if not dt_str:
        return datetime.max
    # Handle YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
    cleaned = dt_str.replace("Z", "").split(".")[0]
    formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return datetime.max

def parse_time_str(t_str: str) -> time:
    """Parses HH:MM string to datetime.time."""
    parts = t_str.split(":")
    return time(hour=int(parts[0]), minute=int(parts[1]))

class TaskUrgencyModel:
    """
    Computes an explainable urgency score for each task using scikit-learn.
    """
    def __init__(self):
        self.scaler = MinMaxScaler()

    def compute_urgency_scores(self, tasks, current_time: datetime):
        """
        Calculates and assigns an 'urgency_score' to each task dictionary.
        Returns the sorted list of tasks.
        """
        if not tasks:
            return []

        priority_map = {"High": 3.0, "Medium": 2.0, "Low": 1.0}
        type_multiplier = {"Assignment": 1.1, "Revision": 1.0}

        features = []
        for task in tasks:
            due_dt = parse_iso_datetime(task.get("due_date"))
            duration_mins = task.get("duration_mins", 45)
            duration_hours = max(0.25, duration_mins / 60.0)

            # Hours remaining until deadline
            time_diff = (due_dt - current_time).total_seconds() / 3600.0
            hours_left = max(0.1, time_diff)

            # Feature 1: Deadline proximity (inverted log scale so closer deadlines produce higher value)
            # log2(hours_left + 1): 1 hour -> 1.0; 24h -> 4.64; 168h -> 7.4.
            # Inverting gives higher score to closer deadlines.
            deadline_prox = 10.0 / (math.log2(hours_left + 2.0))

            # Feature 2: Workload pressure = duration / hours_left
            workload_pressure = min(10.0, duration_hours / hours_left)

            # Feature 3: Priority weight
            prio_val = priority_map.get(task.get("priority", "Medium"), 2.0)
            prio_val *= type_multiplier.get(task.get("task_type", "Assignment"), 1.0)

            features.append([deadline_prox, workload_pressure, prio_val])

        X = np.array(features, dtype=float)

        # Normalize features with scikit-learn MinMaxScaler
        if len(tasks) > 1:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = np.ones_like(X) * 0.5

        # Weighted combination of normalized features
        # 40% deadline urgency, 35% workload pressure, 25% priority
        weights = np.array([0.40, 0.35, 0.25])
        scores = np.dot(X_scaled, weights)

        scored_tasks = []
        for i, task in enumerate(tasks):
            t = dict(task)
            t["urgency_score"] = float(scores[i])
            t["_due_dt"] = parse_iso_datetime(task.get("due_date"))
            scored_tasks.append(t)

        # Sort primarily by urgency score descending, secondary by due date ascending
        scored_tasks.sort(key=lambda x: (-x["urgency_score"], x["_due_dt"]))
        return scored_tasks

def generate_study_plan(tasks, settings, availability, current_time=None):
    """
    Generates a scheduled study plan respecting availability windows,
    session chunking, relaxed vs tight constraints, and deadline enforcement.

    Parameters:
    - tasks: list of dicts (id, title, duration_mins, due_date, priority, task_type, subject_name, subject_color)
    - settings: dict (session_length, break_length, daily_duration_cap)
    - availability: dict mapping day_of_week (0-6) -> {is_enabled: bool, start_time: 'HH:MM', end_time: 'HH:MM'}
    - current_time: optional datetime for deterministic testing

    Returns:
    {
        "sessions": [...],
        "at_risk_tasks": [...],
        "total_planned_minutes": int,
        "total_tasks_scheduled": int
    }
    """
    if current_time is None:
        current_time = datetime.now()

    # Filter out completed tasks
    pending_tasks = [t for t in tasks if t.get("status") != "Complete"]
    if not pending_tasks:
        return {
            "sessions": [],
            "at_risk_tasks": [],
            "total_planned_minutes": 0,
            "total_tasks_scheduled": 0
        }

    # Extract user settings with defaults
    session_length = max(15, int(settings.get("session_length", 45)))
    break_length = max(0, int(settings.get("break_length", 15)))
    daily_duration_cap = max(30, int(settings.get("daily_duration_cap", 240)))

    # Compute urgency scores and sort tasks
    urgency_model = TaskUrgencyModel()
    prioritized_tasks = urgency_model.compute_urgency_scores(pending_tasks, current_time)

    # Prepare chunks for each task
    # A task of 90 mins with session_length 45 -> 2 chunks: [45, 45]
    task_chunks = {}
    for task in prioritized_tasks:
        tid = task["id"]
        total_duration = max(5, int(task.get("duration_mins", 45)))
        chunks = []
        rem = total_duration
        while rem > 0:
            c = min(session_length, rem)
            chunks.append(c)
            rem -= c
        task_chunks[tid] = {
            "task": task,
            "chunks": chunks,
            "total_parts": len(chunks),
            "parts_scheduled": 0,
            "due_dt": task["_due_dt"]
        }

    # Map availability by day of week (0=Mon, ..., 6=Sun)
    avail_by_day = {}
    for item in availability:
        dow = int(item["day_of_week"])
        avail_by_day[dow] = {
            "is_enabled": bool(item.get("is_enabled", 1)),
            "start_time": parse_time_str(item.get("start_time", "09:00")),
            "end_time": parse_time_str(item.get("end_time", "18:00"))
        }

    # Ensure all days 0-6 exist in avail_by_day
    for d in range(7):
        if d not in avail_by_day:
            avail_by_day[d] = {
                "is_enabled": True,
                "start_time": time(9, 0),
                "end_time": time(18, 0)
            }

    scheduled_sessions = []
    at_risk_tasks = []

    # Check if any enabled day exists at all
    any_day_enabled = any(a["is_enabled"] for a in avail_by_day.values())
    if not any_day_enabled:
        for tinfo in task_chunks.values():
            t = tinfo["task"]
            at_risk_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "subject_name": t.get("subject_name"),
                "reason": "No available study days enabled in Profile settings."
            })
        return {
            "sessions": [],
            "at_risk_tasks": at_risk_tasks,
            "total_planned_minutes": 0,
            "total_tasks_scheduled": 0
        }

    # Helper function: calculate remaining relaxed study capacity up to a target deadline
    def get_relaxed_capacity_until(target_dt: datetime, from_date: date) -> int:
        cap_mins = 0
        cur_d = from_date
        while cur_d <= target_dt.date():
            dow = cur_d.weekday()
            cfg = avail_by_day.get(dow)
            if cfg and cfg["is_enabled"]:
                w_start = datetime.combine(cur_d, cfg["start_time"])
                w_end = datetime.combine(cur_d, cfg["end_time"])
                if cur_d == current_time.date():
                    w_start = max(w_start, current_time)
                if cur_d == target_dt.date():
                    w_end = min(w_end, target_dt)
                if w_end > w_start:
                    w_mins = int((w_end - w_start).total_seconds() / 60)
                    cap_mins += min(daily_duration_cap, w_mins)
            cur_d += timedelta(days=1)
        return cap_mins

    # Helper function: collective tightness check based on Earliest Deadline First capacity
    def is_schedule_tight(cur_date: date, remaining_tasks: list) -> bool:
        # Group needed minutes by deadline
        for tid in remaining_tasks:
            target_due = task_chunks[tid]["due_dt"]
            # Sum all remaining work for tasks due on or before this deadline
            work_needed = 0
            for other_id in remaining_tasks:
                if task_chunks[other_id]["due_dt"] <= target_due:
                    rem_parts = task_chunks[other_id]["chunks"][task_chunks[other_id]["parts_scheduled"]:]
                    work_needed += sum(rem_parts)
            
            relaxed_cap = get_relaxed_capacity_until(target_due, cur_date)
            if work_needed > relaxed_cap:
                return True
        return False

    # Simulate calendar day by day starting from today
    max_days = 60
    cur_date = current_time.date()
    active_task_ids = [t["id"] for t in prioritized_tasks]

    day_counter = 0
    while active_task_ids and day_counter < max_days:
        day_counter += 1
        dow = cur_date.weekday()
        day_avail = avail_by_day.get(dow)

        if not day_avail or not day_avail["is_enabled"]:
            cur_date += timedelta(days=1)
            continue

        window_start_dt = datetime.combine(cur_date, day_avail["start_time"])
        window_end_dt = datetime.combine(cur_date, day_avail["end_time"])

        # If today is current_date, start from current_time rounded up to 5 min
        if cur_date == current_time.date():
            if current_time > window_start_dt:
                minutes_mod = current_time.minute % 5
                add_mins = (5 - minutes_mod) if minutes_mod != 0 else 0
                rounded_start = current_time + timedelta(minutes=add_mins, seconds=-current_time.second, microseconds=-current_time.microsecond)
                window_start_dt = max(window_start_dt, rounded_start)

        # If the window is already closed today, advance
        if window_start_dt >= window_end_dt:
            cur_date += timedelta(days=1)
            continue

        # Check if tight deadline mode should be activated
        tight_mode = is_schedule_tight(cur_date, active_task_ids)

        if tight_mode:
            # Exceed relaxed limits to prevent missed deadlines
            max_tasks_today = 999
            max_mins_today = int((window_end_dt - window_start_dt).total_seconds() / 60)
        else:
            # Relaxed standard limits: at most 3 tasks per day, at most daily_duration_cap
            max_tasks_today = 3
            max_mins_today = min(daily_duration_cap, int((window_end_dt - window_start_dt).total_seconds() / 60))

        today_scheduled_mins = 0
        today_task_ids = set()
        slot_ptr = window_start_dt

        # Schedule slots continuously within today's window
        while slot_ptr < window_end_dt:
            scheduled_any = False
            for tid in list(active_task_ids):
                tinfo = task_chunks[tid]
                task_obj = tinfo["task"]
                due_dt = tinfo["due_dt"]

                # Deadline already passed
                if due_dt <= slot_ptr:
                    continue

                # Check task count limit for today if relaxed
                if tid not in today_task_ids and len(today_task_ids) >= max_tasks_today:
                    continue

                next_part_idx = tinfo["parts_scheduled"]
                if next_part_idx >= tinfo["total_parts"]:
                    continue

                chunk_mins = tinfo["chunks"][next_part_idx]

                # Check daily duration limit if relaxed mode
                if not tight_mode and (today_scheduled_mins + chunk_mins > max_mins_today):
                    continue

                chunk_end_dt = slot_ptr + timedelta(minutes=chunk_mins)
                if chunk_end_dt > window_end_dt:
                    continue

                # Never schedule after deadline
                if chunk_end_dt > due_dt:
                    continue

                # Record session
                part_no = next_part_idx + 1
                tot_parts = tinfo["total_parts"]
                session_record = {
                    "task_id": tid,
                    "task_title": task_obj.get("title", ""),
                    "subject_id": task_obj.get("subject_id"),
                    "subject_name": task_obj.get("subject_name", ""),
                    "subject_color": task_obj.get("subject_color", "#54552d"),
                    "task_type": task_obj.get("task_type", "Assignment"),
                    "priority": task_obj.get("priority", "Medium"),
                    "session_date": cur_date.strftime("%Y-%m-%d"),
                    "start_time": slot_ptr.strftime("%H:%M"),
                    "end_time": chunk_end_dt.strftime("%H:%M"),
                    "duration_mins": chunk_mins,
                    "part_number": part_no,
                    "total_parts": tot_parts,
                    "urgency_score": round(task_obj.get("urgency_score", 0.0), 3)
                }
                scheduled_sessions.append(session_record)

                tinfo["parts_scheduled"] += 1
                today_scheduled_mins += chunk_mins
                today_task_ids.add(tid)
                slot_ptr = chunk_end_dt + timedelta(minutes=break_length)
                scheduled_any = True

                if tinfo["parts_scheduled"] >= tinfo["total_parts"]:
                    if tid in active_task_ids:
                        active_task_ids.remove(tid)

                # Move to next slot assignment.
                break

            if not scheduled_any:
                break

        cur_date += timedelta(days=1)

    # Check for any tasks that could not be fully scheduled before their deadline
    unique_scheduled_task_ids = set(s["task_id"] for s in scheduled_sessions)
    for tid, tinfo in task_chunks.items():
        if tinfo["parts_scheduled"] < tinfo["total_parts"]:
            task = tinfo["task"]
            scheduled_mins = sum(tinfo["chunks"][:tinfo["parts_scheduled"]])
            total_req = sum(tinfo["chunks"])
            due_str = tinfo["due_dt"].strftime("%Y-%m-%d %H:%M") if tinfo["due_dt"] != datetime.max else "Unknown"

            at_risk_tasks.append({
                "id": task["id"],
                "title": task["title"],
                "subject_name": task.get("subject_name", ""),
                "subject_color": task.get("subject_color", "#54552d"),
                "due_date": task.get("due_date"),
                "duration_mins": total_req,
                "scheduled_mins": scheduled_mins,
                "missing_mins": total_req - scheduled_mins,
                "reason": f"Cannot complete before deadline ({due_str}) with current schedule availability."
            })

    total_planned_mins = sum(s["duration_mins"] for s in scheduled_sessions)
    total_tasks_scheduled = len(unique_scheduled_task_ids)

    return {
        "sessions": scheduled_sessions,
        "at_risk_tasks": at_risk_tasks,
        "total_planned_minutes": total_planned_mins,
        "total_tasks_scheduled": total_tasks_scheduled
    }
