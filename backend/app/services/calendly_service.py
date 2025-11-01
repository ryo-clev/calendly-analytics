"""
Calendly Service - FINAL WORKING VERSION
Downloads data from Calendly API - removes problematic /users endpoint
Based on working reference implementation
"""

import os
import requests
import time
import json
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

from app.core.config import get_settings

# Global progress tracker
download_progress = {
    "current_step": 0,
    "total_steps": 3,  # Simplified: users/me, org_memberships, event_types
    "step_name": "",
    "details": "",
    "percentage": 0
}

class CalendlyService:
    """
    Service for interacting with Calendly API.
    WORKING VERSION - Removes /users endpoint that causes 404.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.calendly_base_url
        self.token = self.settings.calendly_api_key
        
        if not self.token or self.token == "your_calendly_api_key_here":
            print("⚠️  WARNING: Calendly API key not set or is placeholder!")
            print("   Please update backend/.env with your actual API key")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def update_progress(self, step: int, step_name: str, details: str = ""):
        """Update download progress for UI feedback."""
        global download_progress
        download_progress["current_step"] = step
        download_progress["step_name"] = step_name
        download_progress["details"] = details
        download_progress["percentage"] = int((step / download_progress["total_steps"]) * 100)
        
        print(f"[{download_progress['percentage']}%] Step {step}/{download_progress['total_steps']}: {step_name}")
        if details:
            print(f"    → {details}")
    
    async def initialize(self):
        """Initialize service and create data directory."""
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        (self.settings.data_dir / "invitees").mkdir(exist_ok=True)
    
    async def get_json(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API request with rate limiting handling.
        Synchronous requests.get wrapped in async for consistency.
        """
        while True:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 5))
                    print(f"⚠️  Rate limited. Sleeping {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                print(f"❌ HTTP Error: {e}")
                print(f"   Status: {response.status_code}")
                print(f"   URL: {url}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                raise
    
    def _extract_items_from_response(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract items from various Calendly response formats.
        Handles: collection, data, resources, and other top-level keys.
        """
        if isinstance(resp, dict):
            # Standard collection format
            if "collection" in resp:
                return resp["collection"]
            # Event types use "data" key
            if "data" in resp:
                return resp["data"]
            # Some endpoints use "resources"
            if "resources" in resp:
                return resp["resources"]
            # Fallback: collect non-meta keys
            items = []
            for k, v in resp.items():
                if k not in ("pagination", "meta"):
                    items.append({k: v})
            return items
        # Already a list
        if isinstance(resp, list):
            return resp
        return []
    
    async def paginate(self, url: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Handle paginated responses from Calendly API.
        Follows next_page links until exhausted.
        """
        params = params or {}
        results = []
        next_url = url
        next_params = params.copy()

        while next_url:
            resp = await self.get_json(next_url, next_params)
            items = self._extract_items_from_response(resp)
            results.extend(items)

            # Check for pagination
            pagination = resp.get("pagination") or resp.get("meta", {}).get("pagination") or {}
            next_page = pagination.get("next_page")
            
            if next_page:
                next_url = next_page
                next_params = {}  # next_page URL contains all params
            else:
                next_url = None

        return results
    
    async def download_all_data(self) -> Dict[str, Any]:
        """
        Download all Calendly data.
        FIXED VERSION - Removes /users endpoint that causes 404.
        """
        try:
            print("\n" + "=" * 70)
            print("🚀 STARTING CALENDLY DATA DOWNLOAD")
            print("=" * 70 + "\n")
            
            # Ensure directories exist
            await self.initialize()
            
            # ========================================================================
            # Step 1: Get user info to fetch organization URI
            # ========================================================================
            self.update_progress(1, "Fetching user information", "Getting your Calendly account details...")
            me = await self.get_json(f"{self.base_url}/users/me")
            
            with open(self.settings.data_dir / "users_me.json", "w") as f:
                json.dump(me, f, indent=2)
            print("✅ User information saved")

            # Extract organization URI - handle different response structures
            org_uri = None
            try:
                # Standard structure: me["resource"]["current_organization"]
                org_uri = me["resource"]["current_organization"]
            except (KeyError, TypeError):
                # Try alternative structures
                org_uri = (me.get("current_organization") or 
                          me.get("data", {}).get("current_organization") or 
                          me.get("organization"))

            if not org_uri:
                return {"error": "Could not find organization URI in user data"}

            print(f"✅ Organization URI: {org_uri}")

            # ========================================================================
            # Step 2: Fetch organization memberships
            # ========================================================================
            self.update_progress(2, "Fetching organization memberships", "Getting team member information...")
            org_memberships = await self.paginate(
                f"{self.base_url}/organization_memberships",
                {"organization": org_uri}
            )
            with open(self.settings.data_dir / "organization_memberships.json", "w") as f:
                json.dump(org_memberships, f, indent=2)
            print(f"✅ Saved {len(org_memberships)} organization memberships")

            # ========================================================================
            # Step 3: Fetch event types (CRITICAL FILE FOR ANALYTICS)
            # ========================================================================
            self.update_progress(3, "Fetching event types", "Getting all event type configurations...")
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
                print("   Available event types (first 10):")
                for et in event_types[:10]:
                    print(f"      • {self._get_event_name(et)}")

            # ========================================================================
            # FINAL SUMMARY
            # ========================================================================
            print("\n" + "=" * 70)
            print("✅ DATA DOWNLOAD COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   • Organization Memberships: {len(org_memberships)}")
            print(f"   • Event Types: {len(event_types)}")
            print(f"   • Cleverly Introduction Events: {cleverly_count}")
            print(f"\n💾 Data saved to: {self.settings.data_dir}")
            print("=" * 70 + "\n")

            return {
                "success": True,
                "message": "Data downloaded successfully",
                "summary": {
                    "event_types": len(event_types),
                    "cleverly_introduction_events": cleverly_count,
                    "organization_memberships": len(org_memberships)
                }
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"Failed to download data: {e}"
            if hasattr(e, 'response') and e.response.status_code == 401:
                error_msg = "Authentication failed. Please check your Calendly API key in backend/.env"
            print(f"\n❌ ERROR: {error_msg}")
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"Failed to download data: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
    
    def _get_event_name(self, event_type: Dict[str, Any]) -> str:
        """Extract event name from event type object."""
        if isinstance(event_type, dict):
            if "resource" in event_type:
                return event_type["resource"].get("name", "Unknown")
            return event_type.get("name", "Unknown")
        return "Unknown"
    
    def _get_event_type_uri(self, event_type: Dict[str, Any]) -> Optional[str]:
        """Extract event type URI from event type object."""
        if isinstance(event_type, dict):
            if "resource" in event_type:
                return event_type["resource"].get("uri")
            return event_type.get("uri")
        return None
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh all Calendly data (alias for download_all_data)."""
        return await self.download_all_data()

def get_download_progress() -> Dict[str, Any]:
    """Get current download progress for UI polling."""
    return download_progress.copy()