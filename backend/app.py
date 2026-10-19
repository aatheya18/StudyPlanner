import os
from flask import Flask, jsonify
from flask_cors import CORS
from db import init_db
from routes.auth_routes import auth_bp
from routes.profile_routes import profile_bp
from routes.subject_routes import subject_bp
from routes.task_routes import task_bp
from routes.plan_routes import plan_bp

def create_app():
    app = Flask(__name__)

    # Enable CORS for local development with frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize SQLite database automatically
    init_db()

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(subject_bp, url_prefix="/api/subjects")
    app.register_blueprint(task_bp, url_prefix="/api/tasks")
    app.register_blueprint(plan_bp, url_prefix="/api/plan")

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "app": "Meticul Study Planner API"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Meticul Backend on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
