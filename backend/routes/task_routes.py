from datetime import datetime
from flask import Blueprint, request, jsonify
from db import get_db_connection
from auth import login_required

task_bp = Blueprint("tasks", __name__)

@task_bp.route("", methods=["GET"])
@login_required
def get_tasks():
    user_id = request.user["id"]
    search = (request.args.get("search") or "").strip()
    subject_id = request.args.get("subject_id")
    status = request.args.get("status")
    priority = request.args.get("priority")
    sort_by = request.args.get("sort_by", "due_date_asc")

    query = """
        SELECT t.id, t.title, t.description, t.task_type, t.due_date,
               t.priority, t.status, t.duration_mins, t.created_at,
               s.id as subject_id, s.name as subject_name, s.color as subject_color
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.user_id = ?
    """
    params = [user_id]

    if search:
        query += " AND (t.title LIKE ? OR t.description LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])

    if subject_id and subject_id != "all":
        try:
            query += " AND t.subject_id = ?"
            params.append(int(subject_id))
        except ValueError:
            pass

    if status and status != "all":
        query += " AND t.status = ?"
        params.append(status)

    if priority and priority != "all":
        query += " AND t.priority = ?"
        params.append(priority)

    # Sorting
    if sort_by == "due_date_desc":
        query += " ORDER BY t.due_date DESC"
    elif sort_by == "priority_desc":
        # High -> Medium -> Low
        query += """ ORDER BY 
            CASE t.priority 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                WHEN 'Low' THEN 3 
                ELSE 4 
            END ASC, t.due_date ASC"""
    elif sort_by == "duration_desc":
        query += " ORDER BY t.duration_mins DESC"
    elif sort_by == "created_at_desc":
        query += " ORDER BY t.created_at DESC"
    else:  # default: due_date_asc
        query += " ORDER BY t.due_date ASC"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    now_iso = datetime.now().isoformat()
    tasks = []
    for r in rows:
        is_overdue = (r["status"] == "Pending" and r["due_date"] < now_iso)
        tasks.append({
            "id": r["id"],
            "title": r["title"],
            "description": r["description"] or "",
            "task_type": r["task_type"],
            "due_date": r["due_date"],
            "priority": r["priority"],
            "status": r["status"],
            "duration_mins": r["duration_mins"],
            "created_at": r["created_at"],
            "subject_id": r["subject_id"],
            "subject_name": r["subject_name"],
            "subject_color": r["subject_color"],
            "is_overdue": is_overdue
        })

    return jsonify(tasks), 200

@task_bp.route("", methods=["POST"])
@login_required
def create_task():
    user_id = request.user["id"]
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    subject_id = data.get("subject_id")
    task_type = data.get("task_type", "Assignment")
    due_date = (data.get("due_date") or "").strip()
    priority = data.get("priority", "Medium")
    status = data.get("status", "Pending")
    duration_mins = data.get("duration_mins", 45)
    description = (data.get("description") or "").strip()

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if not subject_id:
        return jsonify({"error": "Subject is required. Please select or add a subject first."}), 400

    if task_type not in ("Assignment", "Revision"):
        return jsonify({"error": "Task type must be 'Assignment' or 'Revision'"}), 400

    if not due_date:
        return jsonify({"error": "Due date and time is required"}), 400

    if priority not in ("High", "Medium", "Low"):
        return jsonify({"error": "Priority must be 'High', 'Medium', or 'Low'"}), 400

    if status not in ("Pending", "Complete"):
        return jsonify({"error": "Status must be 'Pending' or 'Complete'"}), 400

    try:
        duration_mins = int(duration_mins)
        if duration_mins <= 0:
            return jsonify({"error": "Duration must be greater than 0 minutes"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid duration minutes"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validate subject belongs to this user
    cursor.execute("SELECT id, name, color FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    subj = cursor.fetchone()
    if not subj:
        conn.close()
        return jsonify({"error": "Selected subject does not exist or does not belong to you"}), 404

    cursor.execute("""
        INSERT INTO tasks (user_id, subject_id, title, description, task_type, due_date, priority, status, duration_mins)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, subject_id, title, description, task_type, due_date, priority, status, duration_mins))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    now_iso = datetime.now().isoformat()
    return jsonify({
        "message": "Task created successfully",
        "task": {
            "id": task_id,
            "title": title,
            "description": description,
            "task_type": task_type,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "duration_mins": duration_mins,
            "subject_id": subj["id"],
            "subject_name": subj["name"],
            "subject_color": subj["color"],
            "is_overdue": (status == "Pending" and due_date < now_iso)
        }
    }), 201

@task_bp.route("/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    user_id = request.user["id"]
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    subject_id = data.get("subject_id")
    task_type = data.get("task_type", "Assignment")
    due_date = (data.get("due_date") or "").strip()
    priority = data.get("priority", "Medium")
    status = data.get("status", "Pending")
    duration_mins = data.get("duration_mins", 45)
    description = (data.get("description") or "").strip()

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if not subject_id:
        return jsonify({"error": "Subject is required"}), 400

    if task_type not in ("Assignment", "Revision"):
        return jsonify({"error": "Task type must be 'Assignment' or 'Revision'"}), 400

    if not due_date:
        return jsonify({"error": "Due date and time is required"}), 400

    if priority not in ("High", "Medium", "Low"):
        return jsonify({"error": "Priority must be 'High', 'Medium', or 'Low'"}), 400

    if status not in ("Pending", "Complete"):
        return jsonify({"error": "Status must be 'Pending' or 'Complete'"}), 400

    try:
        duration_mins = int(duration_mins)
        if duration_mins <= 0:
            return jsonify({"error": "Duration must be greater than 0 minutes"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid duration minutes"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validate task belongs to user
    cursor.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    # Validate subject belongs to user
    cursor.execute("SELECT id, name, color FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    subj = cursor.fetchone()
    if not subj:
        conn.close()
        return jsonify({"error": "Selected subject does not exist or does not belong to you"}), 404

    cursor.execute("""
        UPDATE tasks
        SET subject_id = ?, title = ?, description = ?, task_type = ?,
            due_date = ?, priority = ?, status = ?, duration_mins = ?
        WHERE id = ? AND user_id = ?
    """, (subject_id, title, description, task_type, due_date, priority, status, duration_mins, task_id, user_id))
    conn.commit()
    conn.close()

    now_iso = datetime.now().isoformat()
    return jsonify({
        "message": "Task updated successfully",
        "task": {
            "id": task_id,
            "title": title,
            "description": description,
            "task_type": task_type,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "duration_mins": duration_mins,
            "subject_id": subj["id"],
            "subject_name": subj["name"],
            "subject_color": subj["color"],
            "is_overdue": (status == "Pending" and due_date < now_iso)
        }
    }), 200

@task_bp.route("/<int:task_id>/toggle", methods=["PATCH"])
@login_required
def toggle_task_status(task_id):
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    new_status = "Complete" if task["status"] == "Pending" else "Pending"
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?", (new_status, task_id, user_id))

    # If marked complete, remove any planned sessions for this task
    if new_status == "Complete":
        cursor.execute("DELETE FROM plan_sessions WHERE task_id = ? AND user_id = ?", (task_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Task marked as {new_status}",
        "task_id": task_id,
        "status": new_status
    }), 200

@task_bp.route("/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Task deleted successfully", "task_id": task_id}), 200
