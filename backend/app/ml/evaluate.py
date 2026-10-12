import os
import json
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from backend.app.ml.data_preparation import load_and_validate_dataset, FEATURE_COLUMNS, TARGET_COLUMN
from backend.app.ml.features import load_preprocessor
from backend.app.ml.predict import ModelPredictor


def run_evaluation(
    dataset_path: str = "data/sample/study_dataset.csv",
    artifacts_dir: str = "backend/app/ml/artifacts"
) -> dict:
    predictor = ModelPredictor(artifacts_dir=artifacts_dir)
    df = load_and_validate_dataset(dataset_path)

    # Use 20% holdout for evaluation
    test_df = df.sample(frac=0.2, random_state=123)
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN].values

    if not predictor.loaded:
        return {
            "status": "warning",
            "message": "Model artifacts not fully loaded. Running in heuristic fallback mode.",
            "sample_count": len(test_df)
        }

    proc = load_preprocessor(os.path.join(artifacts_dir, "preprocessor.joblib"))
    X_proc = proc.transform(X_test)

    if hasattr(predictor.model, "predict_proba"):
        probs = predictor.model.predict_proba(X_proc)[:, 1]
    elif hasattr(predictor.model, "predict"):
        preds = predictor.model.predict(X_proc, verbose=0)
        probs = preds.flatten()
    else:
        probs = np.full(len(y_test), 0.5)

    y_pred = (probs >= 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "sample_count": len(test_df),
        "class_balance": {
            "negative_0": int(np.sum(y_test == 0)),
            "positive_1": int(np.sum(y_test == 1))
        }
    }
    return metrics


if __name__ == "__main__":
    results = run_evaluation()
    print(json.dumps(results, indent=2))
