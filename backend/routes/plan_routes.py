from datetime import datetime
from flask import Blueprint, request, jsonify
from db import get_db_connection
from auth import login_required
from planner import generate_study_plan

plan_bp = Blueprint("plan", __name__)

@plan_bp.route("/generate", methods=["POST"])
@login_required
def generate_plan():
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch pending tasks for this user
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.task_type, t.due_date,
               t.priority, t.status, t.duration_mins,
               s.id as subject_id, s.name as subject_name, s.color as subject_color
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.user_id = ? AND t.status = 'Pending'
    """, (user_id,))
    task_rows = cursor.fetchall()
    tasks = [dict(r) for r in task_rows]

    # 2. Fetch user settings
    cursor.execute("""
        SELECT session_length, break_length, daily_duration_cap
        FROM user_settings WHERE user_id = ?
    """, (user_id,))
    settings_row = cursor.fetchone()
    settings = dict(settings_row) if settings_row else {
        "session_length": 45,
        "break_length": 15,
        "daily_duration_cap": 240
    }

    # 3. Fetch user availability
    cursor.execute("""
        SELECT day_of_week, is_enabled, start_time, end_time
        FROM user_availability WHERE user_id = ?
        ORDER BY day_of_week ASC
    """, (user_id,))
    avail_rows = cursor.fetchall()
    availability = [dict(r) for r in avail_rows]

    # 4. Run ML Planner
    now = datetime.now()
    plan_result = generate_study_plan(tasks, settings, availability, current_time=now)

    # 5. Clear previous plan for this user
    cursor.execute("DELETE FROM plan_sessions WHERE user_id = ?", (user_id,))

    # 6. Save newly generated plan sessions
    for session in plan_result["sessions"]:
        cursor.execute("""
            INSERT INTO plan_sessions (
                user_id, task_id, session_date, start_time, end_time,
                duration_mins, part_number, total_parts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            session["task_id"],
            session["session_date"],
            session["start_time"],
            session["end_time"],
            session["duration_mins"],
            session["part_number"],
            session["total_parts"]
        ))

    conn.commit()

    # 7. Get updated counts
    cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE user_id = ? AND status = 'Pending'", (user_id,))
    pending_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE user_id = ? AND status = 'Complete'", (user_id,))
    completed_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COALESCE(SUM(duration_mins), 0) as total FROM plan_sessions WHERE user_id = ?", (user_id,))
    total_planned_mins = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "message": "Study plan generated successfully",
        "sessions": plan_result["sessions"],
        "at_risk_tasks": plan_result["at_risk_tasks"],
        "stats": {
            "pending_count": pending_count,
            "completed_count": completed_count,
            "total_planned_minutes": total_planned_mins,
            "total_tasks_scheduled": plan_result["total_tasks_scheduled"]
        }
    }), 200

@plan_bp.route("/sessions", methods=["GET"])
@login_required
def get_sessions():
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch scheduled sessions
    cursor.execute("""
        SELECT ps.id, ps.task_id, ps.session_date, ps.start_time, ps.end_time,
               ps.duration_mins, ps.part_number, ps.total_parts,
               t.title as task_title, t.task_type, t.priority, t.due_date,
               s.id as subject_id, s.name as subject_name, s.color as subject_color
        FROM plan_sessions ps
        JOIN tasks t ON ps.task_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE ps.user_id = ?
        ORDER BY ps.session_date ASC, ps.start_time ASC
    """, (user_id,))
    session_rows = cursor.fetchall()
    sessions = [dict(r) for r in session_rows]

    # Calculate stats
    cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE user_id = ? AND status = 'Pending'", (user_id,))
    pending_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE user_id = ? AND status = 'Complete'", (user_id,))
    completed_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COALESCE(SUM(duration_mins), 0) as total FROM plan_sessions WHERE user_id = ?", (user_id,))
    total_planned_mins = cursor.fetchone()["total"]

    # Check for at_risk tasks among pending tasks
    # Either tasks that are overdue or tasks whose planned duration is less than total required duration
    cursor.execute("""
        SELECT t.id, t.title, t.due_date, t.duration_mins,
               s.name as subject_name, s.color as subject_color,
               COALESCE(SUM(ps.duration_mins), 0) as scheduled_mins
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        LEFT JOIN plan_sessions ps ON t.id = ps.task_id AND ps.user_id = ?
        WHERE t.user_id = ? AND t.status = 'Pending'
        GROUP BY t.id
    """, (user_id, user_id))
    task_status_rows = cursor.fetchall()
    conn.close()

    now_iso = datetime.now().isoformat()
    at_risk_tasks = []
    for r in task_status_rows:
        is_overdue = r["due_date"] < now_iso
        missing_mins = r["duration_mins"] - r["scheduled_mins"]
        if is_overdue:
            at_risk_tasks.append({
                "id": r["id"],
                "title": r["title"],
                "subject_name": r["subject_name"],
                "subject_color": r["subject_color"],
                "due_date": r["due_date"],
                "duration_mins": r["duration_mins"],
                "scheduled_mins": r["scheduled_mins"],
                "missing_mins": max(0, missing_mins),
                "reason": "Task is past due date."
            })
        elif missing_mins > 0 and len(sessions) > 0:
            at_risk_tasks.append({
                "id": r["id"],
                "title": r["title"],
                "subject_name": r["subject_name"],
                "subject_color": r["subject_color"],
                "due_date": r["due_date"],
                "duration_mins": r["duration_mins"],
                "scheduled_mins": r["scheduled_mins"],
                "missing_mins": missing_mins,
                "reason": f"Only {r['scheduled_mins']} of {r['duration_mins']} mins could be scheduled before deadline."
            })

    return jsonify({
        "sessions": sessions,
        "at_risk_tasks": at_risk_tasks,
        "stats": {
            "pending_count": pending_count,
            "completed_count": completed_count,
            "total_planned_minutes": total_planned_mins,
            "total_tasks_scheduled": len(set(s["task_id"] for s in sessions))
        }
    }), 200
