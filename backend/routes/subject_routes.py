import re
from flask import Blueprint, request, jsonify
from db import get_db_connection
from auth import login_required

subject_bp = Blueprint("subjects", __name__)

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")

@subject_bp.route("", methods=["GET"])
@login_required
def get_subjects():
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve subjects along with count of associated tasks
    cursor.execute("""
        SELECT s.id, s.name, s.color, s.description, s.created_at,
               COUNT(t.id) as task_count
        FROM subjects s
        LEFT JOIN tasks t ON s.id = t.subject_id AND t.user_id = ?
        WHERE s.user_id = ?
        GROUP BY s.id
        ORDER BY s.name ASC
    """, (user_id, user_id))
    rows = cursor.fetchall()
    conn.close()

    subjects = [
        {
            "id": r["id"],
            "name": r["name"],
            "color": r["color"],
            "description": r["description"] or "",
            "task_count": r["task_count"],
            "created_at": r["created_at"]
        }
        for r in rows
    ]
    return jsonify(subjects), 200

@subject_bp.route("", methods=["POST"])
@login_required
def create_subject():
    user_id = request.user["id"]
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    color = (data.get("color") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify({"error": "Subject name is required"}), 400

    if not color or not HEX_COLOR_REGEX.match(color):
        return jsonify({"error": "Valid hex color code is required (e.g., #54552d)"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for duplicate subject name for this user
    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND LOWER(name) = LOWER(?)", (user_id, name))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": f"A subject named '{name}' already exists"}), 409

    cursor.execute("""
        INSERT INTO subjects (user_id, name, color, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, name, color, description))
    subject_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subject created successfully",
        "subject": {
            "id": subject_id,
            "name": name,
            "color": color,
            "description": description,
            "task_count": 0
        }
    }), 201

@subject_bp.route("/<int:subject_id>", methods=["PUT"])
@login_required
def update_subject(subject_id):
    user_id = request.user["id"]
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    color = (data.get("color") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify({"error": "Subject name is required"}), 400

    if not color or not HEX_COLOR_REGEX.match(color):
        return jsonify({"error": "Valid hex color code is required (e.g., #54552d)"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute("SELECT id FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Subject not found"}), 404

    # Check duplicate name with other subject
    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND LOWER(name) = LOWER(?) AND id != ?", (user_id, name, subject_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Another subject named '{name}' already exists"}), 409

    cursor.execute("""
        UPDATE subjects
        SET name = ?, color = ?, description = ?
        WHERE id = ? AND user_id = ?
    """, (name, color, description, subject_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subject updated successfully",
        "subject": {
            "id": subject_id,
            "name": name,
            "color": color,
            "description": description
        }
    }), 200

@subject_bp.route("/<int:subject_id>/task-count", methods=["GET"])
@login_required
def get_subject_task_count(subject_id):
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    subj = cursor.fetchone()
    if not subj:
        conn.close()
        return jsonify({"error": "Subject not found"}), 404

    cursor.execute("SELECT COUNT(id) as count FROM tasks WHERE subject_id = ? AND user_id = ?", (subject_id, user_id))
    task_count = cursor.fetchone()["count"]
    conn.close()

    return jsonify({
        "subject_id": subject_id,
        "subject_name": subj["name"],
        "task_count": task_count
    }), 200

@subject_bp.route("/<int:subject_id>", methods=["DELETE"])
@login_required
def delete_subject(subject_id):
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    subj = cursor.fetchone()
    if not subj:
        conn.close()
        return jsonify({"error": "Subject not found"}), 404

    # Count tasks that will be deleted
    cursor.execute("SELECT COUNT(id) as count FROM tasks WHERE subject_id = ? AND user_id = ?", (subject_id, user_id))
    deleted_task_count = cursor.fetchone()["count"]

    # Delete subject with cascade to tasks and plan_sessions
    cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Subject '{subj['name']}' and its {deleted_task_count} tasks deleted successfully",
        "deleted_tasks_count": deleted_task_count
    }), 200
