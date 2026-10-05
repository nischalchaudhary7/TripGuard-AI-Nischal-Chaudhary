from datetime import UTC, datetime

from app.config import Settings
from app.core.models.assessment import RiskResult, ScoreFactor
from app.core.models.signal import Signal, SignalCategory
from app.core.synthesis.ai_synthesizer import AISynthesizer


def make_signal() -> Signal:
    return Signal(
        id="sig-1",
        source="National Weather Service",
        category=SignalCategory.FORECAST,
        location="DFW",
        severity=0.6,
        confidence=0.8,
        summary="60% chance of precipitation near DFW",
        evidence="Showers and thunderstorms likely near the airport.",
        fetched_at=datetime.now(UTC),
        source_url="https://api.weather.gov",
    )


def make_risk() -> RiskResult:
    return RiskResult(
        score=42,
        level="MODERATE",
        verdict="Some disruption risk is present; monitor conditions before departure.",
        factors=[ScoreFactor(signal_id="sig-1", description="weather", contribution=30)],
    )


class FakeGeminiResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class FakeGeminiInteractions:
    def __init__(self, output_text: str | None = None, exc: Exception | None = None):
        self.output_text = output_text
        self.exc = exc
        self.called = False

    def create(self, **kwargs):
        self.called = True
        if self.exc:
            raise self.exc
        return FakeGeminiResponse(self.output_text or "{}")


class FakeGeminiClient:
    def __init__(self, interactions: FakeGeminiInteractions):
        self.interactions = interactions


async def test_gemini_configured_uses_structured_synthesis():
    interactions = FakeGeminiInteractions(
        """
        {
          "concise_verdict": "Moderate disruption risk from forecast storms.",
          "main_risks": [{"description": "Thunderstorms may affect DFW operations.", "signal_ids": ["sig-1"]}],
          "recommended_actions": ["Monitor airline updates."],
          "confidence_explanation": "Confidence reflects one weather signal.",
          "caveats": ["Operational conditions can change."]
        }
        """
    )
    synthesizer = AISynthesizer(
        Settings(ai_provider="gemini", gemini_api_key="test-key"),
        gemini_client=FakeGeminiClient(interactions),
    )

    result = await synthesizer.synthesize(make_risk(), [make_signal()], ["caveat"], confidence=0.7)

    assert interactions.called is True
    assert result.summary == "Moderate disruption risk from forecast storms."
    assert result.cited_signal_ids == ["sig-1"]
    assert "sig-1" in result.main_risks[0]


async def test_missing_gemini_key_uses_deterministic_fallback():
    interactions = FakeGeminiInteractions(exc=AssertionError("Gemini should not be called"))
    synthesizer = AISynthesizer(
        Settings(ai_provider="gemini", gemini_api_key=None),
        gemini_client=FakeGeminiClient(interactions),
    )

    result = await synthesizer.synthesize(make_risk(), [make_signal()], ["caveat"], confidence=0.7)

    assert interactions.called is False
    assert result.summary.startswith("MODERATE risk (42/100)")


async def test_gemini_failure_uses_deterministic_fallback():
    interactions = FakeGeminiInteractions(exc=RuntimeError("rate limited"))
    synthesizer = AISynthesizer(
        Settings(ai_provider="gemini", gemini_api_key="test-key"),
        gemini_client=FakeGeminiClient(interactions),
    )

    result = await synthesizer.synthesize(make_risk(), [make_signal()], ["caveat"], confidence=0.7)

    assert interactions.called is True
    assert result.summary.startswith("MODERATE risk (42/100)")


async def test_invalid_gemini_signal_ids_use_deterministic_fallback():
    interactions = FakeGeminiInteractions(
        """
        {
          "concise_verdict": "Invented claim.",
          "main_risks": [{"description": "Unsupported issue.", "signal_ids": ["missing-signal"]}],
          "recommended_actions": ["Act on unsupported issue."],
          "confidence_explanation": "Invalid.",
          "caveats": []
        }
        """
    )
    synthesizer = AISynthesizer(
        Settings(ai_provider="gemini", gemini_api_key="test-key"),
        gemini_client=FakeGeminiClient(interactions),
    )

    result = await synthesizer.synthesize(make_risk(), [make_signal()], ["caveat"], confidence=0.7)

    assert result.summary.startswith("MODERATE risk (42/100)")
    assert result.cited_signal_ids == ["sig-1"]


async def test_ai_provider_none_uses_deterministic_fallback():
    synthesizer = AISynthesizer(Settings(ai_provider="none", gemini_api_key="test-key"))

    result = await synthesizer.synthesize(make_risk(), [make_signal()], ["caveat"], confidence=0.7)

    assert result.summary.startswith("MODERATE risk (42/100)")
    assert result.confidence_explanation.startswith("Confidence is 70%")
