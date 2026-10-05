import { ShieldAlert } from "lucide-react";
import type { Assessment } from "../api/types";
import { riskAccent } from "../lib/risk";

export function RiskSummary({ assessment }: { assessment: Assessment }) {
  return (
    <section className={`rounded-2xl border border-l-4 bg-white p-5 shadow-sm ${riskAccent(assessment.risk.level)}`}>
      <div className="grid gap-5 lg:grid-cols-[0.7fr_1fr] lg:items-center">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <ShieldAlert className="h-4 w-4" />
            Overall trip risk
          </div>
          <div className="mt-2 flex flex-wrap items-end gap-3">
            <div className="text-4xl font-bold tracking-tight md:text-5xl">{assessment.risk.level}</div>
            <div className="pb-1 text-2xl font-semibold text-slate-700">{assessment.risk.score} / 100</div>
          </div>
        </div>
        <div>
          <p className="text-base leading-7 text-slate-800">{assessment.risk.verdict}</p>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-slate-700">Confidence:</span>
            <span className="rounded-full border border-line bg-white px-3 py-1 font-semibold text-slate-700">
              {assessment.confidence_label} - {Math.round(assessment.confidence * 100)}%
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
