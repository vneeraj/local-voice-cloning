# Track 01 Implementation Plan: Project Foundation & Backend Core

## Phase 1: Project Scaffold & Shell Scripts

- [ ] Create `backend/app/` package structure (`__init__.py`, `main.py`, `tts_service.py`, `profiles.py`, `audio.py`)
- [ ] Create `backend/requirements.txt` with pinned dependencies
- [ ] Create `frontend/` placeholder (empty `index.html` + `vite.config.ts` stubs) so `setup.sh` can run `npm install`
- [ ] Write `setup.sh`:
  - Download and install `uv` to `backend/.uv/` if not found in PATH
  - Use `uv` to create `backend/.venv` with Python 3.11
  - Run `uv pip install -r backend/requirements.txt` into the venv
  - Run `npm install` in `frontend/`
  - Run `npm run build` in `frontend/`
  - Print setup complete message
- [ ] Write `start.sh`:
  - Start uvicorn via `backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`
  - Trap SIGINT/SIGTERM to kill uvicorn PID and exit cleanly
  - Print the local URL on startup
- [ ] Write `backend/tests/conftest.py` with pytest fixtures (test client, temp dirs)

## Phase 2: Audio Ingestion Layer

- [ ] Implement `backend/app/audio.py`:
  - `normalize_audio(input_path, output_path)` — ffmpeg pipeline: highpass, lowpass, loudnorm, silenceremove, resample to 24 kHz mono WAV
  - `extract_youtube(url, output_dir)` — yt-dlp download + normalize
- [ ] Write `backend/tests/test_audio.py` — unit tests with a real short WAV fixture; mock yt-dlp for YouTube tests
- [ ] Add `UPLOAD_DIR` and `OUTPUT_DIR` configuration via environment variables with sensible defaults

## Phase 3: F5-TTS Service

- [ ] Implement `backend/app/tts_service.py`:
  - `class F5TTSService` with lazy model loading on first use
  - `device_selection()` — return `"mps"` if `torch.backends.mps.is_available()` else `"cpu"`
  - `generate(text: str, reference_wav: str, output_path: str) -> None`
- [ ] Write `backend/tests/test_tts_service.py` — mock `f5_tts` to avoid loading the model in CI

## Phase 4: FastAPI API Endpoints

- [ ] Implement `POST /api/upload_reference` in `backend/app/main.py`
- [ ] Implement `POST /api/upload_youtube`
- [ ] Implement `POST /api/generate`
- [ ] Implement `backend/app/profiles.py`:
  - `list_profiles()`, `save_profile(name, reference_id)`, `get_profile(id)`, `delete_profile(id)`
  - Profiles stored as JSON files in `PROFILES_DIR`
- [ ] Implement `GET /api/profiles`, `POST /api/profiles`, `GET /api/profiles/{id}/audio`, `DELETE /api/profiles/{id}`
- [ ] Mount `StaticFiles` for uploads, outputs, and the built React `dist/`
- [ ] Write `backend/tests/test_api.py` — full endpoint tests using `httpx.AsyncClient` + TestClient; mock TTS service

## Phase 5: Validation & Cleanup

- [ ] Run `ruff check` and fix all linting issues
- [ ] Run `pytest --cov=app --cov-report=term-missing`; achieve >80% coverage
- [ ] Verify `setup.sh` runs cleanly in a temp directory (no cached state)
- [ ] Verify `start.sh` / Ctrl-C exits without zombie processes
- [ ] Update `conductor/tracks.md` status to 🟢 Complete
