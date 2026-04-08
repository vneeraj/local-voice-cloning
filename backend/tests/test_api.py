"""End-to-end API tests for the VoiceForge FastAPI application."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import make_wav_bytes


# ---------------------------------------------------------------------------
# /api/upload_reference
# ---------------------------------------------------------------------------


class TestUploadReference:
    def test_upload_wav_returns_reference_id(self, client: TestClient) -> None:
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("test.wav", io.BytesIO(make_wav_bytes()), "audio/wav")},
        )
        assert response.status_code == 200
        body = response.json()
        assert "reference_id" in body
        assert "preview_url" in body
        assert body["preview_url"].endswith("_ref.wav")

    def test_upload_mp3_is_accepted(self, client: TestClient) -> None:
        # Content-type doesn't matter; extension does.
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("clip.mp3", io.BytesIO(b"fake mp3"), "audio/mpeg")},
        )
        assert response.status_code == 200

    def test_upload_unsupported_format_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("video.mp4", io.BytesIO(b"fake mp4"), "video/mp4")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_txt_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# /api/upload_youtube
# ---------------------------------------------------------------------------


class TestUploadYoutube:
    def test_youtube_upload_returns_reference_id(
        self, client: TestClient, tmp_upload_dir: Path
    ) -> None:
        from unittest.mock import patch  # noqa: PLC0415

        fake_ref = tmp_upload_dir / "abc123_ref.wav"
        fake_ref.write_bytes(make_wav_bytes())

        with patch("app.main.extract_youtube", return_value=fake_ref):
            response = client.post(
                "/api/upload_youtube",
                data={"url": "https://youtube.com/watch?v=test"},
            )

        assert response.status_code == 200
        body = response.json()
        assert "reference_id" in body
        assert body["reference_id"] == "abc123"

    def test_youtube_download_failure_returns_422(self, client: TestClient) -> None:
        from unittest.mock import patch  # noqa: PLC0415

        with patch("app.main.extract_youtube", side_effect=RuntimeError("network error")):
            response = client.post(
                "/api/upload_youtube",
                data={"url": "https://youtube.com/watch?v=bad"},
            )

        assert response.status_code == 422
        assert "network error" in response.json()["detail"]


# ---------------------------------------------------------------------------
# /api/generate
# ---------------------------------------------------------------------------


class TestGenerate:
    def _create_reference(self, client: TestClient, upload_dir: Path) -> str:
        """Upload a WAV and return the reference_id."""
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("ref.wav", io.BytesIO(make_wav_bytes()), "audio/wav")},
        )
        assert response.status_code == 200
        return response.json()["reference_id"]

    def test_generate_returns_wav(
        self, client: TestClient, tmp_upload_dir: Path
    ) -> None:
        ref_id = self._create_reference(client, tmp_upload_dir)
        response = client.post(
            "/api/generate",
            data={"text": "Hello, world!", "reference_id": ref_id},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_generate_missing_reference_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/generate",
            data={"text": "Hello!", "reference_id": "nonexistent"},
        )
        assert response.status_code == 404

    def test_generate_empty_text_returns_400(
        self, client: TestClient, tmp_upload_dir: Path
    ) -> None:
        ref_id = self._create_reference(client, tmp_upload_dir)
        response = client.post(
            "/api/generate",
            data={"text": "   ", "reference_id": ref_id},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# /api/profiles
# ---------------------------------------------------------------------------


class TestProfiles:
    def _upload_reference(self, client: TestClient) -> str:
        response = client.post(
            "/api/upload_reference",
            files={"audio": ("ref.wav", io.BytesIO(make_wav_bytes()), "audio/wav")},
        )
        assert response.status_code == 200
        return response.json()["reference_id"]

    def test_list_profiles_empty(self, client: TestClient) -> None:
        response = client.get("/api/profiles")
        assert response.status_code == 200
        assert response.json() == []

    def test_save_and_list_profile(self, client: TestClient) -> None:
        ref_id = self._upload_reference(client)
        save_resp = client.post(
            "/api/profiles",
            data={"name": "Morgan Freeman", "reference_id": ref_id},
        )
        assert save_resp.status_code == 201
        profile = save_resp.json()
        assert profile["name"] == "Morgan Freeman"
        assert "id" in profile

        list_resp = client.get("/api/profiles")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["id"] == profile["id"]

    def test_save_profile_invalid_reference_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/profiles",
            data={"name": "Ghost Voice", "reference_id": "doesnotexist"},
        )
        assert response.status_code == 404

    def test_save_profile_invalid_name_returns_400(
        self, client: TestClient
    ) -> None:
        ref_id = self._upload_reference(client)
        response = client.post(
            "/api/profiles",
            data={"name": "!!!@@@", "reference_id": ref_id},
        )
        assert response.status_code == 400

    def test_get_profile_audio(self, client: TestClient) -> None:
        ref_id = self._upload_reference(client)
        save_resp = client.post(
            "/api/profiles",
            data={"name": "Test Voice", "reference_id": ref_id},
        )
        profile_id = save_resp.json()["id"]

        audio_resp = client.get(f"/api/profiles/{profile_id}/audio")
        assert audio_resp.status_code == 200
        assert audio_resp.headers["content-type"] == "audio/wav"

    def test_get_audio_unknown_profile_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/profiles/nonexistent/audio")
        assert response.status_code == 404

    def test_delete_profile(self, client: TestClient) -> None:
        ref_id = self._upload_reference(client)
        save_resp = client.post(
            "/api/profiles",
            data={"name": "Delete Me", "reference_id": ref_id},
        )
        profile_id = save_resp.json()["id"]

        del_resp = client.delete(f"/api/profiles/{profile_id}")
        assert del_resp.status_code == 204

        list_resp = client.get("/api/profiles")
        assert list_resp.json() == []

    def test_delete_unknown_profile_returns_404(self, client: TestClient) -> None:
        response = client.delete("/api/profiles/nonexistent")
        assert response.status_code == 404
