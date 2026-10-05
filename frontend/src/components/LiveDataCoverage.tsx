import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import type { SourceCoverage } from "../api/types";
import { formatTimestamp, relativeTimestamp } from "../lib/date";

export function LiveDataCoverage({ coverage }: { coverage: SourceCoverage[] }) {
  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-ink">Live data coverage</h2>
      <div className="grid gap-2 md:grid-cols-2">
        {coverage.map((item) => {
          const Icon = item.status === "available" ? CheckCircle2 : item.status === "not_applicable" ? CircleDashed : XCircle;
          return (
            <div key={item.source} className="rounded-xl border border-line p-3">
              <div className="flex gap-3">
                <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${item.status === "available" ? "text-emerald-600" : "text-amber-700"}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-ink">{item.source}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium uppercase text-slate-600">{item.status.replace("_", " ")}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500" title={formatTimestamp(item.fetched_at)}>
                    {relativeTimestamp(item.fetched_at)}
                  </p>
                </div>
              </div>
              <details className="mt-2 text-sm text-slate-600">
                <summary className="cursor-pointer text-xs font-semibold text-indigo-700">Details</summary>
                <p className="mt-2">{item.message}</p>
              </details>
            </div>
          );
        })}
      </div>
    </section>
  );
}
