# AgenteWeb — Sistema autónomo de presencia digital

Sistema 100% autónomo que detecta negocios sin web en Latinoamérica,
analiza oportunidades con IA local (Ollama), genera sitios estáticos,
contacta dueños por email y publica en GitHub Pages al confirmar pago.

## 🎯 Objetivo

Construye un sistema 100% autónomo que:
1. Detecta zonas de Latinoamérica con negocios sin web cada 24h
2. Analiza oportunidades con IA local (Ollama llama3.2)
3. Genera sitios web estáticos personalizados por negocio
4. Contacta automáticamente a los dueños por email
5. Cobra vía Mercado Pago con link de pago automático
6. Entrega el sitio publicado en GitHub Pages al confirmar pago
7. Muestra todo en un dashboard web de control

## ⚙️ Restricciones Críticas

- Costo total: $0 (salvo comisión Mercado Pago al cobrar)
- IA: Ollama local en http://localhost:11434 (llama3.2)
- Sin Docker, sin npm, sin Node.js
- Frontend: HTML/CSS/JS vanilla puro
- Python 3.12 en Windows
- UTF-8 en todos los archivos
- Scraping ético: delays 2-3s, User-Agent real
- NUNCA subir .env a git (.gitignore obligatorio)

## 📁 Estructura

```
C:\BusinessScanner\
├── backend\
│   ├── main.py
│   ├── scheduler.py
│   ├── config.py
│   ├── database.py
│   ├── routers\
│   │   ├── scan.py
│   │   ├── analysis.py
│   │   ├── generator.py
│   │   ├── outreach.py
│   │   ├── payments.py
│   │   └── dashboard.py
│   ├── services\
│   │   ├── overpass.py
│   │   ├── scraper.py
│   │   ├── ollama_ai.py
│   │   ├── site_gen.py
│   │   ├── email_service.py
│   │   ├── mercadopago.py
│   │   └── github_pages.py
│   └── models\
│       └── schemas.py
├── frontend\
│   ├── index.html
│   ├── css\styles.css
│   └── js\
│       ├── dashboard.js
│       ├── map.js
│       ├── pipeline.js
│       └── api.js
├── generated_sites\
├── templates\
│   └── email_outreach.html
├── .env
├── .gitignore
└── README.md
```

## 🚀 Requisitos

- Python 3.12
- Ollama con modelo llama3.2 (`ollama serve`)
- Cuenta Gmail con App Password
- Cuenta GitHub con token
- Cuenta Mercado Pago (opcional)

## 🛠️ Instalación

```powershell
cd C:\BusinessScanner\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Prospección inicial con Playwright

```powershell
pip install playwright
python -m playwright install chromium
python services/playwright_prospector.py --niche "dentista" --city "Santiago, Chile" --max-results 30 --format both --out leads_dentistas
```

El script exporta leads normalizados (`json/csv`) con nombre, categoría, teléfono, web, dirección y URL de Maps.

## ▶️ Ejecución

**Terminal 1 (Ollama):**
```powershell
ollama serve
```

**Terminal 2 (Backend):**
```powershell
cd C:\BusinessScanner\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 (Frontend):**
```powershell
cd C:\BusinessScanner\frontend
python -m http.server 8080
```

**Navegador:** http://localhost:8080

## 📊 Dashboard

El dashboard tiene 5 pestañas:
1. **Pipeline** — Estado del ciclo autónomo en tiempo real
2. **Mapa** — Leaflet con todos los negocios escaneados
3. **Negocios** — Tabla con todos los registros
4. **Ingresos** — Resumen financiero
5. **Config** — Ajustes del sistema

## 🗃️ Base de Datos

SQLite con 6 tablas:
- `zonas` — Zonas de búsqueda
- `businesses` — Negocios detectados
- `analyses` — Análisis de IA
- `outreach` — Emails enviados
- `payments` — Pagos recibidos
- `sites` — Sitios generados
- `scheduler_log` — Log de ciclos

## 🔧 Configuración (.env)

```
GMAIL_USER=weblocal.agencia@gmail.com
GMAIL_APP_PASSWORD=tu_app_password
GITHUB_TOKEN=tu_github_token
MP_ACCESS_TOKEN=tu_mercado_pago_token
SECRET_KEY=businessscanner2026
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
SCAN_INTERVAL_HOURS=24
MIN_SCORE_TO_CONTACT=70
MAX_EMAILS_PER_DAY=50
```

## 📜 Licencia

MIT — Sistema desarrollado para automatizar presencia digital.