import Plot from "react-plotly.js";

interface StressChartProps {
  strain: number[];
  stress: number[];
}

export function StressChart({ strain, stress }: StressChartProps) {
  return (
    <Plot
      data={[
        {
          x: strain,
          y: stress,
          type: "scatter",
          mode: "lines",
          hovertemplate: "ε %{x:.3f}<br>σ %{y:.3f} GPa<extra></extra>",
          line: { color: "#b8ff65", width: 3, shape: "spline" },
          fill: "tozeroy",
          fillcolor: "rgba(184,255,101,0.08)",
        },
      ]}
      layout={{
        autosize: true,
        height: 275,
        margin: { l: 52, r: 16, t: 14, b: 42 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: "#91a7a1", family: "Inter, sans-serif", size: 11 },
        xaxis: {
          title: { text: "Strain (ε)" },
          gridcolor: "rgba(255,255,255,0.07)",
          zerolinecolor: "rgba(255,255,255,0.1)",
        },
        yaxis: {
          title: { text: "Stress (GPa)" },
          gridcolor: "rgba(255,255,255,0.07)",
          zerolinecolor: "rgba(255,255,255,0.1)",
        },
        showlegend: false,
      }}
      config={{ displayModeBar: false, responsive: true }}
      useResizeHandler
      style={{ width: "100%" }}
    />
  );
}

