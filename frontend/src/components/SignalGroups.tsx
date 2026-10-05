import { CloudRain, ExternalLink, Plane, RadioTower, ShieldAlert } from "lucide-react";
import type { Signal } from "../api/types";
import { formatTimestamp, relativeTimestamp } from "../lib/date";
import { severityAccent, severityLabel } from "../lib/risk";

export function SignalGroups({ signals }: { signals: Signal[] }) {
  const sorted = [...signals].sort((a, b) => b.severity - a.severity);
  const grouped = sorted.reduce<Record<string, Signal[]>>((groups, signal) => {
    groups[signal.location] = [...(groups[signal.location] ?? []), signal];
    return groups;
  }, {});

  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">What could affect your trip?</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600">{signals.length} signals</span>
      </div>
      {sorted.length === 0 ? (
        <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No disruption signals were returned by available sources.</div>
      ) : (
        <div className="grid gap-5">
          {Object.entries(grouped).map(([location, items]) => (
            <div key={location}>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700">
                <Plane className="h-3.5 w-3.5" />
                {location} - {items.length}
              </div>
              <div className="grid gap-3">
                {items.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const category = categoryLabel(signal);
  const Icon = signal.category === "AVIATION_WEATHER" ? RadioTower : signal.category === "FORECAST" || signal.category === "WEATHER_ALERT" ? CloudRain : ShieldAlert;
  const title = displayTitle(signal);
  const description = travelerDescription(signal);
  const severity = severityLabel(signal.severity);
  return (
    <article className={`rounded-xl border border-l-4 border-line bg-white p-4 transition hover:shadow-sm ${severityAccent(signal.severity)}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <Icon className="h-4 w-4 text-slate-500" />
            <span>{category}</span>
            <span>{signal.location}</span>
            <span className={severityPill(signal.severity)}>{severity} severity</span>
          </div>
          <h3 className="mt-2 text-base font-semibold text-ink">{title}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>
          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-semibold text-indigo-700">View details</summary>
            <SignalDetails signal={signal} />
          </details>
        </div>
        <a className="inline-flex shrink-0 items-center justify-center gap-1 rounded-lg border border-line px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500" href={signal.source_url} target="_blank" rel="noreferrer">
          View source
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
      <div className="mt-3 text-xs text-slate-500" title={formatTimestamp(signal.fetched_at)}>
        {signal.source} - {relativeTimestamp(signal.fetched_at)}
      </div>
    </article>
  );
}

function SignalDetails({ signal }: { signal: Signal }) {
  const dataEntries = displayDataEntries(signal);
  return (
    <>
      {dataEntries.length ? (
        <dl className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
          {dataEntries.map(([key, value]) => (
              <div key={key} className="rounded-lg bg-slate-50 p-2">
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{key}</dt>
                <dd className="mt-0.5 font-medium text-slate-800">{value}</dd>
              </div>
            ))}
        </dl>
      ) : null}
      {signal.evidence ? (
        <details className="mt-3 text-sm text-slate-600">
          <summary className="cursor-pointer font-semibold text-indigo-700">Evidence details</summary>
          <p className="mt-2 max-w-3xl leading-6">{formatAviationText(signal.evidence)}</p>
        </details>
      ) : null}
      {signal.full_evidence ? (
        <details className="mt-3 text-sm text-slate-600">
          <summary className="cursor-pointer font-semibold text-indigo-700">Full forecast</summary>
          <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 font-sans text-sm leading-6">{signal.full_evidence}</pre>
        </details>
      ) : null}
      {signal.raw_data ? (
        <details className="mt-3 text-sm text-slate-600">
          <summary className="cursor-pointer font-semibold text-indigo-700">Raw METAR/TAF</summary>
          <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs leading-5">{signal.raw_data}</pre>
        </details>
      ) : null}
      <details className="mt-3 text-xs text-slate-500">
        <summary className="cursor-pointer font-medium">Technical details</summary>
        <div className="mt-2 grid gap-1">
          <div>Signal ID {signal.id}</div>
          <div>Category {signal.category}</div>
        </div>
      </details>
    </>
  );
}

function categoryLabel(signal: Signal) {
  if (signal.category === "AVIATION_WEATHER") return signal.id.includes("awc-metar") ? "Current aviation conditions" : "Aviation forecast";
  if (signal.category === "FORECAST") return "Weather forecast";
  if (signal.category === "WEATHER_ALERT") return "Weather alert";
  if (signal.category === "FAA_OPERATIONAL") return "Airport operations";
  return signal.category.replaceAll("_", " ");
}

function displayTitle(signal: Signal) {
  if (signal.category === "AVIATION_WEATHER" && signal.summary.includes("Low cloud ceiling")) {
    return signal.id.includes("awc-metar") ? `Low cloud ceiling observed at ${signal.location}` : `Low cloud ceiling forecast at ${signal.location}`;
  }
  return signal.summary;
}

function travelerDescription(signal: Signal) {
  if (signal.category === "AVIATION_WEATHER") {
    const weather = formatWeatherCodes(signal.structured_data.precipitation_weather);
    const ceiling = formatCloudCeiling(signal.structured_data.cloud_ceiling);
    const visibility = formatVisibility(signal.structured_data.visibility);
    const parts = [weather, ceiling, visibility].filter(Boolean);
    return parts.length ? parts.join(". ") + "." : "Aviation weather may affect airport operations.";
  }
  return shortEvidence(signal.evidence);
}

function shortEvidence(value: string) {
  const firstTwo = value
    .replace(/\s+/g, " ")
    .split(/(?<=\.)\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");
  return firstTwo.length > 240 ? `${firstTwo.slice(0, 237)}...` : firstTwo;
}

function displayDataEntries(signal: Signal): Array<[string, string]> {
  return Object.entries(signal.structured_data ?? {})
    .filter(([, value]) => value)
    .map(([key, value]) => [labelForKey(key), formatStructuredValue(key, value)]);
}

function labelForKey(key: string) {
  return key.replaceAll("_", " ");
}

function formatStructuredValue(key: string, value: string) {
  if (key === "precipitation_weather") return formatWeatherCodes(value);
  if (key === "cloud_ceiling") return formatCloudCeiling(value);
  if (key === "visibility") return formatVisibility(value);
  if (key === "wind") return formatWind(value);
  return value;
}

function formatWeatherCodes(value?: string) {
  if (!value) return "";
  const labels: Record<string, string> = {
    RA: "Rain",
    SHRA: "Rain showers",
    BR: "Mist",
    FG: "Fog",
    TS: "Thunderstorms",
    SN: "Snow",
    FZRA: "Freezing rain",
    BLSN: "Blowing snow"
  };
  return value
    .split(",")
    .map((item) => labels[item.trim()] ?? item.trim())
    .filter(Boolean)
    .join(" and ");
}

function formatCloudCeiling(value?: string) {
  if (!value) return "";
  return value.replace("OVC", "Overcast").replace("BKN", "Broken clouds").replace("VV", "Vertical visibility");
}

function formatVisibility(value?: string) {
  if (!value) return "";
  return value.replace("statute miles", "miles");
}

function formatWind(value?: string) {
  if (!value) return "";
  return value.replace(" degrees at ", " degrees at ");
}

function formatAviationText(value: string) {
  return value
    .replaceAll("Weather: RA", "Weather: Rain")
    .replaceAll("Weather: SHRA, BR", "Weather: Rain showers and mist")
    .replaceAll("Cloud ceiling: OVC", "Cloud ceiling: Overcast")
    .replaceAll("Cloud ceiling: BKN", "Cloud ceiling: Broken clouds")
    .replaceAll("statute miles", "miles");
}

function severityPill(value: number) {
  if (value >= 0.75) return "rounded-full bg-red-50 px-2 py-0.5 text-red-700";
  if (value >= 0.45) return "rounded-full bg-amber-50 px-2 py-0.5 text-amber-800";
  return "rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700";
}
