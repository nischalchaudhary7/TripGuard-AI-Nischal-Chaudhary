import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import type { SourceCoverage } from "../api/types";
import { formatTimestamp } from "../lib/date";

export function SourceCoveragePanel({ coverage }: { coverage: SourceCoverage[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-ink">Data coverage</h2>
      <div className="grid gap-3">
        {coverage.map((item) => {
          const Icon = item.status === "available" ? CheckCircle2 : item.status === "not_applicable" ? CircleDashed : XCircle;
          return (
            <div key={item.source} className="flex gap-3 rounded-md border border-line p-3">
              <Icon className={`mt-0.5 h-5 w-5 ${item.status === "available" ? "text-emerald-600" : "text-amber-700"}`} />
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-ink">{item.source}</span>
                  <span className="rounded-md bg-panel px-2 py-1 text-xs font-medium uppercase text-slate-600">{item.status.replace("_", " ")}</span>
                </div>
                <p className="mt-1 text-sm text-slate-600">{item.message}</p>
                <p className="mt-1 text-xs text-slate-500">Fetched {formatTimestamp(item.fetched_at)}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

