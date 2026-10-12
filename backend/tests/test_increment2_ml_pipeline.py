import os
import pytest
from datetime import datetime, timedelta, timezone
from backend.app.ml.data_preparation import generate_synthetic_dataset, load_and_validate_dataset, FEATURE_COLUMNS, TARGET_COLUMN
from backend.app.ml.features import build_preprocessor, extract_candidate_features
from backend.app.ml.train import train_model
from backend.app.ml.predict import ModelPredictor
from backend.app.models.entities import Task


def test_dataset_generation_and_validation(tmp_path):
    csv_file = str(tmp_path / "test_dataset.csv")
    df = generate_synthetic_dataset(output_path=csv_file, num_samples=100)
    assert len(df) == 100
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert TARGET_COLUMN in df.columns

    # Load and validate
    loaded = load_and_validate_dataset(csv_file)
    assert len(loaded) == 100


def test_preprocessing_consistency(tmp_path):
    csv_file = str(tmp_path / "test_dataset.csv")
    df = generate_synthetic_dataset(output_path=csv_file, num_samples=50)

    preprocessor = build_preprocessor()
    X_proc = preprocessor.fit_transform(df[FEATURE_COLUMNS])

    # Extract feature from candidate task
    class MockTask:
        id = 1
        priority = "High"
        task_type = "assignment"
        estimated_duration_minutes = 60
        due_at = datetime.now(timezone.utc) + timedelta(days=2)

    now = datetime.now(timezone.utc)
    cand_df = extract_candidate_features(
        MockTask(),
        slot_start=now + timedelta(hours=5),
        slot_end=now + timedelta(hours=6),
        daily_workload_minutes=45
    )
    for col in FEATURE_COLUMNS:
        assert col in cand_df.columns

    cand_proc = preprocessor.transform(cand_df)
    assert cand_proc.shape[1] == X_proc.shape[1]


def test_train_and_predict_pipeline(tmp_path):
    csv_file = str(tmp_path / "train_test_data.csv")
    art_dir = str(tmp_path / "artifacts")
    generate_synthetic_dataset(output_path=csv_file, num_samples=200)

    # Train model
    meta = train_model(
        dataset_path=csv_file,
        artifacts_dir=art_dir,
        epochs=5,
        batch_size=16
    )
    assert "evaluation_metrics" in meta
    assert "accuracy" in meta["evaluation_metrics"]
    assert "baseline_metrics" in meta
    assert os.path.exists(os.path.join(art_dir, "preprocessor.joblib"))

    # Load predictor
    predictor = ModelPredictor(artifacts_dir=art_dir)
    assert predictor.loaded is True

    class MockTask:
        id = 10
        priority = "Medium"
        task_type = "revision"
        estimated_duration_minutes = 45
        due_at = datetime.now(timezone.utc) + timedelta(days=1)

    now = datetime.now(timezone.utc)
    score, reason = predictor.predict_candidate_slot(
        task=MockTask(),
        slot_start=now + timedelta(hours=2),
        slot_end=now + timedelta(hours=3),
        daily_workload_minutes=60
    )
    assert 0.0 <= score <= 1.0
    assert len(reason) > 0


def test_missing_artifacts_fallback(tmp_path):
    empty_dir = str(tmp_path / "empty_dir")
    os.makedirs(empty_dir, exist_ok=True)
    predictor = ModelPredictor(artifacts_dir=empty_dir)
    assert predictor.loaded is False

    class MockTask:
        id = 99
        priority = "Low"
        task_type = "reading"
        estimated_duration_minutes = 30
        due_at = datetime.now(timezone.utc) + timedelta(days=2)

    now = datetime.now(timezone.utc)
    score, reason = predictor.predict_candidate_slot(
        task=MockTask(),
        slot_start=now + timedelta(hours=4),
        slot_end=now + timedelta(hours=5),
        daily_workload_minutes=0
    )
    assert 0.0 <= score <= 1.0
    assert "Heuristic" in reason
