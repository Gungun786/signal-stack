import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.api.routes import router as api_router
from app.scheduler.jobs import start_scheduler, scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("signal_stack")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Signal Stack Engine API",
    description="Company Intelligence and Monday Morning Brief Engine",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing Signal Stack backend...")
    start_scheduler()
    logger.info("Signal Stack Engine is live and ready.")

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down Signal Stack backend...")
    if scheduler.running:
        scheduler.shutdown(wait=False)

@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "signal-stack-backend",
        "env": settings.ENV,
        "database": "connected"
    }

# Mount frontend dist at root if it exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "Signal Stack API is running.",
            "docs_url": "/docs",
            "health_url": "/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
