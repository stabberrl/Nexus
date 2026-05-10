from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run() -> None:
    """Start the Python backend server as a sidecar process."""
    backend_dir = Path(__file__).parent.parent / "backend"
    main_py = backend_dir / "main.py"

    if not main_py.exists():
        print(f"Error: Backend not found at {main_py}")
        sys.exit(1)

    try:
        subprocess.Popen(
            [sys.executable, str(main_py)],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        print(f"Error starting backend: {error}")
        sys.exit(1)
