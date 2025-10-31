from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path

from app.core.config import Settings, get_settings
from app.api.endpoints import router as api_router
from app.services.calendly_service import CalendlyService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Calendly Analytics API")
    
    # Initialize services
    calendly_service = CalendlyService()
    await calendly_service.initialize()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Calendly Analytics API")

def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="Calendly Analytics API",
        description="FAANG-grade analytics platform for Calendly data",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Serve frontend in production
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
        
        @app.get("/")
        async def serve_frontend():
            return FileResponse(frontend_path / "index.html")
    
    return app

app = create_application()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # You might want to use datetime.utcnow().isoformat()
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )