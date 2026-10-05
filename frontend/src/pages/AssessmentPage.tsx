import { Activity, AlertCircle } from "lucide-react";
import { useState } from "react";
import { assessTrip } from "../api/client";
import type { Assessment } from "../api/types";
import { AssessmentForm } from "../components/AssessmentForm";
import { ConfidencePanel } from "../components/ConfidencePanel";
import { Recommendations } from "../components/Recommendations";
import { RiskSummary } from "../components/RiskSummary";
import { ScoreExplanation } from "../components/ScoreExplanation";
import { SignalEvidenceList } from "../components/SignalEvidenceList";
import { SourceCoveragePanel } from "../components/SourceCoveragePanel";
import { formatTimestamp } from "../lib/date";

export function AssessmentPage() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runAssessment(payload: { origin: string; destination: string; travel_date: string }) {
    setLoading(true);
    setError(null);
    try {
      setAssessment(await assessTrip(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to assess this trip.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              <Activity className="h-4 w-4" />
              Travel Disruption Intelligence
            </div>
            <h1 className="mt-2 text-3xl font-bold text-ink">TripGuard AI</h1>
          </div>
          {assessment ? (
            <div className="text-sm text-slate-600">
              {assessment.origin.iata_code} to {assessment.destination.iata_code} · Updated {formatTimestamp(assessment.last_updated)}
            </div>
          ) : null}
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-6">
        <AssessmentForm onSubmit={runAssessment} loading={loading} />

        {error ? (
          <div className="flex items-start gap-3 rounded-md border border-red-200 bg-red-50 p-4 text-red-900">
            <AlertCircle className="mt-0.5 h-5 w-5" />
            <div>
              <p className="font-semibold">Assessment failed</p>
              <p className="mt-1 text-sm">{error}</p>
            </div>
          </div>
        ) : null}

        {loading ? (
          <div className="rounded-md border border-line bg-white p-8 text-center shadow-sm">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-ink" />
            <p className="mt-4 font-medium text-slate-700">Checking airport, weather, aviation, and FAA source coverage...</p>
          </div>
        ) : null}

        {assessment ? (
          <>
            <RiskSummary assessment={assessment} />
            <div className="grid gap-5 lg:grid-cols-[1.4fr_0.8fr]">
              <div className="grid gap-5">
                <SignalEvidenceList signals={assessment.signals} />
                <ScoreExplanation assessment={assessment} />
              </div>
              <div className="grid content-start gap-5">
                <Recommendations actions={assessment.synthesis.recommended_actions} />
                <SourceCoveragePanel coverage={assessment.source_coverage} />
                <ConfidencePanel confidence={assessment.confidence} confidenceLabel={assessment.confidence_label} caveats={assessment.caveats} />
              </div>
            </div>
          </>
        ) : (
          !loading && (
            <section className="rounded-md border border-line bg-white p-8 text-center shadow-sm">
              <h2 className="text-xl font-semibold text-ink">Ready for assessment</h2>
              <p className="mt-2 text-slate-600">Enter a U.S. origin, destination, and travel date to collect disruption signals.</p>
            </section>
          )
        )}
      </div>
    </main>
  );
}
