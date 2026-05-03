"""Generator router — site generation."""
from fastapi import APIRouter
from services.site_gen import SiteGeneratorService

router = APIRouter(prefix="/api/generate", tags=["generator"])

@router.post("/")
async def generate_site(business_name: str, categoria: str = None, ciudad: str = ""):
    svc = SiteGeneratorService()
    path = svc.generate_site(business_name, categoria, ciudad)
    return {"path": path, "status": "generated"}