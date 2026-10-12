# Dataset Documentation

## Overview
This directory contains sample training and evaluation data for the AI-Powered Study Planner (Increment 2).

## Dataset Schema: `data/sample/study_dataset.csv`
- `task_priority`: Categorical (`Low`, `Medium`, `High`)
- `task_type`: Categorical (`assignment`, `revision`, `reading`, `practice`)
- `estimated_duration`: Integer (minutes)
- `hours_until_deadline`: Float (hours remaining between candidate slot and task due date)
- `day_of_week`: Integer (`0`=Monday to `6`=Sunday)
- `slot_start_hour`: Integer (`0` to `23`)
- `daily_workload_scheduled`: Integer (minutes of study already planned on that day)
- `slot_duration`: Integer (minutes, e.g. `30`, `45`, `60`)
- `is_suitable_slot`: Target label (`1` if candidate slot is deemed suitable, `0` otherwise)

## Synthetic Label Generation Rules
1. **Prime Daytime Hours (9:00 - 17:00)**: Yield positive score bonuses (+0.35); late evening yields smaller bonuses; late night/early morning penalizes.
2. **Workload & Fatigue**: Daily scheduled study loads < 120 minutes yield bonuses (+0.25); loads > 200 minutes penalize (-0.30).
3. **Task Urgency & Priority Matching**: High priority tasks with deadlines < 24h receive bonuses; last-minute crunch (< 3h) receives penalties.
4. **Duration Matching**: Long tasks (> 75m) scheduled early in the day receive bonuses.
5. **Noise**: Realistic variance is injected via Gaussian noise before sigmoid thresholding.

## Reproducibility
To regenerate or inspect the dataset:
```bash
python -m backend.app.ml.train
```
Or use the data preparation script directly:
```bash
python -c "from backend.app.ml.data_preparation import generate_synthetic_dataset; generate_synthetic_dataset()"
```
