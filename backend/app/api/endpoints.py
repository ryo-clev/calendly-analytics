from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
import asyncio

from app.services.analytics_service import AnalyticsService
from app.services.calendly_service import CalendlyService, get_download_progress
from app.models.schemas import (
    HealthResponse,
    AnalyticsResponse,
    DataPreviewResponse,
    AnalyticsRequest
)

router = APIRouter()

# Global state to track download status
download_state = {
    "is_downloading": False,
    "progress": 0,
    "message": "",
    "error": None,
    "step_name": "",
    "details": ""
}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

@router.post("/analytics/download-data")
async def download_calendly_data(background_tasks: BackgroundTasks):
    """Download all Calendly data and store in calendly_dump"""
    global download_state
    
    if download_state["is_downloading"]:
        return {
            "status": "already_downloading",
            "message": "Data download is already in progress",
            "progress": download_state["progress"]
        }
    
    calendly_service = CalendlyService()
    
    async def download_task():
        global download_state
        try:
            download_state["is_downloading"] = True
            download_state["progress"] = 0
            download_state["message"] = "Starting download..."
            download_state["error"] = None
            download_state["step_name"] = "Initializing"
            download_state["details"] = ""
            
            print("\n" + "="*70)
            print("📥 BACKGROUND DOWNLOAD TASK STARTED")
            print("="*70 + "\n")
            
            result = await calendly_service.download_all_data()
            
            if "error" in result:
                download_state["error"] = result["error"]
                download_state["message"] = f"Download failed: {result['error']}"
                download_state["progress"] = 0
                print(f"\n❌ Download task failed: {result['error']}\n")
            else:
                download_state["progress"] = 100
                download_state["message"] = "Download completed successfully"
                download_state["step_name"] = "Complete"
                download_state["details"] = f"Downloaded {result['summary']['event_types']} event types, {result['summary']['scheduled_events']} events"
                print("\n✅ Download task completed successfully\n")
                
        except Exception as e:
            error_msg = str(e)
            download_state["error"] = error_msg
            download_state["message"] = f"Download failed: {error_msg}"
            download_state["progress"] = 0
            print(f"\n❌ Download task exception: {error_msg}\n")
            import traceback
            traceback.print_exc()
        finally:
            download_state["is_downloading"] = False
            print("📥 Download task finished\n")
    
    background_tasks.add_task(download_task)
    
    return {
        "status": "started",
        "message": "Data download started in background. Use /analytics/download-status to check progress."
    }

@router.get("/analytics/download-status")
async def get_download_status():
    """Get the current status of data download"""
    global download_state
    
    # Get progress from the calendly service
    progress_data = get_download_progress()
    
    # Update download state with progress data
    if download_state["is_downloading"]:
        download_state["progress"] = progress_data.get("percentage", 0)
        download_state["step_name"] = progress_data.get("step_name", "")
        download_state["details"] = progress_data.get("details", "")
        download_state["message"] = f"{progress_data.get('step_name', 'Downloading...')} - {progress_data.get('details', '')}"
    
    return {
        "is_downloading": download_state["is_downloading"],
        "progress": download_state["progress"],
        "message": download_state["message"],
        "error": download_state["error"],
        "step_name": download_state["step_name"],
        "details": download_state["details"],
        "current_step": progress_data.get("current_step", 0),
        "total_steps": progress_data.get("total_steps", 6)
    }

@router.post("/analytics/refresh-data")
async def refresh_data(background_tasks: BackgroundTasks):
    """Refresh Calendly data in the background (alias for download-data)"""
    return await download_calendly_data(background_tasks)

@router.get("/analytics/cleverly-introduction", response_model=AnalyticsResponse)
async def get_cleverly_analytics():
    """Get comprehensive analytics for Cleverly Introduction events"""
    analytics_service = AnalyticsService()
    
    # Check if data exists
    try:
        has_data = await analytics_service.data_processor.check_data_exists()
        if not has_data:
            raise HTTPException(
                status_code=404, 
                detail="No data available. Please download Calendly data first using the download button."
            )
    except Exception as e:
        print(f"Error checking data existence: {e}")
        raise HTTPException(
            status_code=404,
            detail="No data available. Please download Calendly data first."
        )
    
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
    
    has_data = await analytics_service.data_processor.check_data_exists()
    if not has_data:
        return {
            "error": "No data available", 
            "message": "Please download data first using the download button"
        }
    
    await analytics_service.data_processor.load_data()
    df = analytics_service.data_processor.create_analytics_dataframe()
    
    if df.empty:
        return {"error": "No data available", "message": "Please download data first"}
    
    return {
        "columns": df.columns.tolist(),
        "shape": df.shape,
        "sample": df.head(10).to_dict('records'),
        "total_records": len(df)
    }