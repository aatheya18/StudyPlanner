from flask import Blueprint, request, jsonify
from db import get_db_connection, create_default_user_settings
from auth import hash_password, verify_password, create_token, login_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters long"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters long"}), 400
    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username is already taken"}), 409

    pwd_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, pwd_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Create default settings and availability
    create_default_user_settings(user_id, display_name=username)

    token = create_token(user_id, username)
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "display_name": username,
            "theme": "light"
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        conn.close()
        return jsonify({"error": "Invalid username or password"}), 401

    user_id = user["id"]
    cursor.execute("SELECT display_name, theme FROM user_settings WHERE user_id = ?", (user_id,))
    settings = cursor.fetchone()
    conn.close()

    display_name = settings["display_name"] if settings and settings["display_name"] else user["username"]
    theme = settings["theme"] if settings and settings["theme"] else "light"

    token = create_token(user_id, user["username"])
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user_id,
            "username": user["username"],
            "display_name": display_name,
            "theme": theme
        }
    }), 200

@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    user_id = request.user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("SELECT display_name, theme, session_length, break_length, daily_duration_cap FROM user_settings WHERE user_id = ?", (user_id,))
    settings = cursor.fetchone()
    conn.close()

    display_name = settings["display_name"] if settings and settings["display_name"] else user["username"]
    theme = settings["theme"] if settings and settings["theme"] else "light"

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "display_name": display_name,
        "theme": theme,
        "session_length": settings["session_length"] if settings else 45,
        "break_length": settings["break_length"] if settings else 15,
        "daily_duration_cap": settings["daily_duration_cap"] if settings else 240
    }), 200
