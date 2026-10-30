export interface Targets {
  temperature_c: number;
  density_g_cm3: number;
  strength_mpa: number;
}

export interface Thermodynamics {
  passed: boolean;
  mixing_enthalpy_kj_mol: number;
  vec: number;
  radius_mismatch_pct: number;
  reasons: string[];
}

export interface Predictions {
  formation_energy_ev_atom: number;
  density_g_cm3: number;
  young_modulus_gpa: number;
  yield_strength_mpa: number;
  max_force_ev_angstrom: number;
  stress_gpa: number[];
  strain: number[];
  engine: string;
}

export interface Candidate {
  rank: number;
  composition: Record<string, number>;
  reward: number;
  thermodynamics: Thermodynamics;
  predictions: Predictions;
}

export interface DesignResponse {
  design_id: string;
  status: "completed" | "rejected";
  framework: "pytorch";
  policy: string;
  best_candidate: Candidate | null;
  top_candidates: Candidate[];
  rejected_candidates: number;
  policy_loss: number;
  artifacts: { cif: string; mat: string; pdf: string } | null;
  message: string;
}

