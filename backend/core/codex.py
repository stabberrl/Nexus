"""
Nexus AI - Code Executor (Sandboxed)
Ejecuta código Python en un entorno aislado con límites de recursos.
"""

import ast
import io
import sys
import textwrap
import traceback
from contextlib import redirect_stdout, redirect_stderr


# Lista de módulos permitidos (whitelist)
ALLOWED_MODULES = {
    "json", "math", "random", "datetime", "collections", "itertools",
    "statistics", "string", "re", "typing", "enum", "functools",
    "textwrap", "pathlib", "os.path", "csv",
}

# Módulos prohibidos explícitamente
BLOCKED_PATTERNS = [
    "import os", "from os ", "import subprocess", "from subprocess",
    "import shutil", "from shutil", "import sys", "from sys",
    "__import__", "eval(", "exec(", "open(", "__builtins__",
    "import ctypes", "from ctypes",
]


class SandboxError(Exception):
    """Error de ejecución en el sandbox."""
    pass


class CodeExecutor:
    """Ejecuta código Python de forma segura."""

    MAX_OUTPUT_LENGTH = 5000
    MAX_CODE_LENGTH = 2000
    TIMEOUT_SECONDS = 15

    def _validate_code(self, code: str):
        """Valida que el código sea seguro."""
        # Verificar longitud
        if len(code) > self.MAX_CODE_LENGTH:
            raise SandboxError(f"Código demasiado largo ({len(code)} > {self.MAX_CODE_LENGTH} caracteres)")

        # Verificar patrones bloqueados
        for pattern in BLOCKED_PATTERNS:
            if pattern in code:
                raise SandboxError(f"Código bloqueado: contiene '{pattern}'")

        # Parsear AST para verificar sintaxis
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SandboxError(f"Error de sintaxis: {e}")

        # Verificar imports permitidos
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in ALLOWED_MODULES:
                        raise SandboxError(f"Módulo no permitido: '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] not in ALLOWED_MODULES:
                    raise SandboxError(f"Módulo no permitido: '{node.module}'")

    async def execute(self, code: str) -> dict:
        """
        Ejecuta código Python en sandbox.
        Devuelve {"success": bool, "output": str, "error": str|null}
        """
        # Limpiar formato markdown si viene del LLM
        code = code.strip()
        if code.startswith("```"):
            code = code.split("\n", 1)[1] if "\n" in code else code[3:]
        if code.endswith("```"):
            code = code.rsplit("\n", 1)[0] if "\n" in code else code[:-3]
        if code.startswith("python"):
            code = code.split("\n", 1)[1] if "\n" in code else code[7:]

        code = code.strip()

        try:
            self._validate_code(code)
        except SandboxError as e:
            return {"success": False, "output": "", "error": str(e)}

        # Capturar stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Entorno limitado
        restricted_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "True": True,
                "False": False,
                "None": None,
                "abs": abs,
                "all": all,
                "any": any,
                "enumerate": enumerate,
                "filter": filter,
                "map": map,
                "max": max,
                "min": min,
                "round": round,
                "sorted": sorted,
                "sum": sum,
                "zip": zip,
                "isinstance": isinstance,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
                "range": range,
                "reversed": reversed,
                "iter": iter,
                "next": next,
                "slice": slice,
                "format": format,
                "bytes": bytes,
                "bytearray": bytearray,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "Exception": Exception,
            }
        }

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(textwrap.dedent(code), restricted_globals)

            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()

            if len(output) > self.MAX_OUTPUT_LENGTH:
                output = output[:self.MAX_OUTPUT_LENGTH] + f"\n\n... [truncado, {len(output)} caracteres totales]"

            return {
                "success": not bool(error),
                "output": output,
                "error": error or None,
            }

        except Exception as e:
            error_output = stderr_capture.getvalue() or ""
            tb = traceback.format_exc()
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": f"{type(e).__name__}: {e}\n{tb}",
            }
