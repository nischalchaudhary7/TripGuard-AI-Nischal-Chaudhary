import { ArrowRight, CalendarDays, Plane, Repeat2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { localDateOffset } from "../lib/date";

interface Props {
  onSubmit: (payload: { origin: string; destination: string; travel_date: string }) => void;
  loading: boolean;
}

const AIRPORT_HINTS: Record<string, string> = {
  ATL: "Hartsfield-Jackson Atlanta International Airport",
  DEN: "Denver International Airport",
  DFW: "Dallas/Fort Worth International Airport",
  JFK: "John F. Kennedy International Airport",
  LAX: "Los Angeles International Airport",
  MIA: "Miami International Airport",
  ORD: "Chicago O'Hare International Airport",
  SEA: "Seattle-Tacoma International Airport",
  SFO: "San Francisco International Airport"
};

export function AssessmentForm({ onSubmit, loading }: Props) {
  const [origin, setOrigin] = useState("DFW");
  const [destination, setDestination] = useState("DEN");
  const [travelDate, setTravelDate] = useState(() => localDateOffset(0));
  const today = localDateOffset(0);
  const tomorrow = localDateOffset(1);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit({ origin: origin.trim().toUpperCase(), destination: destination.trim().toUpperCase(), travel_date: travelDate });
  }

  function swapRoute() {
    setOrigin(destination);
    setDestination(origin);
  }

  function quickDateClass(value: string) {
    const selected = travelDate === value;
    return `rounded-full border px-3 py-1.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
      selected ? "border-indigo-600 bg-indigo-50 text-indigo-700" : "border-line text-slate-700 hover:bg-slate-50"
    }`;
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-line bg-white p-4 shadow-sm transition-shadow md:p-5">
      <div className="grid gap-3 lg:grid-cols-[1fr_auto_1fr_240px_auto] lg:items-end">
        <AirportField id="origin" label="From" value={origin} onChange={setOrigin} />
        <button
          type="button"
          onClick={swapRoute}
          className="flex h-11 w-11 items-center justify-center rounded-full border border-line bg-white text-slate-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 lg:mb-1"
          aria-label="Swap origin and destination"
          disabled={loading}
        >
          <Repeat2 className="h-4 w-4" />
        </button>
        <AirportField id="destination" label="To" value={destination} onChange={setDestination} />
        <label className="grid gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Date
          <span className="flex min-h-16 items-center gap-3 rounded-xl border border-line bg-slate-50 px-3 focus-within:ring-2 focus-within:ring-indigo-500">
            <CalendarDays className="h-4 w-4 text-indigo-600" />
            <input
              className="h-11 w-full bg-transparent text-base font-semibold text-ink outline-none"
              type="date"
              value={travelDate}
              min={today}
              onChange={(event) => setTravelDate(event.target.value)}
            />
          </span>
        </label>
        <button className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:translate-y-0 disabled:cursor-not-allowed disabled:bg-slate-400" disabled={loading}>
          {loading ? "Assessing" : "Assess trip"}
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={() => setTravelDate(today)} className={quickDateClass(today)} aria-pressed={travelDate === today}>
          Today
        </button>
        <button type="button" onClick={() => setTravelDate(tomorrow)} className={quickDateClass(tomorrow)} aria-pressed={travelDate === tomorrow}>
          Tomorrow
        </button>
      </div>
    </form>
  );
}

function AirportField({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (value: string) => void }) {
  const airportName = AIRPORT_HINTS[value.trim().toUpperCase()] ?? "Use a U.S. IATA code";
  return (
    <label className="grid gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500" htmlFor={id}>
      {label}
      <span className="flex min-h-16 items-center gap-3 rounded-xl border border-line bg-slate-50 px-3 focus-within:ring-2 focus-within:ring-indigo-500">
        <Plane className="h-4 w-4 text-indigo-600" />
        <span className="min-w-0 flex-1">
          <input
            id={id}
            list="airport-suggestions"
            className="h-8 w-full bg-transparent text-xl font-bold uppercase tracking-wide text-ink outline-none"
            maxLength={4}
            value={value}
            onChange={(event) => onChange(event.target.value.toUpperCase())}
          />
          <span className="block truncate text-xs font-medium normal-case tracking-normal text-slate-500">{airportName}</span>
        </span>
      </span>
      <datalist id="airport-suggestions">
        {Object.entries(AIRPORT_HINTS).map(([code, name]) => (
          <option key={code} value={code}>
            {name}
          </option>
        ))}
      </datalist>
    </label>
  );
}
