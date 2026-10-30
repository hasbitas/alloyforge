from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TargetProperties(BaseModel):
    temperature_c: float = Field(1000, ge=-200, le=2500)
    density_g_cm3: float = Field(4.5, ge=0.5, le=22)
    strength_mpa: float = Field(900, ge=25, le=5000)


class DesignRequest(BaseModel):
    targets: TargetProperties
    candidates: int = Field(32, ge=4, le=128)
    allowed_elements: list[str] = Field(
        default_factory=lambda: ["Ti", "Al", "V", "Cr", "Ni", "Mo"]
    )
    run_physics_engine: bool = True

    @field_validator("allowed_elements")
    @classmethod
    def validate_elements(cls, elements: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(symbol.strip().title() for symbol in elements))
        if len(cleaned) < 2:
            raise ValueError("Select at least two distinct elements.")
        return cleaned


class ThermodynamicResult(BaseModel):
    passed: bool
    mixing_enthalpy_kj_mol: float
    vec: float
    radius_mismatch_pct: float
    reasons: list[str]


class PredictedProperties(BaseModel):
    formation_energy_ev_atom: float
    density_g_cm3: float
    young_modulus_gpa: float
    yield_strength_mpa: float
    max_force_ev_angstrom: float
    stress_gpa: list[float]
    strain: list[float]
    engine: str


class CandidateSummary(BaseModel):
    rank: int
    composition: dict[str, float]
    reward: float
    thermodynamics: ThermodynamicResult
    predictions: PredictedProperties | None = None


class ArtifactLinks(BaseModel):
    cif: str
    mat: str
    pdf: str


class DesignResponse(BaseModel):
    design_id: str
    status: Literal["completed", "rejected"]
    framework: Literal["pytorch"] = "pytorch"
    policy: str
    best_candidate: CandidateSummary | None
    top_candidates: list[CandidateSummary]
    rejected_candidates: int
    policy_loss: float
    artifacts: ArtifactLinks | None
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    framework: Literal["pytorch"]
    torch_version: str
    cuda_available: bool
    chgnet_available: bool

