import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from planner import generate_study_plan, TaskUrgencyModel

class TestStudyPlanner(unittest.TestCase):
    def setUp(self):
        # Base availability: Mon to Sun 09:00 - 18:00 (540 mins/day window)
        self.availability = [
            {"day_of_week": i, "is_enabled": 1, "start_time": "09:00", "end_time": "18:00"}
            for i in range(7)
        ]
        self.settings = {
            "session_length": 45,
            "break_length": 15,
            "daily_duration_cap": 240  # 4 hours relaxed
        }
        # Fixed reference time for deterministic testing: a Monday at 09:00
        self.ref_time = datetime(2026, 10, 19, 9, 0, 0)

    def test_urgency_scoring(self):
        """Urgent tasks (high priority, imminent deadline) score higher than relaxed tasks."""
        model = TaskUrgencyModel()
        tasks = [
            {
                "id": 1,
                "title": "Relaxed Task",
                "priority": "Low",
                "task_type": "Revision",
                "due_date": (self.ref_time + timedelta(days=14)).isoformat(),
                "duration_mins": 45
            },
            {
                "id": 2,
                "title": "Crucial Task",
                "priority": "High",
                "task_type": "Assignment",
                "due_date": (self.ref_time + timedelta(hours=6)).isoformat(),
                "duration_mins": 90
            }
        ]
        scored = model.compute_urgency_scores(tasks, self.ref_time)
        self.assertEqual(len(scored), 2)
        # Crucial Task must have a higher urgency score and come first
        self.assertEqual(scored[0]["id"], 2)
        self.assertGreater(scored[0]["urgency_score"], scored[1]["urgency_score"])

    def test_relaxed_schedule(self):
        """When schedule is relaxed, daily study does not exceed daily_duration_cap or 3 tasks/day."""
        # Create 5 small tasks due 10 days from now
        tasks = [
            {
                "id": i,
                "title": f"Task {i}",
                "priority": "Medium",
                "task_type": "Assignment",
                "due_date": (self.ref_time + timedelta(days=10)).isoformat(),
                "duration_mins": 60,
                "status": "Pending"
            }
            for i in range(1, 6)
        ]

        result = generate_study_plan(tasks, self.settings, self.availability, current_time=self.ref_time)

        self.assertEqual(len(result["at_risk_tasks"]), 0, "No task should be at risk with ample time.")
        self.assertEqual(result["total_tasks_scheduled"], 5)

        # Check day 1 session limits
        day1_str = self.ref_time.date().strftime("%Y-%m-%d")
        day1_sessions = [s for s in result["sessions"] if s["session_date"] == day1_str]
        day1_tasks = set(s["task_id"] for s in day1_sessions)
        day1_minutes = sum(s["duration_mins"] for s in day1_sessions)

        # In relaxed schedule, day 1 should have <= 3 tasks and <= 240 mins
        self.assertLessEqual(len(day1_tasks), 3)
        self.assertLessEqual(day1_minutes, 240)

        # Check session chunking: each chunk <= 45 mins
        for s in result["sessions"]:
            self.assertLessEqual(s["duration_mins"], self.settings["session_length"])

    def test_tight_deadline_exceeds_limits(self):
        """When deadlines are tight, the planner exceeds relaxed caps to fit all tasks before deadline."""
        # 4 tasks due by tomorrow at 18:00
        # Under relaxed limits (max 3 tasks, max 240 mins), all 4 could not finish today
        # But today's total window has 9 hours (540 mins), so tight mode allows all 4 to finish!
        tomorrow_close = (self.ref_time + timedelta(days=1)).replace(hour=18, minute=0)
        tasks = [
            {
                "id": i,
                "title": f"Urgent Task {i}",
                "priority": "High",
                "task_type": "Assignment",
                "due_date": tomorrow_close.isoformat(),
                "duration_mins": 75,
                "status": "Pending"
            }
            for i in range(1, 5)
        ]

        result = generate_study_plan(tasks, self.settings, self.availability, current_time=self.ref_time)

        # All 4 tasks must be successfully scheduled before their deadline
        self.assertEqual(len(result["at_risk_tasks"]), 0)
        self.assertEqual(result["total_tasks_scheduled"], 4)

        # Verify no session starts or ends after deadline
        for s in result["sessions"]:
            session_end = datetime.strptime(f"{s['session_date']} {s['end_time']}", "%Y-%m-%d %H:%M")
            self.assertLessEqual(session_end, tomorrow_close)

    def test_impossible_deadline_flagged_at_risk(self):
        """Tasks with impossible deadlines (e.g. 180 min task due in 45 min) are flagged at risk."""
        impossible_due = self.ref_time + timedelta(minutes=45)
        tasks = [
            {
                "id": 99,
                "title": "Impossible Huge Exam Prep",
                "priority": "High",
                "task_type": "Revision",
                "due_date": impossible_due.isoformat(),
                "duration_mins": 180,  # 3 hours, but only 45 mins left!
                "status": "Pending"
            }
        ]

        result = generate_study_plan(tasks, self.settings, self.availability, current_time=self.ref_time)

        # Must flag task 99 as at risk
        self.assertEqual(len(result["at_risk_tasks"]), 1)
        self.assertEqual(result["at_risk_tasks"][0]["id"], 99)

        # Any scheduled session must NOT end after the deadline
        for s in result["sessions"]:
            session_end = datetime.strptime(f"{s['session_date']} {s['end_time']}", "%Y-%m-%d %H:%M")
            self.assertLessEqual(session_end, impossible_due)

    def test_overdue_task_flagged_at_risk(self):
        """Tasks whose deadline is already in the past cannot be scheduled and are flagged at risk."""
        past_due = self.ref_time - timedelta(hours=2)
        tasks = [
            {
                "id": 100,
                "title": "Already Overdue Project",
                "priority": "High",
                "task_type": "Assignment",
                "due_date": past_due.isoformat(),
                "duration_mins": 60,
                "status": "Pending"
            }
        ]

        result = generate_study_plan(tasks, self.settings, self.availability, current_time=self.ref_time)

        self.assertEqual(len(result["sessions"]), 0, "Never schedule a task after its deadline.")
        self.assertEqual(len(result["at_risk_tasks"]), 1)
        self.assertEqual(result["at_risk_tasks"][0]["id"], 100)

if __name__ == "__main__":
    unittest.main()
