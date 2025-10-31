import os
import requests
import time
import json
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

from app.core.config import get_settings

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
                print(f"Rate limited. Sleeping {wait}s...")
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
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh all Calendly data"""
        try:
            # Get user info to fetch organization URI
            me = await self.get_json(f"{self.base_url}/users/me")
            with open(self.settings.data_dir / "users_me.json", "w") as f:
                json.dump(me, f, indent=2)

            # Extract organization URI
            org_uri = None
            try:
                org_uri = me["resource"]["current_organization"]
            except Exception:
                org_uri = me.get("current_organization") or me.get("data", {}).get("current_organization") or me.get("organization")

            if not org_uri:
                return {"error": "Could not find organization URI"}

            print("Organization URI:", org_uri)

            # Fetch all endpoints
            endpoints = {
                "organization_memberships": (f"{self.base_url}/organization_memberships", {"organization": org_uri}),
                "users": (f"{self.base_url}/users", {"organization": org_uri}),
                "event_types": (f"{self.base_url}/event_types", {"organization": org_uri}),
                "scheduled_events": (f"{self.base_url}/scheduled_events", {"organization": org_uri}),
            }

            fetched = {}
            for name, (url, params) in endpoints.items():
                print(f"Fetching {name}...")
                try:
                    items = await self.paginate(url, params)
                except Exception as e:
                    print(f"Error fetching {name}: {e}")
                    items = []
                with open(self.settings.data_dir / f"{name}.json", "w") as f:
                    json.dump(items, f, indent=2)
                print(f"Saved {len(items)} items to {name}.json")
                fetched[name] = items

            # Fetch invitees for each scheduled event
            scheduled = fetched.get("scheduled_events", [])
            for ev in scheduled:
                ev_data = ev.get('resource', ev)
                ev_uri = ev_data.get('uri') or ev_data.get('id')
                if not ev_uri:
                    continue

                if isinstance(ev_uri, str) and ev_uri.startswith("https://api.calendly.com/scheduled_events/"):
                    ev_id = ev_uri.rsplit("/", 1)[-1]
                else:
                    ev_id = ev_uri

                url = f"{self.base_url}/scheduled_events/{ev_id}/invitees"
                try:
                    inv = await self.paginate(url)
                except Exception as e:
                    print(f"Failed invitees for {ev_id}: {e}")
                    inv = []
                with open(self.settings.data_dir / "invitees" / f"{ev_id}.json", "w") as f:
                    json.dump(inv, f, indent=2)
                print(f"Saved {len(inv)} invitees for event {ev_id}")

            return {"success": True, "message": "Data refreshed successfully"}

        except Exception as e:
            return {"error": f"Failed to refresh data: {str(e)}"}