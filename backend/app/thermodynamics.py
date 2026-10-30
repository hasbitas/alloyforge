from math import sqrt

from .domain import ELEMENTS, pair_enthalpy
from .schemas import ThermodynamicResult


class ThermodynamicFilter:
    """Fast, explainable pre-screening layer.

    This MVP uses a regular-solution approximation derived from binary alloy
    enthalpies rather than a fully calibrated Miedema model.
    """

    enthalpy_min = -35.0
    enthalpy_max = 8.0
    vec_min = 3.0
    vec_max = 10.5
    radius_mismatch_max_pct = 9.5

    def evaluate(self, composition: dict[str, float]) -> ThermodynamicResult:
        items = [(symbol, fraction) for symbol, fraction in composition.items() if fraction > 0]
        enthalpy = 0.0
        for index, (left, left_fraction) in enumerate(items):
            for right, right_fraction in items[index + 1 :]:
                enthalpy += 4.0 * pair_enthalpy(left, right) * left_fraction * right_fraction

        vec = sum(ELEMENTS[symbol].vec * fraction for symbol, fraction in items)
        mean_radius = sum(ELEMENTS[symbol].radius_angstrom * fraction for symbol, fraction in items)
        mismatch = 100 * sqrt(
            sum(
                fraction * (1 - ELEMENTS[symbol].radius_angstrom / mean_radius) ** 2
                for symbol, fraction in items
            )
        )

        reasons: list[str] = []
        if not self.enthalpy_min <= enthalpy <= self.enthalpy_max:
            reasons.append(
                f"ΔH_mix={enthalpy:.2f} kJ/mol is outside the allowed "
                f"[{self.enthalpy_min}, {self.enthalpy_max}] range."
            )
        if not self.vec_min <= vec <= self.vec_max:
            reasons.append(f"VEC={vec:.2f} is outside the electronic stability range.")
        if mismatch > self.radius_mismatch_max_pct:
            reasons.append(f"Atomic radius mismatch of {mismatch:.2f}% exceeds the screening limit.")
        if len(items) < 2:
            reasons.append("An alloy must contain at least two active elements.")

        return ThermodynamicResult(
            passed=not reasons,
            mixing_enthalpy_kj_mol=round(enthalpy, 4),
            vec=round(vec, 4),
            radius_mismatch_pct=round(mismatch, 4),
            reasons=reasons,
        )

