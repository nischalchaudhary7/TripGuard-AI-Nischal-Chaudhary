from datetime import UTC, date, datetime

from app.config import Settings
from app.connectors.aviation_weather import AviationWeatherConnector
from app.connectors.faa import FAAConnector
from app.connectors.nws import NWSConnector
from app.connectors.ourairports import OurAirportsResolver
from app.core.models.assessment import Assessment
from app.core.models.signal import SignalCategory
from app.core.models.source import SourceCoverage, SourceStatus
from app.core.scoring.risk_score import score_signals
from app.core.synthesis.ai_synthesizer import AISynthesizer
from app.services.airport_resolution import AirportResolutionService
from app.services.signal_collection import SignalCollectionService
from app.utils.time_horizon import days_until_travel


class AssessmentService:
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def assess(self, origin: str, destination: str, travel_date: date) -> Assessment:
        resolver = OurAirportsResolver(self.client, self.settings)
        origin_airport, destination_airport = await AirportResolutionService(resolver).resolve_pair(origin, destination)
        airports = [origin_airport, destination_airport]
        collection = SignalCollectionService(
            [
                NWSConnector(self.client),
                AviationWeatherConnector(self.client),
                FAAConnector(self.client, self.settings),
            ]
        )
        signals, coverage = await collection.collect(airports, travel_date)
        coverage.insert(
            0,
            SourceCoverage(
                source="OurAirports",
                status=SourceStatus.AVAILABLE,
                fetched_at=datetime.now(UTC),
                message="Resolved origin and destination airport metadata.",
                source_url=self.settings.ourairports_csv_url,
            ),
        )
        risk = score_signals(signals)
        caveats = self._caveats(travel_date, coverage)
        confidence = self._confidence(signals, coverage, travel_date)
        confidence_label = self._confidence_label(confidence)
        synthesis = await AISynthesizer(self.settings, self.client).synthesize(
            risk,
            signals,
            caveats,
            origin=origin_airport,
            destination=destination_airport,
            travel_date=travel_date,
            confidence=confidence,
        )
        return Assessment(
            origin=origin_airport,
            destination=destination_airport,
            travel_date=travel_date,
            risk=risk,
            signals=signals,
            synthesis=synthesis,
            confidence=confidence,
            confidence_label=confidence_label,
            caveats=caveats,
            source_coverage=coverage,
            last_updated=datetime.now(UTC),
        )

    def _confidence(self, signals, coverage, travel_date: date) -> float:
        if not coverage:
            return 0.1
        status_scores = {
            SourceStatus.AVAILABLE: 1.0,
            SourceStatus.NOT_APPLICABLE: 0.75,
            SourceStatus.UNAVAILABLE: 0.45,
            SourceStatus.FAILED: 0.25,
        }
        source_score = sum(status_scores[item.status] for item in coverage) / len(coverage)
        if any(
            item.source in {"Aviation Weather Center", "FAA NAS Status"}
            and item.status in {SourceStatus.FAILED, SourceStatus.UNAVAILABLE}
            for item in coverage
        ):
            source_score *= 0.82

        days = days_until_travel(travel_date)
        if days <= 2:
            relevance_score = 1.0
        elif days <= 5:
            relevance_score = 0.82
        elif days <= 7:
            relevance_score = 0.65
        else:
            relevance_score = 0.45

        relevant_signals = [signal for signal in signals if signal.category != SignalCategory.AIRPORT_STATUS]
        signal_score = sum(signal.confidence for signal in relevant_signals) / len(relevant_signals) if relevant_signals else 0.65
        confidence = (source_score * 0.55) + (relevance_score * 0.25) + (signal_score * 0.2)
        if days > 2:
            confidence = min(confidence, 0.79)
        if days > 5:
            confidence = min(confidence, 0.69)
        return round(max(0.1, min(0.95, confidence)), 2)

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "High"
        if confidence >= 0.55:
            return "Medium"
        return "Low"

    def _caveats(self, travel_date: date, coverage) -> list[str]:
        caveats: list[str] = []
        days = days_until_travel(travel_date)
        if days > 2:
            caveats.append("Live operational and METAR data are less predictive for trips more than two days away.")
        if days > 7:
            caveats.append("Forecast and operational confidence is limited beyond a one-week horizon.")
        failed = [item.source for item in coverage if item.status in {SourceStatus.FAILED, SourceStatus.UNAVAILABLE}]
        if failed:
            caveats.append(f"Assessment is limited by unavailable or failed sources: {', '.join(failed)}.")
        return caveats
