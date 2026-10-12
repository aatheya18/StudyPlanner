import os
import sys

# Ensure workspace root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.ml.train import train_model

if __name__ == "__main__":
    print("Starting ML Model training pipeline...")
    meta = train_model()
    print("Training complete! Model metadata:")
    import json
    print(json.dumps(meta, indent=2))
