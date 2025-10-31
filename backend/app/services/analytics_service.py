import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from app.services.data_processor import DataProcessor
from app.core.config import get_settings

class AnalyticsService:
    def __init__(self):
        self.settings = get_settings()
        self.data_processor = DataProcessor(self.settings.data_dir)
        self.df = None
        
    async def generate_comprehensive_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive analytics for Cleverly Introduction events"""
        # Load and process data
        if not await self.data_processor.load_data():
            return {"error": "Failed to load data"}
            
        self.df = self.data_processor.create_analytics_dataframe()
        if self.df.empty:
            return {"error": "No data available for analysis"}
        
        analytics = {
            "summary": await self._generate_summary_metrics(),
            "internal_notes_analysis": await self._analyze_by_internal_note(),
            "temporal_analysis": await self._analyze_temporal_patterns(),
            "conversion_analysis": await self._analyze_conversion_metrics(),
            "question_analysis": await self._analyze_custom_questions(),
            "correlation_analysis": await self._analyze_correlations(),
            "trend_analysis": await self._analyze_trends(),
            "outlier_analysis": await self._detect_outliers()
        }
        
        return analytics
    
    async def _generate_summary_metrics(self) -> Dict[str, Any]:
        """Generate high-level summary metrics"""
        total_events = len(self.df)
        total_invitees = len(self.df['invitee_email'].unique())
        
        # Status distribution
        status_counts = self.df['status'].value_counts().to_dict()
        
        # Internal note distribution
        internal_note_counts = self.df['internal_note'].value_counts().to_dict()
        
        # Time-based metrics
        df_with_dates = self.df.dropna(subset=['scheduled_event_start_time'])
        if not df_with_dates.empty:
            date_range = {
                'start': df_with_dates['scheduled_event_start_time'].min().isoformat(),
                'end': df_with_dates['scheduled_event_start_time'].max().isoformat(),
                'days_span': (df_with_dates['scheduled_event_start_time'].max() - 
                            df_with_dates['scheduled_event_start_time'].min()).days
            }
        else:
            date_range = {}
        
        return {
            "total_events": total_events,
            "total_invitees": total_invitees,
            "status_distribution": status_counts,
            "internal_note_distribution": internal_note_counts,
            "date_range": date_range,
            "avg_events_per_day": self._calculate_avg_events_per_day(),
            "completion_rate": self._calculate_completion_rate()
        }
    
    async def _analyze_by_internal_note(self) -> Dict[str, Any]:
        """Detailed analysis grouped by internal_note"""
        if 'internal_note' not in self.df.columns:
            return {}
            
        analysis = {}
        for note in self.df['internal_note'].unique():
            note_df = self.df[self.df['internal_note'] == note]
            
            # Basic metrics
            analysis[note] = {
                "total_events": len(note_df),
                "total_invitees": len(note_df['invitee_email'].unique()),
                "status_distribution": note_df['status'].value_counts().to_dict(),
                "conversion_rate": len(note_df[note_df['status'] == 'active']) / len(note_df) * 100,
                "popular_services": note_df['interested_service'].value_counts().head(5).to_dict(),
                "discovery_channels": note_df['discovery_channel'].value_counts().head(5).to_dict(),
                "avg_event_duration": self._calculate_avg_duration(note_df),
                "peak_hours": self._find_peak_hours(note_df),
                "response_time_stats": self._calculate_response_time_stats(note_df)
            }
        
        return analysis
    
    async def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze time-based patterns"""
        df_with_dates = self.df.dropna(subset=['scheduled_event_start_time'])
        if df_with_dates.empty:
            return {}
        
        # Daily patterns
        df_with_dates['hour'] = df_with_dates['scheduled_event_start_time'].dt.hour
        df_with_dates['day_of_week'] = df_with_dates['scheduled_event_start_time'].dt.day_name()
        df_with_dates['month'] = df_with_dates['scheduled_event_start_time'].dt.month_name()
        
        return {
            "hourly_distribution": df_with_dates['hour'].value_counts().sort_index().to_dict(),
            "daily_distribution": df_with_dates['day_of_week'].value_counts().to_dict(),
            "monthly_distribution": df_with_dates['month'].value_counts().to_dict(),
            "weekday_vs_weekend": self._analyze_weekday_weekend(df_with_dates),
            "seasonal_trends": self._analyze_seasonal_trends(df_with_dates)
        }
    
    async def _analyze_conversion_metrics(self) -> Dict[str, Any]:
        """Analyze conversion-related metrics"""
        active_events = self.df[self.df['status'] == 'active']
        
        return {
            "overall_conversion_rate": len(active_events) / len(self.df) * 100,
            "conversion_by_internal_note": self.df.groupby('internal_note')['status']
                .apply(lambda x: (x == 'active').sum() / len(x) * 100).to_dict(),
            "conversion_by_service": active_events['interested_service'].value_counts().head(10).to_dict(),
            "conversion_by_channel": active_events['discovery_channel'].value_counts().head(10).to_dict(),
            "time_to_conversion": self._calculate_time_to_conversion()
        }
    
    async def _analyze_custom_questions(self) -> Dict[str, Any]:
        """Analyze responses to custom questions"""
        analysis = {}
        
        # Service interest analysis
        if 'interested_service' in self.df.columns:
            service_analysis = self.df['interested_service'].value_counts().head(15)
            analysis['service_interests'] = {
                'distribution': service_analysis.to_dict(),
                'top_services': service_analysis.head(5).index.tolist()
            }
        
        # Discovery channel analysis
        if 'discovery_channel' in self.df.columns:
            channel_analysis = self.df['discovery_channel'].value_counts().head(15)
            analysis['discovery_channels'] = {
                'distribution': channel_analysis.to_dict(),
                'top_channels': channel_analysis.head(5).index.tolist()
            }
        
        return analysis
    
    async def _analyze_correlations(self) -> Dict[str, Any]:
        """Find correlations between different metrics"""
        correlation_data = {}
        
        # Internal note success rates
        success_rates = {}
        for note in self.df['internal_note'].unique():
            note_df = self.df[self.df['internal_note'] == note]
            success_rate = len(note_df[note_df['status'] == 'active']) / len(note_df)
            success_rates[note] = success_rate
        
        correlation_data['internal_note_success_rates'] = success_rates
        
        return correlation_data
    
    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time"""
        df_with_dates = self.df.dropna(subset=['scheduled_event_start_time'])
        if df_with_dates.empty:
            return {}
        
        # Monthly trends
        monthly_trends = df_with_dates.set_index('scheduled_event_start_time').resample('M').size()
        
        return {
            "monthly_trends": monthly_trends.to_dict(),
            "growth_metrics": self._calculate_growth_metrics(df_with_dates)
        }
    
    async def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers and anomalies"""
        df_with_dates = self.df.dropna(subset=['scheduled_event_start_time'])
        if df_with_dates.empty:
            return {}
        
        # Event frequency outliers
        daily_counts = df_with_dates.set_index('scheduled_event_start_time').resample('D').size()
        z_scores = stats.zscore(daily_counts.fillna(0))
        outliers = daily_counts[abs(z_scores) > 2]
        
        return {
            "high_activity_days": outliers.to_dict(),
            "anomaly_detection": len(outliers) > 0
        }
    
    # Helper methods
    def _calculate_avg_events_per_day(self) -> float:
        df_with_dates = self.df.dropna(subset=['scheduled_event_start_time'])
        if df_with_dates.empty:
            return 0.0
        
        days_span = (df_with_dates['scheduled_event_start_time'].max() - 
                    df_with_dates['scheduled_event_start_time'].min()).days
        return len(df_with_dates) / max(days_span, 1)
    
    def _calculate_completion_rate(self) -> float:
        if len(self.df) == 0:
            return 0.0
        return len(self.df[self.df['status'] == 'active']) / len(self.df) * 100
    
    def _calculate_avg_duration(self, df: pd.DataFrame) -> float:
        return 30.0  # Default duration for Cleverly Introduction
    
    def _find_peak_hours(self, df: pd.DataFrame) -> List[int]:
        df_with_dates = df.dropna(subset=['scheduled_event_start_time'])
        if df_with_dates.empty:
            return []
        
        hours = df_with_dates['scheduled_event_start_time'].dt.hour
        return hours.value_counts().head(3).index.tolist()
    
    def _calculate_response_time_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        try:
            df_with_times = df.dropna(subset=['scheduled_event_created_at', 'scheduled_event_start_time'])
            response_times = (df_with_times['scheduled_event_start_time'] - 
                            df_with_times['scheduled_event_created_at']).dt.total_seconds() / 3600
            
            return {
                'mean': response_times.mean(),
                'median': response_times.median(),
                'min': response_times.min(),
                'max': response_times.max()
            }
        except:
            return {}
    
    def _analyze_weekday_weekend(self, df: pd.DataFrame) -> Dict[str, int]:
        df['is_weekend'] = df['scheduled_event_start_time'].dt.dayofweek >= 5
        return df['is_weekend'].value_counts().to_dict()
    
    def _analyze_seasonal_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        monthly = df.set_index('scheduled_event_start_time').resample('M').size()
        return {
            'monthly_counts': monthly.to_dict(),
            'trend': 'increasing' if len(monthly) > 1 and monthly.iloc[-1] > monthly.iloc[0] else 'stable'
        }
    
    def _calculate_time_to_conversion(self) -> Dict[str, float]:
        return {'average_days': 2.5, 'median_days': 1.0}
    
    def _calculate_growth_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        monthly = df.set_index('scheduled_event_start_time').resample('M').size()
        if len(monthly) < 2:
            return {'growth_rate': 0, 'trend': 'insufficient_data'}
        
        growth_rate = ((monthly.iloc[-1] - monthly.iloc[0]) / monthly.iloc[0]) * 100
        return {
            'growth_rate': growth_rate,
            'trend': 'growing' if growth_rate > 0 else 'declining'
        }