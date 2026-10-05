from app.core.models.signal import Signal, SignalCategory


HIGH_RISK_TERMS = [
    "airport closure",
    "ground stop",
    "tornado warning",
    "blizzard warning",
    "ice storm warning",
]


def is_high_risk_override(signal: Signal) -> bool:
    text = f"{signal.summary} {signal.evidence}".lower()
    return signal.severity >= 0.85 and any(term in text for term in HIGH_RISK_TERMS)


def category_weight(signal: Signal) -> float:
    if signal.category == SignalCategory.FAA_OPERATIONAL:
        return 1.25
    if signal.category == SignalCategory.WEATHER_ALERT:
        return 1.15
    if signal.category == SignalCategory.AVIATION_WEATHER:
        return 1.0
    if signal.category == SignalCategory.FORECAST:
        return 0.85
    return 0.8

