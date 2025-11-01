import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cleverly_events = []
        self.cleverly_scheduled_events = []
        self.invitees_data = []
        
    async def check_data_exists(self) -> bool:
        """Check if required data files exist"""
        event_types_path = self.data_dir / "event_types.json"
        exists = event_types_path.exists()
        print(f"Checking data existence: {event_types_path} - Exists: {exists}")
        return exists
    
    async def load_data(self) -> bool:
        """Load and process all Calendly data asynchronously"""
        try:
            # Load event types to find Cleverly Introduction events
            event_types_path = self.data_dir / "event_types.json"
            if not event_types_path.exists():
                print(f"Event types file not found: {event_types_path}")
                return False
                
            with open(event_types_path, 'r') as f:
                event_types = json.load(f)
            
            print(f"Loaded {len(event_types)} event types from file")
            
            # Find all Cleverly Introduction events
            cleverly_event_uris = []
            self.cleverly_events = []
            
            for event in event_types:
                event_data = event.get('resource', event)
                event_name = event_data.get('name', '')
                
                if event_name == 'Cleverly Introduction':
                    cleverly_event_uris.append(event_data['uri'])
                    self.cleverly_events.append(event_data)
            
            print(f"Found {len(cleverly_event_uris)} Cleverly Introduction event types")
            
            if len(self.cleverly_events) == 0:
                print("WARNING: No 'Cleverly Introduction' events found in event_types.json")
                print("Available event names:")
                for event in event_types[:5]:  # Print first 5
                    event_data = event.get('resource', event)
                    print(f"  - {event_data.get('name', 'Unknown')}")
            
            # Load scheduled events
            scheduled_events_path = self.data_dir / "scheduled_events.json"
            if not scheduled_events_path.exists():
                print(f"Scheduled events file not found: {scheduled_events_path}")
                print("This is OK - analytics will work with event types only")
                self.cleverly_scheduled_events = []
            else:
                with open(scheduled_events_path, 'r') as f:
                    scheduled_events = json.load(f)
                
                print(f"Loaded {len(scheduled_events)} scheduled events from file")
                
                # Filter for Cleverly Introduction events
                self.cleverly_scheduled_events = []
                for event in scheduled_events:
                    event_data = event.get('resource', event)
                    event_type_uri = event_data.get('event_type')
                    
                    # Also check the added metadata
                    event_name = event.get('_event_type_name', '')
                    
                    if event_type_uri in cleverly_event_uris or event_name == 'Cleverly Introduction':
                        self.cleverly_scheduled_events.append(event_data)
                
                print(f"Found {len(self.cleverly_scheduled_events)} scheduled Cleverly Introduction events")
            
            # Load invitees for these events
            await self.load_invitees_data()
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def load_invitees_data(self):
        """Load invitees data for Cleverly Introduction events asynchronously"""
        self.invitees_data = []
        invitees_dir = self.data_dir / "invitees"
        
        if not invitees_dir.exists():
            print("Invitees directory not found - this is OK for basic analytics")
            return
        
        for event in self.cleverly_scheduled_events:
            event_uri = event.get('uri', '')
            event_id = event_uri.split('/')[-1] if event_uri else event.get('id', '')
            
            invitee_file = invitees_dir / f"{event_id}.json"
            if invitee_file.exists():
                try:
                    with open(invitee_file, 'r') as f:
                        event_invitees = json.load(f)
                        for invitee in event_invitees:
                            invitee_data = invitee.get('resource', invitee)
                            # Add event information to invitee data
                            invitee_data['event_data'] = event
                            self.invitees_data.append(invitee_data)
                except Exception as e:
                    print(f"Error loading invitees for event {event_id}: {e}")
        
        print(f"Loaded {len(self.invitees_data)} invitee records")
    
    def create_analytics_dataframe(self) -> pd.DataFrame:
        """Create a comprehensive DataFrame for analysis"""
        
        # If we have invitees data, use that (most detailed)
        if self.invitees_data:
            print("Creating DataFrame from invitees data (most detailed)")
            return self._create_dataframe_from_invitees()
        
        # If we have scheduled events but no invitees, use scheduled events
        elif self.cleverly_scheduled_events:
            print("Creating DataFrame from scheduled events")
            return self._create_dataframe_from_scheduled_events()
        
        # If we only have event types, create a basic dataframe
        elif self.cleverly_events:
            print("Creating DataFrame from event types only (basic analytics)")
            return self._create_dataframe_from_event_types()
        
        print("No data available to create DataFrame")
        return pd.DataFrame()
    
    def _create_dataframe_from_invitees(self) -> pd.DataFrame:
        """Create dataframe from invitees data (most detailed)"""
        records = []
        for invitee in self.invitees_data:
            event_data = invitee.get('event_data', {})
            event_type_uri = event_data.get('event_type', '')
            
            # Find matching event type to get internal_note and custom_questions
            internal_note = "Unknown"
            custom_questions = []
            for event_type in self.cleverly_events:
                if event_type.get('uri') == event_type_uri:
                    internal_note = event_type.get('internal_note', 'No Internal Note')
                    custom_questions = event_type.get('custom_questions', [])
                    break
            
            record = {
                'invitee_id': invitee.get('uri', ''),
                'event_id': event_data.get('uri', ''),
                'event_type_uri': event_type_uri,
                'internal_note': internal_note,
                'invitee_name': invitee.get('name', ''),
                'invitee_email': invitee.get('email', ''),
                'status': invitee.get('status', ''),
                'created_at': invitee.get('created_at', ''),
                'updated_at': invitee.get('updated_at', ''),
                'scheduled_event_created_at': event_data.get('created_at', ''),
                'scheduled_event_start_time': event_data.get('start_time', ''),
                'scheduled_event_end_time': event_data.get('end_time', ''),
                'questions_and_answers': invitee.get('questions_and_answers', []),
                'tracking': invitee.get('tracking', {})
            }
            
            # Extract custom question answers
            questions_answers = invitee.get('questions_and_answers', [])
            for qa in questions_answers:
                question = qa.get('question', '').lower()
                answer = qa.get('answer', '')
                
                if 'service' in question and 'interested' in question:
                    record['interested_service'] = answer
                elif 'how did you find' in question or 'find us' in question:
                    record['discovery_channel'] = answer
                elif 'website' in question:
                    record['website_url'] = answer
                elif 'phone' in question:
                    record['phone_number'] = answer
                elif 'linkedin' in question and 'profile' in question:
                    record['linkedin_url'] = answer
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Convert datetime columns
        datetime_columns = ['created_at', 'updated_at', 'scheduled_event_created_at', 
                          'scheduled_event_start_time', 'scheduled_event_end_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    def _create_dataframe_from_scheduled_events(self) -> pd.DataFrame:
        """Create dataframe from scheduled events"""
        records = []
        for event in self.cleverly_scheduled_events:
            event_type_uri = event.get('event_type', '')
            
            # Find matching event type
            internal_note = "Unknown"
            for event_type in self.cleverly_events:
                if event_type.get('uri') == event_type_uri:
                    internal_note = event_type.get('internal_note', 'No Internal Note')
                    break
            
            record = {
                'event_id': event.get('uri', ''),
                'event_type_uri': event_type_uri,
                'internal_note': internal_note,
                'status': event.get('status', ''),
                'scheduled_event_created_at': event.get('created_at', ''),
                'scheduled_event_start_time': event.get('start_time', ''),
                'scheduled_event_end_time': event.get('end_time', ''),
                'name': event.get('name', ''),
                'location': event.get('location', {})
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Convert datetime columns
        datetime_columns = ['scheduled_event_created_at', 'scheduled_event_start_time', 'scheduled_event_end_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    def _create_dataframe_from_event_types(self) -> pd.DataFrame:
        """Create basic dataframe from event types only"""
        records = []
        for event_type in self.cleverly_events:
            record = {
                'event_type_uri': event_type.get('uri', ''),
                'name': event_type.get('name', ''),
                'internal_note': event_type.get('internal_note', 'No Internal Note'),
                'slug': event_type.get('slug', ''),
                'scheduling_url': event_type.get('scheduling_url', ''),
                'duration': event_type.get('duration', 0),
                'active': event_type.get('active', False),
                'created_at': event_type.get('created_at', ''),
                'updated_at': event_type.get('updated_at', ''),
                'booking_method': event_type.get('booking_method', ''),
                'color': event_type.get('color', ''),
                'kind': event_type.get('kind', ''),
                'pooling_type': event_type.get('pooling_type', ''),
                'custom_questions_count': len(event_type.get('custom_questions', []))
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Convert datetime columns
        datetime_columns = ['created_at', 'updated_at']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    async def get_data_preview(self) -> Dict[str, Any]:
        """Get preview of available data"""
        if not await self.check_data_exists():
            return {
                'total_events': 0,
                'total_invitees': 0,
                'internal_notes_distribution': {},
                'status_distribution': {},
                'date_range': {'min_date': None, 'max_date': None},
                'columns_available': [],
                'message': 'No data available. Please download Calendly data first.'
            }
        
        if not self.invitees_data and not self.cleverly_scheduled_events:
            await self.load_data()
        
        df = self.create_analytics_dataframe()
        
        if df.empty:
            return {
                'total_events': 0,
                'total_invitees': 0,
                'internal_notes_distribution': {},
                'status_distribution': {},
                'date_range': {'min_date': None, 'max_date': None},
                'columns_available': []
            }
        
        # Calculate preview metrics
        preview = {
            'total_events': len(self.cleverly_scheduled_events) if self.cleverly_scheduled_events else len(self.cleverly_events),
            'total_invitees': len(self.invitees_data),
            'internal_notes_distribution': df['internal_note'].value_counts().to_dict() if 'internal_note' in df.columns else {},
            'status_distribution': df['status'].value_counts().to_dict() if 'status' in df.columns else {},
            'date_range': {},
            'columns_available': list(df.columns)
        }
        
        # Add date range if available
        if 'scheduled_event_start_time' in df.columns:
            date_col = df['scheduled_event_start_time'].dropna()
            if not date_col.empty:
                preview['date_range'] = {
                    'min_date': date_col.min().isoformat(),
                    'max_date': date_col.max().isoformat()
                }
        elif 'created_at' in df.columns:
            date_col = df['created_at'].dropna()
            if not date_col.empty:
                preview['date_range'] = {
                    'min_date': date_col.min().isoformat(),
                    'max_date': date_col.max().isoformat()
                }
        
        return preview