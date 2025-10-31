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
            
            # Find all Cleverly Introduction events
            cleverly_event_uris = []
            for event in event_types:
                event_data = event.get('resource', event)
                if event_data.get('name') == 'Cleverly Introduction':
                    cleverly_event_uris.append(event_data['uri'])
                    self.cleverly_events.append(event_data)
            
            print(f"Found {len(cleverly_event_uris)} Cleverly Introduction event types")
            
            # Load scheduled events
            scheduled_events_path = self.data_dir / "scheduled_events.json"
            if not scheduled_events_path.exists():
                print(f"Scheduled events file not found: {scheduled_events_path}")
                return False
                
            with open(scheduled_events_path, 'r') as f:
                scheduled_events = json.load(f)
            
            # Filter for Cleverly Introduction events
            self.cleverly_scheduled_events = []
            for event in scheduled_events:
                event_data = event.get('resource', event)
                event_type_uri = event_data.get('event_type')
                if event_type_uri in cleverly_event_uris:
                    self.cleverly_scheduled_events.append(event_data)
            
            print(f"Found {len(self.cleverly_scheduled_events)} scheduled Cleverly Introduction events")
            
            # Load invitees for these events
            await self.load_invitees_data()
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    async def load_invitees_data(self):
        """Load invitees data for Cleverly Introduction events asynchronously"""
        self.invitees_data = []
        invitees_dir = self.data_dir / "invitees"
        
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
        if not self.invitees_data:
            return pd.DataFrame()
        
        records = []
        for invitee in self.invitees_data:
            event_data = invitee.get('event_data', {})
            event_type_uri = event_data.get('event_type', '')
            
            # Find matching event type to get internal_note
            internal_note = "Unknown"
            for event_type in self.cleverly_events:
                if event_type.get('uri') == event_type_uri:
                    internal_note = event_type.get('internal_note', 'Unknown')
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
                'scheduling_url': next(
                    (et.get('scheduling_url', '') for et in self.cleverly_events 
                     if et.get('uri') == event_type_uri), ''
                ),
                'questions_and_answers': invitee.get('questions_and_answers', []),
                'tracking': invitee.get('tracking', {})
            }
            
            # Extract custom question answers
            questions_answers = invitee.get('questions_and_answers', [])
            for qa in questions_answers:
                question = qa.get('question', '')
                answer = qa.get('answer', '')
                if 'service' in question.lower():
                    record['interested_service'] = answer
                elif 'how did you find' in question.lower():
                    record['discovery_channel'] = answer
                elif 'website' in question.lower():
                    record['website_url'] = answer
                elif 'phone' in question.lower():
                    record['phone_number'] = answer
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Convert datetime columns
        datetime_columns = ['created_at', 'updated_at', 'scheduled_event_created_at', 
                          'scheduled_event_start_time', 'scheduled_event_end_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    async def get_data_preview(self) -> Dict[str, Any]:
        """Get preview of available data"""
        if not self.invitees_data:
            await self.load_data()
        
        df = self.create_analytics_dataframe()
        
        preview = {
            'total_events': len(self.cleverly_scheduled_events),
            'total_invitees': len(self.invitees_data),
            'internal_notes_distribution': df['internal_note'].value_counts().to_dict(),
            'status_distribution': df['status'].value_counts().to_dict(),
            'date_range': {
                'min_date': df['scheduled_event_start_time'].min().isoformat() if not df.empty else None,
                'max_date': df['scheduled_event_start_time'].max().isoformat() if not df.empty else None
            },
            'columns_available': list(df.columns) if not df.empty else []
        }
        
        return preview