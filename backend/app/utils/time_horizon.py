from datetime import UTC, date, datetime


def days_until_travel(travel_date: date, now: datetime | None = None) -> int:
    current = (now or datetime.now(UTC)).date()
    return (travel_date - current).days


def operational_relevance(travel_date: date, now: datetime | None = None) -> float:
    days = days_until_travel(travel_date, now)
    if days <= 0:
        return 1.0
    if days == 1:
        return 0.85
    if days == 2:
        return 0.55
    if days <= 5:
        return 0.25
    return 0.1


def forecast_relevance(travel_date: date, now: datetime | None = None) -> float:
    days = days_until_travel(travel_date, now)
    if days <= 2:
        return 1.0
    if days <= 4:
        return 0.65
    if days <= 7:
        return 0.35
    return 0.15

