export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "SEVERE";

export interface Airport {
  iata_code: string;
  icao_code: string | null;
  name: string;
  city: string | null;
  region: string | null;
  country: string;
  latitude: number;
  longitude: number;
  source_url: string;
}

export interface Signal {
  id: string;
  source: string;
  category: string;
  location: string;
  severity: number;
  confidence: number;
  summary: string;
  evidence: string;
  structured_data: Record<string, string>;
  raw_data: string | null;
  full_evidence: string | null;
  observed_at: string | null;
  expires_at: string | null;
  fetched_at: string;
  source_url: string;
}

export interface SourceCoverage {
  source: string;
  status: "available" | "failed" | "unavailable" | "not_applicable";
  fetched_at: string | null;
  message: string;
  source_url: string | null;
}

export interface Assessment {
  origin: Airport;
  destination: Airport;
  travel_date: string;
  risk: {
    score: number;
    level: RiskLevel;
    verdict: string;
    factors: Array<{ signal_id: string | null; description: string; contribution: number }>;
  };
  signals: Signal[];
  synthesis: {
    summary: string;
    main_risks: string[];
    recommended_actions: string[];
    confidence_explanation: string;
    caveats: string[];
    cited_signal_ids: string[];
    provider: string;
    fallback_used: boolean;
  };
  confidence: number;
  confidence_label: "Low" | "Medium" | "High";
  caveats: string[];
  source_coverage: SourceCoverage[];
  last_updated: string;
}
