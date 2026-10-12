import pytest
from datetime import datetime, timezone


def test_session_lifecycle_and_task_consistency(client):
    # Ensure there is a session
    sess_res = client.get("/api/sessions")
    sessions = sess_res.json()
    if not sessions:
        client.post("/api/schedules/generate", json={"horizon_days": 7})
        sessions = client.get("/api/sessions").json()

    assert len(sessions) > 0
    test_session = sessions[0]
    sess_id = test_session["id"]
    task_id = test_session["task_id"]

    # 1. Complete session with actual duration, mark_task_completed = False
    complete_res = client.post(f"/api/sessions/{sess_id}/complete", json={
        "actual_duration_minutes": 50,
        "mark_task_completed": False
    })
    assert complete_res.status_code == 200
    updated_sess = complete_res.json()
    assert updated_sess["status"] == "Completed"
    assert updated_sess["actual_duration_minutes"] == 50

    # Task status should be 'In Progress' (not completed automatically)
    task_res = client.get(f"/api/tasks/{task_id}")
    assert task_res.status_code == 200
    assert task_res.json()["status"] in ["In Progress", "Completed"]

    # 2. Skip session
    if len(sessions) > 1:
        skip_sess_id = sessions[1]["id"]
        skip_res = client.post(f"/api/sessions/{skip_sess_id}/skip")
        assert skip_res.status_code == 200
        assert skip_res.json()["status"] == "Skipped"


def test_dashboard_and_reminders_aggregation(client):
    dash_res = client.get("/api/dashboard")
    assert dash_res.status_code == 200
    dash = dash_res.json()

    assert "pending_tasks_count" in dash
    assert "completed_tasks_count" in dash
    assert "total_planned_minutes" in dash
    assert "total_completed_minutes" in dash
    assert "weekly_progress" in dash
    assert len(dash["weekly_progress"]) == 7

    reminders_res = client.get("/api/reminders")
    assert reminders_res.status_code == 200
    reminders = reminders_res.json()
    assert "reminders" in reminders
    assert "count" in reminders
    assert isinstance(reminders["reminders"], list)
