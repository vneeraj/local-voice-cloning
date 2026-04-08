"""Voice profile persistence — save, list, retrieve, and delete named profiles."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import PROFILES_DIR, UPLOAD_DIR


class ProfileNotFoundError(Exception):
    """Raised when a requested profile ID does not exist."""


def _profile_path(profile_id: str) -> Path:
    return PROFILES_DIR / f"{profile_id}.json"


def _ref_wav_path(reference_id: str) -> Path:
    """Resolve the normalised WAV path for a given reference ID."""
    return UPLOAD_DIR / f"{reference_id}_ref.wav"


def save_profile(name: str, reference_id: str) -> dict:
    """Persist a new voice profile and return its metadata dict.

    Args:
        name: Human-readable profile name (will be stored as-is; sanitisation
            is the caller's responsibility).
        reference_id: The ID returned by the upload endpoints, used to locate
            the reference WAV on disk.

    Returns:
        A dict with keys ``id``, ``name``, ``reference_id``, and
        ``created_at`` (ISO 8601 UTC string).

    Raises:
        FileNotFoundError: If the reference WAV for *reference_id* does not
            exist on disk.
    """
    ref_wav = _ref_wav_path(reference_id)
    if not ref_wav.exists():
        raise FileNotFoundError(
            f"Reference audio not found for reference_id={reference_id!r}"
        )

    profile_id = uuid.uuid4().hex
    profile = {
        "id": profile_id,
        "name": name,
        "reference_id": reference_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _profile_path(profile_id).write_text(json.dumps(profile, indent=2))
    return profile


def list_profiles() -> list[dict]:
    """Return all saved profiles sorted by creation date (newest first).

    Returns:
        List of profile metadata dicts.  Corrupt files are silently skipped.
    """
    profiles = []
    for path in PROFILES_DIR.glob("*.json"):
        try:
            profiles.append(json.loads(path.read_text()))
        except Exception:  # noqa: BLE001
            continue
    profiles.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return profiles


def get_profile(profile_id: str) -> dict:
    """Return metadata for a single profile.

    Args:
        profile_id: The profile's UUID hex string.

    Returns:
        Profile metadata dict.

    Raises:
        ProfileNotFoundError: If no profile with *profile_id* exists.
    """
    path = _profile_path(profile_id)
    if not path.exists():
        raise ProfileNotFoundError(profile_id)
    return json.loads(path.read_text())


def get_profile_wav(profile_id: str) -> Path:
    """Return the Path to the reference WAV for *profile_id*.

    Args:
        profile_id: The profile's UUID hex string.

    Returns:
        Path to the reference WAV file.

    Raises:
        ProfileNotFoundError: If the profile metadata does not exist.
        FileNotFoundError: If the WAV file has been deleted from disk.
    """
    profile = get_profile(profile_id)
    wav = _ref_wav_path(profile["reference_id"])
    if not wav.exists():
        raise FileNotFoundError(
            f"Reference WAV missing for profile {profile_id!r}: {wav}"
        )
    return wav


def delete_profile(profile_id: str) -> None:
    """Delete a profile's metadata JSON.

    The reference WAV is intentionally *not* deleted — it may be shared with
    other profiles or still in use.

    Args:
        profile_id: The profile's UUID hex string.

    Raises:
        ProfileNotFoundError: If the profile does not exist.
    """
    path = _profile_path(profile_id)
    if not path.exists():
        raise ProfileNotFoundError(profile_id)
    path.unlink()
