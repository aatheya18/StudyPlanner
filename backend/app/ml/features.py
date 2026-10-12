import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from datetime import datetime, timezone
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

CATEGORICAL_FEATURES = ["task_priority", "task_type"]
NUMERICAL_FEATURES = [
    "estimated_duration",
    "hours_until_deadline",
    "day_of_week",
    "slot_start_hour",
    "daily_workload_scheduled",
    "slot_duration"
]


def build_preprocessor() -> ColumnTransformer:
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ],
        remainder="drop"
    )
    return preprocessor


def save_preprocessor(preprocessor: ColumnTransformer, save_path: str):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(preprocessor, save_path)


def load_preprocessor(load_path: str) -> ColumnTransformer:
    if not os.path.exists(load_path):
        raise FileNotFoundError(f"Preprocessor artifact not found at {load_path}")
    return joblib.load(load_path)


def extract_candidate_features(
    task: Any,
    slot_start: datetime,
    slot_end: datetime,
    daily_workload_minutes: int,
    reference_time: datetime = None
) -> pd.DataFrame:
    """
    Extracts identical feature schema from a single candidate task-slot combination.
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    slot_s = slot_start if slot_start.tzinfo is not None else slot_start.replace(tzinfo=timezone.utc)
    slot_e = slot_end if slot_end.tzinfo is not None else slot_end.replace(tzinfo=timezone.utc)

    task_due = task.due_at if task.due_at.tzinfo is not None else task.due_at.replace(tzinfo=timezone.utc)
    hours_to_deadline = max(0.0, (task_due - slot_s).total_seconds() / 3600.0)
    slot_duration = int((slot_e - slot_s).total_seconds() / 60)

    data = {
        "task_priority": [getattr(task, "priority", "Medium")],
        "task_type": [getattr(task, "task_type", "assignment")],
        "estimated_duration": [getattr(task, "estimated_duration_minutes", 60)],
        "hours_until_deadline": [round(hours_to_deadline, 1)],
        "day_of_week": [slot_s.weekday()],
        "slot_start_hour": [slot_s.hour],
        "daily_workload_scheduled": [daily_workload_minutes],
        "slot_duration": [slot_duration]
    }
    return pd.DataFrame(data)
