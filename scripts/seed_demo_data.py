import os
import sys

# Ensure workspace root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.database import SessionLocal, Base, engine
from backend.app.db.init_db import init_db

if __name__ == "__main__":
    print("Initializing database tables and demo seed data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        profile = init_db(db)
        print(f"Database successfully seeded for student: {profile.display_name}")
    finally:
        db.close()
