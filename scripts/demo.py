"""Run the full AlloyForge MVP pipeline without a web server or frontend."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
# Allow running from a source checkout as well as an editable installation.
sys.path.insert(0, str(ROOT / "backend"))

import torch  # noqa: E402

from app.config import settings  # noqa: E402
from app.orchestrator import AlloyDesignOrchestrator  # noqa: E402
from app.schemas import DesignRequest, TargetProperties  # noqa: E402


def main() -> int:
    """Use CPU and a fixed seed; only run IDs and artifact metadata vary."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    settings.artifact_dir = ROOT / "runtime" / "artifacts"
    request = DesignRequest(
        targets=TargetProperties(temperature_c=1000, density_g_cm3=4.5, strength_mpa=900),
        candidates=32,
        allowed_elements=["Ti", "Al", "V", "Cr", "Ni", "Mo"],
        run_physics_engine=True,
    )
    response = AlloyDesignOrchestrator(seed=42, device="cpu").design(request)
    print("AlloyForge CLI demo | seed=42 | device=cpu")
    print("Targets: 1000 C | 4.5 g/cm3 | 900 MPa | 32 candidates")
    print(f"Status: {response.status} | Rejected: {response.rejected_candidates}")
    print(response.message)
    print("\nComposition: atomic percentages. Properties are illustrative MVP estimates.")
    headers = [
        "Rank", "Composition (at.%)", "Density", "Yield MPa", "E GPa",
        "Ef eV/atom", "dH kJ/mol", "VEC", "Radius %", "Reward", "Engine",
    ]
    rows = []
    for candidate in response.top_candidates:
        prediction = candidate.predictions
        if prediction is None:
            raise RuntimeError("A ranked candidate has no predicted properties.")
        thermo = candidate.thermodynamics
        rows.append([
            str(candidate.rank),
            " ".join(f"{symbol}:{fraction * 100:.2f}" for symbol, fraction in candidate.composition.items()),
            f"{prediction.density_g_cm3:.3f}",
            f"{prediction.yield_strength_mpa:.1f}",
            f"{prediction.young_modulus_gpa:.1f}",
            f"{prediction.formation_energy_ev_atom:.4f}",
            f"{thermo.mixing_enthalpy_kj_mol:.3f}",
            f"{thermo.vec:.3f}",
            f"{thermo.radius_mismatch_pct:.3f}",
            f"{candidate.reward:.3f}",
            prediction.engine,
        ])
    widths = [max(len(row[i]) for row in [headers, *rows]) for i in range(len(headers))]
    for row in [headers, ["-" * width for width in widths], *rows]:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths, strict=True)))

    if response.artifacts is None:
        print("No artifacts generated: all candidates failed screening.")
        return 1
    print("\nGenerated artifacts for the top candidate (density in g/cm3):")
    for kind, link in response.artifacts.model_dump().items():
        path = settings.artifact_dir / response.design_id / Path(link).name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty artifact: {path}")
        print(f"  {kind.upper()}: {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
