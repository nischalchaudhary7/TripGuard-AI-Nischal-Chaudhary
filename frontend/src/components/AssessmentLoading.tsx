import { Circle } from "lucide-react";
import { useEffect, useState } from "react";

const STAGES = [
  "Resolving airports",
  "Checking weather",
  "Checking aviation conditions",
  "Checking airport operations",
  "Evaluating disruption signals",
  "Preparing trip brief"
];

export function AssessmentLoading() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => setActive((value) => (value + 1) % STAGES.length), 1400);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <section className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
      <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-ink">Preparing assessment</h2>
        <p className="mt-1 text-sm text-slate-600">TripGuard is collecting live evidence and evaluating it against your travel date.</p>
        <div className="mt-5 grid gap-3">
          {STAGES.map((stage, index) => (
            <div key={stage} className={`flex items-center gap-3 text-sm ${index === active ? "font-semibold text-indigo-700" : "text-slate-600"}`}>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full ${index === active ? "bg-indigo-600 text-white" : "bg-indigo-50 text-indigo-300"}`}>
                <Circle className="h-2.5 w-2.5 fill-current" />
              </span>
              {index === active ? `${stage}...` : stage}
            </div>
          ))}
        </div>
      </div>
      <div className="grid gap-4">
        <div className="h-40 animate-pulse rounded-2xl border border-line bg-white p-5 shadow-sm">
          <div className="h-4 w-32 rounded bg-slate-200" />
          <div className="mt-6 h-9 w-48 rounded bg-slate-200" />
          <div className="mt-4 h-4 w-3/4 rounded bg-slate-200" />
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="h-32 animate-pulse rounded-2xl border border-line bg-white shadow-sm" />
          <div className="h-32 animate-pulse rounded-2xl border border-line bg-white shadow-sm" />
        </div>
      </div>
    </section>
  );
}
