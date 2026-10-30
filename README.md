# AlloyForge

A local web demo that suggests metal mixtures and shows illustrative estimates of their properties.

[Quick start](#quick-start-5-minutes) · [Try the demo](#try-the-demo) · [Limitations](#limitations) · [MIT license](LICENSE)

## What does it do?

Choose a temperature, weight per volume, and strength for a metal mixture (an **alloy**).
AlloyForge suggests mixtures of the elements you select and ranks them against your targets.
It shows a simple 3D atom preview, a stretching curve, and downloadable files.
For example: `1000 °C + 4.5 g/cm³ + 900 MPa → suggested mixtures + a report`.
These are demonstration estimates, not measurements or proof that a material will work.

## Quick start (5 minutes)

Allow extra time for the first download: the Python packages can be large.
You need an internet connection for setup. No API key or paid model service is needed.

1. **Install the tools.** Install [Python 3.11 or newer](https://www.python.org/downloads/).
   On Windows, tick **Add Python to PATH** in the installer.
   Also install [Node.js LTS](https://nodejs.org/) (20.19+, 22.12+, or a newer LTS).
   Reopen your terminal after installing them. A terminal is a window where you type commands;
   use PowerShell on Windows or Terminal on macOS/Linux.
2. **Download this project.** On this repository's GitHub page, click the green **Code** button,
   then **Download ZIP**. Extract the ZIP to a normal folder before continuing.
   If you already use Git, you can instead run:

   ```sh
   git clone https://github.com/hasbitas/alloyforge.git
   cd alloyforge
   ```

3. **Install the project.** On Windows, open the extracted project folder and double-click
   `setup.bat`. Wait for **Setup complete**. On macOS/Linux, open a terminal in the
   extracted folder (the one containing `README.md`) and run:

   ```sh
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

   Setup creates `.venv`, a private Python environment for this project, and installs
   the Python and browser interface packages. Run it again after dependency changes.
4. **Start it.** On Windows, double-click `start.bat`. On macOS/Linux, run:

   ```sh
   ./start.sh
   ```

5. **Open the page.** Keep the command window open. When it shows the address, open
   <http://127.0.0.1:5173> in your browser. Wait for the frontend's **Local** address
   before loading the page. You should see **AlloyForge**, target inputs, and a
   **Start design** button. Press **Ctrl+C** in the launcher window to stop both servers
   (on Windows, answer **Y** if asked to terminate the batch job).

The interface uses port 5173 and the Python server uses port 8000. A port is a
number that identifies a local service. These launchers serve only your computer.

## Try the demo

**In the browser:** start the app as above, keep the default values, and click
**Start design**. You should see ranked mixtures, a 3D preview, and a stretching
curve. Use the **CIF / MAT / PDF** links to download the best candidate's files.

**Without a browser:** after setup, open a terminal in the project folder and run
one command. No running server is needed.

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

macOS / Linux:

```sh
./.venv/bin/python scripts/demo.py
```

This prints up to five candidates and checks that the output files exist.
It uses 1000 °C, 4.5 g/cm³, 900 MPa, and Ti, Al, V, Cr, Ni, Mo
(titanium, aluminium, vanadium, chromium, nickel, molybdenum).
Look in `runtime/artifacts/`: each run gets its own folder containing
`alloy.cif`, `simulation.mat`, and `report.pdf`.
The command demo uses seed 42 (a fixed starting point for random choices), the
CPU, and one PyTorch thread. Numerical results repeat with the same dependency
versions; run IDs and file metadata vary.

## How it works

The **frontend**, the page in your browser, sends your targets to the **backend**,
the Python program doing the calculations. A proposal method picks mixtures.
A rough filter rejects some of them. A **surrogate**, a quick stand-in for a
slower calculation, estimates properties and gives each remaining mixture a score.
The best result gets a preview and files.

Names in the diagram:

- **React** builds the page; **3Dmol.js** draws atoms; **Plotly** draws the chart.
- **FastAPI** handles browser requests; **Pydantic** checks the input format.
- **PyTorch** runs numerical models; **PPO** (Proximal Policy Optimization) is a learning method used here to propose mixtures.
- A **sigmoid gate** maps proposal values between zero and one; **L1 normalization** makes the remaining amounts add up to one.
- **Thermodynamic pre-screening** is a rough check of mixture properties: **mixing enthalpy** estimates the energy change when mixing, **VEC** is the average valence electron count per atom weighted by atomic fractions, and **atomic radius mismatch** compares atom sizes.
- **Deterministic** means the same inputs and starting conditions give the same numbers.
- A **heuristic tensile curve** is a rule-based estimate of how a material responds to stretching.
- **CIF** stores crystal information; **MAT** stores MATLAB data; **PDF** is a readable report.

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

This is a pipeline demonstration. Its property model is not trained on measured
materials data. See [Limitations](#limitations) before interpreting the numbers.

## Folder guide

| Folder / file | Purpose |
| --- | --- |
| `setup.bat` / `setup.sh` | Install everything needed to run the local demo. |
| `start.bat` / `start.sh` | Start both local servers. |
| `backend/app/` | Python code for requests, proposals, screening, estimates, and output files. |
| `backend/tests/` | Checks for the calculation pipeline and server responses. |
| `frontend/src/` | Browser interface, atom viewer, chart, and server connection. |
| `frontend/package.json` | Browser interface dependencies and development commands. |
| `scripts/demo.py` | Run a repeatable example without the browser or a server. |
| `scripts/dev.ps1` | Windows server launcher used by `start.bat`. |
| `docs/` | Place for screenshots, GIFs, and other documentation images. |
| `runtime/artifacts/` | Generated files; Git ignores new run folders. |
| `pyproject.toml` | Python requirements and developer tool settings. |
| `.venv/` | Local Python environment created by setup; not part of the download. |

## Troubleshooting

| Problem | What to try |
| --- | --- |
| Python is not found, or the version is too old | Install Python 3.11+ from python.org. On Windows, enable **Add Python to PATH** and reopen the terminal. On macOS/Linux, check `python3 --version`. |
| Setup or pip installation fails | Read the first error above the final message. Check your internet connection, available disk space, and Python version, then rerun setup. If Linux reports that `venv` is missing, install your distribution's Python venv package (often `python3-venv`). If Node/npm is missing, install Node.js LTS and reopen the terminal. |
| Port 8000 or 5173 is already in use | Stop an earlier AlloyForge window with Ctrl+C, or close the app using that port. Run the launcher again; it will not silently switch ports. |
| A model/package download is slow, or there is no internet | Initial setup downloads large packages, including PyTorch. Let it finish, then rerun setup if interrupted. The default pipeline does not download model weights; once packages are installed, it runs locally without internet. |
| CUDA is not available | CUDA lets supported NVIDIA graphics cards run calculations. A CPU is fine: the app automatically uses it when CUDA is unavailable. You do not need to install CUDA for this demo. |
| The page cannot connect, or `./setup.sh` says permission denied | Keep the launcher running and wait for both servers. Open the exact URL printed above. On macOS/Linux, run `chmod +x setup.sh start.sh` before starting; ZIP downloads may lose executable permissions. |

## For developers

Run commands below from the repository root unless a block explicitly changes
folders. The root setup/start scripts are the recommended route; these are manual
alternatives. Python dependencies are declared in `pyproject.toml`, not a
requirements.txt file.

### Manual installation and servers

Windows / PowerShell, first terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix frontend install
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal at the repository root:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

`npm.cmd` avoids PowerShell's script execution policy restriction on `npm.ps1`.
No Python environment activation is required.

macOS / Linux, first terminal:

```sh
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e '.[dev]'
npm --prefix frontend install
./.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

In a second terminal at the repository root:

```sh
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

For these manual commands, stop each terminal with Ctrl+C.

### Tests and build

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

macOS / Linux:

```sh
./.venv/bin/python -m pytest -q -p no:cacheprovider
npm --prefix frontend run build
```

Tests cover normalization, screening, API errors, artifact creation/downloads,
and repeatable command demo results. Build output in `frontend/dist/` is ignored
by Git. To check setup prerequisites without installing packages, run
`cmd /c .\setup.bat --check` on Windows or `./setup.sh --check` on macOS/Linux.

### API and configuration

The **API**, the routes programs use to talk to the backend, is documented at
<http://127.0.0.1:8000/docs> when the backend is running.
Check its health at <http://127.0.0.1:8000/health>.
Vite (the frontend development server) forwards `/api` and `/health` requests
to the backend.

With the backend running, send a request from another terminal using curl (bash):

```sh
curl -X POST http://127.0.0.1:8000/api/v1/design \
  -H 'Content-Type: application/json' \
  -d '{"targets":{"temperature_c":1000,"density_g_cm3":4.5,"strength_mpa":900},"candidates":32,"allowed_elements":["Ti","Al","V","Cr","Ni","Mo"],"run_physics_engine":true}'
```

Or PowerShell:

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
inputs return HTTP 422. Full request/response schemas are in `/docs`.

Settings live in `backend/app/config.py`. Environment variables use the `ALLOY_`
prefix; a local `.env` file is also supported. Examples include
`ALLOY_ARTIFACT_DIR`, `ALLOY_RANDOM_SEED`, `ALLOY_DEFAULT_CANDIDATES`, and
`ALLOY_MAX_CANDIDATES`. Defaults are 32 candidates and a maximum of 128.
For a separately hosted frontend, set `VITE_API_BASE_URL` at build time and
configure CORS (which browser origins may access the backend) with
`ALLOY_ALLOWED_ORIGINS`, a JSON array such as
`["http://localhost:5173","http://127.0.0.1:5173"]`.

### Output details

| File | Contents |
| --- | --- |
| `alloy.cif` | Illustrative unit cell with composition occupancies; not a relaxed crystal. |
| `simulation.mat` | Element symbols, fractions, strain, stress in GPa, and reward. |
| `report.pdf` | One-page target, composition, screening, property, and tensile summary. |

Only the top candidate gets files. Download them through
`/api/v1/artifacts/<design_id>/<file_name>` or open the run's folder under
`runtime/artifacts/`. Delete old run folders manually when no longer needed.

### Model and integration status

- The default surrogate is a fast deterministic PyTorch model, combining elemental
  heuristics with a fixed-weight neural correction. It is not a trained materials
  predictor and does not run CHGNet. `best_candidate.predictions.engine` (also
  present on each top candidate) reports `pytorch-mvp`.
- PPO samples a batch and performs an update on its rewards. The policy is
  initialized afresh for each request. Training is not persisted, and the update
  does not refine the current batch. This is not a converged optimization system.
- CHGNet, a separate materials prediction model, is not implemented here. The
  optional `quantum` extra only installs dependencies. For developers who need
  those packages, after setup run `.\.venv\Scripts\python.exe -m pip install -e ".[quantum]"`
  on Windows or `./.venv/bin/python -m pip install -e '.[quantum]'` on macOS/Linux.
- LAMMPS, a separate atom simulation program, is not integrated. It needs a
  separate installation, suitable interatomic potentials, and a validated
  simulation workflow. The legacy request flag `run_physics_engine` controls
  **artifact generation only**; `false` still returns surrogate predictions.

## Glossary

- **Alloy:** a mixture of elements that includes a metal.
- **Candidate:** one proposed mixture to compare with your targets.
- **Composition:** the amounts of each element; atomic percentages count atoms, not mass.
- **Density:** mass per volume, shown here in grams per cubic centimetre (g/cm³).
- **Yield strength:** stress at which permanent deformation begins, shown here in megapascals (MPa).
- **Tensile curve:** a chart of stress against strain as a material is stretched.
- **Surrogate:** a quick model used in place of a more expensive calculation.
- **Reward:** the score used to rank a candidate against the selected targets.
- **CPU / GPU:** the computer's main processor / graphics processor.
- **Artifact:** an output file created by a run, such as a PDF report.

## Limitations

This is a portfolio prototype, **not a tool for real metallurgical decisions**.
Screening thresholds and property formulas are illustrative and uncalibrated.
Passing the filter does not prove stability, manufacturability, or performance.
The tensile curve is heuristic, not molecular dynamics (a simulation of atom motion).
The 3D colors do not represent calculated atomic stresses. CIF coordinates are
placeholders, not a physical microstructure. Density is a simple weighted
approximation. Target values also feed the surrogate, so apparent target
agreement is not validation. Results require independent physics calculations
and experimental validation.

The development API has no authentication, rate limits, or artifact retention
policy. It is intended for local use.

## License

[MIT](LICENSE) — Copyright (c) 2026 hasbitas.

## Acknowledgements

Built with FastAPI, Pydantic, PyTorch, NumPy, SciPy, ReportLab, React, Vite,
3Dmol.js, Plotly, and Lucide icons. These projects provide the software tools;
the estimates in this demo are not validated by their maintainers.
