import type { DesignResponse, Targets } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export async function createDesign(
  targets: Targets,
  candidates: number,
  allowedElements: string[],
): Promise<DesignResponse> {
  const response = await fetch(`${API_BASE}/api/v1/design`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      targets,
      candidates,
      allowed_elements: allowedElements,
      run_physics_engine: true,
    }),
  });

  const body = await response.json();
  if (!response.ok) {
    const message = typeof body.detail === "string" ? body.detail : "Could not generate a design.";
    throw new Error(message);
  }
  return body as DesignResponse;
}

export function artifactUrl(path: string): string {
  return `${API_BASE}${path}`;
}

