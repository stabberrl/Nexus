@echo off
echo ============================================
echo   The Old's Greg Tavern - Modo Desarrollo
echo ============================================
echo.
echo Iniciando backend Python...
start "Tavern Backend" cmd /c "cd /d %~dp0backend && python main.py"
timeout /t 3 /nobreak >nul
echo.
echo Iniciando frontend Vite...
cd /d %~dp0
call npm run dev
