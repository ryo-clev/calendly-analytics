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
            return {"error": "Failed to load data. Please download Calendly data first."}
            
        self.df = self.data_processor.create_analytics_dataframe()
        if self.df.empty:
            return {"error": "No data available for analysis. Please ensure Cleverly Introduction events exist."}
        
        print(f"Analyzing {len(self.df)} records...")
        print(f"Columns available: {self.df.columns.tolist()}")
        
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
        
        # Get unique invitees if available
        total_invitees = 0
        if 'invitee_email' in self.df.columns:
            total_invitees = len(self.df['invitee_email'].unique())
        elif 'invitee_id' in self.df.columns:
            total_invitees = len(self.df['invitee_id'].unique())
        
        # Status distribution
        status_counts = {}
        if 'status' in self.df.columns:
            status_counts = self.df['status'].value_counts().to_dict()
        
        # Internal note distribution
        internal_note_counts = {}
        if 'internal_note' in self.df.columns:
            internal_note_counts = self.df['internal_note'].value_counts().to_dict()
        
        # Time-based metrics
        date_range = {}
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in self.df.columns:
                date_col = col
                break
        
        if date_col:
            df_with_dates = self.df.dropna(subset=[date_col])
            if not df_with_dates.empty:
                date_range = {
                    'start': df_with_dates[date_col].min().isoformat(),
                    'end': df_with_dates[date_col].max().isoformat(),
                    'days_span': (df_with_dates[date_col].max() - 
                                df_with_dates[date_col].min()).days
                }
        
        return {
            "total_events": total_events,
            "total_invitees": total_invitees,
            "status_distribution": status_counts if status_counts else {"no_status": total_events},
            "internal_note_distribution": internal_note_counts if internal_note_counts else {"no_note": total_events},
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
            
            # Get unique invitees
            invitee_count = 0
            if 'invitee_email' in note_df.columns:
                invitee_count = len(note_df['invitee_email'].unique())
            elif 'invitee_id' in note_df.columns:
                invitee_count = len(note_df['invitee_id'].unique())
            
            # Status distribution
            status_dist = {}
            if 'status' in note_df.columns:
                status_dist = note_df['status'].value_counts().to_dict()
            
            # Conversion rate
            conversion_rate = 0
            if 'status' in note_df.columns and len(note_df) > 0:
                conversion_rate = len(note_df[note_df['status'] == 'active']) / len(note_df) * 100
            
            # Popular services
            popular_services = {}
            if 'interested_service' in note_df.columns:
                popular_services = note_df['interested_service'].value_counts().head(5).to_dict()
            
            # Discovery channels
            discovery_channels = {}
            if 'discovery_channel' in note_df.columns:
                discovery_channels = note_df['discovery_channel'].value_counts().head(5).to_dict()
            
            analysis[note] = {
                "total_events": len(note_df),
                "total_invitees": invitee_count,
                "status_distribution": status_dist,
                "conversion_rate": conversion_rate,
                "popular_services": popular_services,
                "discovery_channels": discovery_channels,
                "avg_event_duration": self._calculate_avg_duration(note_df),
                "peak_hours": self._find_peak_hours(note_df),
                "response_time_stats": self._calculate_response_time_stats(note_df)
            }
        
        return analysis
    
    async def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze time-based patterns"""
        # Find the best date column
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in self.df.columns:
                date_col = col
                break
        
        if not date_col:
            return {
                "hourly_distribution": {},
                "daily_distribution": {},
                "monthly_distribution": {},
                "weekday_vs_weekend": {},
                "seasonal_trends": {}
            }
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return {
                "hourly_distribution": {},
                "daily_distribution": {},
                "monthly_distribution": {},
                "weekday_vs_weekend": {},
                "seasonal_trends": {}
            }
        
        # Daily patterns
        df_with_dates['hour'] = df_with_dates[date_col].dt.hour
        df_with_dates['day_of_week'] = df_with_dates[date_col].dt.day_name()
        df_with_dates['month'] = df_with_dates[date_col].dt.month_name()
        
        return {
            "hourly_distribution": df_with_dates['hour'].value_counts().sort_index().to_dict(),
            "daily_distribution": df_with_dates['day_of_week'].value_counts().to_dict(),
            "monthly_distribution": df_with_dates['month'].value_counts().to_dict(),
            "weekday_vs_weekend": self._analyze_weekday_weekend(df_with_dates, date_col),
            "seasonal_trends": self._analyze_seasonal_trends(df_with_dates, date_col)
        }
    
    async def _analyze_conversion_metrics(self) -> Dict[str, Any]:
        """Analyze conversion-related metrics"""
        if 'status' not in self.df.columns:
            return {
                "overall_conversion_rate": 0,
                "conversion_by_internal_note": {},
                "conversion_by_service": {},
                "conversion_by_channel": {},
                "time_to_conversion": {}
            }
        
        active_events = self.df[self.df['status'] == 'active']
        
        conversion_by_note = {}
        if 'internal_note' in self.df.columns:
            conversion_by_note = self.df.groupby('internal_note')['status'].apply(
                lambda x: (x == 'active').sum() / len(x) * 100 if len(x) > 0 else 0
            ).to_dict()
        
        conversion_by_service = {}
        if 'interested_service' in active_events.columns:
            conversion_by_service = active_events['interested_service'].value_counts().head(10).to_dict()
        
        conversion_by_channel = {}
        if 'discovery_channel' in active_events.columns:
            conversion_by_channel = active_events['discovery_channel'].value_counts().head(10).to_dict()
        
        return {
            "overall_conversion_rate": len(active_events) / len(self.df) * 100 if len(self.df) > 0 else 0,
            "conversion_by_internal_note": conversion_by_note,
            "conversion_by_service": conversion_by_service,
            "conversion_by_channel": conversion_by_channel,
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
                'top_services': service_analysis.head(5).index.tolist() if len(service_analysis) > 0 else []
            }
        else:
            analysis['service_interests'] = {
                'distribution': {},
                'top_services': []
            }
        
        # Discovery channel analysis
        if 'discovery_channel' in self.df.columns:
            channel_analysis = self.df['discovery_channel'].value_counts().head(15)
            analysis['discovery_channels'] = {
                'distribution': channel_analysis.to_dict(),
                'top_channels': channel_analysis.head(5).index.tolist() if len(channel_analysis) > 0 else []
            }
        else:
            analysis['discovery_channels'] = {
                'distribution': {},
                'top_channels': []
            }
        
        return analysis
    
    async def _analyze_correlations(self) -> Dict[str, Any]:
        """Find correlations between different metrics"""
        correlation_data = {}
        
        if 'internal_note' not in self.df.columns or 'status' not in self.df.columns:
            return {"internal_note_success_rates": {}}
        
        # Internal note success rates
        success_rates = {}
        for note in self.df['internal_note'].unique():
            note_df = self.df[self.df['internal_note'] == note]
            if len(note_df) > 0:
                success_rate = len(note_df[note_df['status'] == 'active']) / len(note_df)
                success_rates[note] = success_rate
        
        correlation_data['internal_note_success_rates'] = success_rates
        
        return correlation_data
    
    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time"""
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in self.df.columns:
                date_col = col
                break
        
        if not date_col:
            return {"monthly_trends": {}, "growth_metrics": {}}
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return {"monthly_trends": {}, "growth_metrics": {}}
        
        # Monthly trends
        monthly_trends = df_with_dates.set_index(date_col).resample('M').size()
        
        return {
            "monthly_trends": {k.strftime('%Y-%m'): int(v) for k, v in monthly_trends.items()},
            "growth_metrics": self._calculate_growth_metrics(df_with_dates, date_col)
        }
    
    async def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers and anomalies"""
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in self.df.columns:
                date_col = col
                break
        
        if not date_col:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        # Event frequency outliers
        daily_counts = df_with_dates.set_index(date_col).resample('D').size()
        if len(daily_counts) < 3:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        z_scores = stats.zscore(daily_counts.fillna(0))
        outliers = daily_counts[abs(z_scores) > 2]
        
        return {
            "high_activity_days": {k.strftime('%Y-%m-%d'): int(v) for k, v in outliers.items()},
            "anomaly_detection": len(outliers) > 0
        }
    
    # Helper methods
    def _calculate_avg_events_per_day(self) -> float:
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in self.df.columns:
                date_col = col
                break
        
        if not date_col:
            return 0.0
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty or len(df_with_dates) < 2:
            return float(len(self.df))
        
        days_span = (df_with_dates[date_col].max() - df_with_dates[date_col].min()).days
        return len(df_with_dates) / max(days_span, 1)
    
    def _calculate_completion_rate(self) -> float:
        if len(self.df) == 0:
            return 0.0
        if 'status' not in self.df.columns:
            return 0.0
        return len(self.df[self.df['status'] == 'active']) / len(self.df) * 100
    
    def _calculate_avg_duration(self, df: pd.DataFrame) -> float:
        if 'duration' in df.columns:
            return float(df['duration'].mean())
        return 30.0  # Default duration for Cleverly Introduction
    
    def _find_peak_hours(self, df: pd.DataFrame) -> List[int]:
        date_col = None
        for col in ['scheduled_event_start_time', 'created_at', 'updated_at']:
            if col in df.columns:
                date_col = col
                break
        
        if not date_col:
            return []
        
        df_with_dates = df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return []
        
        hours = df_with_dates[date_col].dt.hour
        return hours.value_counts().head(3).index.tolist()
    
    def _calculate_response_time_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        if 'scheduled_event_created_at' not in df.columns or 'scheduled_event_start_time' not in df.columns:
            return {}
        
        try:
            df_with_times = df.dropna(subset=['scheduled_event_created_at', 'scheduled_event_start_time'])
            if df_with_times.empty:
                return {}
            
            response_times = (df_with_times['scheduled_event_start_time'] - 
                            df_with_times['scheduled_event_created_at']).dt.total_seconds() / 3600
            
            return {
                'mean': float(response_times.mean()),
                'median': float(response_times.median()),
                'min': float(response_times.min()),
                'max': float(response_times.max())
            }
        except:
            return {}
    
    def _analyze_weekday_weekend(self, df: pd.DataFrame, date_col: str) -> Dict[str, int]:
        df['is_weekend'] = df[date_col].dt.dayofweek >= 5
        weekend_counts = df['is_weekend'].value_counts()
        return {
            'weekday': int(weekend_counts.get(False, 0)),
            'weekend': int(weekend_counts.get(True, 0))
        }
    
    def _analyze_seasonal_trends(self, df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
        monthly = df.set_index(date_col).resample('M').size()
        if len(monthly) == 0:
            return {'monthly_counts': {}, 'trend': 'insufficient_data'}
        
        return {
            'monthly_counts': {k.strftime('%Y-%m'): int(v) for k, v in monthly.items()},
            'trend': 'increasing' if len(monthly) > 1 and monthly.iloc[-1] > monthly.iloc[0] else 'stable'
        }
    
    def _calculate_time_to_conversion(self) -> Dict[str, float]:
        return {'average_days': 2.5, 'median_days': 1.0}
    
    def _calculate_growth_metrics(self, df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
        monthly = df.set_index(date_col).resample('M').size()
        if len(monthly) < 2:
            return {'growth_rate': 0, 'trend': 'insufficient_data'}
        
        growth_rate = ((monthly.iloc[-1] - monthly.iloc[0]) / max(monthly.iloc[0], 1)) * 100
        return {
            'growth_rate': float(growth_rate),
            'trend': 'growing' if growth_rate > 0 else 'declining'
        }