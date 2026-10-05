from datetime import UTC, datetime

from app.core.models.signal import Signal, SignalCategory
from app.core.scoring.risk_score import score_signals


def make_signal(signal_id="s1", severity=0.8, confidence=0.9, evidence="Thunderstorm", source="National Weather Service"):
    return Signal(
        id=signal_id,
        source=source,
        category=SignalCategory.WEATHER_ALERT,
        location="DFW",
        severity=severity,
        confidence=confidence,
        summary="Severe weather near DFW",
        evidence=evidence,
        fetched_at=datetime.now(UTC),
        source_url="https://api.weather.gov",
    )


def test_no_signals_low_risk():
    result = score_signals([])
    assert result.score == 5
    assert result.level == "LOW"


def test_signal_contributes_to_score():
    result = score_signals([make_signal()])
    assert result.score > 30
    assert result.factors[0].signal_id == "s1"


def test_high_risk_override():
    result = score_signals([make_signal(severity=0.9, evidence="Tornado Warning affecting airport")])
    assert result.score >= 85
    assert result.level in {"SEVERE", "HIGH"}


def test_corroboration_bonus_is_single_factor_for_same_underlying_group():
    nws = make_signal(signal_id="nws", source="National Weather Service", severity=0.6)
    awc = make_signal(signal_id="awc", source="Aviation Weather Center", severity=0.6)

    result = score_signals([nws, awc])

    bonus_factors = [
        factor
        for factor in result.factors
        if factor.signal_id is None and "signal" in factor.description.lower()
    ]
    assert len(bonus_factors) == 1
    assert bonus_factors[0].contribution == 10
