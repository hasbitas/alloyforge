from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas
from scipy.io import savemat

from .schemas import CandidateSummary, TargetProperties


class ArtifactService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def create(
        self,
        design_id: str,
        candidate: CandidateSummary,
        targets: TargetProperties,
    ) -> dict[str, str]:
        folder = self.root / design_id
        folder.mkdir(parents=True, exist_ok=True)
        self._write_cif(folder / "alloy.cif", candidate.composition)
        self._write_mat(folder / "simulation.mat", candidate)
        self._write_pdf(folder / "report.pdf", design_id, candidate, targets)
        return {
            "cif": f"/api/v1/artifacts/{design_id}/alloy.cif",
            "mat": f"/api/v1/artifacts/{design_id}/simulation.mat",
            "pdf": f"/api/v1/artifacts/{design_id}/report.pdf",
        }

    @staticmethod
    def _write_cif(path: Path, composition: dict[str, float]) -> None:
        lines = [
            "data_alloyforge",
            "_symmetry_space_group_name_H-M 'P 1'",
            "_cell_length_a 3.200",
            "_cell_length_b 3.200",
            "_cell_length_c 3.200",
            "_cell_angle_alpha 90",
            "_cell_angle_beta 90",
            "_cell_angle_gamma 90",
            "loop_",
            "_atom_site_label",
            "_atom_site_type_symbol",
            "_atom_site_fract_x",
            "_atom_site_fract_y",
            "_atom_site_fract_z",
            "_atom_site_occupancy",
        ]
        positions = [(0, 0, 0), (0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5)]
        for index, (symbol, fraction) in enumerate(composition.items()):
            x, y, z = positions[index % len(positions)]
            lines.append(f"{symbol}{index + 1} {symbol} {x} {y} {z} {fraction:.6f}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _write_mat(path: Path, candidate: CandidateSummary) -> None:
        predictions = candidate.predictions
        savemat(
            path,
            {
                "elements": list(candidate.composition),
                "fractions": list(candidate.composition.values()),
                "strain": predictions.strain if predictions else [],
                "stress_gpa": predictions.stress_gpa if predictions else [],
                "reward": candidate.reward,
            },
        )

    @staticmethod
    def _write_pdf(
        path: Path,
        design_id: str,
        candidate: CandidateSummary,
        targets: TargetProperties,
    ) -> None:
        buffer = BytesIO()
        pdf = Canvas(buffer, pagesize=A4)
        width, height = A4
        pdf.setTitle(f"AlloyForge Report - {design_id}")
        ink = HexColor("#101815")
        muted = HexColor("#66756F")
        line = HexColor("#DDE6E2")
        acid = HexColor("#9BDD55")
        cyan = HexColor("#36B8CB")
        paper = HexColor("#F5F8F6")
        pdf.setFillColor(paper)
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

        # Header
        pdf.setFillColor(HexColor("#101A17"))
        pdf.rect(0, height - 150, width, 150, fill=1, stroke=0)
        pdf.setFillColor(acid)
        pdf.roundRect(42, height - 62, 31, 31, 7, fill=1, stroke=0)
        pdf.setFillColor(HexColor("#101A17"))
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(57.5, height - 52, "A")
        pdf.setFillColor(HexColor("#F3FAF7"))
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(86, height - 49, "AlloyForge")
        pdf.setFillColor(acid)
        pdf.drawString(86, height - 74, "Design Report")
        pdf.setFillColor(HexColor("#8EA29B"))
        pdf.setFont("Helvetica", 8)
        pdf.drawString(42, height - 111, f"DESIGN ID  /  {design_id.upper()}")
        pdf.drawRightString(width - 42, height - 111, "PYTORCH PPO  /  MVP 01")
        pdf.setStrokeColor(HexColor("#32413C"))
        pdf.line(42, height - 125, width - 42, height - 125)

        # Target cards
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(42, 670, "TARGET PROPERTIES")
        target_cards = [
            ("TEMPERATURE", f"{targets.temperature_c:.0f}", "C"),
            ("DENSITY", f"{targets.density_g_cm3:.2f}", "g/cm3"),
            ("STRENGTH", f"{targets.strength_mpa:.0f}", "MPa"),
        ]
        card_width = (width - 100) / 3
        for index, (label, value, unit) in enumerate(target_cards):
            x = 42 + index * (card_width + 8)
            pdf.setFillColor(HexColor("#EAF0ED"))
            pdf.roundRect(x, 600, card_width, 56, 5, fill=1, stroke=0)
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica-Bold", 6.5)
            pdf.drawString(x + 12, 638, label)
            pdf.setFillColor(ink)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(x + 12, 615, value)
            value_width = pdf.stringWidth(value, "Helvetica-Bold", 16)
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica", 7)
            pdf.drawString(x + 16 + value_width, 617, unit)

        # Composition and physics
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(42, 574, "PROPOSED COMPOSITION")
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawRightString(350, 574, "SIGMOID GATE + L1 NORMALIZATION")
        bar_colors = [acid, cyan, HexColor("#F3A74B"), HexColor("#E56E83"), HexColor("#8C7BD5")]
        for index, (symbol, fraction) in enumerate(candidate.composition.items()):
            y = 548 - index * 20
            pdf.setFillColor(ink)
            pdf.setFont("Helvetica-Bold", 7.5)
            pdf.drawString(42, y, symbol)
            pdf.setFillColor(HexColor("#E1E8E5"))
            pdf.roundRect(68, y - 2, 215, 7, 3.5, fill=1, stroke=0)
            pdf.setFillColor(bar_colors[index % len(bar_colors)])
            pdf.roundRect(68, y - 2, max(4, 215 * fraction), 7, 3.5, fill=1, stroke=0)
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica", 7)
            pdf.drawRightString(348, y, f"{fraction * 100:.2f}%")

        pdf.setFillColor(HexColor("#EAF0ED"))
        pdf.roundRect(372, 430, width - 414, 125, 5, fill=1, stroke=0)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(385, 536, "PRE-SCREEN")
        pdf.setFillColor(acid)
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawRightString(width - 55, 536, "PASSED")
        filter_rows = [
            ("Mixing enthalpy", f"{candidate.thermodynamics.mixing_enthalpy_kj_mol:.3f} kJ/mol"),
            ("Valence electron concentration", f"{candidate.thermodynamics.vec:.3f}"),
            ("Radius mismatch", f"{candidate.thermodynamics.radius_mismatch_pct:.3f}%"),
            ("PPO reward", f"{candidate.reward:.3f}"),
        ]
        for index, (label, value) in enumerate(filter_rows):
            y = 512 - index * 21
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica", 6.5)
            pdf.drawString(385, y, label)
            pdf.setFillColor(ink)
            pdf.setFont("Helvetica-Bold", 7)
            pdf.drawRightString(width - 55, y, value)

        # Mechanical metrics
        predictions = candidate.predictions
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(42, 414, "SURROGATE + VIRTUAL TENSILE TEST")
        pdf.setFont("Helvetica", 6.5)
        pdf.drawRightString(width - 42, 414, predictions.engine if predictions else "No prediction")
        metrics = [
            ("DENSITY", f"{predictions.density_g_cm3:.2f}" if predictions else "-", "g/cm3"),
            ("YOUNG'S MODULUS", f"{predictions.young_modulus_gpa:.1f}" if predictions else "-", "GPa"),
            ("YIELD STRENGTH", f"{predictions.yield_strength_mpa:.0f}" if predictions else "-", "MPa"),
            ("FORMATION ENERGY", f"{predictions.formation_energy_ev_atom:.3f}" if predictions else "-", "eV/atom"),
        ]
        metric_width = (width - 108) / 4
        for index, (label, value, unit) in enumerate(metrics):
            x = 42 + index * (metric_width + 8)
            pdf.setStrokeColor(line)
            pdf.setLineWidth(0.7)
            pdf.roundRect(x, 342, metric_width, 55, 4, fill=0, stroke=1)
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica-Bold", 5.8)
            pdf.drawString(x + 9, 381, label)
            pdf.setFillColor(ink if index != 2 else HexColor("#47871D"))
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x + 9, 359, value)
            value_width = pdf.stringWidth(value, "Helvetica-Bold", 12)
            pdf.setFillColor(muted)
            pdf.setFont("Helvetica", 5.8)
            pdf.drawString(x + 12 + value_width, 361, unit)

        # Stress-strain chart
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(42, 308, "STRESS - STRAIN CURVE")
        chart_left, chart_bottom, chart_width, chart_height = 62, 90, width - 104, 188
        pdf.setStrokeColor(line)
        pdf.setLineWidth(0.5)
        for step in range(5):
            y = chart_bottom + step * chart_height / 4
            pdf.line(chart_left, y, chart_left + chart_width, y)
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 6)
        pdf.drawString(42, chart_bottom + chart_height - 2, "GPa")
        pdf.drawRightString(chart_left + chart_width, chart_bottom - 14, "Strain")
        if predictions and predictions.strain and predictions.stress_gpa:
            max_strain = max(predictions.strain) or 1
            max_stress = max(predictions.stress_gpa) or 1
            path_line = pdf.beginPath()
            for index, (strain, stress) in enumerate(
                zip(predictions.strain, predictions.stress_gpa, strict=True)
            ):
                x = chart_left + strain / max_strain * chart_width
                y = chart_bottom + stress / max_stress * chart_height
                if index == 0:
                    path_line.moveTo(x, y)
                else:
                    path_line.lineTo(x, y)
            pdf.setStrokeColor(HexColor("#70B82E"))
            pdf.setLineWidth(2)
            pdf.drawPath(path_line, fill=0, stroke=1)

        pdf.setFillColor(muted)
        pdf.setFont("Helvetica-Oblique", 6.5)
        pdf.drawString(
            42,
            36,
            "MVP estimate only. Not for engineering certification or production decisions.",
        )
        pdf.setFont("Helvetica", 6.5)
        pdf.drawRightString(width - 42, 36, "ALLOYFORGE  /  1 OF 1")
        pdf.save()
        path.write_bytes(buffer.getvalue())
