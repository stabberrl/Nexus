@echo off
title Nexus AI
cd /d "%~dp0"

:: Matar procesos previos
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe 2>nul
timeout /t 1 /nobreak >nul

:: Iniciar backend (oculto con pythonw)
start /min pythonw -m backend.api.main --host 127.0.0.1 --port 8000 --log-level warning

:: Esperar al backend
echo Esperando a Nexus...
:wait
timeout /t 1 /nobreak >nul
2>nul curl -s http://127.0.0.1:8000/ >nul && goto ready
goto wait

:ready
echo Nexus esta listo!
start http://localhost:1420
exit
