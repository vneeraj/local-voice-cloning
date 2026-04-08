"""Tests for backend/app/audio.py."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_wav_bytes


# ---------------------------------------------------------------------------
# normalize_audio
# ---------------------------------------------------------------------------


class TestNormalizeAudio:
    def test_success_copies_to_output(self, tmp_path: Path) -> None:
        """normalize_audio should produce a file at output_path on success."""
        input_wav = tmp_path / "input.wav"
        input_wav.write_bytes(make_wav_bytes())
        output_wav = tmp_path / "output.wav"

        # Patch subprocess.run to simulate a successful ffmpeg call.
        with patch("app.audio.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Simulate ffmpeg writing the output file.
            output_wav.write_bytes(make_wav_bytes())

            from app.audio import normalize_audio  # noqa: PLC0415

            normalize_audio(input_wav, output_wav)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert str(input_wav) in cmd
        assert str(output_wav) in cmd

    def test_raises_on_ffmpeg_failure(self, tmp_path: Path) -> None:
        """normalize_audio should raise RuntimeError when ffmpeg exits non-zero."""
        input_wav = tmp_path / "input.wav"
        input_wav.write_bytes(make_wav_bytes())
        output_wav = tmp_path / "output.wav"

        with patch("app.audio.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr=b"ffmpeg: some error",
            )

            from app.audio import normalize_audio  # noqa: PLC0415

            with pytest.raises(RuntimeError, match="ffmpeg normalisation failed"):
                normalize_audio(input_wav, output_wav)

    def test_ffmpeg_command_includes_filters(self, tmp_path: Path) -> None:
        """The ffmpeg command should include the audio filter chain."""
        input_wav = tmp_path / "input.wav"
        input_wav.write_bytes(make_wav_bytes())
        output_wav = tmp_path / "output.wav"

        with patch("app.audio.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            output_wav.write_bytes(make_wav_bytes())

            from app.audio import normalize_audio  # noqa: PLC0415

            normalize_audio(input_wav, output_wav)

        cmd = mock_run.call_args[0][0]
        joined = " ".join(cmd)
        assert "loudnorm" in joined
        assert "highpass" in joined
        assert "24000" in joined


# ---------------------------------------------------------------------------
# extract_youtube
# ---------------------------------------------------------------------------


class TestExtractYoutube:
    def test_raises_import_error_when_yt_dlp_missing(self, tmp_path: Path) -> None:
        """extract_youtube should raise ImportError if yt-dlp is not installed."""
        import builtins  # noqa: PLC0415
        real_import = builtins.__import__

        def _block_yt_dlp(name: str, *args, **kwargs):
            if name == "yt_dlp":
                raise ImportError("No module named 'yt_dlp'")
            return real_import(name, *args, **kwargs)

        from app.audio import extract_youtube  # noqa: PLC0415

        with patch("builtins.__import__", side_effect=_block_yt_dlp):
            with pytest.raises(ImportError, match="yt-dlp is required"):
                extract_youtube("https://youtube.com/watch?v=test", tmp_path)

    def test_raises_runtime_error_on_download_failure(self, tmp_path: Path) -> None:
        """extract_youtube should raise RuntimeError when yt-dlp fails."""
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("network error")

        with patch.dict("sys.modules", {"yt_dlp": MagicMock(YoutubeDL=MagicMock(return_value=mock_ydl))}):
            from app.audio import extract_youtube  # noqa: PLC0415

            with pytest.raises(RuntimeError, match="yt-dlp download failed"):
                extract_youtube("https://youtube.com/watch?v=test", tmp_path)

    def test_raises_runtime_error_when_wav_not_found(self, tmp_path: Path) -> None:
        """extract_youtube should raise RuntimeError if yt-dlp produces no WAV."""
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None  # "succeeds" but writes nothing

        with patch.dict("sys.modules", {"yt_dlp": MagicMock(YoutubeDL=MagicMock(return_value=mock_ydl))}):
            from app.audio import extract_youtube  # noqa: PLC0415

            with pytest.raises(RuntimeError, match="did not produce a WAV"):
                extract_youtube("https://youtube.com/watch?v=test", tmp_path)

    def test_happy_path_returns_normalised_wav(self, tmp_path: Path) -> None:
        """extract_youtube should return a Path to the normalised WAV on success."""
        import uuid  # noqa: PLC0415

        # Capture the file_id that extract_youtube generates internally
        # by watching uuid.uuid4 calls.
        captured_id: list[str] = []
        real_uuid4 = uuid.uuid4

        def _capture_uuid():
            uid = real_uuid4()
            captured_id.append(uid.hex)
            return uid

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)

        def _fake_extract_info(url: str, download: bool):
            # Write the raw WAV that yt-dlp would produce.
            raw = tmp_path / f"{captured_id[0]}_raw.wav"
            raw.write_bytes(make_wav_bytes())

        mock_ydl.extract_info.side_effect = _fake_extract_info

        with (
            patch.dict("sys.modules", {"yt_dlp": MagicMock(YoutubeDL=MagicMock(return_value=mock_ydl))}),
            patch("app.audio.uuid.uuid4", side_effect=_capture_uuid),
            patch("app.audio.normalize_audio", side_effect=lambda src, dst: shutil.copy(src, dst)),
        ):
            from app.audio import extract_youtube  # noqa: PLC0415

            result = extract_youtube("https://youtube.com/watch?v=test", tmp_path)

        assert result.exists()
        assert result.suffix == ".wav"
        assert result.name.endswith("_ref.wav")
