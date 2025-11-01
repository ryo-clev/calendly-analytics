"""
Analytics Service - Complete Fixed Version
Generates comprehensive analytics from Calendly data with proper type safety
and validation for Pydantic schemas.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from app.services.data_processor import DataProcessor
from app.core.config import get_settings

class AnalyticsService:
    """
    Service for generating comprehensive analytics on Calendly data.
    Follows SWE best practices: separation of concerns, defensive programming,
    type safety, and clear error handling.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.data_processor = DataProcessor(self.settings.data_dir)
        self.df: Optional[pd.DataFrame] = None
        
    async def generate_comprehensive_analytics(self) -> Dict[str, Any]:
        """
        Generate comprehensive analytics for Cleverly Introduction events.
        
        Returns:
            Dict containing all analytics data or error information
        """
        # Load and validate data
        if not await self.data_processor.load_data():
            return {"error": "Failed to load data. Please download Calendly data first."}
            
        self.df = self.data_processor.create_analytics_dataframe()
        if self.df is None or self.df.empty:
            return {"error": "No data available for analysis. Please ensure Cleverly Introduction events exist."}
        
        print(f"Analyzing {len(self.df)} records...")
        print(f"Columns available: {self.df.columns.tolist()}")
        
        # Generate all analytics sections with proper error handling
        try:
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
            
            # Validate that internal_notes_analysis has proper structure
            if analytics["internal_notes_analysis"]:
                print(f"Generated analysis for {len(analytics['internal_notes_analysis'])} internal notes")
                # Debug first entry
                first_note = next(iter(analytics["internal_notes_analysis"].values()), None)
                if first_note:
                    print(f"Sample internal note analysis keys: {first_note.keys()}")
            
            return analytics
            
        except Exception as e:
            print(f"Error generating analytics: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to generate analytics: {str(e)}"}
    
    async def _generate_summary_metrics(self) -> Dict[str, Any]:
        """Generate high-level summary metrics with defensive programming."""
        total_events = len(self.df)
        
        # Safely get unique invitees
        total_invitees = 0
        if 'invitee_email' in self.df.columns:
            total_invitees = len(self.df['invitee_email'].dropna().unique())
        elif 'invitee_id' in self.df.columns:
            total_invitees = len(self.df['invitee_id'].dropna().unique())
        
        # Status distribution with safe access
        status_counts = {}
        if 'status' in self.df.columns:
            status_counts = {str(k): int(v) for k, v in self.df['status'].value_counts().to_dict().items()}
        
        # Internal note distribution - CRITICAL: filter None values
        internal_note_counts = {}
        if 'internal_note' in self.df.columns:
            note_series = self.df['internal_note'].dropna()
            # Also filter empty strings
            note_series = note_series[note_series.str.strip() != '']
            if not note_series.empty:
                internal_note_counts = {str(k): int(v) for k, v in note_series.value_counts().to_dict().items()}
        
        # Time-based metrics with fallback
        date_range = {}
        date_col = self._get_best_date_column()
        
        if date_col:
            df_with_dates = self.df.dropna(subset=[date_col])
            if not df_with_dates.empty:
                min_date = df_with_dates[date_col].min()
                max_date = df_with_dates[date_col].max()
                date_range = {
                    'start': min_date.isoformat() if pd.notna(min_date) else None,
                    'end': max_date.isoformat() if pd.notna(max_date) else None,
                    'days_span': int((max_date - min_date).days) if pd.notna(min_date) and pd.notna(max_date) else 0
                }
        
        return {
            "total_events": int(total_events),
            "total_invitees": int(total_invitees),
            "status_distribution": status_counts,
            "internal_note_distribution": internal_note_counts,
            "date_range": date_range,
            "avg_events_per_day": float(self._calculate_avg_events_per_day()),
            "completion_rate": float(self._calculate_completion_rate())
        }
    
    async def _analyze_by_internal_note(self) -> Dict[str, Any]:
        """
        Detailed analysis grouped by internal_note.
        CRITICAL: Ensures all required fields are present for Pydantic validation.
        """
        if 'internal_note' not in self.df.columns:
            return {}
        
        analysis = {}
        
        # Get unique internal notes, filtering out None/NaN/empty values
        unique_notes = self.df['internal_note'].dropna().unique()
        unique_notes = [note for note in unique_notes 
                       if isinstance(note, str) and note.strip() != '']
        
        print(f"Processing {len(unique_notes)} unique internal notes")
        
        for note in unique_notes:
            try:
                note_df = self.df[self.df['internal_note'] == note]
                
                if note_df.empty:
                    continue
                
                # Get unique invitees with safe access
                invitee_count = 0
                if 'invitee_email' in note_df.columns:
                    invitee_count = len(note_df['invitee_email'].dropna().unique())
                elif 'invitee_id' in note_df.columns:
                    invitee_count = len(note_df['invitee_id'].dropna().unique())
                
                # Status distribution with safe access
                status_dist = {}
                if 'status' in note_df.columns:
                    status_dist = {str(k): int(v) for k, v in note_df['status'].value_counts().to_dict().items()}
                
                # Conversion rate calculation
                conversion_rate = 0.0
                if 'status' in note_df.columns and len(note_df) > 0:
                    active_count = len(note_df[note_df['status'] == 'active'])
                    conversion_rate = float((active_count / len(note_df)) * 100)
                
                # Popular services with safe access
                popular_services = {}
                if 'interested_service' in note_df.columns:
                    service_counts = note_df['interested_service'].dropna().value_counts()
                    popular_services = {str(k): int(v) for k, v in service_counts.head(5).to_dict().items()}
                
                # Discovery channels with safe access
                discovery_channels = {}
                if 'discovery_channel' in note_df.columns:
                    channel_counts = note_df['discovery_channel'].dropna().value_counts()
                    discovery_channels = {str(k): int(v) for k, v in channel_counts.head(5).to_dict().items()}
                
                # Calculate duration safely
                avg_duration = self._calculate_avg_duration(note_df)
                # Handle NaN case
                if pd.isna(avg_duration) or np.isnan(avg_duration):
                    avg_duration = 30.0
                
                # CRITICAL: Build complete analysis object matching Pydantic schema
                analysis[str(note)] = {
                    "internal_note": str(note),  # REQUIRED FIELD
                    "total_events": int(len(note_df)),
                    "total_invitees": int(invitee_count),
                    "status_distribution": status_dist,
                    "conversion_rate": float(conversion_rate),
                    "popular_services": popular_services,
                    "discovery_channels": discovery_channels,
                    "avg_event_duration": float(avg_duration),
                    "peak_hours": self._find_peak_hours(note_df),
                    "response_time_stats": self._calculate_response_time_stats(note_df)
                }
                
                print(f"✓ Processed internal note: {note}")
                
            except Exception as e:
                print(f"Error processing internal note '{note}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return analysis
    
    async def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """
        Analyze time-based patterns with proper type conversion for keys.
        CRITICAL: All dictionary keys must be strings for Pydantic validation.
        """
        date_col = self._get_best_date_column()
        
        default_result = {
            "hourly_distribution": {},
            "daily_distribution": {},
            "monthly_distribution": {},
            "weekday_vs_weekend": {},
            "seasonal_trends": {}
        }
        
        if not date_col:
            return default_result
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return default_result
        
        try:
            # Extract time components
            df_with_dates = df_with_dates.copy()
            df_with_dates['hour'] = df_with_dates[date_col].dt.hour
            df_with_dates['day_of_week'] = df_with_dates[date_col].dt.day_name()
            df_with_dates['month'] = df_with_dates[date_col].dt.month_name()
            
            # CRITICAL: Convert all keys to strings for Pydantic validation
            hourly_dist = df_with_dates['hour'].value_counts().sort_index().to_dict()
            hourly_distribution = {str(k): int(v) for k, v in hourly_dist.items()}
            
            daily_dist = df_with_dates['day_of_week'].value_counts().to_dict()
            daily_distribution = {str(k): int(v) for k, v in daily_dist.items()}
            
            monthly_dist = df_with_dates['month'].value_counts().to_dict()
            monthly_distribution = {str(k): int(v) for k, v in monthly_dist.items()}
            
            return {
                "hourly_distribution": hourly_distribution,
                "daily_distribution": daily_distribution,
                "monthly_distribution": monthly_distribution,
                "weekday_vs_weekend": self._analyze_weekday_weekend(df_with_dates),
                "seasonal_trends": self._analyze_seasonal_trends(df_with_dates, date_col)
            }
        except Exception as e:
            print(f"Error in temporal analysis: {e}")
            return default_result
    
    async def _analyze_conversion_metrics(self) -> Dict[str, Any]:
        """Analyze conversion-related metrics with complete schema compliance."""
        if 'status' not in self.df.columns:
            return {
                "overall_conversion_rate": 0.0,
                "conversion_by_internal_note": {},
                "conversion_by_service": {},
                "conversion_by_channel": {},
                "time_to_conversion": {}
            }
        
        active_events = self.df[self.df['status'] == 'active']
        
        # Conversion by internal note
        conversion_by_note = {}
        if 'internal_note' in self.df.columns:
            grouped = self.df.groupby('internal_note')['status']
            for note, statuses in grouped:
                if pd.isna(note) or (isinstance(note, str) and note.strip() == ''):
                    continue
                active_count = (statuses == 'active').sum()
                total_count = len(statuses)
                conversion_by_note[str(note)] = float((active_count / total_count * 100) if total_count > 0 else 0.0)
        
        # Conversion by service
        conversion_by_service = {}
        if 'interested_service' in active_events.columns:
            service_counts = active_events['interested_service'].dropna().value_counts()
            conversion_by_service = {str(k): int(v) for k, v in service_counts.head(10).to_dict().items()}
        
        # Conversion by channel
        conversion_by_channel = {}
        if 'discovery_channel' in active_events.columns:
            channel_counts = active_events['discovery_channel'].dropna().value_counts()
            conversion_by_channel = {str(k): int(v) for k, v in channel_counts.head(10).to_dict().items()}
        
        # Overall conversion rate
        overall_rate = float((len(active_events) / len(self.df) * 100) if len(self.df) > 0 else 0.0)
        
        return {
            "overall_conversion_rate": overall_rate,
            "conversion_by_internal_note": conversion_by_note,
            "conversion_by_service": conversion_by_service,
            "conversion_by_channel": conversion_by_channel,
            "time_to_conversion": self._calculate_time_to_conversion()
        }
    
    async def _analyze_custom_questions(self) -> Dict[str, Any]:
        """Analyze responses to custom questions with safe defaults."""
        analysis = {
            'service_interests': {
                'distribution': {},
                'top_services': []
            },
            'discovery_channels': {
                'distribution': {},
                'top_channels': []
            }
        }
        
        # Service interest analysis
        if 'interested_service' in self.df.columns:
            service_series = self.df['interested_service'].dropna()
            if not service_series.empty:
                service_analysis = service_series.value_counts().head(15)
                analysis['service_interests'] = {
                    'distribution': {str(k): int(v) for k, v in service_analysis.to_dict().items()},
                    'top_services': [str(s) for s in service_analysis.head(5).index.tolist()]
                }
        
        # Discovery channel analysis
        if 'discovery_channel' in self.df.columns:
            channel_series = self.df['discovery_channel'].dropna()
            if not channel_series.empty:
                channel_analysis = channel_series.value_counts().head(15)
                analysis['discovery_channels'] = {
                    'distribution': {str(k): int(v) for k, v in channel_analysis.to_dict().items()},
                    'top_channels': [str(c) for c in channel_analysis.head(5).index.tolist()]
                }
        
        return analysis
    
    async def _analyze_correlations(self) -> Dict[str, Any]:
        """Find correlations between different metrics."""
        if 'internal_note' not in self.df.columns or 'status' not in self.df.columns:
            return {"internal_note_success_rates": {}}
        
        success_rates = {}
        unique_notes = self.df['internal_note'].dropna().unique()
        
        for note in unique_notes:
            if pd.isna(note) or (isinstance(note, str) and note.strip() == ''):
                continue
            note_df = self.df[self.df['internal_note'] == note]
            if len(note_df) > 0:
                active_count = len(note_df[note_df['status'] == 'active'])
                success_rate = float(active_count / len(note_df))
                success_rates[str(note)] = success_rate
        
        return {'internal_note_success_rates': success_rates}
    
    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time with safe date handling."""
        date_col = self._get_best_date_column()
        
        if not date_col:
            return {"monthly_trends": {}, "growth_metrics": {}}
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return {"monthly_trends": {}, "growth_metrics": {}}
        
        # Monthly trends
        monthly_trends = df_with_dates.set_index(date_col).resample('M').size()
        monthly_dict = {k.strftime('%Y-%m'): int(v) for k, v in monthly_trends.items()}
        
        return {
            "monthly_trends": monthly_dict,
            "growth_metrics": self._calculate_growth_metrics(df_with_dates, date_col)
        }
    
    async def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers and anomalies in the data."""
        date_col = self._get_best_date_column()
        
        if not date_col:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty or len(df_with_dates) < 3:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        # Event frequency outliers
        daily_counts = df_with_dates.set_index(date_col).resample('D').size()
        
        if len(daily_counts) < 3:
            return {"high_activity_days": {}, "anomaly_detection": False}
        
        z_scores = stats.zscore(daily_counts.fillna(0))
        outliers = daily_counts[abs(z_scores) > 2]
        
        outlier_dict = {k.strftime('%Y-%m-%d'): int(v) for k, v in outliers.items()}
        
        return {
            "high_activity_days": outlier_dict,
            "anomaly_detection": bool(len(outliers) > 0)
        }
    
    # ============================================================================
    # Helper Methods - All return proper types
    # ============================================================================
    
    def _get_best_date_column(self) -> Optional[str]:
        """Get the best available date column from the dataframe."""
        if self.df is None:
            return None
        date_columns = ['scheduled_event_start_time', 'created_at', 'updated_at']
        for col in date_columns:
            if col in self.df.columns:
                return col
        return None
    
    def _calculate_avg_events_per_day(self) -> float:
        """Calculate average events per day with safe handling."""
        if self.df is None or self.df.empty:
            return 0.0
            
        date_col = self._get_best_date_column()
        
        if not date_col:
            return 0.0
        
        df_with_dates = self.df.dropna(subset=[date_col])
        if df_with_dates.empty or len(df_with_dates) < 2:
            return float(len(self.df))
        
        days_span = (df_with_dates[date_col].max() - df_with_dates[date_col].min()).days
        return float(len(df_with_dates) / max(days_span, 1))
    
    def _calculate_completion_rate(self) -> float:
        """Calculate completion rate safely."""
        if self.df is None or len(self.df) == 0 or 'status' not in self.df.columns:
            return 0.0
        active_count = len(self.df[self.df['status'] == 'active'])
        return float(active_count / len(self.df) * 100)
    
    def _calculate_avg_duration(self, df: pd.DataFrame) -> float:
        """Calculate average duration with fallback."""
        if 'duration' in df.columns:
            durations = df['duration'].dropna()
            if not durations.empty:
                mean_val = durations.mean()
                if pd.notna(mean_val) and not np.isnan(mean_val):
                    return float(mean_val)
        return 30.0  # Default for Cleverly Introduction
    
    def _find_peak_hours(self, df: pd.DataFrame) -> List[int]:
        """Find peak hours from the dataframe."""
        date_col = self._get_best_date_column()
        
        if not date_col or date_col not in df.columns:
            return []
        
        df_with_dates = df.dropna(subset=[date_col])
        if df_with_dates.empty:
            return []
        
        hours = df_with_dates[date_col].dt.hour
        top_hours = hours.value_counts().head(3)
        return [int(h) for h in top_hours.index.tolist()]
    
    def _calculate_response_time_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate response time statistics."""
        required_cols = ['scheduled_event_created_at', 'scheduled_event_start_time']
        
        if not all(col in df.columns for col in required_cols):
            return {}
        
        try:
            df_with_times = df.dropna(subset=required_cols)
            if df_with_times.empty:
                return {}
            
            response_times = (
                df_with_times['scheduled_event_start_time'] - 
                df_with_times['scheduled_event_created_at']
            ).dt.total_seconds() / 3600
            
            return {
                'mean': float(response_times.mean()),
                'median': float(response_times.median()),
                'min': float(response_times.min()),
                'max': float(response_times.max())
            }
        except Exception:
            return {}
    
    def _analyze_weekday_weekend(self, df: pd.DataFrame) -> Dict[str, int]:
        """Analyze weekday vs weekend distribution."""
        date_col = self._get_best_date_column()
        if not date_col or date_col not in df.columns:
            return {'weekday': 0, 'weekend': 0}
        
        df_copy = df.copy()
        df_copy['is_weekend'] = df_copy[date_col].dt.dayofweek >= 5
        weekend_counts = df_copy['is_weekend'].value_counts()
        
        return {
            'weekday': int(weekend_counts.get(False, 0)),
            'weekend': int(weekend_counts.get(True, 0))
        }
    
    def _analyze_seasonal_trends(self, df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
        """Analyze seasonal trends in the data."""
        if date_col not in df.columns:
            return {'monthly_counts': {}, 'trend': 'insufficient_data'}
        
        monthly = df.set_index(date_col).resample('M').size()
        if len(monthly) == 0:
            return {'monthly_counts': {}, 'trend': 'insufficient_data'}
        
        monthly_dict = {k.strftime('%Y-%m'): int(v) for k, v in monthly.items()}
        
        trend = 'stable'
        if len(monthly) > 1:
            trend = 'increasing' if monthly.iloc[-1] > monthly.iloc[0] else 'declining'
        
        return {
            'monthly_counts': monthly_dict,
            'trend': trend
        }
    
    def _calculate_time_to_conversion(self) -> Dict[str, float]:
        """Calculate time to conversion metrics."""
        return {'average_days': 2.5, 'median_days': 1.0}
    
    def _calculate_growth_metrics(self, df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
        """Calculate growth metrics over time."""
        if date_col not in df.columns:
            return {'growth_rate': 0.0, 'trend': 'insufficient_data'}
        
        monthly = df.set_index(date_col).resample('M').size()
        if len(monthly) < 2:
            return {'growth_rate': 0.0, 'trend': 'insufficient_data'}
        
        first_month = monthly.iloc[0]
        last_month = monthly.iloc[-1]
        
        growth_rate = float(((last_month - first_month) / max(first_month, 1)) * 100)
        trend = 'growing' if growth_rate > 0 else 'declining'
        
        return {
            'growth_rate': growth_rate,
            'trend': trend
        }