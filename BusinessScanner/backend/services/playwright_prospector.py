"""Lead prospecting with Playwright over Google Maps search results.

Usage example:
    python services/playwright_prospector.py --niche "dentista" --city "Santiago, Chile"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import parse_qs, quote_plus, urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


@dataclass
class Lead:
    """Normalized lead row extracted from a listing."""

    query: str
    city: str
    source: str
    name: str
    category: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    reviews: Optional[int]
    maps_url: str


class PlaywrightLeadProspector:
    """Collects business leads from Google Maps result pages."""

    RESULTS_PANEL_SELECTORS = (
        'div[role="feed"]',
        'div[aria-label*="Results for"]',
        'div[aria-label*="Resultados de"]',
    )

    RESULT_CARD_SELECTORS = (
        "a.hfpxzc",
        'div[role="feed"] a[href*="/maps/place"]',
    )

    def __init__(
        self,
        *,
        headless: bool = True,
        slow_mo_ms: int = 0,
        timeout_ms: int = 12000,
        delay_seconds: float = 1.2,
    ) -> None:
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self.timeout_ms = timeout_ms
        self.delay_seconds = delay_seconds

    def prospect(self, niche: str, city: str, max_results: int = 25) -> list[Lead]:
        """Run one lead prospecting pass.

        Args:
            niche: Business niche to search (e.g. "dentista")
            city: City or area to search in
            max_results: Maximum number of leads to extract

        Returns:
            List of normalized leads.
        """
        if max_results < 1:
            raise ValueError("max_results must be >= 1")

        query = f"{niche.strip()} {city.strip()}".strip()
        search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        leads: list[Lead] = []
        seen_keys: set[tuple[str, str]] = set()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless, slow_mo=self.slow_mo_ms)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="es-ES",
            )
            page = context.new_page()
            page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._dismiss_possible_dialogs(page)

            if not self._wait_for_results_panel(page):
                print("[WARN] No se encontró panel de resultados de Maps.")
                context.close()
                browser.close()
                return leads

            self._scroll_results_panel(page, expected=max_results)
            cards = self._get_result_cards(page)
            total_cards = cards.count()
            target = min(max_results, total_cards)

            for idx in range(target):
                card = cards.nth(idx)
                try:
                    card.scroll_into_view_if_needed(timeout=3000)
                    card.click(timeout=5000)
                    page.wait_for_timeout(1000)
                    lead = self._extract_lead(page, query, city)
                    key = (lead.name.lower(), (lead.phone or lead.address or "").lower())
                    if lead.name and key not in seen_keys:
                        leads.append(lead)
                        seen_keys.add(key)
                except PlaywrightTimeoutError:
                    print(f"[WARN] Timeout al procesar resultado #{idx + 1}")
                except Exception as exc:
                    print(f"[WARN] Error al procesar resultado #{idx + 1}: {exc}")
                finally:
                    page.wait_for_timeout(int(self.delay_seconds * 1000))

            context.close()
            browser.close()

        return leads

    def _dismiss_possible_dialogs(self, page: Page) -> None:
        """Attempt to dismiss consent dialogs that block interaction."""
        button_labels = (
            "Aceptar todo",
            "Accept all",
            "I agree",
            "Aceptar",
            "Reject all",
        )
        for label in button_labels:
            try:
                button = page.get_by_role("button", name=label)
                if button.count() > 0:
                    button.first.click(timeout=1800)
                    page.wait_for_timeout(500)
                    return
            except Exception:
                continue

    def _wait_for_results_panel(self, page: Page) -> bool:
        deadline = time.monotonic() + (self.timeout_ms / 1000)
        while time.monotonic() < deadline:
            for selector in self.RESULTS_PANEL_SELECTORS:
                if page.locator(selector).count() > 0:
                    return True
            page.wait_for_timeout(250)
        return False

    def _scroll_results_panel(self, page: Page, expected: int) -> None:
        """Scroll result pane until enough cards appear or scrolling stalls."""
        panel = None
        for selector in self.RESULTS_PANEL_SELECTORS:
            if page.locator(selector).count() > 0:
                panel = page.locator(selector).first
                break
        if panel is None:
            return

        stable_rounds = 0
        last_count = 0
        while stable_rounds < 3:
            current_count = self._get_result_cards(page).count()
            if current_count >= expected:
                return

            try:
                panel.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            except Exception:
                return
            page.wait_for_timeout(900)

            new_count = self._get_result_cards(page).count()
            if new_count <= last_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
            last_count = new_count

    def _get_result_cards(self, page: Page):
        for selector in self.RESULT_CARD_SELECTORS:
            locator = page.locator(selector)
            if locator.count() > 0:
                return locator
        return page.locator(self.RESULT_CARD_SELECTORS[0])

    def _extract_lead(self, page: Page, query: str, city: str) -> Lead:
        name = self._normalize_text(
            self._first_text(
                page,
                (
                    "h1.DUwDvf",
                    "h1.fontHeadlineLarge",
                ),
            )
        ) or ""
        category = self._normalize_text(
            self._first_text(
                page,
                (
                    'button[jsaction*="pane.rating.category"]',
                    "button.DkEaL",
                ),
            )
        )

        address_raw = self._first_attr(
            page,
            (
                'button[data-item-id="address"]',
                'button[aria-label*="Address"]',
                'button[aria-label*="Dirección"]',
            ),
            "aria-label",
        ) or self._first_text(
            page,
            (
                'button[data-item-id="address"]',
                'button[aria-label*="Address"]',
                'button[aria-label*="Dirección"]',
            ),
        )
        address = self._clean_prefixed_text(address_raw, ("Address", "Dirección"))

        phone_raw = self._first_attr(
            page,
            (
                'button[data-item-id*="phone"]',
                'button[aria-label*="Phone"]',
                'button[aria-label*="Teléfono"]',
            ),
            "aria-label",
        ) or self._first_text(
            page,
            (
                'button[data-item-id*="phone"]',
                'button[aria-label*="Phone"]',
                'button[aria-label*="Teléfono"]',
            ),
        )
        phone = self._clean_prefixed_text(phone_raw, ("Phone", "Teléfono"))

        website = self._normalize_website(
            self._first_attr(
                page,
                (
                    'a[data-item-id="authority"]',
                    'a[aria-label*="Website"]',
                    'a[aria-label*="Sitio web"]',
                ),
                "href",
            )
        )

        rating, reviews = self._extract_rating_and_reviews(page)

        return Lead(
            query=query,
            city=city,
            source="google_maps",
            name=name,
            category=category,
            address=address,
            phone=phone,
            website=website,
            rating=rating,
            reviews=reviews,
            maps_url=page.url,
        )

    def _extract_rating_and_reviews(self, page: Page) -> tuple[Optional[float], Optional[int]]:
        aria_label_selectors = (
            'button[jsaction*="pane.reviewChart.moreReviews"]',
            'button[jsaction*="pane.rating.moreReviews"]',
            'button[jsaction*="pane.rating"]',
            'button[aria-label*="reseña"]',
            'button[aria-label*="review"]',
            'span[aria-label*="estrellas"]',
            'span[aria-label*="stars"]',
            'div[role="img"][aria-label*="estrellas"]',
            'div[role="img"][aria-label*="stars"]',
        )
        for selector in aria_label_selectors:
            locator = page.locator(selector)
            try:
                count = min(locator.count(), 3)
            except Exception:
                continue
            for index in range(count):
                try:
                    label = locator.nth(index).get_attribute("aria-label", timeout=1200)
                except Exception:
                    continue
                rating, reviews = self._parse_rating_and_reviews(label or "")
                if rating is not None or reviews is not None:
                    return rating, reviews

        rating_text = self._normalize_text(
            self._first_text(
                page,
                (
                    "span.MW4etd",
                    "div.F7nice span[aria-hidden='true']",
                    "div.F7nice span",
                ),
            )
        )
        reviews_text = self._normalize_text(
            self._first_text(
                page,
                (
                    "span.UY7F9",
                    "div.F7nice span:nth-child(2)",
                ),
            )
        )

        rating = self._parse_decimal_number(rating_text)
        reviews = self._parse_reviews_count(reviews_text)
        if rating is not None or reviews is not None:
            return rating, reviews

        combined = self._normalize_text(
            " ".join(
                part
                for part in (
                    rating_text,
                    reviews_text,
                    self._first_text(page, ("div.F7nice",)),
                )
                if part
            )
        ) or ""
        return self._parse_rating_and_reviews(combined)

    @staticmethod
    def _normalize_text(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        cleaned = value.replace("\u00A0", " ")
        cleaned = re.sub(r"[\uE000-\uF8FF]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -|·•\t\r\n")
        return cleaned or None

    @staticmethod
    def _normalize_website(value: Optional[str]) -> Optional[str]:
        normalized = PlaywrightLeadProspector._normalize_text(value)
        if not normalized:
            return None

        parsed = urlparse(normalized)
        if parsed.netloc.endswith("google.com") and parsed.path == "/url":
            candidate = parse_qs(parsed.query).get("q", [None])[0]
            normalized = PlaywrightLeadProspector._normalize_text(candidate)
            if not normalized:
                return None

        if normalized.startswith(("http://", "https://")):
            return normalized
        return None

    @staticmethod
    def _parse_decimal_number(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        match = re.search(r"(?<!\d)([0-5](?:[.,]\d)?)", value)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _parse_reviews_count(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        match = re.search(r"(\d[\d\.,]*)", value)
        if not match:
            return None
        digits = re.sub(r"[^\d]", "", match.group(1))
        if not digits:
            return None
        return int(digits)

    @staticmethod
    def _parse_rating_and_reviews(label: str) -> tuple[Optional[float], Optional[int]]:
        text = PlaywrightLeadProspector._normalize_text(label) or ""
        if not text:
            return None, None

        rating = PlaywrightLeadProspector._parse_decimal_number(text)
        reviews = None

        reviews_match = re.search(
            r"(\d[\d\.,]*)\s*(?:reviews?|reseñas?|opiniones?)",
            text,
            flags=re.IGNORECASE,
        )
        if reviews_match:
            reviews = PlaywrightLeadProspector._parse_reviews_count(reviews_match.group(1))
        else:
            paren_match = re.search(r"\((\d[\d\.,]*)\)", text)
            if paren_match:
                reviews = PlaywrightLeadProspector._parse_reviews_count(paren_match.group(1))

        return rating, reviews

    @staticmethod
    def _first_text(page: Page, selectors: Iterable[str]) -> Optional[str]:
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = min(locator.count(), 3)
            except Exception:
                continue
            for index in range(count):
                item = locator.nth(index)
                try:
                    txt = (item.inner_text(timeout=1500) or "").strip()
                except Exception:
                    continue
                if txt:
                    return txt
        return None

    @staticmethod
    def _first_attr(page: Page, selectors: Iterable[str], attribute: str) -> Optional[str]:
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = min(locator.count(), 3)
            except Exception:
                continue
            for index in range(count):
                item = locator.nth(index)
                try:
                    value = item.get_attribute(attribute, timeout=1500)
                except Exception:
                    continue
                if value:
                    return value.strip()
        return None

    @staticmethod
    def _clean_prefixed_text(value: Optional[str], prefixes: Iterable[str]) -> Optional[str]:
        normalized = PlaywrightLeadProspector._normalize_text(value)
        if not normalized:
            return None

        cleaned = normalized
        for prefix in prefixes:
            pattern = rf"^{re.escape(prefix)}\s*:?\s*"
            if re.match(pattern, cleaned, flags=re.IGNORECASE):
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
                break
        return PlaywrightLeadProspector._normalize_text(cleaned)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prospección inicial de leads en Google Maps con Playwright."
    )
    parser.add_argument("--niche", required=True, help="Nicho de negocio (ej. dentista)")
    parser.add_argument("--city", required=True, help="Ciudad/zona (ej. Santiago, Chile)")
    parser.add_argument("--max-results", type=int, default=25, help="Máximo de leads a extraer")
    parser.add_argument(
        "--out",
        default="leads",
        help="Ruta base de salida (sin extensión para ambos formatos).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "both"),
        default="both",
        help="Formato de exportación.",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Ejecuta con navegador visible para debugging.",
    )
    parser.add_argument("--slow-mo-ms", type=int, default=0, help="Retardo Playwright por acción.")
    parser.add_argument("--delay-seconds", type=float, default=1.2, help="Delay entre leads.")
    return parser.parse_args()


def resolve_output_paths(base: Path, output_format: str) -> tuple[Optional[Path], Optional[Path]]:
    if output_format == "json":
        return (base if base.suffix.lower() == ".json" else base.with_suffix(".json")), None
    if output_format == "csv":
        return None, (base if base.suffix.lower() == ".csv" else base.with_suffix(".csv"))

    stem = base.with_suffix("") if base.suffix else base
    return stem.with_suffix(".json"), stem.with_suffix(".csv")


def save_json(leads: list[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(lead) for lead in leads]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(leads: list[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [field.name for field in Lead.__dataclass_fields__.values()]  # type: ignore[attr-defined]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            writer.writerow(asdict(lead))


def main() -> None:
    args = parse_args()
    prospector = PlaywrightLeadProspector(
        headless=not args.headful,
        slow_mo_ms=args.slow_mo_ms,
        delay_seconds=args.delay_seconds,
    )
    leads = prospector.prospect(args.niche, args.city, args.max_results)
    json_path, csv_path = resolve_output_paths(Path(args.out), args.format)

    if json_path is not None:
        save_json(leads, json_path)
    if csv_path is not None:
        save_csv(leads, csv_path)

    print(
        f"[OK] Leads extraídos: {len(leads)}"
        + (f" | JSON: {json_path}" if json_path else "")
        + (f" | CSV: {csv_path}" if csv_path else "")
    )


if __name__ == "__main__":
    main()
