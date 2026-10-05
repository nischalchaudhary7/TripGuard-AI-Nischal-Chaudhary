import { Gauge } from "lucide-react";

export function ConfidencePanel({ confidence, confidenceLabel, caveats }: { confidence: number; confidenceLabel: string; caveats: string[] }) {
  const tone =
    confidenceLabel === "High"
      ? "text-emerald-700 bg-emerald-50"
      : confidenceLabel === "Medium"
        ? "text-amber-800 bg-amber-50"
        : "text-red-800 bg-red-50";

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
        <Gauge className="h-5 w-5 text-slate-600" />
          <h2 className="text-lg font-semibold text-ink">Assessment confidence</h2>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${tone}`}>{confidenceLabel}</span>
      </div>
      <div className="mt-4 flex items-end gap-2">
        <span className="text-3xl font-bold text-ink">{Math.round(confidence * 100)}%</span>
        <span className="pb-1 text-sm font-medium text-slate-500">confidence</span>
      </div>
      <p aria-hidden="true" className="hidden">
        {Math.round(confidence * 100)}% confidence · {confidenceLabel}
      </p>
      <p className="sr-only">
        {Math.round(confidence * 100)}% confidence - {confidenceLabel}
      </p>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full bg-indigo-600" style={{ width: `${Math.round(confidence * 100)}%` }} />
      </div>
      <ul className="mt-4 grid gap-2 text-sm text-slate-600">
        {caveats.length ? caveats.map((caveat) => <li key={caveat}>{caveat}</li>) : <li>No additional uncertainty notes.</li>}
      </ul>
    </section>
  );
}
