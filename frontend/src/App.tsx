import {
  Atom,
  Box,
  Cpu,
  Download,
  Flame,
  Gauge,
  LoaderCircle,
  Play,
  ShieldCheck,
  Sparkles,
  Weight,
  Zap,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { artifactUrl, createDesign } from "./api";
import { AtomViewer } from "./components/AtomViewer";
import { StressChart } from "./components/StressChart";
import type { DesignResponse, Targets } from "./types";

const ELEMENTS = ["Ti", "Al", "V", "Cr", "Ni", "Mo"];
const COLORS = ["#b8ff65", "#62e8ff", "#ffb657", "#fd7b90", "#b69cff", "#8ce6c2"];

function formatComposition(composition: Record<string, number>) {
  return Object.entries(composition)
    .map(([element, fraction]) => `${element}${(fraction * 100).toFixed(1)}`)
    .join(" · ");
}

export default function App() {
  const [targets, setTargets] = useState<Targets>({
    temperature_c: 1000,
    density_g_cm3: 4.5,
    strength_mpa: 900,
  });
  const [elements, setElements] = useState(ELEMENTS);
  const [candidateCount, setCandidateCount] = useState(32);
  const [result, setResult] = useState<DesignResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const candidate = result?.best_candidate ?? null;
  const circumference = 2 * Math.PI * 43;
  const compositionEntries = useMemo(
    () => Object.entries(candidate?.composition ?? {}),
    [candidate],
  );

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      setResult(await createDesign(targets, candidateCount, elements));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const setTarget = (key: keyof Targets, value: number) => {
    setTargets((current) => ({ ...current, [key]: value }));
  };

  const toggleElement = (element: string) => {
    setElements((current) =>
      current.includes(element)
        ? current.length > 2
          ? current.filter((item) => item !== element)
          : current
        : [...current, element],
    );
  };

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brand-mark"><Atom size={23} /></span>
          <span>ALLOY<span>FORGE</span></span>
        </a>
        <div className="system-status">
          <span className="pulse" />
          PyTorch MVP surrogate
          <span className="status-divider" />
          <Cpu size={14} />
          PPO / MVP
        </div>
      </header>

      <section className="hero">
        <div>
          <div className="eyebrow"><Sparkles size={14} /> AI MATERIALS LAB · MVP 01</div>
          <h1>From atoms to performance,<br /><em>one design cycle.</em></h1>
          <p>
            Set your target properties. A PyTorch PPO agent proposes compositions,
            and a thermodynamic pre-screen filters candidates before surrogate prediction.
          </p>
        </div>
        <div className="pipeline-mini" aria-label="Design pipeline">
          {["PPO", "ΔH + VEC", "SURROGATE", "ARTIFACTS"].map((label, index) => (
            <div className="pipeline-step" key={label}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{label}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="workspace">
        <form className="control-panel panel" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <span className="section-index">01</span>
              <h2>Target properties</h2>
            </div>
            <Gauge size={20} />
          </div>

          <label className="input-group">
            <span><Flame size={16} /> Operating temperature <b>{targets.temperature_c} °C</b></span>
            <input
              type="range"
              min="20"
              max="2000"
              step="10"
              value={targets.temperature_c}
              onChange={(event) => setTarget("temperature_c", Number(event.target.value))}
            />
            <small><i>20 °C</i><i>2000 °C</i></small>
          </label>

          <label className="input-group">
            <span><Weight size={16} /> Target density <b>{targets.density_g_cm3.toFixed(1)} g/cm³</b></span>
            <input
              type="range"
              min="1"
              max="20"
              step="0.1"
              value={targets.density_g_cm3}
              onChange={(event) => setTarget("density_g_cm3", Number(event.target.value))}
            />
            <small><i>1 g/cm³</i><i>20 g/cm³</i></small>
          </label>

          <label className="input-group">
            <span><Zap size={16} /> Yield strength <b>{targets.strength_mpa} MPa</b></span>
            <input
              type="range"
              min="100"
              max="3000"
              step="25"
              value={targets.strength_mpa}
              onChange={(event) => setTarget("strength_mpa", Number(event.target.value))}
            />
            <small><i>100 MPa</i><i>3000 MPa</i></small>
          </label>

          <div className="field-block">
            <div className="field-title">Element space <span>at least 2</span></div>
            <div className="element-grid">
              {ELEMENTS.map((element, index) => (
                <button
                  className={elements.includes(element) ? "element active" : "element"}
                  key={element}
                  type="button"
                  onClick={() => toggleElement(element)}
                  style={{ "--element-color": COLORS[index] } as React.CSSProperties}
                >
                  <small>{index + 13}</small>
                  <strong>{element}</strong>
                </button>
              ))}
            </div>
          </div>

          <label className="candidate-count">
            <span>Candidate pool</span>
            <select value={candidateCount} onChange={(event) => setCandidateCount(Number(event.target.value))}>
              <option value="16">16 — quick</option>
              <option value="32">32 — balanced</option>
              <option value="64">64 — thorough</option>
              <option value="128">128 — extensive</option>
            </select>
          </label>

          <button className="run-button" disabled={loading} type="submit">
            {loading ? <LoaderCircle className="spinner" size={19} /> : <Play size={18} fill="currentColor" />}
            {loading ? "Exploring compositions…" : "Start design"}
          </button>
          {error && <div className="error-message">{error}</div>}
          {result && <p role="status">{result.message}</p>}
        </form>

        <section className="result-area">
          <div className="viewer-card panel">
            <div className="panel-heading compact">
              <div>
                <span className="section-index">02</span>
                <h2>Atomic preview</h2>
              </div>
              <div className="viewer-legend"><span /> Illustrative <span /> unit cell</div>
            </div>
            <div className="viewer-shell">
              <AtomViewer cifPath={result?.artifacts?.cif} />
              <div className="viewer-overlay">
                <span>3D ATOMIC LATTICE</span>
                <strong>{candidate ? formatComposition(candidate.composition) : "Waiting for a design"}</strong>
              </div>
              <div className="axis-gizmo"><b>Z</b><i>Y</i><span>X</span></div>
            </div>
          </div>

          <div className="metric-grid">
            <article className="metric-card panel">
              <div><Box size={18} /><span>Density</span></div>
              <strong>{candidate ? candidate.predictions.density_g_cm3.toFixed(2) : "—"} <small>g/cm³</small></strong>
              <em>{candidate ? `${Math.abs(candidate.predictions.density_g_cm3 - targets.density_g_cm3).toFixed(2)} from target` : "not calculated"}</em>
            </article>
            <article className="metric-card panel">
              <div><Zap size={18} /><span>Young's modulus</span></div>
              <strong>{candidate ? candidate.predictions.young_modulus_gpa.toFixed(1) : "—"} <small>GPa</small></strong>
              <em>{candidate ? candidate.predictions.engine : "surrogate estimate"}</em>
            </article>
            <article className="metric-card panel accent">
              <div><ShieldCheck size={18} /><span>Yield strength</span></div>
              <strong>{candidate ? candidate.predictions.yield_strength_mpa.toFixed(0) : "—"} <small>MPa</small></strong>
              <em>{candidate ? `reward ${candidate.reward.toFixed(2)}` : "PPO result"}</em>
            </article>
          </div>
        </section>
      </section>

      <section className="analysis-grid">
        <article className="panel chart-card">
          <div className="panel-heading compact">
            <div><span className="section-index">03</span><h2>Virtual tensile test</h2></div>
            <span className="tag">HEURISTIC CURVE</span>
          </div>
          {candidate ? (
            <StressChart strain={candidate.predictions.strain} stress={candidate.predictions.stress_gpa} />
          ) : (
            <div className="chart-placeholder">The stress–strain curve will appear here after a design completes.</div>
          )}
        </article>

        <article className="panel composition-card">
          <div className="panel-heading compact">
            <div><span className="section-index">04</span><h2>Proposed composition</h2></div>
            <span className="tag">L1 NORMALIZED</span>
          </div>
          {candidate ? (
            <div className="composition-content">
              <div className="donut">
                <svg viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="43" className="donut-track" />
                  {compositionEntries.map(([element, fraction], index) => {
                    const before = compositionEntries.slice(0, index).reduce((sum, [, value]) => sum + value, 0);
                    return (
                      <circle
                        key={element}
                        cx="50"
                        cy="50"
                        r="43"
                        fill="none"
                        stroke={COLORS[ELEMENTS.indexOf(element)] ?? COLORS[index]}
                        strokeWidth="10"
                        strokeDasharray={`${fraction * circumference} ${circumference}`}
                        strokeDashoffset={-before * circumference}
                        transform="rotate(-90 50 50)"
                      />
                    );
                  })}
                </svg>
                <div><strong>{compositionEntries.length}</strong><span>elements</span></div>
              </div>
              <div className="composition-list">
                {compositionEntries.map(([element, fraction], index) => (
                  <div key={element}>
                    <span style={{ background: COLORS[ELEMENTS.indexOf(element)] ?? COLORS[index] }} />
                    <b>{element}</b>
                    <i>{(fraction * 100).toFixed(2)}%</i>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="chart-placeholder">Elements selected by the sigmoid gate will appear here.</div>
          )}
        </article>

        <article className="panel physics-card">
          <div className="panel-heading compact">
            <div><span className="section-index">05</span><h2>Thermodynamic pre-screen</h2></div>
            <span className={candidate ? "tag pass" : "tag"}>{candidate ? "PASSED" : "WAITING"}</span>
          </div>
          <div className="physics-rows">
            <div>
              <span>Mixing enthalpy, ΔH<sub>mix</sub></span>
              <strong>{candidate ? `${candidate.thermodynamics.mixing_enthalpy_kj_mol.toFixed(2)} kJ/mol` : "—"}</strong>
            </div>
            <div>
              <span>Valence electron concentration</span>
              <strong>{candidate ? candidate.thermodynamics.vec.toFixed(3) : "—"}</strong>
            </div>
            <div>
              <span>Atomic radius mismatch</span>
              <strong>{candidate ? `${candidate.thermodynamics.radius_mismatch_pct.toFixed(3)}%` : "—"}</strong>
            </div>
            <div>
              <span>Rejected candidates</span>
              <strong>{result ? `${result.rejected_candidates} / ${candidateCount}` : "—"}</strong>
            </div>
          </div>
          {result?.artifacts && (
            <div className="downloads">
              {Object.entries(result.artifacts).map(([format, path]) => (
                <a href={artifactUrl(path)} key={format} download>
                  <Download size={14} /> .{format.toUpperCase()}
                </a>
              ))}
            </div>
          )}
        </article>
      </section>

      <footer>
        <span>AlloyForge / PyTorch computational materials lab</span>
        <span>MVP estimates require experimental validation.</span>
      </footer>
    </main>
  );
}

