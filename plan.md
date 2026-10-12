# Build an AI-Powered Study Planner — Increment 1 and Increment 2

## 1. Project Overview

Build a complete, runnable web application named **AI-Powered Study Planner**. The application will help students organize academic tasks, manage deadlines, generate study schedules, monitor progress, and receive machine-learning-based scheduling recommendations.

The project follows an incremental software development model. Implement only the first two increments described below.

### Increment 1 — Basic Study Planner

Build a fully functional study planner using conventional rule-based scheduling. Do not use AI or machine learning to generate the initial schedule.

### Increment 2 — AI Scheduling Suggestions

Add a machine-learning pipeline that analyzes task and availability features and generates scheduling recommendations. Integrate these recommendations into the existing application without breaking Increment 1 functionality.

Do not implement later-increment features such as adaptive rescheduling based on long-term performance, exam-readiness prediction, deadline-risk prediction, Google Calendar integration, or Trello integration.

## 2. Instructions Before Development

1. Inspect the existing workspace and repository before creating or modifying files.
2. If an application already exists, preserve useful existing code and extend it rather than replacing everything.
3. If the workspace is empty, create the complete project structure described below.
4. Implement the project in small, verifiable steps, starting with the backend and database foundation, followed by Increment 1, then Increment 2.
5. Do not merely create mock screens or a static prototype. All core features must work end to end.
6. Do not leave buttons, forms, API calls, database operations, or AI recommendations as placeholders.
7. Use clean, modular, maintainable code with clear naming, error handling, validation, and appropriate separation of responsibilities.
8. Do not invent successful ML results. If no real dataset is available, create a documented synthetic demonstration dataset and clearly state its limitations.
9. Run the available tests and build commands. Fix implementation errors before declaring the application complete.
10. Maintain a README with exact setup, configuration, database migration, model-training, testing, and execution commands.

If an important implementation decision is unspecified, choose a sensible default, document the assumption, and continue rather than stopping for unnecessary clarification.

## 3. Technology Stack

Use the following technologies:

### Frontend
- TypeScript
- React
- Vite
- Tailwind CSS
- React Router for navigation
- A suitable React calendar library, such as FullCalendar
- A lightweight charting library if charts are needed
- Fetch API or Axios for REST API communication

### Backend
- Python
- FastAPI
- Pydantic for request and response validation
- SQLAlchemy for database access
- Alembic for database migrations

### Database
- PostgreSQL
- Use relational tables, primary keys, foreign keys, indexes where appropriate, and database constraints.

### Machine Learning
- Python
- Pandas and NumPy for data processing
- TensorFlow/Keras for model training and inference
- scikit-learn for data splitting, preprocessing utilities, and evaluation metrics
- Persist the trained model and its associated preprocessing configuration.

### Testing and Development
- Pytest for backend and ML tests
- Vitest and React Testing Library for frontend tests
- Git for version control
- Environment variables for configuration and credentials

Use compatible, stable package versions and include all required dependencies in the appropriate dependency files.

## 4. Required Application Modules

### Module A: Student Profile and Study Preferences

Implement:
- Create and edit a local student profile.
- Store the student's name or display name.
- Store preferred study start and end times.
- Store available study days and time ranges.
- Configure preferred session duration.
- Configure break duration between sessions.
- Configure a maximum daily study duration.
- Store the student's timezone.
- Validate preferences before generating a schedule.

For the initial MVP, a single local/demo profile is acceptable. Do not introduce complex authentication unless the existing project already has it.

### Module B: Subject Management

Implement:
- Create, view, edit, and delete subjects.
- Store subject name, optional description, and optional display color.
- Associate tasks with subjects.
- Prevent deletion from silently orphaning tasks; use an appropriate restriction or explicit confirmation and handling strategy.

### Module C: Task Management

Each task should support:
- Title
- Description
- Subject
- Task type, such as assignment, revision, reading, or practice
- Due date and time
- Estimated duration in minutes
- Priority: Low, Medium, or High
- Status: Pending, In Progress, or Completed
- Optional earliest start date
- Creation and update timestamps

Implement:
- Create, view, edit, and delete tasks.
- Search and filter by subject, status, priority, and deadline.
- Sort by due date, priority, or estimated duration.
- Validate required fields, positive durations, valid dates, and subject references.
- Provide useful empty states and clear error messages.

### Module D: Rule-Based Scheduling Engine — Increment 1

Create a dedicated scheduling module in the backend. Do not put scheduling logic directly inside API route handlers.

The scheduler must:
1. Retrieve incomplete tasks and the student's availability.
2. Identify feasible study slots within the planning horizon.
3. Prioritize tasks using a documented rule-based scoring system that considers:
   - Deadline urgency
   - Task priority
   - Estimated duration
   - Available study time
4. Schedule tasks only within available study periods.
5. Avoid overlapping sessions.
6. Respect maximum daily study time and configured breaks.
7. Split long tasks into smaller sessions when feasible.
8. Avoid scheduling sessions after a task's deadline.
9. Report tasks that cannot be scheduled rather than silently discarding them.
10. Allow the user to regenerate a schedule.
11. Validate all generated sessions before saving them.

Use deterministic rules and scoring for Increment 1. Do not call the ML model from this module.

If tasks cannot fit within available time, show a clear unscheduled-task list with reasons. Do not falsely report that all tasks have been scheduled.

### Module E: Calendar and Study Sessions

Implement:
- Weekly calendar or agenda view.
- Daily view of scheduled study sessions.
- Display task title, subject, time range, and status.
- View session details.
- Mark a session as completed or skipped.
- Record actual study duration if the user provides it.
- Allow manual session adjustments where feasible.
- Prevent invalid or overlapping session changes.
- Keep task status and session status consistent.

A task may have multiple study sessions. Track task-level completion separately from session-level completion so that completing one session does not automatically mark a multi-session task as complete.

### Module F: Dashboard and Progress Tracking

Create a dashboard displaying:
- Today's scheduled sessions.
- Tasks due soon.
- Overdue tasks.
- Pending and completed tasks.
- Total planned study time.
- Completed study time.
- Upcoming deadlines.
- A simple weekly progress chart.

All dashboard data must be derived from persisted application data through backend APIs. Do not hardcode dashboard statistics.

### Module G: Reminders

Implement basic in-app reminders for:
- Upcoming scheduled sessions.
- Approaching task deadlines.
- Overdue tasks.

Use a simple, reliable mechanism suitable for a local MVP. If scheduled background reminders are implemented, document how the background process runs. Do not claim email or push notifications are supported unless actually implemented.

### Module H: Dataset Preparation and Feature Engineering — Increment 2

Create a separate ML package.

Define a documented dataset schema containing appropriate features, such as:
- Task priority
- Task type
- Estimated duration
- Time remaining until deadline
- Day of week
- Candidate study-slot start time
- Student availability
- Planned workload for that day
- Subject or task category where useful
- Historical task/session outcomes when legitimately available

Create a preprocessing pipeline that:
- Validates dataset columns and data types.
- Handles missing and invalid values.
- Encodes categorical features.
- Processes numerical features consistently.
- Prevents information leakage from future outcomes.
- Separates training, validation, and test data appropriately.
- Saves preprocessing artifacts needed during inference.

Do not assume that a dataset containing only task descriptions and deadlines provides reliable labels about whether a student will complete a task successfully.

If real labeled data is unavailable:
- Generate a small, reproducible synthetic dataset.
- Document how the synthetic labels are generated.
- Clearly distinguish synthetic examples from real student observations.
- Make it possible to replace the dataset later without changing the API contract.

### Module I: ML Model Training and Evaluation — Increment 2

Implement a reproducible training pipeline.

Define the prediction target explicitly. For the first version, use a binary classification target such as whether a candidate task-slot combination is considered suitable according to the documented dataset labeling rules.

The model must estimate suitability for candidate slots, not generate an entire schedule independently.

Requirements:
- Train a TensorFlow/Keras model using the prepared features.
- Compare model performance against a documented simple baseline.
- Use an appropriate train/validation/test strategy.
- Evaluate with suitable metrics such as precision, recall, F1, and ROC-AUC when valid for the label distribution.
- Report class distribution and disclose limitations of synthetic or small datasets.
- Save the trained model and preprocessing configuration.
- Include a reproducible command to train or retrain the model.
- Provide a model status check and meaningful error handling when model artifacts are missing or invalid.
- Never report fabricated evaluation scores.
- Do not automatically retrain the model from user feedback in this increment.

If the available data cannot support meaningful evaluation, make that limitation explicit and keep the recommendation feature operational in a clearly labeled demo mode.

### Module J: AI Recommendation Service — Increment 2

Create a separate recommendation service that can be invoked by the backend.

Its responsibilities:
1. Receive eligible tasks, student preferences, and candidate time slots.
2. Extract the same features used during training.
3. Load the saved model and preprocessing artifacts.
4. Score candidate task-slot combinations.
5. Rank feasible candidates by model score, combined with documented scheduling considerations.
6. Apply hard constraints after scoring.
7. Return recommended slots and human-readable reasons.
8. Report tasks for which no feasible recommendation exists.
9. Handle missing model artifacts and prediction errors safely.

Hard constraints must take precedence over ML scores. The model must never recommend a slot outside the student's availability, an overlapping slot, or a slot after the relevant task deadline.

The recommendation service must not directly write to the database. The main backend owns persistence and validation.

Keep the recommendation service separate from the baseline scheduler so that each can be tested independently.

### Module K: AI Suggestions Interface and Feedback

Implement:
- A dedicated AI Suggestions page or a clear AI recommendations section in the scheduling interface.
- A button to generate or refresh suggestions.
- Display recommended task, date, start time, end time, and score or suitability indicator.
- Explain recommendations using available factors, such as urgency, available time, and estimated duration.
- Clearly label model scores as estimates, not guarantees.
- Allow students to accept or reject recommendations.
- Allow regeneration of suggestions.
- Record feedback, including the recommendation, action, and timestamp.

When the user accepts a recommendation:
- Revalidate it on the backend.
- Verify that the task still needs work.
- Verify availability, deadline, daily limits, and conflicts.
- Save the session only if valid.
- Return an understandable error if the recommendation has become invalid.

When the user rejects a recommendation:
- Record the rejection.
- Do not change the saved schedule.

Feedback is for measurement and future development only in this increment. Do not imply that the model immediately learns or updates itself after each feedback action.

## 5. Database Design

Create normalized relational models and migrations for at least the following entities:

1. StudentProfile
2. Subject
3. Task
4. StudySession
5. AvailabilityWindow or equivalent study-availability representation
6. StudyPreference, if preferences are not stored directly on StudentProfile
7. Recommendation
8. RecommendationFeedback

Suggested fields:

### StudentProfile
- id
- display_name
- timezone
- created_at
- updated_at

### Subject
- id
- student_id or profile_id
- name
- description
- color
- created_at
- updated_at

### Task
- id
- subject_id
- title
- description
- task_type
- due_at
- earliest_start_at, nullable
- estimated_duration_minutes
- priority
- status
- created_at
- updated_at

### StudySession
- id
- task_id
- start_at
- end_at
- status
- actual_duration_minutes, nullable
- created_at
- updated_at

### AvailabilityWindow
- id
- profile_id
- day_of_week
- start_time
- end_time
- is_active

### StudyPreference
- id
- profile_id
- preferred_session_minutes
- break_duration_minutes
- maximum_daily_study_minutes
- created_at
- updated_at

### Recommendation
- id
- task_id
- recommended_start_at
- recommended_end_at
- suitability_score, nullable
- model_version
- explanation
- status
- created_at

### RecommendationFeedback
- id
- recommendation_id
- action
- feedback_note, nullable
- created_at

Adapt this schema when necessary, but preserve referential integrity and the required relationships. Avoid storing the same information redundantly without a clear reason.

Use UTC for persisted timestamps where appropriate and convert to the student's configured timezone for display. Define consistent handling of recurring weekly availability, daylight-saving changes where applicable, and date-only deadlines.

Use database migrations rather than relying on automatic table creation in production-style application startup.

## 6. API Design

Create REST APIs with consistent request/response formats and validation.

Suggested endpoints:

### Profile and Preferences
- GET /api/profile
- PUT /api/profile
- GET /api/preferences
- PUT /api/preferences

### Subjects
- GET /api/subjects
- POST /api/subjects
- GET /api/subjects/{subject_id}
- PUT /api/subjects/{subject_id}
- DELETE /api/subjects/{subject_id}

### Tasks
- GET /api/tasks
- POST /api/tasks
- GET /api/tasks/{task_id}
- PUT /api/tasks/{task_id}
- DELETE /api/tasks/{task_id}

Support appropriate filtering and sorting through query parameters.

### Scheduling and Sessions
- POST /api/schedules/generate
- GET /api/schedules
- GET /api/schedules?start=...&end=...
- GET /api/sessions
- PUT /api/sessions/{session_id}
- POST /api/sessions/{session_id}/complete
- POST /api/sessions/{session_id}/skip

### Dashboard and Reminders
- GET /api/dashboard
- GET /api/reminders

### AI Recommendations
- POST /api/ai/recommendations/generate
- GET /api/ai/recommendations
- POST /api/ai/recommendations/{recommendation_id}/accept
- POST /api/ai/recommendations/{recommendation_id}/reject
- GET /api/ai/status

You may adjust the exact endpoints to maintain a clean API, but document the final contract.

Use appropriate HTTP methods and status codes. Validate all input on the backend. Return actionable error messages without exposing stack traces, database credentials, or internal implementation details.

Enable CORS only for the configured frontend origin.

## 7. Module Interconnection and Data Flow

Implement the following flows.

### Flow A: Creating a Task
React task form → FastAPI task endpoint → validation → SQLAlchemy → PostgreSQL → response → refresh task list and dashboard.

### Flow B: Generating a Baseline Schedule
Student preferences + availability + incomplete tasks → rule-based scheduler → conflict and deadline validation → persist study sessions → return schedule → render calendar.

### Flow C: Generating AI Suggestions
Existing tasks + preferences + candidate slots → recommendation endpoint → feature extraction → saved preprocessing pipeline → TensorFlow model → ranked candidates → hard-constraint validation → recommendation response → AI Suggestions UI.

### Flow D: Accepting a Recommendation
Student accepts suggestion → backend revalidates task and slot → save StudySession → update recommendation status → refresh calendar and dashboard.

### Flow E: Recording Feedback
Student rejects or accepts a suggestion → persist RecommendationFeedback → make feedback available for later analysis. Do not retrain automatically.

Keep the frontend, core backend logic, scheduling algorithm, database models, and ML pipeline in separate modules.

## 8. Suggested Repository Structure

Create a structure similar to the following:

study-planner/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── tasks/
│   │   │   ├── subjects/
│   │   │   ├── calendar/
│   │   │   └── recommendations/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── profile/
│   │   │   ├── preferences/
│   │   │   ├── tasks/
│   │   │   ├── subjects/
│   │   │   ├── schedule/
│   │   │   ├── dashboard/
│   │   │   └── recommendations/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── task_service.py
│   │   │   ├── scheduling_service.py
│   │   │   ├── session_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── recommendation_service.py
│   │   ├── scheduling/
│   │   │   ├── rules.py
│   │   │   ├── candidate_slots.py
│   │   │   └── constraints.py
│   │   ├── ml/
│   │   │   ├── data_preparation.py
│   │   │   ├── features.py
│   │   │   ├── train.py
│   │   │   ├── evaluate.py
│   │   │   ├── predict.py
│   │   │   └── artifacts/
│   │   ├── main.py
│   │   └── config.py
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── data/
│   ├── sample/
│   └── README.md
├── scripts/
├── docs/
├── docker-compose.yml
├── .gitignore
└── README.md

This is a logical guide, not a requirement to create empty files. Create files only when needed and ensure imports, configuration, and commands work. If the project already has an established structure, adapt this layout without unnecessarily duplicating components.

Do not commit generated model binaries, local secrets, virtual environments, dependency caches, or database data files.

## 9. User Interface and Experience

Create a polished, modern, student-friendly productivity application.

Include:
- A consistent sidebar or top navigation.
- Dashboard.
- Tasks.
- Subjects.
- Weekly calendar.
- Study preferences.
- AI Suggestions.
- Clear loading, success, empty, and error states.
- Responsive desktop and mobile layouts.
- Accessible labels, keyboard-friendly controls, and readable contrast.
- Confirmation before destructive actions.
- Consistent date/time formatting.
- Toast notifications or equivalent user feedback.

Use a coherent visual design system with reusable buttons, forms, cards, dialogs, and badges. Avoid excessive animations and unnecessary visual clutter.

Do not prioritize visual polish over functional correctness.

## 10. Testing Requirements

### Increment 1 tests
- Create, update, retrieve, and delete tasks.
- Create and associate subjects.
- Validate invalid task durations and dates.
- Generate a schedule for available tasks.
- Verify that sessions never overlap.
- Verify that sessions respect availability and daily limits.
- Verify that sessions are not scheduled after deadlines.
- Verify that unschedulable tasks are reported.
- Verify session completion and task-status consistency.
- Verify dashboard values against database records.
- Verify data persistence across application restarts.

### Increment 2 tests
- Validate dataset schemas and missing-data handling.
- Verify preprocessing is consistent between training and inference.
- Verify reproducible training and model artifact loading.
- Verify model evaluation handles class imbalance and invalid metrics appropriately.
- Verify recommendation API request and response schemas.
- Verify that AI recommendations respect all hard scheduling constraints.
- Verify that a missing or broken model does not crash the basic planner.
- Verify accepting a recommendation persists a valid session.
- Verify rejecting a recommendation records feedback without changing the schedule.
- Verify duplicate requests or repeated acceptance do not create duplicate sessions.
- Verify the UI handles an empty recommendation list and ML-service errors.

Use unit tests, API integration tests, and frontend component tests where appropriate. Add an end-to-end smoke-test checklist to the README.

## 11. Acceptance Criteria

Increment 1 is complete only when:
- A user can create and manage subjects, tasks, and study preferences.
- Tasks and schedules persist in PostgreSQL.
- The rule-based scheduler generates a feasible schedule.
- Invalid and unschedulable sessions are handled transparently.
- The calendar, task views, and dashboard reflect saved data.
- Users can record session completion and see progress.
- The frontend communicates with the backend through working APIs.
- The application can be run from documented instructions.

Increment 2 is complete only when:
- The dataset preparation and training pipeline can be executed with documented commands.
- The model's target, features, and limitations are documented.
- Evaluation compares the trained model with a baseline.
- The saved model can be loaded by the recommendation service.
- The UI can request and display real model-generated recommendations.
- Recommendations pass hard scheduling constraints.
- Users can accept or reject recommendations.
- Feedback is stored persistently.
- Missing model artifacts or ML failures are handled gracefully.
- Increment 1 continues to work when the ML component is unavailable.

## 12. Environment Configuration and Documentation

Provide `.env.example` files with placeholder values for settings such as:
- DATABASE_URL
- FRONTEND_ORIGIN
- API_BASE_URL
- MODEL_ARTIFACT_PATH
- DATASET_PATH
- APPLICATION_ENV

Never hardcode credentials or commit actual secrets.

Document:
- Prerequisites and supported runtime versions.
- Installation commands for the frontend and backend.
- PostgreSQL setup.
- Database migration commands.
- Commands to seed demo data.
- Commands to prepare the dataset, train the model, and evaluate it.
- Commands to start the backend and frontend.
- How to run tests.
- Example API requests where useful.
- Known limitations of the ML demo.
- Troubleshooting for database, CORS, and model-loading issues.

If Docker Compose is used, configure it correctly and document both Docker-based and local execution where practical.

## 13. Implementation Order

Follow this sequence:

Phase 1: Inspect the workspace, choose the final structure, establish configuration, and create the database models and migrations.

Phase 2: Implement profile/preferences, subjects, tasks, and backend validation. Test the APIs.

Phase 3: Implement the rule-based scheduler, study sessions, calendar, dashboard, and progress tracking. Complete Increment 1 tests.

Phase 4: Implement the dataset schema, synthetic demo data if necessary, preprocessing, training, evaluation, and saved ML artifacts.

Phase 5: Implement candidate-slot generation, ML inference, recommendation ranking, and hard-constraint validation.

Phase 6: Integrate AI suggestions and feedback into the React interface. Test acceptance, rejection, and error handling.

Phase 7: Run all tests, resolve build/runtime issues, verify persistence, and finalize documentation.

At the end of each phase, verify the implemented functionality before moving forward. Do not silently skip a failed phase.

## 14. Final Deliverables

Provide:
1. Complete frontend source code.
2. Complete backend source code.
3. Database models and migrations.
4. A working rule-based scheduling engine.
5. Dataset preparation and feature-engineering code.
6. ML training and evaluation scripts.
7. A functioning recommendation service.
8. Integration between the frontend, backend, database, and ML component.
9. Automated tests.
10. Demo seed data and documented data-generation procedures.
11. Environment examples and dependency files.
12. A detailed README with exact execution commands.
13. A concise architecture document describing modules and their interactions.
14. A clear list of completed functionality, commands executed, test results, and any remaining limitations.

Start by inspecting the workspace and reporting the implementation plan. Then proceed with the actual implementation. Do not stop after producing a plan, wireframe, or code snippets. Build and verify the runnable application.
