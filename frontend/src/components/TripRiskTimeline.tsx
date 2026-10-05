import { CheckCircle2, Plane, TriangleAlert } from "lucide-react";
import type { Assessment, Airport, Signal } from "../api/types";
import { severityLabel } from "../lib/risk";

export function TripRiskTimeline({ assessment }: { assessment: Assessment }) {
  const byLocation = new Map<string, Signal[]>();
  for (const signal of assessment.signals) {
    byLocation.set(signal.location, [...(byLocation.get(signal.location) ?? []), signal]);
  }

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-ink">Trip risk timeline</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-start">
        <TimelineStop label="Departure" airport={assessment.origin} signals={byLocation.get(assessment.origin.iata_code) ?? []} />
        <div className="flex items-center justify-center py-2 text-indigo-600 md:pt-8">
          <span className="h-px w-16 bg-slate-200 md:w-24" />
          <Plane className="mx-3 h-5 w-5" />
          <span className="h-px w-16 bg-slate-200 md:w-24" />
        </div>
        <TimelineStop label="Arrival" airport={assessment.destination} signals={byLocation.get(assessment.destination.iata_code) ?? []} />
      </div>
    </section>
  );
}

function TimelineStop({ label, airport, signals }: { label: string; airport: Airport; signals: Signal[] }) {
  const topSignals = [...signals].sort((a, b) => b.severity - a.severity).slice(0, 2);
  return (
    <div className="rounded-xl border border-line bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-ink">{airport.iata_code}</div>
      <div className="text-sm text-slate-500">{airport.city ?? airport.name}</div>
      <div className="mt-4 grid gap-2">
        {topSignals.length ? (
          topSignals.map((signal) => (
            <div key={signal.id} className="flex gap-2 rounded-lg bg-white p-3 text-sm">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <div>
                <div className="font-medium text-slate-800">{signal.summary}</div>
                <div className="mt-0.5 text-xs text-slate-500">{severityLabel(signal.severity)} severity</div>
              </div>
            </div>
          ))
        ) : (
          <div className="flex gap-2 rounded-lg bg-white p-3 text-sm text-slate-600">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
            No significant disruption signals detected.
          </div>
        )}
      </div>
    </div>
  );
}
