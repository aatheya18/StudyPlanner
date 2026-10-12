from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.config import settings
from backend.app.db.database import SessionLocal, engine, Base
from backend.app.db.init_db import init_db
from backend.app.api.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist and initialize seed profile
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AI-Powered Study Planner API",
    description="Backend API for AI-Powered Study Planner with Rule-Based Engine & ML Recommendations",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": "AI-Powered Study Planner API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
