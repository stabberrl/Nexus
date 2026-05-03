"""Outreach router — email sending."""
from fastapi import APIRouter
from services.email_service import EmailService

router = APIRouter(prefix="/api/email", tags=["outreach"])

@router.post("/send")
async def send_email(to: str, nombre: str, slug: str, precio_clp: int, precio_usd: int, mp_link: str = ""):
    svc = EmailService("weblocal.agencia@gmail.com", "pqgwpksptqutydne")
    ok = svc.send_outreach_email(to, nombre, slug, precio_clp, precio_usd, mp_link)
    return {"sent": ok}