"""APScheduler-based autonomous cycle for AgenteWeb.

Runs the full pipeline every 24 hours:
scan → analyze → generate → outreach → log.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional

from config import get_config
from database import get_connection, init_db
from services.overpass import OverpassService
from services.scraper import ScraperService
from services.ollama_ai import OllamaService
from services.site_gen import SiteGeneratorService
from services.email_service import EmailService
from services.mercadopago import MercadoPagoService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class AutonomousScheduler:
    """Manages the 24h autonomous cycle for business scanning and outreach."""

    def __init__(self) -> None:
        self.config = get_config()
        self.scheduler = BackgroundScheduler()
        self.zona_index = 0
        self.overpass = OverpassService()
        self.scraper = ScraperService()
        self.ollama = OllamaService(self.config.get_ollama_url(), self.config.get_ollama_model())
        self.site_gen = SiteGeneratorService()
        self.email = EmailService(self.config.GMAIL_USER, self.config.GMAIL_APP_PASSWORD)
        self.mp: Optional[MercadoPagoService] = None
        if self.config.MP_ACCESS_TOKEN:
            self.mp = MercadoPagoService(self.config.MP_ACCESS_TOKEN)

    def _log_cycle(self, zona_nombre: str, encontrados: int,
                   analizados: int, contactados: int, error: Optional[str] = None) -> None:
        """Log scheduler cycle results to database."""
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO scheduler_log (zona, started_at, finished_at,
                   encontrados, analizados, contactados, errores)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (zona_nombre, datetime.now(), datetime.now(),
                 encontrados, analizados, contactados, error),
            )
            conn.commit()
        finally:
            conn.close()

    def run_cycle(self) -> None:
        """Execute one full autonomous cycle."""
        zona = self.config.ZONAS_LATAM[self.zona_index]
        self.zona_index = (self.zona_index + 1) % len(self.config.ZONAS_LATAM)

        logger.info(f"Starting cycle for zone: {zona['nombre']}")
        encontrados = analizados = contactados = 0
        error_msg = None

        try:
            # 1. Fetch businesses via Overpass
            businesses = self.overpass.fetch_businesses(zona["lat"], zona["lng"])
            encontrados = len(businesses)
            logger.info(f"Found {encontrados} businesses in {zona['nombre']}")

            # 2. Filter: verify no website
            sin_web = []
            for b in businesses[:50]:  # Limit per cycle
                if not self.scraper.has_website(b.nombre, zona["nombre"]):
                    sin_web.append(b)
            logger.info(f"Confirmed {len(sin_web)} without website")

            # 3. Analyze with Ollama (top 20)
            for b in sin_web[:20]:
                analysis = self.ollama.analyze_business(b.nombre, b.categoria, zona["nombre"], b.telefono)
                if analysis and analysis.score >= self.config.MIN_SCORE_TO_CONTACT:
                    analizados += 1
                    # 4. Generate site
                    self.site_gen.generate_site(
                        b.nombre, b.categoria, zona["nombre"],
                        precio_clp=analysis.precio_sugerido_clp, business_id=0
                    )
                    # 5. Send email if within daily limit
                    if contactados < self.config.MAX_EMAILS_PER_DAY and b.telefono:
                        mp_link = ""
                        if self.mp:
                            pref = self.mp.create_preference(
                                b.nombre, analysis.precio_sugerido_clp, str(0))
                            if pref:
                                mp_link = pref.get("init_point", "")
                        self.email.send_outreach_email(
                            "test@example.com", b.nombre,
                            self.site_gen._slugify(b.nombre),
                            analysis.precio_sugerido_clp, analysis.precio_sugerido_usd,
                            mp_link
                        )
                        contactados += 1

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Cycle error for {zona['nombre']}: {e}")
        finally:
            self._log_cycle(zona["nombre"], encontrados, analizados, contactados, error_msg)
            logger.info(f"Cycle complete for {zona['nombre']}: {encontrados}/{analizados}/{contactados}")

    def start(self) -> None:
        """Start the background scheduler."""
        init_db()
        self.scheduler.add_job(
            self.run_cycle,
            trigger=IntervalTrigger(hours=self.config.SCAN_INTERVAL_HOURS),
            id="autonomous_cycle",
            max_instances=1,
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("Autonomous scheduler started — 24h cycles")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")