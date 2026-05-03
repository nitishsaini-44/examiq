"""
ExamIQ — AI-Powered Smart Study Strategist
FastAPI Backend Entry Point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS
from app.api import upload, analysis, planner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="ExamIQ API",
    description="AI-Powered Smart Study Strategist — Transform past papers into actionable study intelligence",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(planner.router)


@app.get("/")
async def root():
    return {
        "name": "ExamIQ API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
