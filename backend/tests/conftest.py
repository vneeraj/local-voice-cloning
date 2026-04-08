"""Shared pytest fixtures for the VoiceForge backend test suite."""

from __future__ import annotations

import io
import struct
import wave
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Temporary directory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override UPLOAD_DIR to a temporary directory for the duration of a test."""
    upload = tmp_path / "uploads"
    upload.mkdir()
    monkeypatch.setattr("app.config.UPLOAD_DIR", upload)
    monkeypatch.setattr("app.audio.UPLOAD_DIR", upload, raising=False)
    monkeypatch.setattr("app.main.UPLOAD_DIR", upload)
    monkeypatch.setattr("app.profiles.UPLOAD_DIR", upload)
    return upload


@pytest.fixture()
def tmp_output_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override OUTPUT_DIR to a temporary directory for the duration of a test."""
    output = tmp_path / "outputs"
    output.mkdir()
    monkeypatch.setattr("app.config.OUTPUT_DIR", output)
    monkeypatch.setattr("app.main.OUTPUT_DIR", output)
    return output


@pytest.fixture()
def tmp_profiles_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override PROFILES_DIR to a temporary directory for the duration of a test."""
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    monkeypatch.setattr("app.config.PROFILES_DIR", profiles)
    monkeypatch.setattr("app.profiles.PROFILES_DIR", profiles)
    return profiles


# ---------------------------------------------------------------------------
# Minimal WAV fixture
# ---------------------------------------------------------------------------


def make_wav_bytes(duration_s: float = 0.5, sample_rate: int = 24000) -> bytes:
    """Return the raw bytes of a minimal silent WAV file."""
    n_samples = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *([0] * n_samples)))
    return buf.getvalue()


@pytest.fixture()
def sample_wav_bytes() -> bytes:
    """Return bytes for a minimal silent WAV file."""
    return make_wav_bytes()


@pytest.fixture()
def sample_wav_file(tmp_path: Path) -> Path:
    """Write a minimal silent WAV to a temp file and return its path."""
    path = tmp_path / "sample.wav"
    path.write_bytes(make_wav_bytes())
    return path


# ---------------------------------------------------------------------------
# FastAPI test client with mocked TTS and audio processing
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(
    tmp_upload_dir: Path,
    tmp_output_dir: Path,
    tmp_profiles_dir: Path,
) -> TestClient:
    """Return a TestClient with mocked TTS service and audio normalization.

    - ``normalize_audio`` is patched to copy the input to the output path so
      tests don't need a real ffmpeg binary.
    - ``tts_service.generate`` is patched to write a silent WAV so tests don't
      need the F5-TTS model.
    """
    import shutil

    def _fake_normalize(input_path: str | Path, output_path: str | Path) -> None:
        shutil.copy(str(input_path), str(output_path))

    def _fake_generate(
        text: str,
        reference_wav: str,
        output_path: str,
        ref_text: str = "",
    ) -> None:
        Path(output_path).write_bytes(make_wav_bytes())

    with (
        patch("app.main.normalize_audio", side_effect=_fake_normalize),
        patch("app.main.tts_service.generate", side_effect=_fake_generate),
    ):
        from app.main import app  # noqa: PLC0415

        yield TestClient(app)
