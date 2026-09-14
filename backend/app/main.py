from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import ai, analytics, auth, budgets, goals, notifications, transactions

# Creates tables on startup for the SQLite/local-prototype flow.
# For production Postgres, prefer a proper migration tool (Alembic).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinMate AI API",
    description="AI-powered personal finance platform - backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {"name": "FinMate AI API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
