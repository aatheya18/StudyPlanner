import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

def hash_password(password: str) -> str:
    """Hashes a plaintext password securely."""
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a plaintext password against the stored hash."""
    return check_password_hash(password_hash, password)

def create_token(user_id: int, username: str) -> str:
    """Creates a signed JWT token valid for the configured expiration period."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str):
    """Decodes a JWT token, returning the payload or None if invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    """Decorator to enforce JWT authentication on Flask routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication token missing or invalid format"}), 401
        
        token = auth_header.split(" ")[1].strip()
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Token is expired or invalid"}), 401
        
        # Attach user info to request
        request.user = {
            "id": payload.get("user_id"),
            "username": payload.get("username")
        }
        return f(*args, **kwargs)
    return decorated_function
