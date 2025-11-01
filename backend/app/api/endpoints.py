from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.services.analytics_service import AnalyticsService
from app.services.calendly_service import CalendlyService
from app.models.schemas import (
    HealthResponse,
    AnalyticsResponse,
    DataPreviewResponse,
    AnalyticsRequest
)

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

@router.post("/analytics/refresh-data")
async def refresh_data(background_tasks: BackgroundTasks):
    """Refresh Calendly data in the background"""
    calendly_service = CalendlyService()
    
    async def refresh_task():
        result = await calendly_service.refresh_data()
        print(f"Data refresh completed: {result}")
    
    background_tasks.add_task(refresh_task)
    return {
        "message": "Data refresh started in background",
        "status": "processing",
        "note": "Check the data preview endpoint to see when data is available"
    }

@router.get("/analytics/cleverly-introduction", response_model=AnalyticsResponse)
async def get_cleverly_analytics():
    """Get comprehensive analytics for Cleverly Introduction events"""
    analytics_service = AnalyticsService()
    analytics = await analytics_service.generate_comprehensive_analytics()
    
    if "error" in analytics:
        raise HTTPException(status_code=500, detail=analytics["error"])
    
    return analytics

@router.get("/analytics/data-preview", response_model=DataPreviewResponse)
async def get_data_preview():
    """Get preview of available data"""
    analytics_service = AnalyticsService()
    preview = await analytics_service.data_processor.get_data_preview()
    return preview

@router.get("/analytics/raw-data")
async def get_raw_data():
    """Get raw data for debugging"""
    analytics_service = AnalyticsService()
    await analytics_service.data_processor.load_data()
    df = analytics_service.data_processor.create_analytics_dataframe()
    
    if df.empty:
        return {"error": "No data available", "message": "Please refresh data first"}
    
    return {
        "columns": df.columns.tolist(),
        "shape": df.shape,
        "sample": df.head(10).to_dict('records'),
        "total_records": len(df)
    }