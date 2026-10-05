import { Activity, AlertCircle, Radar, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { AssessmentApiError, assessTrip } from "../api/client";
import type { Assessment } from "../api/types";
import { AITripBrief } from "../components/AITripBrief";
import { AssessmentForm } from "../components/AssessmentForm";
import { AssessmentLoading } from "../components/AssessmentLoading";
import { ConfidencePanel } from "../components/ConfidencePanel";
import { LiveDataCoverage } from "../components/LiveDataCoverage";
import { Recommendations } from "../components/Recommendations";
import { RiskSummary } from "../components/RiskSummary";
import { RouteSummary } from "../components/RouteSummary";
import { ScoreExplanation } from "../components/ScoreExplanation";
import { SignalGroups } from "../components/SignalGroups";
import { TripRiskTimeline } from "../components/TripRiskTimeline";

type RequestPayload = { origin: string; destination: string; travel_date: string };

export function AssessmentExperience() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<RequestPayload | null>(null);

  async function runAssessment(payload: RequestPayload) {
    setLoading(true);
    setError(null);
    setLastPayload(payload);
    try {
      setAssessment(await assessTrip(payload));
    } catch (err) {
      console.error("TripGuard assessment failed", err);
      setError(friendlyError(err));
    } finally {
      setLoading(false);
    }
  }

  const failedSources = assessment?.source_coverage.filter((source) => source.status === "failed" || source.status === "unavailable") ?? [];

  return (
    <main className="min-h-screen bg-panel text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <div>
              <div className="text-lg font-bold text-ink">TripGuard AI</div>
              <div className="text-sm text-slate-500">Travel Disruption Intelligence</div>
            </div>
          </div>
          <div className="hidden items-center gap-4 text-sm font-medium text-slate-600 sm:flex">
            <span className="inline-flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Live intelligence
            </span>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:py-7">
        <section className="grid gap-4">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-indigo-700">
              <Activity className="h-4 w-4" />
              Travel intelligence
            </div>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-ink md:text-5xl">Know what could disrupt your trip before you leave.</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
              Weather, aviation and airport operational intelligence combined into one evidence-grounded assessment.
            </p>
          </div>
          <AssessmentForm onSubmit={runAssessment} loading={loading} />
        </section>

        {error ? <ErrorState message={error} onRetry={lastPayload ? () => runAssessment(lastPayload) : undefined} /> : null}

        {loading ? <AssessmentLoading /> : null}

        {assessment && !loading ? (
          <div className="grid gap-5">
            {failedSources.length ? (
              <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
                <div>
                  <p className="font-semibold">Some live sources are unavailable.</p>
                  <p className="mt-1 text-sm">This assessment uses the remaining evidence. Review live data coverage below for details.</p>
                </div>
              </div>
            ) : null}

            <RouteSummary assessment={assessment} />
            <div className="grid gap-5 lg:grid-cols-[1fr_360px] lg:items-start">
              <div className="grid gap-5">
                <RiskSummary assessment={assessment} />
                <ScoreExplanation assessment={assessment} />
                <AITripBrief assessment={assessment} />
                <TripRiskTimeline assessment={assessment} />
                <SignalGroups signals={assessment.signals} />
                <LiveDataCoverage coverage={assessment.source_coverage} />
              </div>
              <div className="grid gap-5">
                <Recommendations assessment={assessment} />
                <ConfidencePanel confidence={assessment.confidence} confidenceLabel={assessment.confidence_label} caveats={assessment.caveats} />
              </div>
            </div>
          </div>
        ) : null}

        {!assessment && !loading && !error ? <EmptyState /> : null}
      </div>
    </main>
  );
}

function EmptyState() {
  return (
    <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-ink">Ready to assess your trip</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            TripGuard checks weather, aviation conditions and airport operations to identify potential disruptions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm font-medium text-slate-600">
          <span className="rounded-full bg-slate-100 px-3 py-1">Weather</span>
          <span className="rounded-full bg-slate-100 px-3 py-1">Aviation</span>
          <span className="rounded-full bg-slate-100 px-3 py-1">Airport operations</span>
        </div>
      </div>
    </section>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900">
      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="flex-1">
        <p className="font-semibold">Assessment failed</p>
        <p className="mt-1 text-sm">{message}</p>
      </div>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="inline-flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm font-semibold text-red-900 shadow-sm transition hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500">
          <Radar className="h-4 w-4" />
          Try again
        </button>
      ) : null}
    </div>
  );
}

function friendlyError(err: unknown) {
  if (err instanceof AssessmentApiError) {
    if (err.kind === "network") {
      return "We couldn't reach the TripGuard assessment service.";
    }
    if (err.kind === "invalid_airport") {
      return "We couldn't identify that airport. Try a U.S. IATA code such as DFW, DEN, JFK or LAX.";
    }
    if (err.kind === "server") {
      return "TripGuard couldn't complete this assessment. Please try again.";
    }
    return err.detail ?? "TripGuard couldn't complete this assessment. Please try again.";
  }
  const message = err instanceof Error ? err.message : "Assessment failed.";
  if (message.toLowerCase().includes("failed to fetch") || message.toLowerCase().includes("network")) {
    return "We couldn't reach the TripGuard assessment service.";
  }
  return "TripGuard couldn't complete this assessment. Please try again.";
}
