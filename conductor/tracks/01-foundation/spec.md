# Track 01 Specification: Project Foundation & Backend Core

## Goal

Stand up the complete project skeleton — directory structure, dependency management, shell scripts, and the FastAPI backend with all API endpoints — so that subsequent tracks can build the frontend and polish the UI on top of a working server.

## Scope

### In Scope

1. **Project scaffold**: `backend/`, `frontend/` directory structure; `setup.sh`, `start.sh`
2. **Dependency management**: `uv`-based Python venv at `backend/.venv`; `backend/requirements.txt`
3. **F5-TTS integration**: `backend/app/tts_service.py` wrapping F5-TTS inference with MPS/CPU device selection
4. **Audio ingestion**: ffmpeg-based normalization for uploaded files and yt-dlp YouTube extraction
5. **FastAPI API endpoints**:
   - `POST /api/upload_reference` — upload audio file, return reference ID
   - `POST /api/upload_youtube` — extract audio from YouTube URL, return reference ID
   - `POST /api/generate` — synthesize speech from text + reference ID, return WAV
   - `GET  /api/profiles` — list saved voice profiles
   - `POST /api/profiles` — save a new voice profile (name + reference ID)
   - `GET  /api/profiles/{id}/audio` — stream the reference audio for a saved profile
   - `DELETE /api/profiles/{id}` — delete a saved profile
6. **Static file serving**: FastAPI mounts the built React `dist/` at `/`
7. **Tests**: pytest unit tests for the TTS service and each API endpoint (mocked model)

### Out of Scope (future tracks)

- React frontend implementation
- Browser microphone recording
- Profile waveform visualization

## Acceptance Criteria

- `./setup.sh` runs on a fresh macOS arm64 machine (with only `curl` and `bash` available), installs all dependencies into `backend/.venv` and `frontend/node_modules`, builds the React app
- `./start.sh` starts the server and exits cleanly on Ctrl-C with no zombie processes
- All 7 API endpoints respond correctly to valid requests
- Invalid inputs return appropriate HTTP error codes with descriptive messages
- `pytest` passes with >80% coverage on `backend/app/`
- F5-TTS uses `mps` device when available, falls back to `cpu`

## Dependencies

- F5-TTS Python package (`f5-tts`)
- PyTorch with MPS support (macOS arm64 wheel)
- ffmpeg (via `imageio-ffmpeg`)
- yt-dlp
- `uv` (bootstrapped by `setup.sh`)
