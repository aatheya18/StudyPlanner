# Meticul Study Planner — Verification & Architecture Report

## 1. Overview
**Meticul** has been built end-to-end as a locally-run study planner with a Flask REST API backend, SQLite3 database (`backend/db.sql`), scikit-learn ML urgency scoring, and a React + Vite frontend styled with the exact CSS color palette in both Light and Dark themes.

---

## 2. Browser E2E Test Recording
The browser session below validates user registration, subject creation, task creation with foreign key relations, ML plan generation with session chunking, Week & Month calendar views, and dark mode toggling:

![Meticul End-to-End Walkthrough](C:/Users/Windows 11/.gemini/antigravity-ide/brain/cf633fa4-7c56-4ba2-8143-27e0759de450/meticul_e2e_demo_1792405196540.webp)

---

## 3. Test Suites & Verification Results

### A. ML Study Planner Unit Tests (`backend/test_planner.py`)
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.013s

OK
```
1. **Urgency Scoring**: Tasks with tighter deadlines and higher priorities receive higher urgency scores via scikit-learn MinMaxScaler and weighted linear combination.
2. **Relaxed Scheduling**: When deadlines are relaxed, daily study is capped at `daily_duration_cap` (240 min) and at most 3 distinct tasks per day.
3. **Tight Deadlines**: When deadlines force crunch, the planner dynamically exceeds relaxed limits up to the full daily availability window.
4. **Impossible Deadlines**: Tasks that cannot fit before their deadline are not scheduled past due dates and are flagged as `is_at_risk = True`.
5. **Overdue Tasks**: Tasks with deadlines already in the past are never scheduled and immediately flagged at risk.

### B. Foreign Key & Cascade Deletion Test
```
CASCADE VERIFICATION PASSED!
```
- Verified that deleting a subject automatically removes all associated tasks and planned sessions via SQLite foreign keys (`ON DELETE CASCADE`).

---

## 4. Quick Execution Guide

### Backend Server:
```bash
cd backend
pip install -r requirements.txt
python app.py
```
*API runs on `http://localhost:5000` (SQLite database initialized at `backend/db.sql`).*

### Frontend Development Server:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*
