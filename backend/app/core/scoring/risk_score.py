from collections import Counter

from app.core.models.assessment import RiskResult, ScoreFactor
from app.core.models.signal import Signal
from app.core.scoring.rules import category_weight, is_high_risk_override


def risk_level(score: int) -> str:
    if score >= 85:
        return "SEVERE"
    if score >= 65:
        return "HIGH"
    if score >= 35:
        return "MODERATE"
    return "LOW"


def score_signals(signals: list[Signal]) -> RiskResult:
    if not signals:
        return RiskResult(
            score=5,
            level="LOW",
            verdict="No disruption signals were found from available sources.",
            factors=[ScoreFactor(description="No active disruption signals", contribution=5)],
        )

    factors: list[ScoreFactor] = []
    weighted = []
    for signal in sorted(signals, key=lambda item: item.severity, reverse=True):
        contribution = signal.severity * signal.confidence * category_weight(signal) * 45
        weighted.append(contribution)
        factors.append(
            ScoreFactor(
                signal_id=signal.id,
                description=f"{signal.source}: {signal.summary}",
                contribution=round(contribution, 1),
            )
        )

    score = min(100, int(round(sum(weighted[:5]))))
    location_counts = Counter(signal.location for signal in signals if signal.severity >= 0.4)
    source_counts = Counter(signal.source for signal in signals if signal.severity >= 0.4)

    same_airport = any(count >= 2 for count in location_counts.values())
    multiple_sources = len(source_counts) >= 2
    if same_airport or multiple_sources:
        if same_airport and multiple_sources:
            bonus = 10
            description = "Multiple sources report relevant signals affecting the same airport"
        elif multiple_sources:
            bonus = 7
            description = "Risk is supported by signals from multiple sources"
        else:
            bonus = 6
            description = "Multiple relevant signals affect the same airport"
        score = min(100, score + bonus)
        factors.append(ScoreFactor(description=description, contribution=bonus))

    if any(is_high_risk_override(signal) for signal in signals):
        score = max(score, 85)
        factors.append(ScoreFactor(description="High-risk override triggered by a severe event", contribution=85))

    level = risk_level(score)
    verdict = {
        "LOW": "Normal travel risk based on currently available signals.",
        "MODERATE": "Some disruption risk is present; monitor conditions before departure.",
        "HIGH": "Significant disruption risk is present; prepare alternate plans.",
        "SEVERE": "Severe disruption risk is present; confirm operations before traveling.",
    }[level]
    return RiskResult(score=score, level=level, verdict=verdict, factors=factors)
