"""Application configuration — all tuneable values in one place."""

import os
from pathlib import Path

# Root of the backend directory (one level up from this file)
BACKEND_DIR = Path(__file__).parent.parent

# Directories for uploaded reference audio, generated outputs, and profiles.
# Override via environment variables if needed.
UPLOAD_DIR = Path(os.getenv("VOICEFORGE_UPLOAD_DIR", str(BACKEND_DIR / "data" / "uploads")))
OUTPUT_DIR = Path(os.getenv("VOICEFORGE_OUTPUT_DIR", str(BACKEND_DIR / "data" / "outputs")))
PROFILES_DIR = Path(os.getenv("VOICEFORGE_PROFILES_DIR", str(BACKEND_DIR / "data" / "profiles")))

# Ensure all data directories exist at import time.
for _dir in (UPLOAD_DIR, OUTPUT_DIR, PROFILES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# FastAPI server defaults (used by start.sh; not enforced here).
HOST = os.getenv("VOICEFORGE_HOST", "127.0.0.1")
PORT = int(os.getenv("VOICEFORGE_PORT", "8000"))
