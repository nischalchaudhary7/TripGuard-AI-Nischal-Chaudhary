import type { Assessment } from "../api/types";

export function ScoreExplanation({ assessment }: { assessment: Assessment }) {
  const primary = assessment.risk.factors.find((factor) => factor.signal_id);
  const corroboration = assessment.risk.factors.find((factor) => factor.signal_id === null && factor.description.toLowerCase().includes("multiple"));
  const operational = assessment.signals.some((signal) => signal.category === "FAA_OPERATIONAL")
    ? "FAA operational restrictions are included in the score."
    : "None currently detected for the assessed airports.";

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Why this score?</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Risk score: deterministic</span>
      </div>
      <dl className="mt-4 grid gap-0 overflow-hidden rounded-xl border border-line md:grid-cols-2">
        <ScoreItem label="Primary risk driver" value={primary?.description ?? "No active disruption signals"} />
        <ScoreItem label="Supporting evidence" value={`${assessment.signals.length} signals from ${new Set(assessment.signals.map((signal) => signal.source)).size || 0} sources`} />
        <ScoreItem label="Operational restrictions" value={operational} />
        <ScoreItem label="Corroboration" value={corroboration?.description ?? "No additional corroboration bonus applied."} />
      </dl>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-semibold text-indigo-700">View scoring details</summary>
        <div className="mt-3 grid gap-2">
          {assessment.risk.factors.map((factor, index) => (
            <div key={`${factor.signal_id ?? "rule"}-${index}`} className="flex items-start justify-between gap-4 rounded-xl bg-slate-50 p-3">
              <div>
                <p className="font-medium text-slate-800">{factor.description}</p>
                {factor.signal_id ? <p className="mt-1 text-xs text-slate-500">Signal ID {factor.signal_id}</p> : null}
              </div>
              <span className="shrink-0 rounded-lg bg-white px-2 py-1 text-sm font-semibold text-slate-700">+{factor.contribution}</span>
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}

function ScoreItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-line bg-white p-3 last:border-b-0 md:border-r md:even:border-r-0 md:[&:nth-last-child(-n+2)]:border-b-0">
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-800">{value}</dd>
    </div>
  );
}
