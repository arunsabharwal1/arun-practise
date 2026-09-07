"""
FastAPI application entry point.

Startup:
    - Loads environment config from .env
    - Initializes the database (creates tables)
    - Mounts all routers (projects, financials, teams, risks)

Run:
    uvicorn app.main:app --reload
    
Swagger UI available at: http://localhost:8000/docs
ReDoc available at:       http://localhost:8000/redoc
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import projects, financials, teams, risks

# Load environment variables
load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Project Management API")
APP_ENV = os.getenv("APP_ENV", "development")
API_VERSION = os.getenv("API_VERSION", "v1")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    print(f"🚀 Starting {APP_TITLE} [{APP_ENV}]")
    await init_db()
    print("✅ Database tables initialized")
    yield
    print("👋 Shutting down application")


# ─── App Instance ─────────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_TITLE,
    description=(
        "A REST API for tracking 10 concurrent projects with cost, revenue, "
        "team composition, status, and risk assessment. "
        "Structured for future AI integration. 🤖"
    ),
    version=f"1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── CORS Middleware ──────────────────────────────────────────────────────────
# Allow all origins in development; tighten in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(projects.router)
app.include_router(financials.router)
app.include_router(teams.router)
app.include_router(risks.router)


# ─── Root Endpoint ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="API root / health check")
async def root():
    """Health check and API information."""
    return {
        "status": "running",
        "app": APP_TITLE,
        "environment": APP_ENV,
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "projects": "/projects",
            "financials": "/projects/{id}/financials",
            "team": "/projects/{id}/team",
            "risks": "/projects/{id}/risks",
        },
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok", "environment": APP_ENV}
