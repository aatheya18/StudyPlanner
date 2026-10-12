# AI-Powered Study Planner — Increments 1 & 2

A modern, student-centric academic productivity application built with **React**, **TypeScript**, **FastAPI**, **SQLAlchemy**, and a **TensorFlow/Keras** neural network recommendation pipeline.

---

## 1. System Features

### Increment 1 — Core Study Planner (Rule-Based)
- **Student Profile & Preferences**: Configure student name, timezone, preferred session duration (45 min), break duration (15 min), and maximum daily study duration (240 min).
- **Weekly Availability Windows**: Configure active study windows for each day of the week (Monday through Sunday).
- **Subject Management**: Create, edit, and delete academic courses with custom color tags and descriptions, featuring protective referential checks to prevent orphaned tasks.
- **Task Management**: Create, edit, delete, search, filter (by subject, priority, status), and sort academic tasks with strict validation.
- **Rule-Based Scheduling Engine**: Deterministically scores tasks based on deadline urgency, priority weight, and estimated duration; splits tasks into manageable sessions; respects availability windows and daily limits; and provides an unscheduled tasks report if deadlines cannot be met.
- **Calendar & Session Tracking**: Weekly timetable view showing scheduled study blocks with options to mark completed (recording actual duration) or skipped.
- **Dashboard & Progress Tracking**: Real-time summary cards, today's sessions, tasks due within 72 hours, overdue alerts, and an interactive 7-day progress chart.
- **In-App Reminders**: Real-time notifications for upcoming sessions, approaching deadlines, and overdue tasks.

### Increment 2 — AI Scheduling Suggestions
- **Dataset Pipeline**: Synthetic demonstration dataset of 1,500 candidate study slots reflecting realistic study patterns and fatigue dynamics.
- **Feature Preprocessing**: `StandardScaler` for numerical metrics and `OneHotEncoder` for categorical factors, with artifact persistence to prevent data leakage.
- **Keras Neural Network**: Deep Sequential neural network with Dropout regularization and Sigmoid suitability scoring, benchmarked against `DummyClassifier` and `LogisticRegression` baselines.
- **AI Recommendation Engine**: Evaluates candidate slots and ranks them by suitability score while strictly enforcing hard constraints (no overlaps, before deadline, within daily limits).
- **Interactive Suggestions UI**: Dedicated AI Suggestions screen with suitability percentages, human-readable model insights, and one-click Accept (persists `StudySession`) or Decline actions with feedback recording.

---

## 2. Prerequisites
- **Python**: 3.10+ (Tested on Python 3.11.5)
- **Node.js**: 18+ (Tested on Node.js v22.13.0)
- **npm**: 9+
- **Docker** *(Optional)*: For running PostgreSQL via Docker Compose

---

## 3. Quick Start & Execution

### Step 1: Backend Setup & Dependencies
```bash
# From workspace root
pip install -r backend/requirements.txt
```

### Step 2: Database Initialization & Migrations
The application defaults to SQLite (`sqlite:///./study_planner.db`) for immediate out-of-the-box execution, and fully supports PostgreSQL via `DATABASE_URL` in `backend/.env`.

Run the database migrations:
```bash
alembic -c backend/alembic.ini upgrade head
```

Seed demo subjects, tasks, and student preferences:
```bash
python scripts/seed_demo_data.py
```

### Step 3: Train Machine Learning Model (Increment 2)
Generate the dataset, train the Keras neural network, and evaluate against baselines:
```bash
python scripts/train_model.py
```
*(Model artifacts and metadata will be saved to `backend/app/ml/artifacts/`)*

To evaluate the trained model on an independent holdout set:
```bash
python -m backend.app.ml.evaluate
```

### Step 4: Run Backend Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The interactive API documentation is available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 5: Frontend Setup & Execution
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: [http://localhost:5173](http://localhost:5173)

---

## 4. Running Automated Tests

Run the full automated test suite (14 end-to-end unit and integration tests):
```bash
pytest backend/tests -v
```

Build and validate the frontend TypeScript bundle:
```bash
cd frontend
npm run build
```

---

## 5. PostgreSQL via Docker (Optional)

To run with PostgreSQL instead of SQLite:
1. Start the PostgreSQL container:
   ```bash
   docker compose up -d
   ```
2. In `backend/.env`, set:
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/study_planner
   ```
3. Run migrations and seed data:
   ```bash
   alembic -c backend/alembic.ini upgrade head
   python scripts/seed_demo_data.py
   ```

---

## 6. End-to-End Smoke Test Checklist

- [x] **Dashboard**: Open [http://localhost:5173](http://localhost:5173). Verify planned study duration, completed minutes, and 7-day chart render correctly.
- [x] **Task Creation**: Navigate to **Tasks**, click **New Task**, fill out the form and submit. Verify the task appears in the filtered list.
- [x] **Subject Protection**: Navigate to **Subjects**, attempt to delete a subject with existing tasks. Verify an alert prevents deletion.
- [x] **Rule-Based Scheduler**: Navigate to **Calendar & Sessions**, click **Generate Schedule**, choose a 7-day horizon, and confirm. Verify non-overlapping study blocks appear across the week.
- [x] **Session Completion**: Click a scheduled block on the calendar, enter actual study duration (e.g. 50 mins), and click **Complete Session**. Verify the block turns green and dashboard stats update.
- [x] **AI Recommendations**: Navigate to **AI Recommendations**, click **Generate AI Suggestions**. Verify cards appear with Match %, slot time, and model explanations.
- [x] **Accept Suggestion**: Click **Accept Slot** on an AI card. Verify a new study session is booked on the calendar and feedback is recorded.
- [x] **Preferences & Windows**: Navigate to **Profile & Settings**, update preferred session duration or daily availability, click **Save Settings**, and confirm success banner.

---

## 7. Machine Learning Limitations & Notes
- **Synthetic Ground Truth**: The model is trained on a synthetic demonstration dataset of 1,500 candidate slots reflecting simulated study fatigue and urgency curves. In real-world deployments, real task completion logs should replace synthetic samples over time.
- **Hard Constraints Precedence**: Hard scheduling rules (deadlines, availability windows, overlap prevention) always take strict precedence over neural network suitability predictions.
- **Graceful Fallback**: If model artifacts are missing or corrupted, the system seamlessly operates in heuristic fallback mode without service interruption.
