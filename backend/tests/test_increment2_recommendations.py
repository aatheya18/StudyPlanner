import pytest
from datetime import datetime, timezone


def test_ai_status_endpoint(client):
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "model_loaded" in data
    assert "model_version" in data
    assert "status_detail" in data


def test_ai_recommendation_lifecycle(client):
    # 1. Generate recommendations
    gen_res = client.post("/api/ai/recommendations/generate", json={
        "horizon_days": 5,
        "candidate_slots_per_task": 2
    })
    assert gen_res.status_code == 200
    recs = gen_res.json()
    assert isinstance(recs, list)
    if not recs:
        pytest.skip("No incomplete tasks available for recommendation in test DB.")

    rec = recs[0]
    rec_id = rec["id"]
    task_id = rec["task_id"]

    # Verify fields
    assert "suitability_score" in rec
    assert "explanation" in rec
    assert rec["status"] == "Pending"

    # 2. Verify hard constraints: recommended end time must be before task deadline
    task_res = client.get(f"/api/tasks/{task_id}")
    task_due = datetime.fromisoformat(task_res.json()["due_at"].replace("Z", "+00:00"))
    rec_end = datetime.fromisoformat(rec["recommended_end_at"].replace("Z", "+00:00"))
    assert rec_end <= task_due

    # 3. Accept recommendation
    accept_res = client.post(f"/api/ai/recommendations/{rec_id}/accept", json={
        "note": "Fits my Tuesday afternoon well."
    })
    assert accept_res.status_code == 200
    created_session = accept_res.json()
    assert created_session["task_id"] == task_id
    assert created_session["status"] == "Scheduled"

    # 4. Repeated acceptance must fail
    repeat_res = client.post(f"/api/ai/recommendations/{rec_id}/accept")
    assert repeat_res.status_code == 400

    # 5. Reject another recommendation if exists
    if len(recs) > 1:
        rec_2_id = recs[1]["id"]
        # Count existing sessions before reject
        sess_before = len(client.get("/api/sessions").json())

        reject_res = client.post(f"/api/ai/recommendations/{rec_2_id}/reject", json={
            "note": "Too close to dinner."
        })
        assert reject_res.status_code == 200

        # Verify schedule was not altered
        sess_after = len(client.get("/api/sessions").json())
        assert sess_before == sess_after
