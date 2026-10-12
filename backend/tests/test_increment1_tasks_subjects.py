import pytest
from datetime import datetime, timedelta, timezone


def test_subject_crud_and_orphan_restriction(client):
    # 1. Create subject
    res = client.post("/api/subjects", json={
        "name": "Chemistry",
        "description": "Organic and Inorganic Chemistry",
        "color": "#8B5CF6"
    })
    assert res.status_code == 201
    subj = res.json()
    subj_id = subj["id"]
    assert subj["name"] == "Chemistry"

    # 2. Duplicate subject prevention
    dup_res = client.post("/api/subjects", json={
        "name": "Chemistry",
        "color": "#8B5CF6"
    })
    assert dup_res.status_code == 400

    # 3. Create task associated with subject
    now = datetime.now(timezone.utc)
    task_res = client.post("/api/tasks", json={
        "subject_id": subj_id,
        "title": "Lab Report 1",
        "description": "Titration analysis",
        "task_type": "assignment",
        "due_at": (now + timedelta(days=3)).isoformat(),
        "estimated_duration_minutes": 60,
        "priority": "High",
        "status": "Pending"
    })
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 4. Attempt to delete subject with associated tasks (Must be prevented)
    del_res = client.delete(f"/api/subjects/{subj_id}")
    assert del_res.status_code == 400
    assert "associated task" in del_res.json()["detail"].lower()

    # 5. Delete task first, then delete subject
    del_task_res = client.delete(f"/api/tasks/{task_id}")
    assert del_task_res.status_code == 204

    del_subj_res = client.delete(f"/api/subjects/{subj_id}")
    assert del_subj_res.status_code == 204


def test_task_validations(client):
    # Retrieve existing subject
    subj_res = client.get("/api/subjects")
    assert subj_res.status_code == 200
    subj_id = subj_res.json()[0]["id"]

    now = datetime.now(timezone.utc)

    # 1. Negative or zero duration rejected
    invalid_dur_res = client.post("/api/tasks", json={
        "subject_id": subj_id,
        "title": "Invalid Task",
        "due_at": (now + timedelta(days=2)).isoformat(),
        "estimated_duration_minutes": 0,
        "priority": "Low",
        "status": "Pending"
    })
    assert invalid_dur_res.status_code == 422

    # 2. Earliest start date after due date rejected
    invalid_dates_res = client.post("/api/tasks", json={
        "subject_id": subj_id,
        "title": "Time Traveler Task",
        "due_at": (now + timedelta(days=1)).isoformat(),
        "earliest_start_at": (now + timedelta(days=2)).isoformat(),
        "estimated_duration_minutes": 45,
        "priority": "Medium",
        "status": "Pending"
    })
    assert invalid_dates_res.status_code == 422


def test_task_filtering_and_sorting(client):
    subj_res = client.get("/api/subjects")
    subj_id = subj_res.json()[0]["id"]
    now = datetime.now(timezone.utc)

    client.post("/api/tasks", json={
        "subject_id": subj_id,
        "title": "Filter Test High",
        "due_at": (now + timedelta(days=5)).isoformat(),
        "estimated_duration_minutes": 30,
        "priority": "High",
        "status": "Pending"
    })

    # Filter by priority
    res = client.get("/api/tasks?priority=High")
    assert res.status_code == 200
    items = res.json()
    assert all(t["priority"] == "High" for t in items)

    # Search keyword
    search_res = client.get("/api/tasks?search=Filter")
    assert search_res.status_code == 200
    assert any("Filter Test High" in t["title"] for t in search_res.json())
