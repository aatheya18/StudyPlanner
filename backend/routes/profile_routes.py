import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from db import get_db_connection
from auth import login_required

profile_bp = Blueprint("profile", __name__)

TIME_REGEX = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

@profile_bp.route("", methods=["GET"])
@login_required
def get_profile():
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch settings
    cursor.execute("""
        SELECT display_name, session_length, break_length, daily_duration_cap, theme
        FROM user_settings WHERE user_id = ?
    """, (user_id,))
    settings_row = cursor.fetchone()

    # Fetch availability for all 7 days (0=Mon, ..., 6=Sun)
    cursor.execute("""
        SELECT day_of_week, is_enabled, start_time, end_time
        FROM user_availability WHERE user_id = ?
        ORDER BY day_of_week ASC
    """, (user_id,))
    avail_rows = cursor.fetchall()
    conn.close()

    availability = [
        {
            "day_of_week": r["day_of_week"],
            "is_enabled": bool(r["is_enabled"]),
            "start_time": r["start_time"],
            "end_time": r["end_time"]
        }
        for r in avail_rows
    ]

    # Fill default if days are missing
    existing_days = {a["day_of_week"] for a in availability}
    for d in range(7):
        if d not in existing_days:
            availability.append({
                "day_of_week": d,
                "is_enabled": True,
                "start_time": "09:00",
                "end_time": "18:00"
            })
    availability.sort(key=lambda x: x["day_of_week"])

    settings = {
        "display_name": settings_row["display_name"] if settings_row and settings_row["display_name"] else request.user["username"],
        "session_length": settings_row["session_length"] if settings_row else 45,
        "break_length": settings_row["break_length"] if settings_row else 15,
        "daily_duration_cap": settings_row["daily_duration_cap"] if settings_row else 240,
        "theme": settings_row["theme"] if settings_row else "light"
    }

    return jsonify({
        "settings": settings,
        "availability": availability
    }), 200

@profile_bp.route("", methods=["PUT"])
@login_required
def update_profile():
    user_id = request.user["id"]
    data = request.get_json() or {}
    settings = data.get("settings") or {}
    availability = data.get("availability") or []

    # Validation
    display_name = (settings.get("display_name") or "").strip()
    session_length = settings.get("session_length")
    break_length = settings.get("break_length")
    daily_duration_cap = settings.get("daily_duration_cap")
    theme = (settings.get("theme") or "light").lower()

    if theme not in ("light", "dark"):
        return jsonify({"error": "Theme must be either 'light' or 'dark'"}), 400

    try:
        session_length = int(session_length)
        break_length = int(break_length)
        daily_duration_cap = int(daily_duration_cap)
    except (TypeError, ValueError):
        return jsonify({"error": "Session length, break length, and daily duration cap must be valid integers"}), 400

    if session_length <= 0 or break_length < 0 or daily_duration_cap <= 0:
        return jsonify({"error": "Session length and daily duration must be positive numbers. Break length cannot be negative."}), 400

    if session_length > daily_duration_cap:
        return jsonify({"error": "Session length cannot be greater than the total daily study duration."}), 400

    # Validate availability list
    if not isinstance(availability, list):
        return jsonify({"error": "Availability must be a list of 7 days"}), 400

    validated_avail = []
    for day_item in availability:
        try:
            dow = int(day_item.get("day_of_week"))
            if dow < 0 or dow > 6:
                return jsonify({"error": f"Invalid day_of_week: {dow}"}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "day_of_week must be an integer between 0 and 6"}), 400

        is_enabled = 1 if day_item.get("is_enabled") else 0
        start_time = str(day_item.get("start_time", "09:00")).strip()
        end_time = str(day_item.get("end_time", "18:00")).strip()

        if not TIME_REGEX.match(start_time) or not TIME_REGEX.match(end_time):
            return jsonify({"error": f"Invalid time format for day {dow}. Please use HH:MM 24-hour format."}), 400

        # Check end_time is after start_time if enabled
        if is_enabled:
            s_h, s_m = map(int, start_time.split(":"))
            e_h, e_m = map(int, end_time.split(":"))
            if (e_h * 60 + e_m) <= (s_h * 60 + s_m):
                return jsonify({"error": f"End time must be after start time for day {dow}."}), 400

        validated_avail.append((user_id, dow, is_enabled, start_time, end_time))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update or insert settings
    cursor.execute("""
        INSERT INTO user_settings (user_id, display_name, session_length, break_length, daily_duration_cap, theme, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            display_name = excluded.display_name,
            session_length = excluded.session_length,
            break_length = excluded.break_length,
            daily_duration_cap = excluded.daily_duration_cap,
            theme = excluded.theme,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, display_name or request.user["username"], session_length, break_length, daily_duration_cap, theme))

    # Update or insert availability
    for item in validated_avail:
        cursor.execute("""
            INSERT INTO user_availability (user_id, day_of_week, is_enabled, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, day_of_week) DO UPDATE SET
                is_enabled = excluded.is_enabled,
                start_time = excluded.start_time,
                end_time = excluded.end_time
        """, item)

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Settings updated successfully",
        "settings": {
            "display_name": display_name or request.user["username"],
            "session_length": session_length,
            "break_length": break_length,
            "daily_duration_cap": daily_duration_cap,
            "theme": theme
        }
    }), 200
