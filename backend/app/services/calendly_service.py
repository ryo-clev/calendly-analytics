import os
import requests
import time
import json
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional, Callable

from app.core.config import get_settings

# Global progress tracker
download_progress = {
    "current_step": 0,
    "total_steps": 6,
    "step_name": "",
    "details": "",
    "percentage": 0
}

class CalendlyService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.calendly_base_url
        self.token = self.settings.calendly_api_key
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.progress_callback = None
    
    def update_progress(self, step: int, step_name: str, details: str = ""):
        """Update download progress"""
        global download_progress
        download_progress["current_step"] = step
        download_progress["step_name"] = step_name
        download_progress["details"] = details
        download_progress["percentage"] = int((step / download_progress["total_steps"]) * 100)
        
        print(f"[{download_progress['percentage']}%] Step {step}/{download_progress['total_steps']}: {step_name}")
        if details:
            print(f"    → {details}")
    
    async def initialize(self):
        """Initialize service and create data directory"""
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        (self.settings.data_dir / "invitees").mkdir(exist_ok=True)
    
    async def get_json(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with rate limiting handling"""
        while True:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 5))
                print(f"⚠️  Rate limited. Sleeping {wait}s...")
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
    
    async def paginate(self, url: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Handle paginated responses"""
        params = params or {}
        results = []
        next_url = url
        next_params = params.copy()

        while next_url:
            resp = await self.get_json(next_url, next_params)
            items = self._extract_items_from_response(resp)
            results.extend(items)

            pagination = resp.get("pagination") or resp.get("meta", {}).get("pagination") or {}
            next_page = pagination.get("next_page")
            if next_page:
                next_url = next_page
                next_params = {}
            else:
                next_url = None

        return results
    
    def _extract_items_from_response(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract items from various Calendly response formats"""
        if isinstance(resp, dict):
            if "collection" in resp:
                return resp["collection"]
            if "data" in resp:
                return resp["data"]
            if "resources" in resp:
                return resp["resources"]
            items = []
            for k, v in resp.items():
                if k not in ("pagination", "meta"):
                    items.append({k: v})
            return items
        if isinstance(resp, list):
            return resp
        return []
    
    async def download_all_data(self) -> Dict[str, Any]:
        """Download all Calendly data - Main entry point for data download"""
        try:
            print("\n" + "=" * 70)
            print("🚀 STARTING CALENDLY DATA DOWNLOAD")
            print("=" * 70 + "\n")
            
            # Ensure directories exist
            await self.initialize()
            
            # Step 1: Get user info to fetch organization URI
            self.update_progress(1, "Fetching user information", "Getting your Calendly account details...")
            me = await self.get_json(f"{self.base_url}/users/me")
            with open(self.settings.data_dir / "users_me.json", "w") as f:
                json.dump(me, f, indent=2)
            print("✅ User information saved")

            # Extract organization URI
            org_uri = None
            try:
                org_uri = me["resource"]["current_organization"]
            except Exception:
                org_uri = me.get("current_organization") or me.get("data", {}).get("current_organization") or me.get("organization")

            if not org_uri:
                return {"error": "Could not find organization URI in user data"}

            print(f"✅ Organization URI: {org_uri}")

            # Step 2: Fetch organization memberships
            self.update_progress(2, "Fetching organization memberships", "Getting team member information...")
            org_memberships = await self.paginate(
                f"{self.base_url}/organization_memberships",
                {"organization": org_uri}
            )
            with open(self.settings.data_dir / "organization_memberships.json", "w") as f:
                json.dump(org_memberships, f, indent=2)
            print(f"✅ Saved {len(org_memberships)} organization memberships")

            # Step 3: Fetch users
            self.update_progress(3, "Fetching users", "Getting user profiles...")
            users = await self.paginate(
                f"{self.base_url}/users",
                {"organization": org_uri}
            )
            with open(self.settings.data_dir / "users.json", "w") as f:
                json.dump(users, f, indent=2)
            print(f"✅ Saved {len(users)} users")

            # Step 4: Fetch event types (THIS IS THE KEY FILE)
            self.update_progress(4, "Fetching event types", "Getting all event type configurations...")
            event_types = await self.paginate(
                f"{self.base_url}/event_types",
                {"organization": org_uri}
            )
            with open(self.settings.data_dir / "event_types.json", "w") as f:
                json.dump(event_types, f, indent=2)
            print(f"✅ Saved {len(event_types)} event types")
            
            # Count Cleverly Introduction events
            cleverly_count = sum(
                1 for et in event_types 
                if self._get_event_name(et) == "Cleverly Introduction"
            )
            print(f"   🎯 Found {cleverly_count} 'Cleverly Introduction' event types")
            
            if cleverly_count == 0:
                print("   ⚠️  WARNING: No 'Cleverly Introduction' events found!")
                print("   Available event types:")
                for et in event_types[:10]:
                    print(f"      • {self._get_event_name(et)}")

            # Step 5: Fetch scheduled events for each event type
            self.update_progress(5, "Fetching scheduled events", "Getting booking history...")
            all_scheduled_events = []
            
            event_type_count = 0
            for event_type in event_types:
                event_type_uri = self._get_event_type_uri(event_type)
                event_name = self._get_event_name(event_type)
                
                if not event_type_uri:
                    continue
                
                event_type_count += 1
                if event_type_count % 5 == 0:
                    self.update_progress(
                        5, 
                        "Fetching scheduled events", 
                        f"Processing event type {event_type_count}/{len(event_types)}: {event_name}"
                    )
                
                try:
                    scheduled = await self.paginate(
                        f"{self.base_url}/scheduled_events",
                        {"organization": org_uri, "event_type": event_type_uri}
                    )
                    
                    # Add event type info to each scheduled event
                    for event in scheduled:
                        if isinstance(event, dict):
                            event["_event_type_name"] = event_name
                            event["_event_type_uri"] = event_type_uri
                    
                    all_scheduled_events.extend(scheduled)
                    if len(scheduled) > 0:
                        print(f"   → {len(scheduled)} scheduled events for '{event_name}'")
                    
                except Exception as e:
                    print(f"   ✗ Error fetching scheduled events for {event_name}: {e}")
                    continue
            
            # Save all scheduled events
            with open(self.settings.data_dir / "scheduled_events.json", "w") as f:
                json.dump(all_scheduled_events, f, indent=2)
            print(f"✅ Saved {len(all_scheduled_events)} total scheduled events")

            # Step 6: Fetch invitees for each scheduled event
            self.update_progress(6, "Fetching invitees", "Getting attendee information...")
            invitees_dir = self.settings.data_dir / "invitees"
            invitees_dir.mkdir(exist_ok=True)
            
            invitee_count = 0
            event_count = 0
            for event in all_scheduled_events:
                event_uri = self._get_scheduled_event_uri(event)
                if not event_uri:
                    continue
                
                event_id = event_uri.split('/')[-1] if '/' in event_uri else event_uri
                event_count += 1
                
                if event_count % 10 == 0:
                    self.update_progress(
                        6, 
                        "Fetching invitees", 
                        f"Processing event {event_count}/{len(all_scheduled_events)}"
                    )
                
                try:
                    invitees = await self.paginate(f"{self.base_url}/scheduled_events/{event_id}/invitees")
                    with open(invitees_dir / f"{event_id}.json", "w") as f:
                        json.dump(invitees, f, indent=2)
                    invitee_count += len(invitees)
                except Exception as e:
                    print(f"   ✗ Error fetching invitees for event {event_id}: {e}")
                    continue
            
            print(f"✅ Saved {invitee_count} total invitees across {event_count} events")

            # Final summary
            print("\n" + "=" * 70)
            print("✅ DATA DOWNLOAD COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   • Event Types: {len(event_types)}")
            print(f"   • Cleverly Introduction Events: {cleverly_count}")
            print(f"   • Scheduled Events: {len(all_scheduled_events)}")
            print(f"   • Total Invitees: {invitee_count}")
            print(f"\n💾 Data saved to: {self.settings.data_dir}")
            print("=" * 70 + "\n")
            
            self.update_progress(6, "Download complete", "All data downloaded successfully!")

            return {
                "success": True,
                "message": "Data downloaded successfully",
                "summary": {
                    "event_types": len(event_types),
                    "cleverly_introduction_events": cleverly_count,
                    "scheduled_events": len(all_scheduled_events),
                    "invitees": invitee_count
                }
            }

        except Exception as e:
            error_msg = f"Failed to download data: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
    
    def _get_event_name(self, event_type: Dict[str, Any]) -> str:
        """Extract event name from event type object"""
        if isinstance(event_type, dict):
            if "resource" in event_type:
                return event_type["resource"].get("name", "Unknown")
            return event_type.get("name", "Unknown")
        return "Unknown"
    
    def _get_event_type_uri(self, event_type: Dict[str, Any]) -> Optional[str]:
        """Extract event type URI from event type object"""
        if isinstance(event_type, dict):
            if "resource" in event_type:
                return event_type["resource"].get("uri")
            return event_type.get("uri")
        return None
    
    def _get_scheduled_event_uri(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract scheduled event URI from event object"""
        if isinstance(event, dict):
            if "resource" in event:
                return event["resource"].get("uri") or event["resource"].get("id")
            return event.get("uri") or event.get("id")
        return None
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh all Calendly data (alias for download_all_data)"""
        return await self.download_all_data()

def get_download_progress() -> Dict[str, Any]:
    """Get current download progress"""
    return download_progress.copy()