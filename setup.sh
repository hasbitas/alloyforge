#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
trap 'echo "ERROR: Setup stopped. Read the error above, fix it, and run ./setup.sh again." >&2' ERR
echo "AlloyForge setup - Python 3.11+ and Node.js LTS are required."
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  echo "ERROR: Install Python 3.11+ from https://www.python.org/downloads/" >&2
  exit 1
fi
if ! command -v node >/dev/null || ! command -v npm >/dev/null || ! node -e "const [a,b]=process.versions.node.split('.').map(Number); process.exit(((a===20 && b>=19)||(a===22 && b>=12)||a>22) ? 0 : 1)"; then
  echo "ERROR: Install Node.js LTS from https://nodejs.org/ (20.19+, 22.12+, or newer LTS)." >&2
  exit 1
fi
if [[ "${1:-}" == "--check" ]]; then
  echo "Prerequisite check passed. No packages were installed."
  exit 0
fi
echo "[1/4] Creating the local Python environment..."
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
echo "[2/4] Updating pip..."
.venv/bin/python -m pip install --upgrade pip
echo "[3/4] Installing Python dependencies, including test tools..."
.venv/bin/python -m pip install -e '.[dev]'
echo "[4/4] Installing browser interface dependencies..."
npm --prefix frontend install
echo "Setup complete. Run ./start.sh to open the demo."
