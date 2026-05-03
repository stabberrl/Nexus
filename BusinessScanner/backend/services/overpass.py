"""Overpass API and Nominatim geocoding service.

Fetches businesses from OpenStreetMap via Overpass API
and handles geocoding via Nominatim with rate limiting.
"""

import time
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class BusinessOSM:
    """Business data from OpenStreetMap."""
    nombre: str
    categoria: Optional[str]
    lat: float
    lng: float
    telefono: Optional[str] = None
    osm_id: str = ""

class OverpassService:
    """Service for querying OSM data via Overpass API."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, user_agent: str = "AgenteWeb/1.0") -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def geocode(self, zona_nombre: str) -> Optional[Dict]:
        """Geocode a zone name to lat/lng using Nominatim.

        Args:
            zona_nombre: Zone name (e.g., "Santiago Centro, Santiago")

        Returns:
            Dict with 'lat', 'lng' keys or None
        """
        try:
            resp = self.session.get(
                self.NOMINATIM_URL,
                params={"q": zona_nombre, "format": "json", "limit": 1},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data:
                return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
            return None
        except Exception as e:
            print(f"Geocoding error for {zona_nombre}: {e}")
            return None
        finally:
            time.sleep(1)  # Rate limit: 1 req/sec

    def fetch_businesses(self, lat: float, lng: float, radius: int = 2000) -> List[BusinessOSM]:
        """Fetch businesses around a point from Overpass API.

        Args:
            lat: Latitude center
            lng: Longitude center
            radius: Search radius in meters

        Returns:
            List of BusinessOSM objects
        """
        query = f"""
        [out:json][timeout:25];
        (
          node["shop"](around:{radius},{lat},{lng});
          node["amenity"](around:{radius},{lat},{lng});
          way["shop"](around:{radius},{lat},{lng});
          way["amenity"](around:{radius},{lat},{lng});
        );
        out body;
        >;
        out skel qt;
        """

        try:
            resp = self.session.post(self.OVERPASS_URL, data=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            businesses = []
            seen = set()

            for elem in data.get("elements", []):
                tags = elem.get("tags", {})
                name = tags.get("name")
                if not name or name in seen:
                    continue
                seen.add(name)

                lat_e = elem.get("lat") or elem.get("center", {}).get("lat")
                lng_e = elem.get("lon") or elem.get("center", {}).get("lon")
                if not lat_e or not lng_e:
                    continue

                phone = tags.get("phone") or tags.get("contact:phone")
                businesses.append(BusinessOSM(
                    nombre=name,
                    categoria=tags.get("shop") or tags.get("amenity"),
                    lat=float(lat_e),
                    lng=float(lng_e),
                    telefono=phone,
                    osm_id=str(elem.get("id", "")),
                ))

            return businesses
        except Exception as e:
            print(f"Overpass error: {e}")
            return []
