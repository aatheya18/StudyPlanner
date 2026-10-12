import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from backend.app.ml.features import load_preprocessor, extract_candidate_features


class ModelPredictor:
    def __init__(self, artifacts_dir: str = "backend/app/ml/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.preprocessor = None
        self.model = None
        self.model_type = "None"
        self.metadata = {}
        self.loaded = False
        self._load_artifacts()

    def _load_artifacts(self):
        meta_path = os.path.join(self.artifacts_dir, "model_metadata.json")
        prep_path = os.path.join(self.artifacts_dir, "preprocessor.joblib")
        keras_path = os.path.join(self.artifacts_dir, "study_slot_model.keras")
        joblib_path = os.path.join(self.artifacts_dir, "study_slot_model.joblib")

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}

        if os.path.exists(prep_path):
            try:
                self.preprocessor = load_preprocessor(prep_path)
            except Exception:
                self.preprocessor = None

        # Check Keras model
        if os.path.exists(keras_path):
            try:
                from tensorflow import keras
                self.model = keras.models.load_model(keras_path)
                self.model_type = "TensorFlow/Keras Neural Network"
                self.loaded = True
                return
            except Exception:
                pass

        # Check joblib fallback model
        if os.path.exists(joblib_path):
            try:
                self.model = joblib.load(joblib_path)
                self.model_type = "Logistic Regression"
                self.loaded = True
                return
            except Exception:
                pass

        self.loaded = False
        self.model_type = "Heuristic Fallback Engine"

    def predict_candidate_slot(
        self,
        task: Any,
        slot_start: datetime,
        slot_end: datetime,
        daily_workload_minutes: int,
        reference_time: datetime = None
    ) -> Tuple[float, str]:
        """
        Returns (suitability_score, explanation_str).
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        elif reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        slot_s = slot_start if slot_start.tzinfo is not None else slot_start.replace(tzinfo=timezone.utc)
        task_due = task.due_at if task.due_at.tzinfo is not None else task.due_at.replace(tzinfo=timezone.utc)
        hours_left = max(0.0, (task_due - slot_s).total_seconds() / 3600.0)

        # Build human-readable explanations based on features
        reasons = []
        if getattr(task, "priority", "Medium") == "High":
            reasons.append("High priority task")
        if 9 <= slot_s.hour <= 17:
            reasons.append(f"Daytime prime hours ({slot_s.strftime('%H:%M')})")
        elif slot_s.hour >= 18:
            reasons.append(f"Evening session ({slot_s.strftime('%H:%M')})")

        if daily_workload_minutes < 120:
            reasons.append("Low daily fatigue")
        elif daily_workload_minutes > 180:
            reasons.append(f"Moderate study load ({daily_workload_minutes}m already scheduled)")

        if hours_left < 24:
            reasons.append("Approaching deadline")

        explanation = "; ".join(reasons) if reasons else "Balanced schedule slot"

        # Model prediction
        if self.loaded and self.preprocessor is not None and self.model is not None:
            try:
                feat_df = extract_candidate_features(task, slot_start, slot_end, daily_workload_minutes, reference_time)
                proc_x = self.preprocessor.transform(feat_df)
                if hasattr(self.model, "predict_proba"):
                    prob = float(self.model.predict_proba(proc_x)[0, 1])
                elif hasattr(self.model, "predict"):
                    preds = self.model.predict(proc_x, verbose=0)
                    prob = float(preds[0][0]) if hasattr(preds[0], "__getitem__") else float(preds[0])
                else:
                    prob = 0.5
                return round(float(prob), 3), explanation
            except Exception:
                pass

        # Heuristic scoring fallback
        score = 0.5
        if getattr(task, "priority", "Medium") == "High":
            score += 0.2
        if 9 <= slot_s.hour <= 16:
            score += 0.15
        if daily_workload_minutes < 120:
            score += 0.1
        elif daily_workload_minutes > 180:
            score -= 0.15
        if hours_left < 24:
            score += 0.1
        score = max(0.05, min(0.98, score))
        return round(score, 3), f"{explanation} (Heuristic estimate)"
