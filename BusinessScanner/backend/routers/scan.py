"""Scan router — manual zone scanning."""
from fastapi import APIRouter, Depends
from services.overpass import OverpassService

router = APIRouter(prefix="/api/scan", tags=["scan"])

@router.post("/")
async def scan_zone(lat: float, lng: float, radius: int = 2000):
    svc = OverpassService()
    businesses = svc.fetch_businesses(lat, lng, radius)
    return {"found": len(businesses), "businesses": [b.__dict__ for b in businesses]}