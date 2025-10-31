from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class AnalyticsRequest(BaseModel):
    refresh_data: bool = Field(False, description="Whether to refresh data from Calendly API")

class MetricSummary(BaseModel):
    total_events: int
    total_invitees: int
    completion_rate: float
    avg_events_per_day: float

class InternalNoteAnalysis(BaseModel):
    internal_note: str
    total_events: int
    conversion_rate: float
    popular_services: Dict[str, int]
    discovery_channels: Dict[str, int]
    peak_hours: List[int]
    response_time_stats: Dict[str, float]

class TemporalAnalysis(BaseModel):
    hourly_distribution: Dict[str, int]
    daily_distribution: Dict[str, int]
    monthly_distribution: Dict[str, int]
    seasonal_trends: Dict[str, Any]

class ConversionAnalysis(BaseModel):
    overall_conversion_rate: float
    conversion_by_internal_note: Dict[str, float]
    conversion_by_service: Dict[str, int]
    conversion_by_channel: Dict[str, int]

class QuestionAnalysis(BaseModel):
    service_interests: Dict[str, Any]
    discovery_channels: Dict[str, Any]

class AnalyticsResponse(BaseModel):
    summary: MetricSummary
    internal_notes_analysis: Dict[str, InternalNoteAnalysis]
    temporal_analysis: TemporalAnalysis
    conversion_analysis: ConversionAnalysis
    question_analysis: QuestionAnalysis
    correlation_analysis: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    outlier_analysis: Dict[str, Any]

class DataPreviewResponse(BaseModel):
    total_events: int
    total_invitees: int
    internal_notes_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    date_range: Dict[str, Optional[str]]
    columns_available: List[str]