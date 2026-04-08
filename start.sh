#!/usr/bin/env bash
# start.sh — Launch VoiceForge
# Starts the FastAPI backend (which also serves the built React frontend).
# Press Ctrl-C to stop; the server process is cleaned up automatically.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/backend/.venv"
UVICORN="$VENV_DIR/bin/uvicorn"

if [ ! -x "$UVICORN" ]; then
  echo "ERROR: Virtual environment not found. Run ./setup.sh first." >&2
  exit 1
fi

HOST="${VOICEFORGE_HOST:-127.0.0.1}"
PORT="${VOICEFORGE_PORT:-8000}"

# Start uvicorn in the background so we can capture its PID.
cd "$SCRIPT_DIR/backend"
"$UVICORN" app.main:app --host "$HOST" --port "$PORT" &
SERVER_PID=$!

# Ensure clean shutdown on Ctrl-C or terminal close.
cleanup() {
  echo ""
  echo "Stopping VoiceForge …"
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  echo "Stopped."
}
trap cleanup INT TERM EXIT

echo ""
echo "  VoiceForge is running at http://${HOST}:${PORT}"
echo "  Press Ctrl-C to stop."
echo ""

# Wait for the server process to exit.
wait "$SERVER_PID"
