import pytest
from datetime import datetime, timedelta, timezone


def test_schedule_generation_and_no_overlaps(client):
    res = client.post("/api/schedules/generate", json={
        "horizon_days": 7,
        "clear_existing_scheduled": True
    })
    assert res.status_code == 200
    data = res.json()
    sessions = data["sessions_created"]
    assert len(sessions) > 0

    # Sort sessions by start time and verify no overlap
    parsed_sessions = []
    for s in sessions:
        s_start = datetime.fromisoformat(s["start_at"].replace("Z", "+00:00"))
        s_end = datetime.fromisoformat(s["end_at"].replace("Z", "+00:00"))
        assert s_end > s_start
        parsed_sessions.append((s_start, s_end))

    parsed_sessions.sort(key=lambda x: x[0])
    for i in range(len(parsed_sessions) - 1):
        curr_end = parsed_sessions[i][1]
        next_start = parsed_sessions[i + 1][0]
        assert curr_end <= next_start, f"Overlap detected between session {i} and {i+1}!"


def test_sessions_respect_deadlines(client):
    # Fetch all tasks and map their due dates
    tasks_res = client.get("/api/tasks")
    task_map = {t["id"]: datetime.fromisoformat(t["due_at"].replace("Z", "+00:00")) for t in tasks_res.json()}

    sessions_res = client.get("/api/sessions")
    assert sessions_res.status_code == 200
    sessions = sessions_res.json()

    for s in sessions:
        task_id = s["task_id"]
        if task_id in task_map:
            s_end = datetime.fromisoformat(s["end_at"].replace("Z", "+00:00"))
            task_due = task_map[task_id]
            assert s_end <= task_due, f"Session end {s_end} is after task deadline {task_due}!"


def test_unschedulable_tasks_reported(client):
    # Create an impossible task (estimated duration 180 mins, due in 10 minutes)
    subj_res = client.get("/api/subjects")
    subj_id = subj_res.json()[0]["id"]
    now = datetime.now(timezone.utc)

    task_res = client.post("/api/tasks", json={
        "subject_id": subj_id,
        "title": "Impossible Urgent Task",
        "due_at": (now + timedelta(minutes=10)).isoformat(),
        "estimated_duration_minutes": 180,
        "priority": "High",
        "status": "Pending"
    })
    assert task_res.status_code == 201
    impossible_task_id = task_res.json()["id"]

    # Generate schedule
    gen_res = client.post("/api/schedules/generate", json={
        "horizon_days": 3,
        "clear_existing_scheduled": False
    })
    assert gen_res.status_code == 200
    data = gen_res.json()
    unscheduled = data["unscheduled_tasks"]

    # The impossible task must be reported in unscheduled_tasks
    unscheduled_ids = [u["task_id"] for u in unscheduled]
    assert impossible_task_id in unscheduled_ids
    impossible_entry = next(u for u in unscheduled if u["task_id"] == impossible_task_id)
    assert len(impossible_entry["reason"]) > 0

    # Cleanup
    client.delete(f"/api/tasks/{impossible_task_id}")
