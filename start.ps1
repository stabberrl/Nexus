# Nexus AI - Script de inicio optimizado
# Levanta el backend y frontend con mínimo consumo de recursos

param(
    [switch]$NoFrontend,
    [string]$Port = "8000",
    [string]$TelegramToken = ""
)

$ErrorActionPreference = "SilentlyContinue"
$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "apps\nexus-desktop"

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Nexus AI - Iniciando          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que Ollama esté corriendo
$ollama = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "[!] Ollama no está corriendo. Iniciando..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve"
    Start-Sleep -Seconds 3
}

# 2. Verificar modelo disponible
$modelCheck = & ollama list 2>&1 | Select-String "llama3.2"
if (-not $modelCheck) {
    Write-Host "[!] Descargando llama3.2 (modelo ligero)..." -ForegroundColor Yellow
    & ollama pull llama3.2
}

# 3. Matar servidor previo si existe
$oldServer = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match "uvicorn.*nexus"}
if ($oldServer) {
    $oldServer | Stop-Process -Force
    Start-Sleep -Seconds 1
}

# 4. Iniciar backend
Write-Host "[~] Iniciando backend API en puerto $Port..." -ForegroundColor Green
$backendLog = Join-Path $RootDir "nexus-backend.log"
$backendProcess = Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn backend.api.main:app --host 127.0.0.1 --port $Port --log-level warning" -WorkingDirectory $RootDir -PassThru -RedirectStandardOutput $backendLog -RedirectStandardError $backendLog

# 5. Esperar a que el backend esté listo
$retries = 0
do {
    Start-Sleep -Seconds 1
    $retries++
    $ready = $false
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/" -ErrorAction Stop
        $ready = $true
    } catch {
        $ready = $false
    }
} while (-not $ready -and $retries -lt 20)

if ($ready) {
    Write-Host "[✓] Backend listo en http://127.0.0.1:$Port" -ForegroundColor Green
} else {
    Write-Host "[✗] Error: Backend no respondió después de 20s" -ForegroundColor Red
    Write-Host "    Revisa: $backendLog"
    exit 1
}

# 6. Opcional: Iniciar frontend
if (-not $NoFrontend) {
    Write-Host "[~] Iniciando frontend (Vite)..." -ForegroundColor Green
    $frontendProcess = Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $FrontendDir -PassThru
    Start-Sleep -Seconds 2
    Write-Host "[✓] Frontend en http://localhost:1420" -ForegroundColor Green
    Write-Host "    Para Tauri Desktop: cd apps/nexus-desktop && npm run tauri dev"
}

# 7. Opcional: Iniciar Telegram bot
if ($TelegramToken) {
    Write-Host "[~] Iniciando Telegram bot..." -ForegroundColor Green
    $env:TELEGRAM_BOT_TOKEN = $TelegramToken
    $telegramProcess = Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m backend.core.telegram_bot --token $TelegramToken" -WorkingDirectory $RootDir -PassThru
    Start-Sleep -Seconds 2
    Write-Host "[✓] Telegram bot activo" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Nexus AI está listo para usar       ║" -ForegroundColor Cyan
Write-Host "║  Backend:  http://127.0.0.1:$Port    ║" -ForegroundColor Cyan
Write-Host "║  Estado:   http://127.0.0.1:$Port/   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan

# Mantener el script vivo
Write-Host ""
Write-Host "Presiona Ctrl+C para detener todo" -ForegroundColor DarkGray

# Si se presiona Ctrl+C, limpiar
try {
    Wait-Process -Id $backendProcess.Id
} catch {
    Write-Host "[!] Limpiando procesos..." -ForegroundColor Yellow
}
