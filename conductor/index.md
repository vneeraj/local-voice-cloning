# Conductor Index — VoiceForge

## Project Documentation

| Document | Path | Description |
|---|---|---|
| Product Definition | [./product.md](./product.md) | Vision, goals, features, success criteria |
| Tech Stack | [./tech-stack.md](./tech-stack.md) | Technology choices and rationale |
| Workflow | [./workflow.md](./workflow.md) | Development process, TDD lifecycle, commands |
| Product Guidelines | [./product-guidelines.md](./product-guidelines.md) | UX principles, visual design, component behavior |
| Tracks Registry | [./tracks.md](./tracks.md) | All tracks and their status |

## Code Style Guides

| Guide | Path |
|---|---|
| General | [./code_styleguides/general.md](./code_styleguides/general.md) |
| Python | [./code_styleguides/python.md](./code_styleguides/python.md) |
| JavaScript | [./code_styleguides/javascript.md](./code_styleguides/javascript.md) |
| TypeScript | [./code_styleguides/typescript.md](./code_styleguides/typescript.md) |
| HTML/CSS | [./code_styleguides/html-css.md](./code_styleguides/html-css.md) |

## Quick Reference

- **Backend entrypoint**: `backend/app/main.py`
- **Frontend entrypoint**: `frontend/src/main.tsx`
- **Launch**: `./start.sh`
- **Setup**: `./setup.sh`
- **API base**: `http://127.0.0.1:8000`
- **TTS model**: F5-TTS (`f5-tts` package)
- **Python managed by**: `uv` (venv at `backend/.venv`)
