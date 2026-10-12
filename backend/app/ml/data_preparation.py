import os
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

FEATURE_COLUMNS = [
    "task_priority",
    "task_type",
    "estimated_duration",
    "hours_until_deadline",
    "day_of_week",
    "slot_start_hour",
    "daily_workload_scheduled",
    "slot_duration"
]
TARGET_COLUMN = "is_suitable_slot"


def generate_synthetic_dataset(
    output_path: str = "data/sample/study_dataset.csv",
    num_samples: int = 1500,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a documented synthetic demonstration dataset for candidate task-slot suitability.
    
    Labeling rules:
    - High priority tasks scheduled with lower daily fatigue (< 180 min) and daytime hours (9-17) are suitable.
    - Slots closer to deadline (< 6 hours) or slots during evening when workload is high (> 200 min) are less suitable.
    - Long tasks (> 75 min) scheduled in morning/early afternoon are preferred.
    - Normal noise (10%) is added to simulate real-world variance.
    """
    np.random.seed(random_seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    priorities = np.random.choice(["Low", "Medium", "High"], size=num_samples, p=[0.25, 0.45, 0.30])
    task_types = np.random.choice(["assignment", "revision", "reading", "practice"], size=num_samples)
    durations = np.random.choice([30, 45, 60, 90, 120], size=num_samples, p=[0.2, 0.35, 0.25, 0.15, 0.05])
    hours_to_deadline = np.random.exponential(scale=48.0, size=num_samples) + 2.0
    hours_to_deadline = np.clip(hours_to_deadline, 2.0, 240.0)

    days_of_week = np.random.randint(0, 7, size=num_samples)
    slot_hours = np.random.randint(8, 22, size=num_samples)
    daily_workloads = np.random.choice([0, 45, 90, 135, 180, 225, 270], size=num_samples)
    slot_durations = np.random.choice([30, 45, 60], size=num_samples, p=[0.2, 0.6, 0.2])

    labels = []
    for i in range(num_samples):
        pri = priorities[i]
        dur = durations[i]
        h_dead = hours_to_deadline[i]
        shour = slot_hours[i]
        workload = daily_workloads[i]

        score = 0.0

        # Daylight prime study hours (9:00 - 17:00)
        if 9 <= shour <= 17:
            score += 0.35
        elif 18 <= shour <= 21:
            score += 0.15
        else:
            score -= 0.20

        # Fatigue penalty
        if workload < 120:
            score += 0.25
        elif workload > 200:
            score -= 0.30

        # Urgency & Priority matching
        if pri == "High":
            score += 0.20
            if h_dead < 24:
                score += 0.25
        elif pri == "Medium":
            score += 0.10

        # Avoid extreme last minute crunch
        if h_dead < 3:
            score -= 0.40

        # Long duration needs earlier slot
        if dur >= 90 and shour <= 14:
            score += 0.15

        # Add slight noise
        noise = np.random.normal(0, 0.1)
        prob = 1.0 / (1.0 + np.exp(-(score + noise - 0.25)))
        label = 1 if prob >= 0.5 else 0
        labels.append(label)

    df = pd.DataFrame({
        "task_priority": priorities,
        "task_type": task_types,
        "estimated_duration": durations,
        "hours_until_deadline": np.round(hours_to_deadline, 1),
        "day_of_week": days_of_week,
        "slot_start_hour": slot_hours,
        "daily_workload_scheduled": daily_workloads,
        "slot_duration": slot_durations,
        TARGET_COLUMN: labels
    })

    df.to_csv(output_path, index=False)
    return df


def load_and_validate_dataset(dataset_path: str = "data/sample/study_dataset.csv") -> pd.DataFrame:
    if not os.path.exists(dataset_path):
        return generate_synthetic_dataset(output_path=dataset_path)

    df = pd.read_csv(dataset_path)
    required = FEATURE_COLUMNS + [TARGET_COLUMN]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Dataset missing required column: {col}")

    # Handle missing values if any
    df = df.dropna(subset=[TARGET_COLUMN])
    df["hours_until_deadline"] = df["hours_until_deadline"].fillna(df["hours_until_deadline"].median())
    df["daily_workload_scheduled"] = df["daily_workload_scheduled"].fillna(0)
    return df
