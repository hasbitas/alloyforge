from dataclasses import dataclass


@dataclass(frozen=True)
class Element:
    symbol: str
    atomic_number: int
    atomic_mass: float
    density_g_cm3: float
    vec: float
    melting_point_c: float
    radius_angstrom: float


ELEMENTS: dict[str, Element] = {
    "Al": Element("Al", 13, 26.982, 2.70, 3, 660, 1.43),
    "Ti": Element("Ti", 22, 47.867, 4.51, 4, 1668, 1.47),
    "V": Element("V", 23, 50.942, 6.11, 5, 1910, 1.34),
    "Cr": Element("Cr", 24, 51.996, 7.19, 6, 1907, 1.28),
    "Fe": Element("Fe", 26, 55.845, 7.87, 8, 1538, 1.26),
    "Co": Element("Co", 27, 58.933, 8.90, 9, 1495, 1.25),
    "Ni": Element("Ni", 28, 58.693, 8.91, 10, 1455, 1.24),
    "Cu": Element("Cu", 29, 63.546, 8.96, 11, 1085, 1.28),
    "Zr": Element("Zr", 40, 91.224, 6.52, 4, 1855, 1.60),
    "Nb": Element("Nb", 41, 92.906, 8.57, 5, 2477, 1.46),
    "Mo": Element("Mo", 42, 95.95, 10.28, 6, 2623, 1.39),
    "Ta": Element("Ta", 73, 180.948, 16.69, 5, 3017, 1.46),
    "W": Element("W", 74, 183.84, 19.25, 6, 3422, 1.39),
}

# MVP approximation for binary mixing enthalpy (kJ/mol).
# Missing pairs are estimated from radius and valence electron differences.
PAIR_ENTHALPY: dict[tuple[str, str], float] = {
    ("Al", "Ti"): -30,
    ("Al", "V"): -16,
    ("Al", "Cr"): -10,
    ("Al", "Ni"): -22,
    ("Al", "Mo"): -5,
    ("Cr", "Ti"): -7,
    ("Cr", "V"): -2,
    ("Cr", "Ni"): -7,
    ("Cr", "Mo"): 0,
    ("Ni", "Ti"): -35,
    ("Ni", "V"): -18,
    ("Mo", "Ti"): -4,
    ("Mo", "V"): 0,
    ("Mo", "Ni"): -7,
    ("Ti", "V"): -2,
}


def pair_enthalpy(left: str, right: str) -> float:
    key = tuple(sorted((left, right)))
    if key in PAIR_ENTHALPY:
        return PAIR_ENTHALPY[key]
    a, b = ELEMENTS[left], ELEMENTS[right]
    radius_mismatch = abs(a.radius_angstrom - b.radius_angstrom)
    vec_mismatch = abs(a.vec - b.vec)
    return round(-18 * radius_mismatch + 0.8 * vec_mismatch, 3)

