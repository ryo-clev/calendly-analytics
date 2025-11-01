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
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    internal_note_distribution: Dict[str, int] = Field(default_factory=dict)
    date_range: Dict[str, Any] = Field(default_factory=dict)

class InternalNoteAnalysis(BaseModel):
    internal_note: str
    total_events: int
    total_invitees: int = 0
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    conversion_rate: float
    popular_services: Dict[str, int] = Field(default_factory=dict)
    discovery_channels: Dict[str, int] = Field(default_factory=dict)
    avg_event_duration: float
    peak_hours: List[int] = Field(default_factory=list)
    response_time_stats: Dict[str, float] = Field(default_factory=dict)

class TemporalAnalysis(BaseModel):
    hourly_distribution: Dict[str, int] = Field(default_factory=dict)
    daily_distribution: Dict[str, int] = Field(default_factory=dict)
    monthly_distribution: Dict[str, int] = Field(default_factory=dict)
    weekday_vs_weekend: Dict[str, int] = Field(default_factory=dict)
    seasonal_trends: Dict[str, Any] = Field(default_factory=dict)

class ConversionAnalysis(BaseModel):
    overall_conversion_rate: float
    conversion_by_internal_note: Dict[str, float] = Field(default_factory=dict)
    conversion_by_service: Dict[str, int] = Field(default_factory=dict)
    conversion_by_channel: Dict[str, int] = Field(default_factory=dict)
    time_to_conversion: Dict[str, Any] = Field(default_factory=dict)

class QuestionAnalysis(BaseModel):
    service_interests: Dict[str, Any] = Field(default_factory=dict)
    discovery_channels: Dict[str, Any] = Field(default_factory=dict)

class AnalyticsResponse(BaseModel):
    summary: MetricSummary
    internal_notes_analysis: Dict[str, InternalNoteAnalysis]
    temporal_analysis: TemporalAnalysis
    conversion_analysis: ConversionAnalysis
    question_analysis: QuestionAnalysis
    correlation_analysis: Dict[str, Any] = Field(default_factory=dict)
    trend_analysis: Dict[str, Any] = Field(default_factory=dict)
    outlier_analysis: Dict[str, Any] = Field(default_factory=dict)

class DataPreviewResponse(BaseModel):
    total_events: int
    total_invitees: int
    internal_notes_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    date_range: Dict[str, Optional[str]]
    columns_available: List[str]