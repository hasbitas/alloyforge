# AlloyForge

An AI-assisted alloy design MVP built with **FastAPI, PyTorch, and React**.
Enter a target operating temperature, density, and yield strength; explore alloy
compositions, inspect a 3D unit-cell preview and virtual tensile curve, and
export the best candidate as CIF, MATLAB, and PDF files. No API key or paid
model service is required for the default pipeline.

## Architecture

```text
React + 3Dmol.js + Plotly
            |
       FastAPI / Pydantic
            |
PyTorch PPO proposal -> sigmoid gate -> L1-normalized composition
            |
Thermodynamic pre-screen: mixing enthalpy + VEC + atomic radius mismatch
            |
Deterministic PyTorch property surrogate
            |
Heuristic tensile curve -> CIF / MAT / PDF for the top candidate
```

VEC means valence electron concentration, the per-atom average weighted by atomic
fractions.

## MVP status

- The default surrogate is a **fast deterministic PyTorch model**, combining
  elemental heuristics with a fixed-weight neural correction. It is not a trained
  materials predictor and does **not** run CHGNet. The response's
  `best_candidate.predictions.engine` (also present on each top candidate) reports
  `pytorch-mvp` so the actual path is explicit.
- PPO samples a batch and performs an update on its rewards. The policy is
  initialized afresh for each request; training is not persisted, and the update
  does not refine the current batch. This demonstrates the pipeline, not a
  converged alloy optimization system.
- CHGNet inference is not implemented; the `quantum` extra only installs the
  dependencies (`python -m pip install -e ".[quantum]"`).
- LAMMPS is not integrated. It requires a separate installation, suitable
  interatomic potentials, and a validated simulation workflow. The legacy request
  flag `run_physics_engine` currently controls **artifact generation only**;
  setting it to `false` still returns surrogate predictions.

## Quick start

Requirements: Python 3.11+ and Node.js 20.19+ (or 22.12+). Run from the repository
root. Dependency installation requires internet access.

**Windows / PowerShell** (no activation required):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location frontend
npm.cmd install
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

In a second terminal, run `cd frontend` then `npm.cmd run dev`.
`npm.cmd` avoids PowerShell's script execution policy restriction on `npm.ps1`.

**macOS / Linux / bash:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
(cd frontend && npm install)
python -m uvicorn app.main:app --app-dir backend --reload
# In a second terminal:
cd frontend && npm run dev
```

UI: <http://localhost:5173> | API docs: <http://127.0.0.1:8000/docs> |
health: <http://127.0.0.1:8000/health>. Vite proxies `/api` and `/health` to the
backend. For a separately hosted frontend, set `VITE_API_BASE_URL` at build time
and configure backend CORS via `ALLOY_ALLOWED_ORIGINS` (a JSON array).

## Demo

<!-- DEMO_VIDEO -->

**CLI, no frontend or running server:** after installing backend dependencies,
activate `.venv` (`.\.venv\Scripts\Activate.ps1` on Windows or
`source .venv/bin/activate` in bash), then run:

```bash
python scripts/demo.py
```

On Windows with script activation disabled, use
`.\.venv\Scripts\python.exe scripts/demo.py` directly.
The demo targets 1000 C, 4.5 g/cm3, and 900 MPa using Ti, Al, V, Cr, Ni, and Mo.
It prints a table of up to five candidates with atomic percentages, predicted
properties, screening metrics, rewards, engine names, and verified artifact paths.
Seed 42, CPU execution, and a single PyTorch thread make the numerical results
repeatable within the same dependency versions. Run IDs and file metadata vary.
Files are written to the gitignored `runtime/artifacts/<design_id>/`.

**UI, one command after dependency installation (Windows):**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

This starts both servers and stops the backend when the frontend exits. Open
<http://127.0.0.1:5173>, choose targets and elements, click **Start design**, and
use the CIF / MAT / PDF download links. Ports 8000 and 5173 must be free.

Equivalent bash command, from the repository root with `.venv` activated:

```bash
( python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
  backend_pid=$!
  trap 'kill "$backend_pid" 2>/dev/null; wait "$backend_pid" 2>/dev/null' EXIT
  cd frontend && npm run dev -- --host 127.0.0.1 --strictPort
)
```

Wait for the backend startup message before submitting a design.

## API example

With the backend running, send a request using **curl** (bash):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/design \
  -H 'Content-Type: application/json' \
  -d '{"targets":{"temperature_c":1000,"density_g_cm3":4.5,"strength_mpa":900},"candidates":32,"allowed_elements":["Ti","Al","V","Cr","Ni","Mo"],"run_physics_engine":true}'
```

Or **PowerShell**:

```powershell
$body = @{
  targets = @{ temperature_c = 1000; density_g_cm3 = 4.5; strength_mpa = 900 }
  candidates = 32
  allowed_elements = @("Ti", "Al", "V", "Cr", "Ni", "Mo")
  run_physics_engine = $true
} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/design `
  -Method Post -ContentType "application/json" -Body $body
```

Responses include the best candidate, up to five ranked candidates, screening
values, predictions, rejected count, and artifact download URLs. An all-rejected
batch returns `status: "rejected"` with no best candidate or artifacts. Invalid
inputs return HTTP 422. Interactive request/response schemas are in `/docs`.

## Outputs

| File | Contents |
| --- | --- |
| `alloy.cif` | Illustrative unit cell with composition occupancies; not a relaxed crystal |
| `simulation.mat` | Element symbols, fractions, strain, stress in GPa, and reward |
| `report.pdf` | One-page target, composition, screening, property, and tensile summary |

Only the top candidate gets files. They can be downloaded through
`/api/v1/artifacts/<design_id>/<file_name>` or opened under `runtime/artifacts/`.
Delete old run folders manually when no longer needed.

## Tests

With `.venv` activated:

```bash
python -m pytest -q
cd frontend
npm run build
```

On Windows, the equivalent commands without activation are
`.\.venv\Scripts\python.exe -m pytest -q` and, inside `frontend`,
`npm.cmd run build`. Tests cover normalization, screening, API errors, artifact
creation/downloads, and deterministic CLI results. Build output in `frontend/dist/`
is ignored by Git.

## Project structure

```text
backend/app/        FastAPI, schemas, PPO, thermodynamics, surrogate, artifacts
backend/tests/      Pipeline and API regression tests
frontend/src/       React UI, 3D viewer, tensile chart, API client
scripts/demo.py     Deterministic end-to-end CLI demo
scripts/dev.ps1     Local backend + frontend launcher
runtime/artifacts/  Generated files (gitignored)
pyproject.toml      Python dependencies and tooling
```

## Limitations

This is a portfolio prototype, **not a tool for real metallurgical decisions**.
Screening thresholds and property formulas are illustrative and uncalibrated;
passing the filter does not prove stability, manufacturability, or performance.
The tensile curve is heuristic, not molecular dynamics; the 3D colors do not
represent calculated atomic stresses. CIF coordinates are placeholders, not a
physical microstructure. Density is a simple weighted approximation, and target
values also feed the surrogate, so apparent target agreement is not validation.
Results require independent physics calculations and experimental validation.
The development API has no authentication, rate limits, or artifact retention
policy; it is intended for local use.

## License

[MIT](LICENSE) - Copyright (c) 2026 hasbitas.
