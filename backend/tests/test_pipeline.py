import math
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scipy.io import loadmat

from app.config import settings
from app.main import app
from app.rl_agent import PPOAlloyAgent
from app.schemas import TargetProperties
from app.thermodynamics import ThermodynamicFilter


def test_logistic_gate_and_l1_normalization() -> None:
    agent = PPOAlloyAgent(["Ti", "Al", "V"], seed=7)
    compositions, _ = agent.sample(TargetProperties(), 8)
    for composition in compositions:
        assert len(composition) >= 2
        assert math.isclose(sum(composition.values()), 1.0, abs_tol=2e-6)


def test_thermodynamic_filter_accepts_ti64() -> None:
    result = ThermodynamicFilter().evaluate({"Ti": 0.8, "Al": 0.15, "V": 0.05})
    assert result.passed
    assert result.mixing_enthalpy_kj_mol < 0
    assert 3 < result.vec < 5
    assert 0 < result.radius_mismatch_pct < 9.5


def test_design_endpoint_returns_pytorch_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "artifact_dir", tmp_path)
    client = TestClient(app)
    response = client.post(
        "/api/v1/design",
        json={
            "targets": {
                "temperature_c": 1000,
                "density_g_cm3": 4.5,
                "strength_mpa": 900,
            },
            "candidates": 8,
            "allowed_elements": ["Ti", "Al", "V"],
            "run_physics_engine": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["framework"] == "pytorch"
    assert payload["policy"].startswith("PPO")
    assert payload["best_candidate"] is not None
    assert payload["best_candidate"]["predictions"]["engine"] == "pytorch-mvp"
    assert payload["artifacts"]["pdf"].endswith("report.pdf")
    design_id = payload["design_id"]
    assert (tmp_path / design_id / "alloy.cif").is_file()
    assert (tmp_path / design_id / "simulation.mat").is_file()
    assert (tmp_path / design_id / "report.pdf").is_file()
    assert (tmp_path / design_id / "alloy.cif").read_text().startswith("data_alloyforge")
    assert (tmp_path / design_id / "report.pdf").read_bytes().startswith(b"%PDF-")
    mat = loadmat(tmp_path / design_id / "simulation.mat")
    assert mat["strain"].shape == mat["stress_gpa"].shape == (1, 41)
    assert math.isclose(float(mat["fractions"].sum()), 1, abs_tol=2e-6)
    for link in payload["artifacts"].values():
        download = client.get(link)
        assert download.status_code == 200
        assert download.content == (tmp_path / design_id / link.rsplit("/", 1)[-1]).read_bytes()


@pytest.mark.parametrize(
    ("elements", "message"),
    [(["Ti", "Xx"], "Unsupported elements: Xx"),
     (["Ti", "ti"], "Select at least two distinct elements.")],
)
def test_invalid_elements_return_english_errors(elements: list[str], message: str) -> None:
    response = TestClient(app).post(
        "/api/v1/design", json={"targets": {}, "allowed_elements": elements}
    )
    assert response.status_code == 422
    assert message in response.text


def test_missing_artifact_returns_english_error() -> None:
    response = TestClient(app).get("/api/v1/artifacts/missing/report.pdf")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."


def test_screening_rejects_radius_mismatch() -> None:
    result = ThermodynamicFilter().evaluate({"Cu": 0.5, "Zr": 0.5})
    assert not result.passed
    assert result.radius_mismatch_pct > 9.5
    assert any("Atomic radius mismatch" in reason for reason in result.reasons)


def test_predictions_without_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "artifact_dir", tmp_path)
    response = TestClient(app).post(
        "/api/v1/design", json={"targets": {}, "candidates": 4, "run_physics_engine": False}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["best_candidate"]["predictions"]["engine"] == "pytorch-mvp"
    assert payload["artifacts"] is None
    assert not list(tmp_path.iterdir())


def test_cli_demo_is_repeatable_and_creates_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]
    command = [sys.executable, str(root / "scripts" / "demo.py")]
    runs = [subprocess.run(command, cwd=root, check=True, capture_output=True, text=True, timeout=120)
            for _ in range(2)]
    # UUID paths differ; all numerical results and engine labels must match.
    summaries = [run.stdout.split("\nGenerated artifacts", 1)[0] for run in runs]
    assert summaries[0] == summaries[1]
    assert "pytorch-mvp" in summaries[0]
    assert "Radius %" in summaries[0]
    for run in runs:
        for line in run.stdout.splitlines():
            if line.startswith(("  CIF:", "  MAT:", "  PDF:")):
                path = root / line.split(": ", 1)[1]
                assert path.is_file() and path.stat().st_size > 0
