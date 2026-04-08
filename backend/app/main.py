"""VoiceForge FastAPI application — all API routes."""

from __future__ import annotations

import logging
import os
import re
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.audio import extract_youtube, normalize_audio
from app.config import OUTPUT_DIR, UPLOAD_DIR
from app.profiles import (
    ProfileNotFoundError,
    delete_profile,
    get_profile_wav,
    list_profiles,
    save_profile,
)
from app.tts_service import tts_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VoiceForge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Allowed upload extensions
# ---------------------------------------------------------------------------

_ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}


def _safe_name(raw: str) -> str:
    """Strip any character that isn't alphanumeric, a space, hyphen, or underscore."""
    return re.sub(r"[^\w\s\-]", "", raw).strip()


# ---------------------------------------------------------------------------
# Reference audio endpoints
# ---------------------------------------------------------------------------


@app.post("/api/upload_reference")
async def upload_reference(audio: UploadFile = File(...)) -> dict:
    """Upload a local audio file as a voice reference.

    Accepts WAV, MP3, FLAC, OGG, M4A, and AAC files.  The file is
    normalised to a 24 kHz mono WAV and stored in the uploads directory.

    Returns:
        ``{"reference_id": str, "preview_url": str}``
    """
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in _ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format {suffix!r}. "
            f"Allowed: {sorted(_ALLOWED_AUDIO_EXTS)}",
        )

    file_id = uuid.uuid4().hex
    raw_path = UPLOAD_DIR / f"{file_id}_raw{suffix}"
    ref_path = UPLOAD_DIR / f"{file_id}_ref.wav"

    try:
        with raw_path.open("wb") as fh:
            shutil.copyfileobj(audio.file, fh)

        normalize_audio(raw_path, ref_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        try:
            os.remove(raw_path)
        except OSError:
            pass

    return {
        "reference_id": file_id,
        "preview_url": f"/uploads/{file_id}_ref.wav",
    }


@app.post("/api/upload_youtube")
async def upload_youtube(url: str = Form(...)) -> dict:
    """Extract audio from a YouTube URL as a voice reference.

    Downloads the best audio stream via yt-dlp, normalises it, and stores it
    in the uploads directory.

    Returns:
        ``{"reference_id": str, "preview_url": str}``
    """
    try:
        ref_wav = extract_youtube(url, UPLOAD_DIR)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Derive the reference_id from the WAV filename (<id>_ref.wav).
    reference_id = ref_wav.stem.replace("_ref", "")

    return {
        "reference_id": reference_id,
        "preview_url": f"/uploads/{ref_wav.name}",
    }


# ---------------------------------------------------------------------------
# Generation endpoint
# ---------------------------------------------------------------------------


@app.post("/api/generate")
async def generate(
    text: str = Form(...),
    reference_id: str = Form(...),
) -> FileResponse:
    """Synthesise speech in the cloned voice.

    Locates the normalised reference WAV for *reference_id*, runs F5-TTS
    inference, and returns the generated WAV file.

    Returns:
        WAV audio file (``audio/wav``).
    """
    ref_wav = UPLOAD_DIR / f"{reference_id}_ref.wav"
    if not ref_wav.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Reference audio not found for reference_id={reference_id!r}",
        )

    if not text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    output_id = uuid.uuid4().hex
    output_path = OUTPUT_DIR / f"{output_id}.wav"

    try:
        tts_service.generate(
            text=text,
            reference_wav=str(ref_wav),
            output_path=str(output_path),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return FileResponse(
        path=str(output_path),
        media_type="audio/wav",
        filename=f"voiceforge_{output_id}.wav",
    )


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------


@app.get("/api/profiles")
async def api_list_profiles() -> list[dict]:
    """Return all saved voice profiles, newest first."""
    return list_profiles()


@app.post("/api/profiles", status_code=201)
async def api_save_profile(
    name: str = Form(...),
    reference_id: str = Form(...),
) -> dict:
    """Save a new named voice profile from an existing reference ID.

    Args (form fields):
        name: Human-readable profile name.
        reference_id: ID from a prior upload or YouTube extraction.

    Returns:
        Profile metadata dict.
    """
    safe = _safe_name(name)
    if not safe:
        raise HTTPException(status_code=400, detail="Profile name is invalid")

    try:
        profile = save_profile(safe, reference_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return profile


@app.get("/api/profiles/{profile_id}/audio")
async def api_profile_audio(profile_id: str) -> FileResponse:
    """Stream the reference WAV for a saved profile."""
    try:
        wav_path = get_profile_wav(profile_id)
    except ProfileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id!r} not found")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(path=str(wav_path), media_type="audio/wav")


@app.delete("/api/profiles/{profile_id}", status_code=204)
async def api_delete_profile(profile_id: str) -> None:
    """Delete a saved voice profile by ID."""
    try:
        delete_profile(profile_id)
    except ProfileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id!r} not found")


# ---------------------------------------------------------------------------
# Static file mounts (must come last to avoid shadowing API routes)
# ---------------------------------------------------------------------------

# Serve uploaded reference files so the frontend can preview them.
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Serve generated output files.
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# Serve the built React app.  Falls back gracefully if dist/ doesn't exist yet.
_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
