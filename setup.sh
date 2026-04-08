#!/usr/bin/env bash
# setup.sh — VoiceForge first-time setup
# Bootstraps all Python and Node dependencies into the project folder.
# Requires only: bash, curl (both present on every macOS install).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/tools"
UV_BIN="$TOOLS_DIR/uv"
NODE_DIR="$TOOLS_DIR/node"
NODE_BIN="$NODE_DIR/bin/node"
NPM_BIN="$NODE_DIR/bin/npm"
VENV_DIR="$SCRIPT_DIR/backend/.venv"

# Colours (safe to strip if not a terminal)
if [ -t 1 ]; then
  GREEN="\033[0;32m"; CYAN="\033[0;36m"; YELLOW="\033[1;33m"; RESET="\033[0m"
else
  GREEN=""; CYAN=""; YELLOW=""; RESET=""
fi

step() { echo -e "${CYAN}==>${RESET} $*"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}!${RESET} $*"; }

# ---------------------------------------------------------------------------
# 1. Install uv (Python package manager that bundles its own Python)
# ---------------------------------------------------------------------------
step "Checking for uv …"
mkdir -p "$TOOLS_DIR"

if [ ! -x "$UV_BIN" ]; then
  step "Downloading uv …"
  curl -fsSL https://astral.sh/uv/install.sh \
    | UV_INSTALL_DIR="$TOOLS_DIR" INSTALLER_NO_MODIFY_PATH=1 sh
  # The installer places the binary at $TOOLS_DIR/uv
  if [ ! -x "$UV_BIN" ]; then
    echo "ERROR: uv was not found at $UV_BIN after installation." >&2
    exit 1
  fi
  ok "uv installed at $UV_BIN"
else
  ok "uv already present"
fi

# ---------------------------------------------------------------------------
# 2. Create Python 3.11 virtual environment
# ---------------------------------------------------------------------------
step "Setting up Python 3.11 virtual environment …"
"$UV_BIN" python install 3.11 --quiet
"$UV_BIN" venv --python 3.11 "$VENV_DIR" --quiet
ok "venv created at $VENV_DIR"

# ---------------------------------------------------------------------------
# 3. Install Python dependencies
# ---------------------------------------------------------------------------
step "Installing Python dependencies (this may take a few minutes) …"
# PyTorch for macOS arm64 comes from the default PyPI index as of 2.6+.
"$UV_BIN" pip install \
  --python "$VENV_DIR/bin/python" \
  -r "$SCRIPT_DIR/backend/requirements.txt" \
  --quiet
ok "Python dependencies installed"

# ---------------------------------------------------------------------------
# 4. Install Node.js (build-time only — not needed at runtime)
# ---------------------------------------------------------------------------
step "Checking for Node.js …"

if [ ! -x "$NODE_BIN" ]; then
  NODE_VERSION="22.14.0"
  NODE_ARCHIVE="node-v${NODE_VERSION}-darwin-arm64"
  NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ARCHIVE}.tar.gz"

  step "Downloading Node.js v${NODE_VERSION} for macOS arm64 …"
  mkdir -p "$NODE_DIR"
  curl -fsSL "$NODE_URL" \
    | tar -xz --strip-components=1 -C "$NODE_DIR"
  ok "Node.js installed at $NODE_DIR"
else
  ok "Node.js already present"
fi

# ---------------------------------------------------------------------------
# 5. Install frontend npm dependencies
# ---------------------------------------------------------------------------
step "Installing frontend npm dependencies …"
cd "$SCRIPT_DIR/frontend"
"$NPM_BIN" install --prefer-offline --loglevel=error
ok "npm dependencies installed"

# ---------------------------------------------------------------------------
# 6. Build the React frontend
# ---------------------------------------------------------------------------
step "Building React frontend …"
"$NPM_BIN" run build --loglevel=error
ok "Frontend built to frontend/dist/"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}Setup complete!${RESET}"
echo ""
echo "  Run the app:   ./start.sh"
echo "  Open browser:  http://127.0.0.1:8000"
echo ""
