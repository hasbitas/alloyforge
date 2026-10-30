#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]] || ! command -v npm >/dev/null; then
  echo "ERROR: Dependencies are missing. Run ./setup.sh first." >&2
  exit 1
fi
# Check both ports before starting, so an older server cannot pass our health check.
.venv/bin/python - <<'PY'
import socket
for port in (8000, 5173):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            raise SystemExit(f'ERROR: Port {port} is in use. Stop the other app and try again.')
PY
backend_pid=''
frontend_pid=''
cleanup() {
  trap - EXIT INT TERM
  for pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  for pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$pid" ]]; then wait "$pid" 2>/dev/null || true; fi
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
backend_pid=$!
.venv/bin/python - <<'PY'
import time
import urllib.request
for _ in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1) as response:
            if response.status == 200:
                break
    except OSError:
        time.sleep(0.5)
else:
    raise SystemExit('ERROR: Backend did not become ready. Check the messages above.')
PY
echo "Open http://127.0.0.1:5173 in your browser. API docs: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C here to stop both servers."
# Run Node directly so cleanup owns the server process rather than an npm wrapper.
node frontend/node_modules/vite/bin/vite.js frontend --host 127.0.0.1 --port 5173 --strictPort &
frontend_pid=$!
wait "$frontend_pid"
