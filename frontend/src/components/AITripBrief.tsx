import { Sparkles } from "lucide-react";
import type { Assessment, Signal } from "../api/types";

export function AITripBrief({ assessment }: { assessment: Assessment }) {
  const isAI = assessment.synthesis.provider === "gemini" && assessment.synthesis.fallback_used === false;
  const title = isAI ? "AI Trip Brief" : "Evidence summary";
  const badge = isAI ? `AI-assisted - Grounded in ${assessment.synthesis.cited_signal_ids.length} signals` : "Deterministic summary";
  const citedSignals = assessment.synthesis.cited_signal_ids
    .map((id) => assessment.signals.find((signal) => signal.id === id))
    .filter((signal): signal is Signal => Boolean(signal));
  const evidenceItems = (assessment.synthesis.main_risks.length ? assessment.synthesis.main_risks : citedSignals.map((signal) => signal.summary))
    .map(stripSignalIds)
    .filter(Boolean)
    .slice(0, 3);
  const sourceChips = Array.from(new Set(citedSignals.map(sourceLabel))).slice(0, 4);

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Sparkles className="h-5 w-5 text-indigo-600" />
          {title}
        </h2>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">{badge}</span>
      </div>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">{stripSignalIds(assessment.synthesis.summary)}</p>
      <p className="mt-2 text-xs text-slate-500">AI summarizes the evidence below. It does not determine the risk score.</p>
      {evidenceItems.length ? (
        <div className="mt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Key evidence</div>
          <ul className="mt-2 grid gap-2 text-sm text-slate-700">
            {evidenceItems.map((risk) => (
              <li key={risk} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {sourceChips.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {sourceChips.map((source) => (
            <span key={source} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
              {source}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function stripSignalIds(value: string) {
  return value.replace(/\s*\[[^\]]+\]/g, "").trim();
}

function sourceLabel(signal: Signal) {
  if (signal.source === "National Weather Service") return "NWS";
  if (signal.source === "Aviation Weather Center") return "Aviation Weather";
  if (signal.source === "FAA NAS Status") return "FAA NAS";
  return signal.source;
}
