import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from backend.app.ml.data_preparation import load_and_validate_dataset, FEATURE_COLUMNS, TARGET_COLUMN
from backend.app.ml.features import build_preprocessor, save_preprocessor


def train_model(
    dataset_path: str = "data/sample/study_dataset.csv",
    artifacts_dir: str = "backend/app/ml/artifacts",
    random_seed: int = 42,
    epochs: int = 25,
    batch_size: int = 32
) -> Dict[str, Any]:
    os.makedirs(artifacts_dir, exist_ok=True)
    df = load_and_validate_dataset(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN].values

    # 1. Stratified Train / Val / Test split: 70% train, 15% val, 15% test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=random_seed, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=random_seed, stratify=y_train_val
    )

    # 2. Fit feature preprocessor on training data only (prevent data leakage)
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    # Save preprocessor
    prep_save_path = os.path.join(artifacts_dir, "preprocessor.joblib")
    save_preprocessor(preprocessor, prep_save_path)

    # 3. Simple Baseline Model (Dummy Classifier & Logistic Regression)
    baseline_dummy = DummyClassifier(strategy="most_frequent")
    baseline_dummy.fit(X_train_proc, y_train)
    dummy_preds = baseline_dummy.predict(X_test_proc)

    baseline_lr = LogisticRegression(random_state=random_seed)
    baseline_lr.fit(X_train_proc, y_train)
    lr_preds = baseline_lr.predict(X_test_proc)
    lr_probs = baseline_lr.predict_proba(X_test_proc)[:, 1]

    baseline_metrics = {
        "dummy_accuracy": float(accuracy_score(y_test, dummy_preds)),
        "lr_accuracy": float(accuracy_score(y_test, lr_preds)),
        "lr_f1": float(f1_score(y_test, lr_preds, zero_division=0)),
        "lr_roc_auc": float(roc_auc_score(y_test, lr_probs))
    }

    # 4. Keras / TensorFlow Neural Network Model
    model_type = "Keras Neural Network"
    model_saved_path = os.path.join(artifacts_dir, "study_slot_model.keras")
    model_format = "keras"

    try:
        import tensorflow as tf
        from tensorflow import keras

        # Set seeds
        tf.random.set_seed(random_seed)
        np.random.seed(random_seed)

        input_dim = X_train_proc.shape[1]
        nn_model = keras.Sequential([
            keras.layers.Input(shape=(input_dim,)),
            keras.layers.Dense(32, activation="relu"),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dense(1, activation="sigmoid")
        ])

        nn_model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.003),
            loss="binary_crossentropy",
            metrics=["accuracy"]
        )

        nn_model.fit(
            X_train_proc,
            y_train,
            validation_data=(X_val_proc, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )

        test_probs = nn_model.predict(X_test_proc, verbose=0).flatten()
        test_preds = (test_probs >= 0.5).astype(int)

        nn_model.save(model_saved_path)

    except Exception as e:
        # Fallback to trained LogisticRegression / MLP if TensorFlow is still compiling/unavailable
        import joblib
        model_type = "Logistic Regression (Fallback Engine)"
        model_saved_path = os.path.join(artifacts_dir, "study_slot_model.joblib")
        model_format = "joblib"
        joblib.dump(baseline_lr, model_saved_path)
        test_probs = lr_probs
        test_preds = lr_preds

    # Evaluate metrics
    acc = float(accuracy_score(y_test, test_preds))
    prec = float(precision_score(y_test, test_preds, zero_division=0))
    rec = float(recall_score(y_test, test_preds, zero_division=0))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, test_probs))

    metadata = {
        "model_version": "v1.0",
        "model_type": model_type,
        "model_format": model_format,
        "model_path": model_saved_path,
        "preprocessor_path": prep_save_path,
        "train_samples": int(len(X_train)),
        "val_samples": int(len(X_val)),
        "test_samples": int(len(X_test)),
        "class_distribution": {
            "negative_0": int(np.sum(y == 0)),
            "positive_1": int(np.sum(y == 1))
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "roc_auc": round(roc_auc, 4)
        },
        "baseline_metrics": {
            "dummy_most_frequent_accuracy": round(baseline_metrics["dummy_accuracy"], 4),
            "baseline_lr_accuracy": round(baseline_metrics["lr_accuracy"], 4),
            "baseline_lr_f1": round(baseline_metrics["lr_f1"], 4),
            "baseline_lr_roc_auc": round(baseline_metrics["lr_roc_auc"], 4)
        },
        "limitations": "Model trained on synthetic demonstration dataset. In real student workflows, actual task completion and fatigue curves should be collected over time to replace synthetic ground truth."
    }

    meta_path = os.path.join(artifacts_dir, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == "__main__":
    result = train_model()
    print(json.dumps(result, indent=2))
