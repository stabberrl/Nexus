"""Payments router — Mercado Pago webhook."""
from fastapi import APIRouter, Request
from services.mercadopago import MercadoPagoService

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/webhook")
async def payment_webhook(request: Request):
    body = await request.json()
    return {"status": "received", "data": body}

@router.get("/success")
async def payment_success():
    return {"status": "success"}

@router.get("/failure")
async def payment_failure():
    return {"status": "failure"}