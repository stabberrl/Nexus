"""Mercado Pago payment integration.

Creates payment preferences and handles webhook notifications
for autonomous payment collection.
"""

import requests
from typing import Optional, Dict, Any

class MercadoPagoService:
    """Service for Mercado Pago API integration."""

    BASE_URL = "https://api.mercadopago.com"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def create_preference(
        self, business_name: str, price_clp: int, business_id: str,
        success_url: str = "http://localhost:8000/api/payments/success",
        failure_url: str = "http://localhost:8000/api/payments/failure",
    ) -> Optional[Dict[str, Any]]:
        """Create a Mercado Pago payment preference.

        Args:
            business_name: Name of the business
            price_clp: Price in Chilean Pesos
            business_id: External reference for webhook
            success_url: Redirect URL on success
            failure_url: Redirect URL on failure

        Returns:
            Dict with preference_id and init_point or None
        """
        if not self.access_token:
            print("Mercado Pago access token not configured")
            return None

        payload = {
            "items": [{
                "title": f"Sitio web para {business_name}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": float(price_clp),
            }],
            "back_urls": {"success": success_url, "failure": failure_url},
            "auto_return": "approved",
            "external_reference": business_id,
        }

        try:
            resp = self.session.post(
                f"{self.BASE_URL}/checkout/preferences",
                json=payload,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "preference_id": data.get("id"),
                "init_point": data.get("init_point"),
            }
        except Exception as e:
            print(f"Mercado Pago create preference error: {e}")
            return None

    def verify_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Verify a payment status via Mercado Pago API.

        Args:
            payment_id: Mercado Pago payment ID

        Returns:
            Payment data dict or None
        """
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/v1/payments/{payment_id}",
                timeout=15
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Mercado Pago verify payment error: {e}")
            return None