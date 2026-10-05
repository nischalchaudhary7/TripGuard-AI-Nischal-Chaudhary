from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.models.airport import Airport
from app.core.models.assessment import Assessment, RiskResult, ScoreFactor, Synthesis
from app.core.models.source import SourceCoverage, SourceStatus
from app.main import app


class FakeAssessmentService:
    def __init__(self, client, settings):
        pass

    async def assess(self, origin, destination, travel_date):
        airport = Airport(
            iata_code="DFW",
            icao_code="KDFW",
            name="Dallas Fort Worth International Airport",
            city="Dallas-Fort Worth",
            region="TX",
            country="US",
            latitude=32.8998,
            longitude=-97.0403,
            source_url="https://ourairports.com",
        )
        return Assessment(
            origin=airport,
            destination=airport,
            travel_date=travel_date,
            risk=RiskResult(score=5, level="LOW", verdict="ok", factors=[ScoreFactor(description="none", contribution=5)]),
            signals=[],
            synthesis=Synthesis(summary="ok", main_risks=[], recommended_actions=[], cited_signal_ids=[]),
            confidence=0.8,
            confidence_label="High",
            caveats=[],
            source_coverage=[SourceCoverage(source="test", status=SourceStatus.AVAILABLE, message="ok")],
            last_updated=datetime.now(UTC),
        )


def test_assessment_response(monkeypatch):
    import app.api.routes.assessments as route

    monkeypatch.setattr(route, "AssessmentService", FakeAssessmentService)
    with TestClient(app) as client:
        response = client.post("/api/assessments", json={"origin": "DFW", "destination": "DEN", "travel_date": "2026-10-03"})
    assert response.status_code == 200
    assert response.json()["risk"]["level"] == "LOW"
