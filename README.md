# Meticul — Intelligent Local Study Planner

**Meticul** is a complete, locally-run study planning application designed to organize subjects, prioritize assignments and revisions, and automatically generate optimized study schedules using an explainable machine learning scoring model.

---

## 🎨 Color Palette & Themes

Meticul follows a curated, cohesive color palette via CSS variables:

| Variable | Hex Value | Role in Light Theme | Role in Dark Theme |
| :--- | :--- | :--- | :--- |
| `--pitch-black` | `#0d0d07` | Primary dark text | App background |
| `--dark-khaki` | `#31311a` | Secondary text & borders | Card background |
| `--olive-leaf` | `#54552d` | Primary accent & brand | Secondary contrast |
| `--dusty-olive` | `#787940` | Hover accent | Hover accent |
| `--palm-leaf` | `#9b9d53` | Soft accents & indicators | Muted text & tags |
| `--muted-olive` | `#aaad5b` | Badges & borders | Borders |
| `--golden-sand` | `#bbbe64` | Subtle highlights | Primary dark accent |
| `--vanilla-custard` | `#d3d799` | Badge backgrounds | Secondary text |
| `--beige` | `#e9ebcc` | Sidebar & surface accents | Primary light text |
| `--white` | `#ffffff` | Clean card background | Highlights |

- **Light Theme (Default)**: Crisp beige/white backgrounds with dark-khaki/pitch-black typography and olive accents.
- **Dark Theme**: Pitch-black and dark-khaki backgrounds with beige/vanilla typography and golden-sand accents. Theme switching is instantaneous across all screens.

---

## 🚀 Tech Stack

- **Frontend**: React 18, Vite, Vanilla CSS design system, Lucide React icons.
- **Backend**: Python 3 (Flask), RESTful API with CORS enabled.
- **Database**: Local SQLite stored at `backend/db.sql` using Python's built-in `sqlite3` with foreign keys and `ON DELETE CASCADE`.
- **ML / Scoring**: `scikit-learn` (`MinMaxScaler`, weighted feature regression) for deadline, priority, and workload pressure ranking.

---

## 📁 Project Architecture

```
StudyPlannerTwo/
├── backend/
│   ├── app.py                 # Flask server initialization, CORS, blueprints, error handlers
│   ├── config.py              # Central backend configuration (JWT secret, DB path)
│   ├── db.py                  # SQLite3 schema definition, foreign keys, auto-init
│   ├── auth.py                # Password hashing (Werkzeug), JWT generation, @login_required
│   ├── planner.py             # ML urgency model and Earliest-Deadline-First schedule planner
│   ├── routes/
│   │   ├── auth_routes.py     # Signup, login, current authenticated user profile
│   │   ├── subject_routes.py  # Subject CRUD with task counts, cascade deletes, hex validation
│   │   ├── task_routes.py     # Task CRUD with multi-filtering, search, and sorting
│   │   ├── profile_routes.py  # Study preferences & 7-day availability
│   │   └── plan_routes.py     # Plan generator trigger & calendar session endpoints
│   ├── test_planner.py        # Planner unit tests (relaxed, tight, impossible deadlines)
│   ├── requirements.txt       # Flask, flask-cors, PyJWT, scikit-learn, numpy, werkzeug
│   └── db.sql                 # SQLite database file (created automatically on first launch)
├── frontend/
│   ├── package.json           # React, Vite, Lucide-react
│   ├── vite.config.js         # Vite dev configuration with proxy to backend port 5000
│   ├── index.html             # Entry HTML with Outfit & Inter typography
│   ├── public/
│   │   └── favicon.svg        # Custom Meticul SVG favicon
│   └── src/
│       ├── config.js          # Central API base URL configuration & palette swatches
│       ├── index.css          # Design system, CSS variables, dark/light themes, animations
│       ├── App.jsx            # Main app shell & route state
│       ├── context/
│       │   └── AuthContext.jsx # JWT session persistence, apiFetch wrapper, theme state
│       ├── components/
│       │   ├── Layout.jsx     # Navigation sidebar with active highlighting
│       │   ├── Modal.jsx      # Reusable animated dialog modal
│       │   ├── StatCard.jsx   # Metric card
│       │   └── Calendar/
│       │       ├── WeekView.jsx   # Hourly time-slot week schedule
│       │       └── MonthView.jsx  # Monthly calendar grid with session badges
│       └── pages/
│           ├── HomePage.jsx       # Landing page (Sign Up & Log In forms)
│           ├── DashboardPage.jsx  # Stat cards, plan generator, calendar view toggle, warnings
│           ├── TasksPage.jsx      # Task queue, search, filter by subject/status/priority, sort
│           ├── SubjectsPage.jsx   # Curriculum subjects, color swatches, cascade confirmation
│           └── ProfilePage.jsx    # Session lengths, study duration cap, 7-day availability, theme
└── README.md
```

---

## ⚙️ Local Setup and Run Instructions

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed

---

### Step 1: Start the Backend (Port 5000)

1. Open a terminal in the root directory:
   ```bash
   cd backend
   ```

2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the unit tests to verify the ML planner:
   ```bash
   python -m unittest test_planner.py
   ```

5. Start the Flask API server:
   ```bash
   python app.py
   ```
   *The server starts on `http://localhost:5000`. SQLite tables in `backend/db.sql` are created automatically.*

---

### Step 2: Start the Frontend (Port 5173)

1. Open a second terminal in the project root:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Open your browser at `http://localhost:5173`.*

---

## 🗄️ Database Schema (`backend/db.sql`)

The database uses SQLite with `PRAGMA foreign_keys = ON;`:

1. **`users`**:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `username` TEXT UNIQUE NOT NULL
   - `password_hash` TEXT NOT NULL
   - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

2. **`user_settings`**:
   - `user_id` INTEGER PRIMARY KEY REFERENCES `users(id)` ON DELETE CASCADE
   - `display_name` TEXT
   - `session_length` INTEGER DEFAULT 45 (minutes)
   - `break_length` INTEGER DEFAULT 15 (minutes)
   - `daily_duration_cap` INTEGER DEFAULT 240 (minutes)
   - `theme` TEXT DEFAULT 'light'
   - `updated_at` DATETIME

3. **`user_availability`**:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id` INTEGER REFERENCES `users(id)` ON DELETE CASCADE
   - `day_of_week` INTEGER (0 = Monday, ..., 6 = Sunday)
   - `is_enabled` INTEGER DEFAULT 1
   - `start_time` TEXT DEFAULT '09:00' (24-hour HH:MM)
   - `end_time` TEXT DEFAULT '18:00' (24-hour HH:MM)
   - UNIQUE(`user_id`, `day_of_week`)

4. **`subjects`**:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id` INTEGER REFERENCES `users(id)` ON DELETE CASCADE
   - `name` TEXT NOT NULL
   - `color` TEXT NOT NULL (Hex format `#RRGGBB`)
   - `description` TEXT
   - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

5. **`tasks`**:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id` INTEGER REFERENCES `users(id)` ON DELETE CASCADE
   - `subject_id` INTEGER REFERENCES `subjects(id)` ON DELETE CASCADE
   - `title` TEXT NOT NULL
   - `description` TEXT
   - `task_type` TEXT CHECK(task_type IN ('Assignment', 'Revision'))
   - `due_date` TEXT NOT NULL (ISO format)
   - `priority` TEXT CHECK(priority IN ('High', 'Medium', 'Low'))
   - `status` TEXT CHECK(status IN ('Pending', 'Complete')) DEFAULT 'Pending'
   - `duration_mins` INTEGER DEFAULT 45
   - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

6. **`plan_sessions`**:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id` INTEGER REFERENCES `users(id)` ON DELETE CASCADE
   - `task_id` INTEGER REFERENCES `tasks(id)` ON DELETE CASCADE
   - `session_date` TEXT NOT NULL (YYYY-MM-DD)
   - `start_time` TEXT NOT NULL (HH:MM)
   - `end_time` TEXT NOT NULL (HH:MM)
   - `duration_mins` INTEGER NOT NULL
   - `part_number` INTEGER DEFAULT 1
   - `total_parts` INTEGER DEFAULT 1
   - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

---

## 🧠 ML Urgency Model & Schedule Optimization

The planner in `backend/planner.py` uses scikit-learn and an Earliest-Deadline-First capacity model:

1. **Composite Feature Extraction**:
   - **Deadline Proximity**: $10.0 / \log_2(T_{\text{hours left}} + 2.0)$
   - **Workload Pressure**: $\min\left(10.0, \frac{\text{Duration (hours)}}{T_{\text{hours left}}}\right)$
   - **Priority Factor**: High ($3.0\times$), Medium ($2.0\times$), Low ($1.0\times$) with Assignment multiplier ($1.1\times$).
2. **scikit-learn Normalization**:
   - `MinMaxScaler()` normalizes the multidimensional feature matrix across the user's active tasks into $[0, 1]$.
   - Linear combination weights: $0.40 \times \text{Deadline} + 0.35 \times \text{Pressure} + 0.25 \times \text{Priority}$.
3. **Session Chunking & Break Insertion**:
   - Tasks longer than the preferred session length (e.g., 90m with 45m preference) split into sequential parts with scheduled breaks between sessions.
4. **Relaxed vs. Tight Constraints**:
   - Under normal conditions, daily study caps are enforced: $\le 3$ tasks per day and $\le \text{daily\_duration\_cap}$ (240m).
   - If upcoming deadlines cannot fit under relaxed limits, the algorithm switches to tight mode, utilizing the full day's availability window.
5. **Deadline Safeguards**:
   - No session is ever scheduled past its due date. Tasks that cannot fit before their deadline are flagged as **At Risk / Incomplete** with clear warnings on the Dashboard.
