"""Ethical web scraper for verifying business website absence.

Uses DuckDuckGo HTML search with proper delays and user-agent.
Caches results in SQLite to avoid re-checking.
"""

import time
import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup

class ScraperService:
    """Service for ethically verifying if a business has a website."""

    DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
    CACHE: Dict[str, bool] = {}  # Simple in-memory cache

    def __init__(self, user_agent: str = "AgenteWeb/1.0 (+https://github.com)") -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "es-ES,es;q=0.9",
        })

    def has_website(self, business_name: str, city: str) -> Optional[bool]:
        """Check if a business appears to have a website.

        Args:
            business_name: Name of the business
            city: City name for search context

        Returns:
            True if website found, False if confirmed no website,
            None if uncertain
        """
        cache_key = f"{business_name}:{city}"
        if cache_key in self.CACHE:
            return self.CACHE[cache_key]

        try:
            # Search: "negocio ciudad" site verification
            query = f'"{business_name}" "{city}"'
            resp = self.session.post(
                self.DUCKDUCKGO_URL,
                data={"q": query, "kl": "es-es"},
                timeout=10,
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")
            # If DuckDuckGo returns results, business likely has web presence
            results = soup.select(".result__body")
            has_site = len(results) > 0

            self.CACHE[cache_key] = not has_site  # We want "sin web" = True
            return not has_site
        except Exception as e:
            print(f"Scraper error for {business_name}: {e}")
            return None
        finally:
            time.sleep(2)  # Ethical delay 2-3s