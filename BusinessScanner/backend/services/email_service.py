"""Email service using Gmail SMTP for automated outreach.

Sends HTML emails to business owners with site preview
and Mercado Pago payment links.
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from pathlib import Path


class EmailService:
    """Gmail SMTP email service for business outreach."""

    def __init__(self, gmail_user: str, gmail_app_password: str,
                 preview_base_url: str = "http://localhost:8080/preview") -> None:
        self.gmail_user = gmail_user
        self.gmail_app_password = gmail_app_password
        self.preview_base_url = preview_base_url
        self.template_path = Path("C:/BusinessScanner/templates/email_outreach.html")

    def _render_template(self, nombre_negocio: str, slug: str,
                         precio_clp: int, precio_usd: int, mp_link: str) -> str:
        """Render email HTML template with variables."""
        html = self.template_path.read_text(encoding="utf-8")
        return html.replace("{{ nombre_negocio }}", nombre_negocio) \
                  .replace("{{ preview_url }}", f"{self.preview_base_url}/{slug}") \
                  .replace("{{ precio_clp }}", f"{precio_clp:,}") \
                  .replace("{{ precio_usd }}", str(precio_usd)) \
                  .replace("{{ mp_link }}", mp_link)

    def send_outreach_email(
        self, to_email: str, nombre_negocio: str, slug: str,
        precio_clp: int, precio_usd: int, mp_link: str
    ) -> bool:
        """Send outreach email to business owner.

        Args:
            to_email: Recipient email address
            nombre_negocio: Business name
            slug: Site slug for preview URL
            precio_clp: Price in CLP
            precio_usd: Price in USD
            mp_link: Mercado Pago payment link

        Returns:
            True if sent successfully
        """
        if not self.gmail_user or not self.gmail_app_password:
            print("Gmail credentials not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{nombre_negocio} — Su sitio web ya está listo 🌐"
            msg["From"] = self.gmail_user
            msg["To"] = to_email

            html_body = self._render_template(nombre_negocio, slug, precio_clp, precio_usd, mp_link)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_app_password)
                server.send_message(msg)

            print(f"Email sent to {to_email} for {nombre_negocio}")
            return True
        except Exception as e:
            print(f"Email send error to {to_email}: {e}")
            return False
        finally:
            time.sleep(30)  # Anti-spam delay 30-60s