"""Static site generator for business websites.

Generates HTML/CSS sites based on business category with
predefined color themes. Outputs to generated_sites/[slug]/.
"""

import os
import re
from pathlib import Path
from typing import Optional

THEMES = {
    "restaurant": {"primary": "#e74c3c", "secondary": "#c0392b", "bg": "#fff5f5"},
    "shop": {"primary": "#3498db", "secondary": "#2980b9", "bg": "#f0f8ff"},
    "hotel": {"primary": "#f39c12", "secondary": "#e67e22", "bg": "#fff9e6"},
    "health": {"primary": "#2ecc71", "secondary": "#27ae60", "bg": "#f0fff4"},
    "education": {"primary": "#9b59b6", "secondary": "#8e44ad", "bg": "#f5f0ff"},
    "default": {"primary": "#1abc9c", "secondary": "#16a085", "bg": "#f0fffd"},
}

class SiteGeneratorService:
    """Generates static HTML/CSS websites for businesses."""

    def __init__(self, output_base: str = "C:/BusinessScanner/generated_sites") -> None:
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)

    def _slugify(self, name: str) -> str:
        """Convert business name to URL-friendly slug."""
        name = name.lower()
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"[\s_-]+", "-", name)
        return name.strip("-")[:50]

    def generate_site(
        self,
        business_name: str,
        categoria: Optional[str],
        ciudad: str,
        slug: Optional[str] = None,
        precio_clp: int = 50000,
        business_id: int = 0,
    ) -> Optional[str]:
        """Generate a static site for a business.

        Args:
            business_name: Name of the business
            categoria: Business category for theme selection
            ciudad: City name
            slug: Optional custom slug (auto-generated if None)
            precio_clp: Suggested price in CLP
            business_id: Business ID for tracking

        Returns:
            Path to generated site or None on failure
        """
        try:
            slug = slug or self._slugify(business_name)
            site_dir = self.output_base / slug
            site_dir.mkdir(parents=True, exist_ok=True)

            theme_key = (categoria or "default").lower()
            theme = THEMES.get(theme_key, THEMES["default"])

            # Generate index.html
            html_content = f"""<!-- business_id: {business_id} -->
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="precio" content="{precio_clp}">
  <title>{business_name} | {ciudad}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header style="background:{theme['primary']}">
    <h1>{business_name}</h1>
    <p>{categoria or 'Servicios'} en {ciudad}</p>
  </header>
  <main>
    <section id="inicio">
      <h2>Bienvenido</h2>
      <p>Somos un negocio comprometido con la calidad y el servicio.</p>
    </section>
    <section id="servicios">
      <h2>Nuestros Servicios</h2>
      <ul>
        <li>Servicio personalizado</li>
        <li>Atención de calidad</li>
        <li>Precios competitivos</li>
      </ul>
    </section>
    <section id="contacto">
      <h2>Contáctanos</h2>
      <p>Visítanos en {ciudad}</p>
    </section>
    <section id="pagar" style="text-align:center;padding:40px">
      <h2>¿Te gusta este sitio?</h2>
      <p>Puedes publicarlo con tu nombre oficial por solo ${precio_clp:,} CLP</p>
      <a href="/pagar" style="background:{theme['primary']};color:white;padding:12px 24px;text-decoration:none;border-radius:5px">
        Pagar ahora y publicar
      </a>
    </section>
  </main>
  <footer style="background:{theme['secondary']};color:white;text-align:center;padding:20px">
    © 2026 {business_name} — Creado por AgenteWeb
  </footer>
</body>
</html>"""

            css_content = f"""* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; color:#333; }}
header {{ color:white; padding:40px 20px; text-align:center; }}
header h1 {{ font-size:2em; }}
header p {{ margin-top:10px; opacity:0.9; }}
main {{ max-width:800px; margin:0 auto; padding:20px; }}
section {{ margin:30px 0; }}
h2 {{ color:{theme['primary']}; border-bottom:2px solid {theme['bg']}; padding-bottom:8px; }}
ul {{ margin:10px 0 10px 20px; }}
footer {{ margin-top:40px; }}
"""

            (site_dir / "index.html").write_text(html_content, encoding="utf-8")
            (site_dir / "styles.css").write_text(css_content, encoding="utf-8")

            return str(site_dir)
        except Exception as e:
            print(f"Site generation error for {business_name}: {e}")
            return None
