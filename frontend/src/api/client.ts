import type { Assessment } from "./types";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type AssessmentApiErrorKind = "network" | "invalid_airport" | "server" | "request";

export class AssessmentApiError extends Error {
  kind: AssessmentApiErrorKind;
  status?: number;
  detail?: string;
  cause?: unknown;

  constructor(message: string, kind: AssessmentApiErrorKind, options: { status?: number; detail?: string; cause?: unknown } = {}) {
    super(message);
    this.name = "AssessmentApiError";
    this.kind = kind;
    this.status = options.status;
    this.detail = options.detail;
    this.cause = options.cause;
  }
}

export async function assessTrip(payload: { origin: string; destination: string; travel_date: string }): Promise<Assessment> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/assessments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (err) {
    throw new AssessmentApiError("Unable to reach assessment service.", "network", { cause: err });
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = typeof error.detail === "string" ? error.detail : undefined;
    throw new AssessmentApiError(detail ?? "Assessment failed.", classifyError(response.status, detail), {
      status: response.status,
      detail
    });
  }
  return response.json();
}

function classifyError(status: number, detail?: string): AssessmentApiErrorKind {
  const normalized = (detail ?? "").toLowerCase();
  if (status >= 500) return "server";
  if (status === 400 && normalized.includes("could not resolve")) return "invalid_airport";
  if (status === 422) return "invalid_airport";
  if (normalized.includes("dataset could not be loaded") || normalized.includes("connection") || normalized.includes("timeout")) {
    return "network";
  }
  return "request";
}
