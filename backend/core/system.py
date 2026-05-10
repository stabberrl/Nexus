"""
Nexus AI - System Controller (Lazy Loading)
Control del sistema optimizado: solo importa módulos pesados cuando se usan.
"""

import asyncio
import os
from typing import Optional


class SystemController:
    """Controla el sistema operativo Windows con carga diferida de dependencias."""

    def __init__(self):
        self._psutil = None
        self._pyautogui = None

    def _get_psutil(self):
        """Importa psutil solo cuando se necesita."""
        if self._psutil is None:
            import psutil as _p
            self._psutil = _p
        return self._psutil

    def _get_pyautogui(self):
        """Importa pyautogui solo cuando se necesita."""
        if self._pyautogui is None:
            import pyautogui as _p
            _p.FAILSAFE = True
            _p.PAUSE = 0.3
            self._pyautogui = _p
        return self._pyautogui

    async def execute_powershell(self, command: str) -> str:
        """Ejecuta un comando de PowerShell y devuelve la salida."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30.0
            )
            output = stdout.decode("utf-8", errors="replace").strip()
            error = stderr.decode("utf-8", errors="replace").strip()
            if error and not output:
                return f"Error: {error}"
            return output or "Comando ejecutado correctamente."
        except asyncio.TimeoutError:
            return "Error: El comando tardó demasiado (>30s)."
        except Exception as e:
            return f"Error al ejecutar comando: {str(e)}"

    async def open_application(self, app_name: str) -> str:
        """Abre una aplicación por nombre o ruta."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "cmd.exe", "/c", f"start {app_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return f"Aplicación '{app_name}' iniciada."
        except Exception as e:
            return f"No se pudo abrir '{app_name}': {str(e)}"

    async def open_file(self, path: str) -> str:
        """Abre un archivo con su programa asociado."""
        if not os.path.exists(path):
            return f"Archivo no encontrado: {path}"
        try:
            os.startfile(path)
            return f"Archivo abierto: {path}"
        except Exception as e:
            return f"No se pudo abrir el archivo: {str(e)}"

    async def list_processes(self) -> list[dict]:
        """Lista los procesos en ejecución (top 30 por CPU)."""
        psutil = self._get_psutil()
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        processes.sort(key=lambda p: p.get("cpu_percent", 0) or 0, reverse=True)
        return processes[:30]

    async def kill_process(self, pid: int) -> str:
        """Mata un proceso por PID."""
        psutil = self._get_psutil()
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return f"Proceso {pid} terminado."
        except psutil.NoSuchProcess:
            return f"Proceso {pid} no encontrado."
        except Exception as e:
            return f"No se pudo terminar el proceso: {str(e)}"

    async def get_system_info(self) -> dict:
        """Obtiene información del sistema (CPU, RAM, disco, uptime)."""
        import time as _time
        psutil = self._get_psutil()
        info = {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "cpu_count": psutil.cpu_count(),
            "memory": {},
            "disk": {},
            "uptime": "",
        }
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
        }
        disk = psutil.disk_usage("/")
        info["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
        }
        boot_time = psutil.boot_time()
        uptime_seconds = _time.time() - boot_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        info["uptime"] = f"{hours}h {minutes}m"
        return info

    async def take_screenshot(self) -> str:
        """Toma una captura de pantalla."""
        gui = self._get_pyautogui()
        screenshot_dir = os.path.join(os.environ["TEMP"], "nexus_screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"screenshot_{int(asyncio.get_event_loop().time())}.png")
        screenshot = gui.screenshot()
        screenshot.save(path)
        return path

    async def type_text(self, text: str) -> str:
        """Escribe texto como si fuera el teclado."""
        gui = self._get_pyautogui()
        try:
            gui.write(text, interval=0.01)
            return f"Texto escrito: {len(text)} caracteres."
        except Exception as e:
            return f"Error al escribir texto: {str(e)}"

    async def press_keys(self, keys: str) -> str:
        """Presiona combinación de teclas (ej: 'ctrl+c')."""
        gui = self._get_pyautogui()
        try:
            gui.hotkey(*keys.split("+"))
            return f"Teclas presionadas: {keys}"
        except Exception as e:
            return f"Error al presionar teclas: {str(e)}"

    async def create_folder(self, path: str) -> str:
        """Crea una carpeta en la ruta especificada."""
        try:
            os.makedirs(path, exist_ok=True)
            return f"Carpeta creada: {path}"
        except Exception as e:
            return f"Error al crear carpeta: {str(e)}"

    async def list_directory(self, path: str = ".") -> list[dict]:
        """Lista el contenido de un directorio."""
        try:
            items = []
            for entry in os.scandir(path):
                items.append({
                    "name": entry.name,
                    "type": "folder" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            return items
        except Exception as e:
            return [{"error": str(e)}]

    async def read_file(self, path: str) -> str:
        """Lee el contenido de un archivo de texto."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 5000:
                content = content[:5000] + f"\n\n... [truncado, {len(content)} caracteres totales]"
            return content
        except Exception as e:
            return f"Error al leer archivo: {str(e)}"

    async def write_file(self, path: str, content: str) -> str:
        """Escribe contenido en un archivo."""
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Archivo guardado: {path}"
        except Exception as e:
            return f"Error al escribir archivo: {str(e)}"
