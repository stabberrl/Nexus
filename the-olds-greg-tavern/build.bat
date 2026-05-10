@echo off
echo ============================================
echo   The Old's Greg Tavern - Build Completo
echo ============================================
echo.
echo Construyendo frontend...
cd /d %~dp0
call npm run build
if %errorlevel% neq 0 (
    echo Error en build frontend
    pause
    exit /b 1
)
echo.
echo Build completado. Los archivos estan en: dist/
echo.
echo Para empaquetar con Tauri necesitas Rust:
echo   npm run tauri build
echo.
pause
