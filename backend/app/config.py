import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APPLICATION_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./study_planner.db"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    API_BASE_URL: str = "http://localhost:8000"
    MODEL_ARTIFACT_PATH: str = "backend/app/ml/artifacts"
    DATASET_PATH: str = "data/sample/study_dataset.csv"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
