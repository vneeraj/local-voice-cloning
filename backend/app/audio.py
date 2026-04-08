"""Audio ingestion utilities: normalization and YouTube extraction."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import imageio_ffmpeg

# Cached path to the bundled ffmpeg binary.
_FFMPEG_EXE: str = imageio_ffmpeg.get_ffmpeg_exe()

# ffmpeg audio filter chain applied to every reference clip.
# - highpass/lowpass: strip sub-80 Hz rumble and above-8 kHz hiss
# - loudnorm: EBU R128 loudness normalisation
# - silenceremove: trim leading/trailing silence longer than 1 s at -50 dBFS
_AUDIO_FILTERS = (
    "highpass=f=80,"
    "lowpass=f=8000,"
    "loudnorm,"
    "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"
)

# Target audio format for F5-TTS: 24 kHz mono 16-bit PCM WAV.
_SAMPLE_RATE = 24000
_CHANNELS = 1
_SAMPLE_FMT = "s16"


def normalize_audio(input_path: str | Path, output_path: str | Path) -> None:
    """Convert and normalise *input_path* to a clean 24 kHz mono WAV at *output_path*.

    Runs an ffmpeg filter chain that strips noise, normalises loudness, and
    trims silence.  Raises ``RuntimeError`` on ffmpeg failure.

    Args:
        input_path: Path to any audio file supported by ffmpeg.
        output_path: Destination path for the processed WAV.

    Raises:
        RuntimeError: If ffmpeg exits with a non-zero status.
    """
    cmd = [
        _FFMPEG_EXE,
        "-y",
        "-i", str(input_path),
        "-af", _AUDIO_FILTERS,
        "-ar", str(_SAMPLE_RATE),
        "-ac", str(_CHANNELS),
        "-sample_fmt", _SAMPLE_FMT,
        str(output_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg normalisation failed: {err}")


def extract_youtube(url: str, output_dir: str | Path) -> Path:
    """Download audio from a YouTube URL and return the path to a normalised WAV.

    Uses yt-dlp to fetch the best audio stream, then runs it through
    :func:`normalize_audio`.

    Args:
        url: A YouTube video URL.
        output_dir: Directory in which to place the downloaded and processed files.

    Returns:
        Path to the final normalised WAV file.

    Raises:
        RuntimeError: If the download or normalisation step fails.
        ImportError: If yt-dlp is not installed.
    """
    try:
        import yt_dlp  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("yt-dlp is required for YouTube extraction") from exc

    output_dir = Path(output_dir)
    file_id = uuid.uuid4().hex
    raw_template = str(output_dir / f"{file_id}_raw.%(ext)s")

    ydl_opts = {
        "ffmpeg_location": _FFMPEG_EXE,
        "format": "bestaudio/best",
        "outtmpl": raw_template,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception as exc:
        raise RuntimeError(f"yt-dlp download failed: {exc}") from exc

    # Locate the wav file yt-dlp wrote.
    raw_wav: Path | None = None
    for entry in output_dir.iterdir():
        if entry.name.startswith(f"{file_id}_raw") and entry.suffix == ".wav":
            raw_wav = entry
            break

    if raw_wav is None:
        raise RuntimeError("yt-dlp did not produce a WAV file in the expected location")

    final_wav = output_dir / f"{file_id}_ref.wav"
    normalize_audio(raw_wav, final_wav)

    # Clean up the raw download.
    try:
        os.remove(raw_wav)
    except OSError:
        pass

    return final_wav
