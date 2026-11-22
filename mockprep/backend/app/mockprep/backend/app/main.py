import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from .config import settings
from .database import engine, Base
from .routes import auth_routes, interview_routes, dashboard_routes

# Auto-create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-Stack AI Mock Interview Platform — IET Lucknow Group 05"
)

# CORS — allow all origins so frontend can talk to backend freely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ──────────────────────────────────────────────────────────────
app.include_router(auth_routes.router,       prefix=settings.API_PREFIX)
app.include_router(interview_routes.router,  prefix=settings.API_PREFIX)
app.include_router(dashboard_routes.router,  prefix=settings.API_PREFIX)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "database": "connected",
        "version": settings.VERSION
    }

# ── Frontend Static Files ────────────────────────────────────────────────────
# Works both locally (backend/app → ../../frontend) and on Render
THIS_FILE   = os.path.abspath(__file__)                     # …/backend/app/main.py
APP_DIR     = os.path.dirname(THIS_FILE)                    # …/backend/app
BACKEND_DIR = os.path.dirname(APP_DIR)                      # …/backend
PROJECT_DIR = os.path.dirname(BACKEND_DIR)                  # …/mockprep (repo root)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

if os.path.isdir(FRONTEND_DIR):
    # Serve every static asset (css, js, images) under /static/*
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static_assets"
    )

    # Catch-all: serve index.html for every unknown path so the SPA router works
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse({"error": "Frontend not found"}, status_code=404)
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "MockPrep API running. Frontend not found in: " + FRONTEND_DIR}
