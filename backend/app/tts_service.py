"""F5-TTS inference service with lazy model loading and MPS/CPU device selection."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def device_selection() -> str:
    """Return the best available torch device for F5-TTS inference.

    Prefers Apple MPS (Metal Performance Shaders) on Apple Silicon, falls back
    to CPU.

    Returns:
        ``"mps"`` if available, otherwise ``"cpu"``.
    """
    try:
        import torch  # noqa: PLC0415

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


class F5TTSService:
    """Wrapper around F5-TTS that loads the model lazily on first use.

    The model is large (~1–2 GB).  Deferring load until the first
    ``generate()`` call keeps server startup fast and avoids consuming memory
    when the endpoint is never hit.
    """

    def __init__(self) -> None:
        self._tts: object | None = None
        self._device: str | None = None

    def _ensure_loaded(self) -> None:
        """Load the F5-TTS model into memory if it has not been loaded yet."""
        if self._tts is not None:
            return

        from f5_tts.api import F5TTS  # noqa: PLC0415

        self._device = device_selection()
        logger.info("Loading F5-TTS model on device=%s …", self._device)
        self._tts = F5TTS(device=self._device)
        logger.info("F5-TTS model loaded.")

    def generate(
        self,
        text: str,
        reference_wav: str,
        output_path: str,
        ref_text: str = "",
    ) -> None:
        """Synthesise *text* in the voice captured in *reference_wav*.

        Performs zero-shot voice cloning: the model conditions on the acoustic
        characteristics of *reference_wav* and generates speech for *text*,
        writing a WAV file to *output_path*.

        Args:
            text: The text to synthesise.
            reference_wav: Path to a normalised 24 kHz mono WAV reference clip
                (5–30 seconds works best).
            output_path: Destination path for the generated WAV.
            ref_text: Optional transcript of *reference_wav*.  Leave empty to
                let F5-TTS transcribe it automatically.

        Raises:
            RuntimeError: If the model fails to generate audio.
        """
        self._ensure_loaded()

        try:
            wav, sr, _ = self._tts.infer(  # type: ignore[union-attr]
                ref_file=reference_wav,
                ref_text=ref_text,
                gen_text=text,
                file_wave=output_path,
            )
        except Exception as exc:
            raise RuntimeError(f"F5-TTS inference failed: {exc}") from exc

        logger.debug(
            "Generated %d samples at %d Hz → %s", len(wav), sr, output_path
        )


# Module-level singleton — shared across all requests.
tts_service = F5TTSService()
