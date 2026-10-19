import sqlite3
import os
from config import DB_PATH

def get_db_connection():
    """Returns a SQLite connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes SQLite tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # User settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        display_name TEXT,
        session_length INTEGER DEFAULT 45,
        break_length INTEGER DEFAULT 15,
        daily_duration_cap INTEGER DEFAULT 240,
        theme TEXT DEFAULT 'light',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # User 7-day availability (0 = Monday, ..., 6 = Sunday)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL,
        is_enabled INTEGER DEFAULT 1,
        start_time TEXT DEFAULT '09:00',
        end_time TEXT DEFAULT '18:00',
        UNIQUE(user_id, day_of_week),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Subjects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        task_type TEXT CHECK(task_type IN ('Assignment', 'Revision')) NOT NULL,
        due_date TEXT NOT NULL,
        priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')) NOT NULL,
        status TEXT CHECK(status IN ('Pending', 'Complete')) DEFAULT 'Pending',
        duration_mins INTEGER DEFAULT 45,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    );
    """)

    # Generated Plan Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plan_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration_mins INTEGER NOT NULL,
        part_number INTEGER DEFAULT 1,
        total_parts INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def create_default_user_settings(user_id, display_name=None):
    """Creates default settings and 7-day availability for a new user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO user_settings (user_id, display_name, session_length, break_length, daily_duration_cap, theme)
    VALUES (?, ?, 45, 15, 240, 'light')
    """, (user_id, display_name or ""))

    # Default availability: Monday to Sunday enabled, 09:00 - 18:00
    for day in range(7):
        cursor.execute("""
        INSERT OR IGNORE INTO user_availability (user_id, day_of_week, is_enabled, start_time, end_time)
        VALUES (?, ?, 1, '09:00', '18:00')
        """, (user_id, day))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
