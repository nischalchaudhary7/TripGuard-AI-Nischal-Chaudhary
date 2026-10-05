import type { RiskLevel } from "../api/types";

export function riskTone(level: RiskLevel) {
  return {
    LOW: "border-emerald-500 bg-emerald-50 text-emerald-800",
    MODERATE: "border-amber-500 bg-amber-50 text-amber-900",
    HIGH: "border-orange-500 bg-orange-50 text-orange-900",
    SEVERE: "border-red-600 bg-red-50 text-red-900"
  }[level];
}

export function riskAccent(level: RiskLevel) {
  return {
    LOW: "border-emerald-500 text-emerald-700 bg-emerald-50",
    MODERATE: "border-amber-500 text-amber-800 bg-amber-50",
    HIGH: "border-orange-500 text-orange-800 bg-orange-50",
    SEVERE: "border-red-600 text-red-800 bg-red-50"
  }[level];
}

export function severityAccent(value: number) {
  if (value >= 0.75) return "border-l-red-600";
  if (value >= 0.45) return "border-l-amber-500";
  return "border-l-emerald-500";
}

export function severityLabel(value: number) {
  if (value >= 0.75) return "High";
  if (value >= 0.45) return "Moderate";
  return "Low";
}
