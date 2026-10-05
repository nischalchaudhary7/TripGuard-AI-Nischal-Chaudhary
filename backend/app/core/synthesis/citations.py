from app.core.models.signal import Signal


def valid_signal_ids(signals: list[Signal], cited_ids: list[str]) -> list[str]:
    allowed = {signal.id for signal in signals}
    return [signal_id for signal_id in cited_ids if signal_id in allowed]

