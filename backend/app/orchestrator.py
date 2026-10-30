from uuid import uuid4

from .artifacts import ArtifactService
from .config import settings
from .domain import ELEMENTS
from .rl_agent import PPOAlloyAgent
from .schemas import (
    ArtifactLinks,
    CandidateSummary,
    DesignRequest,
    DesignResponse,
    PredictedProperties,
)
from .surrogate import TorchSurrogate
from .thermodynamics import ThermodynamicFilter


class AlloyDesignOrchestrator:
    def __init__(self, seed: int | None = None, device: str | None = None) -> None:
        self.filter = ThermodynamicFilter()
        self.seed = seed
        self.device = device

    @staticmethod
    def _reward(predictions: PredictedProperties, request: DesignRequest) -> float:
        targets = request.targets
        density_error = abs(predictions.density_g_cm3 - targets.density_g_cm3) / targets.density_g_cm3
        strength_error = abs(predictions.yield_strength_mpa - targets.strength_mpa) / targets.strength_mpa
        stability_bonus = max(0.0, -predictions.formation_energy_ev_atom) * 8
        return round(12 - 6 * density_error - 8 * strength_error + stability_bonus, 6)

    def design(self, request: DesignRequest) -> DesignResponse:
        unknown = sorted(set(request.allowed_elements) - ELEMENTS.keys())
        if unknown:
            raise ValueError(f"Unsupported elements: {', '.join(unknown)}")

        design_id = uuid4().hex[:12]
        agent = PPOAlloyAgent(request.allowed_elements, seed=self.seed, device=self.device)
        surrogate = TorchSurrogate(request.allowed_elements, device=self.device)
        compositions, rollout = agent.sample(request.targets, request.candidates)
        candidates: list[CandidateSummary] = []
        rewards: list[float] = []
        rejected = 0

        for composition in compositions:
            thermo = self.filter.evaluate(composition)
            if not thermo.passed:
                rewards.append(-100.0)
                rejected += 1
                continue
            prediction = surrogate.predict(composition, request.targets)
            reward = self._reward(prediction, request)
            rewards.append(reward)
            candidates.append(
                CandidateSummary(
                    rank=0,
                    composition=composition,
                    reward=reward,
                    thermodynamics=thermo,
                    predictions=prediction,
                )
            )

        policy_loss = agent.update(rollout, rewards)
        candidates.sort(key=lambda candidate: candidate.reward, reverse=True)
        for rank, candidate in enumerate(candidates[:5], 1):
            candidate.rank = rank

        if not candidates:
            return DesignResponse(
                design_id=design_id,
                status="rejected",
                policy="PPO/ActorCritic (PyTorch)",
                best_candidate=None,
                top_candidates=[],
                rejected_candidates=rejected,
                policy_loss=policy_loss,
                artifacts=None,
                message="All candidates were rejected by the thermodynamic pre-screen.",
            )

        best = candidates[0]
        artifact_links = None
        if request.run_physics_engine:
            artifact_links = ArtifactLinks(
                **ArtifactService(settings.artifact_dir).create(
                    design_id, best, request.targets
                )
            )
        return DesignResponse(
            design_id=design_id,
            status="completed",
            policy="PPO/ActorCritic (PyTorch)",
            best_candidate=best,
            top_candidates=candidates[:5],
            rejected_candidates=rejected,
            policy_loss=policy_loss,
            artifacts=artifact_links,
            message=(
                "Design completed using PyTorch PPO and the MVP surrogate; "
                "CHGNet/LAMMPS and experimental validation are required before production use."
            ),
        )
