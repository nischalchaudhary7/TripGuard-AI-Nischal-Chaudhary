import { AlertTriangle, ExternalLink } from "lucide-react";
import type { Signal } from "../api/types";
import { formatTimestamp } from "../lib/date";
import { severityLabel } from "../lib/risk";

export function SignalEvidenceList({ signals }: { signals: Signal[] }) {
  const sorted = [...signals].sort((a, b) => b.severity - a.severity);
  return (
    <section className="rounded-md border border-line bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Top disruption signals</h2>
        <span className="rounded-md bg-panel px-2 py-1 text-sm text-slate-600">{signals.length} signals</span>
      </div>
      {sorted.length === 0 ? (
        <p className="text-sm text-slate-600">No disruption signals were returned by available sources.</p>
      ) : (
        <div className="grid gap-3">
          {sorted.map((signal) => (
            <article key={signal.id} className="rounded-md border border-line p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <span className="font-semibold text-ink">{signal.category.replaceAll("_", " ")}</span>
                    <span className="rounded-md bg-panel px-2 py-1 text-xs font-medium text-slate-700">{signal.location}</span>
                    <span className="rounded-md bg-panel px-2 py-1 text-xs font-medium text-slate-700">{severityLabel(signal.severity)} severity</span>
                  </div>
                  <p className="mt-2 font-medium text-slate-800">{signal.summary}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{signal.evidence}</p>
                  {Object.keys(signal.structured_data ?? {}).length ? (
                    <dl className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                      {Object.entries(signal.structured_data)
                        .filter(([, value]) => value)
                        .map(([key, value]) => (
                          <div key={key}>
                            <dt className="text-xs font-semibold uppercase text-slate-500">{key.replaceAll("_", " ")}</dt>
                            <dd>{value}</dd>
                          </div>
                        ))}
                    </dl>
                  ) : null}
                  {signal.full_evidence ? (
                    <details className="mt-3 text-sm text-slate-600">
                      <summary className="cursor-pointer font-medium text-slate-700">Full forecast</summary>
                      <pre className="mt-2 whitespace-pre-wrap rounded-md bg-panel p-3 font-sans text-sm leading-6">{signal.full_evidence}</pre>
                    </details>
                  ) : null}
                  {signal.raw_data ? (
                    <details className="mt-3 text-sm text-slate-600">
                      <summary className="cursor-pointer font-medium text-slate-700">Raw data</summary>
                      <pre className="mt-2 whitespace-pre-wrap rounded-md bg-panel p-3 text-xs leading-5">{signal.raw_data}</pre>
                    </details>
                  ) : null}
                </div>
                <a className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-slate-700 underline" href={signal.source_url} target="_blank" rel="noreferrer">
                  {signal.source}
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
              <div className="mt-3 text-xs text-slate-500">
                Signal ID {signal.id} · fetched {formatTimestamp(signal.fetched_at)}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
