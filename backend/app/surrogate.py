from importlib.util import find_spec

import torch
from torch import nn

from .domain import ELEMENTS
from .schemas import PredictedProperties, TargetProperties


class AlloyPropertyNet(nn.Module):
    """Deterministic PyTorch MVP surrogate; no CHGNet inference is performed."""

    def __init__(self, element_count: int) -> None:
        super().__init__()
        self.correction = nn.Sequential(
            nn.Linear(element_count + 3, 32),
            nn.SiLU(),
            nn.Linear(32, 4),
            nn.Tanh(),
        )
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.constant_(module.weight, 0.01)
                nn.init.zeros_(module.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.correction(features)


class TorchSurrogate:
    def __init__(self, elements: list[str], device: str | None = None) -> None:
        self.elements = elements
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = AlloyPropertyNet(len(elements)).to(self.device).eval()
        self.chgnet_available = find_spec("chgnet") is not None and find_spec("pymatgen") is not None

    def predict(
        self,
        composition: dict[str, float],
        targets: TargetProperties,
    ) -> PredictedProperties:
        fractions = torch.tensor(
            [composition.get(element, 0.0) for element in self.elements],
            dtype=torch.float32,
            device=self.device,
        )
        element_density = torch.tensor(
            [ELEMENTS[element].density_g_cm3 for element in self.elements],
            dtype=torch.float32,
            device=self.device,
        )
        melting_points = torch.tensor(
            [ELEMENTS[element].melting_point_c for element in self.elements],
            dtype=torch.float32,
            device=self.device,
        )
        vecs = torch.tensor(
            [ELEMENTS[element].vec for element in self.elements],
            dtype=torch.float32,
            device=self.device,
        )
        density = float(torch.dot(fractions, element_density))
        mean_melting = float(torch.dot(fractions, melting_points))
        vec = float(torch.dot(fractions, vecs))

        input_features = torch.cat(
            (
                fractions,
                torch.tensor(
                    [
                        targets.temperature_c / 1500,
                        targets.density_g_cm3 / 12,
                        targets.strength_mpa / 2500,
                    ],
                    device=self.device,
                ),
            )
        )
        with torch.inference_mode():
            correction = self.model(input_features).cpu()

        active = max(2, len(composition))
        formation_energy = -0.18 - 0.035 * active - 0.015 * vec + float(correction[0]) * 0.1
        young_modulus = 38 + 16 * vec + 0.018 * mean_melting + float(correction[1]) * 8
        thermal_retention = max(0.22, 1 - max(0, targets.temperature_c - 500) / 2800)
        yield_strength = (
            (170 + 64 * active + 0.31 * young_modulus * 10)
            * thermal_retention
            + float(correction[2]) * 80
        )
        max_force = 0.02 + young_modulus / 950 + float(correction[3]) * 0.02
        strain = [round(index * 0.0025, 4) for index in range(41)]
        yield_strain = max(0.006, yield_strength / (young_modulus * 1000))
        stress = []
        for value in strain:
            if value <= yield_strain:
                current = young_modulus * value
            else:
                hardening = 0.10 * young_modulus * (value - yield_strain) ** 0.45
                softening = max(0.55, 1 - max(0, value - 0.075) * 8)
                current = (yield_strength / 1000 + hardening) * softening
            stress.append(round(current, 5))

        return PredictedProperties(
            formation_energy_ev_atom=round(formation_energy, 5),
            density_g_cm3=round(density, 4),
            young_modulus_gpa=round(young_modulus, 3),
            yield_strength_mpa=round(yield_strength, 3),
            max_force_ev_angstrom=round(max_force, 5),
            stress_gpa=stress,
            strain=strain,
            engine="pytorch-mvp",
        )

