# Product Definition: VoiceForge

## Overview

VoiceForge is a local, high-fidelity voice cloning tool that runs entirely on an Apple Silicon Mac (M5 MacBook Air, 16 GB RAM). It allows users to clone any voice from a short audio reference and synthesize new speech from arbitrary text — with zero cloud dependency and no data leaving the machine.

## Target Audience

- Content creators who want to generate narration in a specific voice
- Developers and researchers experimenting with local TTS
- Privacy-conscious users who need voice synthesis without cloud APIs

## Core Problems Solved

1. **Cloud TTS privacy**: All processing is local; no audio or text is sent to third-party services
2. **Voice consistency**: Save named voice profiles and reuse them across sessions
3. **Friction in reference capture**: Accept audio files, YouTube URLs, or a voice library — no manual audio editing needed

## Key Features

1. **Zero-shot voice cloning** via F5-TTS — clone a voice from a 5–30 second reference clip
2. **Multiple reference sources**: upload audio files (WAV/MP3/FLAC/OGG), paste a YouTube URL, or pick a saved profile
3. **Voice profile library**: save a cloned voice as a named profile; manage (rename, delete, preview) saved profiles
4. **High-quality audio output**: 24 kHz WAV output, downloadable in-browser
5. **React-based UI**: clean, minimal single-page app — no page reloads, immediate feedback
6. **Self-contained install**: a `setup.sh` + `start.sh` pair; everything lives in the project folder, nothing lingers after the app is stopped

## Success Criteria

- Clone a voice from a 15-second clip and produce intelligible, recognizable output
- End-to-end latency (reference → generated speech) < 60 s on M5 Mac CPU/MPS
- Zero external network calls during generation
- User can save a profile, reload the app, and reuse the profile without re-uploading reference audio
- Setup takes < 10 minutes from a fresh Mac with only Homebrew available

## Differentiators vs Old Version

| Dimension | Old (Kokoro) | VoiceForge (F5-TTS) |
|---|---|---|
| Model | Kokoro (predefined voices) | F5-TTS (zero-shot cloning) |
| UI | Plain HTML | React SPA |
| Deployment | Manual venv | `setup.sh` / `start.sh` |
| Browser recording | No | No (v1) |
| Profile library | Basic JSON | Full CRUD with preview |
