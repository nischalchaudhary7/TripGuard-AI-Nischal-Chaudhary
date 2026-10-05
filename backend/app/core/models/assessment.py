from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.models.airport import Airport
from app.core.models.signal import Signal
from app.core.models.source import SourceCoverage


class ScoreFactor(BaseModel):
    signal_id: str | None = None
    description: str
    contribution: float


class RiskResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str
    verdict: str
    factors: list[ScoreFactor]


class Synthesis(BaseModel):
    summary: str
    main_risks: list[str]
    recommended_actions: list[str]
    confidence_explanation: str = ""
    caveats: list[str] = []
    cited_signal_ids: list[str]
    provider: str = "deterministic"
    fallback_used: bool = True


class Assessment(BaseModel):
    origin: Airport
    destination: Airport
    travel_date: date
    risk: RiskResult
    signals: list[Signal]
    synthesis: Synthesis
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: str
    caveats: list[str]
    source_coverage: list[SourceCoverage]
    last_updated: datetime
