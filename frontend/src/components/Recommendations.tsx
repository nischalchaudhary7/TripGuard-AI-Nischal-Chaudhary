import { CheckCircle2, Check, Copy } from "lucide-react";
import { useState } from "react";
import type { Assessment } from "../api/types";
import { formatTravelDate } from "../lib/date";

type Props = { assessment: Assessment; actions?: never } | { assessment?: never; actions: string[] };

export function Recommendations(props: Props) {
  const [copied, setCopied] = useState(false);
  const assessment = props.assessment;
  const actions = assessment ? assessment.synthesis.recommended_actions : props.actions;

  async function copySummary() {
    if (!assessment) return;
    const signalLines = assessment.signals.length
      ? assessment.signals.map((signal) => `- ${signal.location}: ${signal.summary}`).join("\n")
      : "- No disruption signals returned";
    const actionLines = actions.map((action) => `- ${action}`).join("\n");
    const text = [
      `Trip: ${assessment.origin.iata_code} to ${assessment.destination.iata_code}`,
      `Travel date: ${formatTravelDate(assessment.travel_date)}`,
      `Risk: ${assessment.risk.level} (${assessment.risk.score}/100)`,
      `Confidence: ${assessment.confidence_label} (${Math.round(assessment.confidence * 100)}%)`,
      "",
      "Main disruption signals:",
      signalLines,
      "",
      "Recommended actions:",
      actionLines
    ].join("\n");

    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm lg:sticky lg:top-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Recommended actions</h2>
        {assessment ? (
          <button
            type="button"
            onClick={copySummary}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy summary"}
          </button>
        ) : null}
      </div>
      <div className="mt-4 grid gap-1">
        {actions.map((action) => (
          <div key={action} className="flex gap-3 rounded-lg px-1 py-2 text-sm font-medium text-slate-700">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
            <span>{action}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
