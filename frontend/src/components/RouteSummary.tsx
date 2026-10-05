import { Plane } from "lucide-react";
import type { Assessment } from "../api/types";
import { formatTravelDate, relativeTimestamp } from "../lib/date";

export function RouteSummary({ assessment }: { assessment: Assessment }) {
  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr] md:items-center">
        <AirportBlock code={assessment.origin.iata_code} name={assessment.origin.name} city={assessment.origin.city} align="left" />
        <div className="flex items-center justify-center gap-3 text-indigo-600">
          <span className="h-px w-16 bg-slate-200 md:w-28" />
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-50">
            <Plane className="h-4 w-4" />
          </span>
          <span className="h-px w-16 bg-slate-200 md:w-28" />
        </div>
        <AirportBlock code={assessment.destination.iata_code} name={assessment.destination.name} city={assessment.destination.city} align="right" />
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-3 text-sm text-slate-600">
        <span className="font-medium text-ink">{formatTravelDate(assessment.travel_date)}</span>
        <span title={assessment.last_updated}>{relativeTimestamp(assessment.last_updated)}</span>
      </div>
    </section>
  );
}

function AirportBlock({ code, name, city, align }: { code: string; name: string; city: string | null; align: "left" | "right" }) {
  return (
    <div className={align === "right" ? "text-left md:text-right" : ""}>
      <div className="text-4xl font-bold tracking-wide text-ink">{code}</div>
      <div className="mt-1 font-semibold text-slate-800">{city ?? name}</div>
      <div className="mt-0.5 truncate text-sm text-slate-500">{name}</div>
    </div>
  );
}
