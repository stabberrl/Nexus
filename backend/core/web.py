"""
Nexus AI - Web Navigator (Lazy Loading)
Navegación web automatizada. Playwright solo se importa al usar.
"""

import asyncio
import os


class WebNavigator:
    """Navegador web automatizado con carga diferida de Playwright."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None
        self._playwright_module = None

    def _get_playwright(self):
        """Importa playwright solo cuando se necesita (ahorra ~200MB)."""
        if self._playwright_module is None:
            from playwright.async_api import async_playwright as _p
            self._playwright_module = _p
        return self._playwright_module

    async def _ensure_browser(self):
        """Asegura que el navegador esté iniciado."""
        if self._browser is None or not self._browser.is_connected():
            pw = self._get_playwright()
            self._playwright = await pw().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--no-sandbox"],
            )
            context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )
            self._page = await context.new_page()

    async def search(self, query: str) -> str:
        """Busca en internet usando DuckDuckGo."""
        await self._ensure_browser()
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            await self._page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1)
            results = await self._page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.result');
                    return Array.from(items).slice(0, 5).map(item => ({
                        title: item.querySelector('.result__title')?.innerText?.trim() || '',
                        snippet: item.querySelector('.result__snippet')?.innerText?.trim() || '',
                        url: item.querySelector('.result__url')?.innerText?.trim() || '',
                    }));
                }
            """)
            if not results:
                results = await self._page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a');
                        return Array.from(links).slice(0, 8).map(a => ({
                            title: a.innerText?.trim() || '',
                            url: a.href || '',
                        })).filter(r => r.title && r.url && !r.url.startsWith('javascript:'));
                    }
                """)
            if results:
                formatted = "**Resultados de búsqueda:**\n\n"
                for i, r in enumerate(results, 1):
                    formatted += f"{i}. **{r.get('title', 'Sin título')}**\n"
                    if r.get('snippet'):
                        formatted += f"   {r['snippet']}\n"
                    if r.get('url'):
                        formatted += f"   _{r['url']}_\n"
                    formatted += "\n"
                return formatted
            return "No se encontraron resultados."
        except Exception as e:
            return f"Error en la búsqueda: {str(e)}"

    async def fetch_page(self, url: str) -> str:
        """Obtiene el contenido textual de una página web."""
        await self._ensure_browser()
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(1)
            content = await self._page.evaluate("""
                () => {
                    const remove = document.querySelectorAll('script, style, nav, footer, header, .sidebar, .menu, .advertisement');
                    remove.forEach(el => el.remove());
                    const main = document.querySelector('main, article, .content, #content, .post, body');
                    const text = main?.innerText || document.body?.innerText || '';
                    return text.trim().substring(0, 8000);
                }
            """)
            if content:
                return f"**Contenido de {url}:**\n\n{content}"
            return f"No se pudo extraer contenido de {url}"
        except Exception as e:
            return f"Error al acceder a {url}: {str(e)}"

    async def close(self):
        """Cierra el navegador."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
