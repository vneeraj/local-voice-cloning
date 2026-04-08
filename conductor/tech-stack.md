# Tech Stack

## Backend

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.11 | F5-TTS is Python-native; strong ML ecosystem |
| Framework | FastAPI | Async, clean REST API, automatic OpenAPI docs; used in old version |
| TTS Engine | F5-TTS | Zero-shot voice cloning from short reference clip; supports Apple MPS acceleration |
| Audio processing | ffmpeg (bundled via `imageio-ffmpeg`) | Robust format conversion and audio normalization |
| YouTube ingest | yt-dlp | Actively maintained, no API key required |
| Python env | `uv` + project-local `.venv` | `uv` can bootstrap its own Python; venv stays in project folder |
| ASGI server | Uvicorn | Lightweight, pairs with FastAPI |

## Frontend

| Component | Choice | Rationale |
|---|---|---|
| Framework | React 18 | Component model suits multi-step UX (upload → generate → save); large ecosystem |
| Build tool | Vite | Fast dev server and optimized production builds |
| Styling | CSS Modules + plain CSS | No extra runtime dependency; scoped styles without a CSS-in-JS library |
| HTTP client | Native `fetch` | No dependency overhead for simple API calls |
| Audio playback | Native `<audio>` element | Browser-native, no library needed |
| State management | React hooks (`useState`, `useReducer`, `useContext`) | Sufficient for this app's complexity; avoids Redux overhead |

## Deployment

| Component | Choice | Rationale |
|---|---|---|
| Packaging | Project-local `.venv` + built React `dist/` | Self-contained in the project folder |
| Frontend serving | FastAPI `StaticFiles` mount | Single server process; no separate nginx |
| Launch | `setup.sh` + `start.sh` shell scripts | No external tools required at runtime beyond Python |
| Python bootstrap | `uv` (downloaded by `setup.sh` if absent) | Installs a managed Python 3.11; nothing written outside the project |
| Process cleanup | `start.sh` uses `trap` on EXIT to kill uvicorn PID | No zombie processes after Ctrl-C or terminal close |

## Hardware Target

- **Machine**: Apple M5 MacBook Air, 16 GB unified memory
- **Acceleration**: F5-TTS uses `torch` with MPS backend (`device="mps"`) for Apple Silicon GPU acceleration
- **Fallback**: CPU inference if MPS unavailable (slower but functional)

## Key Dependencies (Python)

```
f5-tts
torch          # MPS-enabled build for macOS arm64
torchaudio
fastapi
uvicorn[standard]
python-multipart
imageio-ffmpeg
yt-dlp
soundfile
```

## Key Dependencies (Node / build-time only)

```
react
react-dom
vite
@vitejs/plugin-react
```
Node and npm are required only during `setup.sh` (build step). The compiled `dist/` is committed or retained; Node is not needed at runtime.

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-04-08 | F5-TTS over Kokoro | Zero-shot cloning; no predefined voice list required |
| 2026-04-08 | React over plain HTML | Better component composition for profile library and multi-step flow |
| 2026-04-08 | Shell scripts over Docker | User preference: no lingering deps; `uv` provides portable Python without Docker overhead |
| 2026-04-08 | `uv` for Python management | Can download its own Python interpreter; keeps everything inside project folder |
