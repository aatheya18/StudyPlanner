import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# SQLite database file named db.sql stored locally on device
DB_PATH = os.path.join(BASE_DIR, 'db.sql')

JWT_SECRET = os.getenv("JWT_SECRET", "meticul_super_secret_jwt_key_2026_spm")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days session
