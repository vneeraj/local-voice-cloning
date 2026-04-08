"""Tests for backend/app/tts_service.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDeviceSelection:
    def test_returns_mps_when_available(self) -> None:
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Re-import to pick up the mock.
            import importlib  # noqa: PLC0415
            import app.tts_service as mod  # noqa: PLC0415

            importlib.reload(mod)
            assert mod.device_selection() == "mps"

    def test_returns_cpu_when_mps_unavailable(self) -> None:
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            import importlib  # noqa: PLC0415
            import app.tts_service as mod  # noqa: PLC0415

            importlib.reload(mod)
            assert mod.device_selection() == "cpu"

    def test_returns_cpu_when_torch_import_fails(self) -> None:
        with patch.dict("sys.modules", {"torch": None}):
            import importlib  # noqa: PLC0415
            import app.tts_service as mod  # noqa: PLC0415

            importlib.reload(mod)
            assert mod.device_selection() == "cpu"


class TestF5TTSService:
    def _make_service(self):
        """Return a fresh F5TTSService without triggering any imports."""
        from app.tts_service import F5TTSService  # noqa: PLC0415

        return F5TTSService()

    def test_model_not_loaded_at_init(self) -> None:
        service = self._make_service()
        assert service._tts is None

    def test_generate_loads_model_on_first_call(self, tmp_path: Path) -> None:
        service = self._make_service()
        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_text("")  # placeholder
        output = tmp_path / "out.wav"

        mock_f5tts_cls = MagicMock()
        mock_model = MagicMock()
        mock_model.infer.return_value = ([0.0] * 100, 24000, None)
        mock_f5tts_cls.return_value = mock_model

        mock_f5_module = MagicMock()
        mock_f5_module.F5TTS = mock_f5tts_cls

        with (
            patch.dict("sys.modules", {"f5_tts": mock_f5_module, "f5_tts.api": mock_f5_module}),
            patch("app.tts_service.device_selection", return_value="cpu"),
        ):
            service.generate(
                text="Hello world.",
                reference_wav=str(ref_wav),
                output_path=str(output),
            )

        mock_f5tts_cls.assert_called_once_with(device="cpu")
        mock_model.infer.assert_called_once()
        assert service._tts is mock_model

    def test_generate_reuses_loaded_model(self, tmp_path: Path) -> None:
        service = self._make_service()
        mock_model = MagicMock()
        mock_model.infer.return_value = ([0.0] * 100, 24000, None)
        service._tts = mock_model  # Inject pre-loaded model.

        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_text("")
        output = tmp_path / "out.wav"

        service.generate(
            text="Second call.",
            reference_wav=str(ref_wav),
            output_path=str(output),
        )

        # Model was already set; infer should be called directly.
        mock_model.infer.assert_called_once()

    def test_generate_raises_on_inference_failure(self, tmp_path: Path) -> None:
        service = self._make_service()
        mock_model = MagicMock()
        mock_model.infer.side_effect = Exception("CUDA OOM")
        service._tts = mock_model

        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_text("")
        output = tmp_path / "out.wav"

        with pytest.raises(RuntimeError, match="F5-TTS inference failed"):
            service.generate(
                text="Fail.",
                reference_wav=str(ref_wav),
                output_path=str(output),
            )
