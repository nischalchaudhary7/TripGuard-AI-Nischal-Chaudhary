from datetime import UTC, date, datetime
from hashlib import sha1

from app.connectors.base import BaseConnector, ConnectorResult
from app.core.models.airport import Airport
from app.core.models.signal import Signal, SignalCategory
from app.core.models.source import SourceStatus
from app.utils.time_horizon import forecast_relevance, operational_relevance


ALERT_SEVERITY = {
    "Extreme": 1.0,
    "Severe": 0.85,
    "Moderate": 0.55,
    "Minor": 0.25,
    "Unknown": 0.35,
}

FORECAST_KEYWORDS = {
    "tornado": 0.95,
    "blizzard": 0.9,
    "ice storm": 0.85,
    "thunderstorm": 0.65,
    "snow": 0.55,
    "freezing rain": 0.75,
    "fog": 0.45,
    "rain": 0.35,
    "heavy rain": 0.5,
}

PRECIPITATION_WORDS = {"rain", "showers", "thunderstorm", "snow", "freezing rain", "sleet"}


class NWSConnector(BaseConnector):
    source_name = "National Weather Service"
    source_url = "https://api.weather.gov"

    async def fetch(self, airports: list[Airport], travel_date: date) -> ConnectorResult:
        fetched_at = datetime.now(UTC)
        signals: list[Signal] = []
        try:
            for airport in airports:
                signals.extend(await self._alerts_for_airport(airport, travel_date, fetched_at))
                signals.extend(await self._forecast_for_airport(airport, travel_date, fetched_at))
            return ConnectorResult(
                signals=signals,
                coverage=self.coverage(SourceStatus.AVAILABLE, f"Fetched NWS alerts and forecasts for {len(airports)} airports.", fetched_at),
            )
        except Exception as exc:
            return ConnectorResult(
                signals=[],
                coverage=self.coverage(SourceStatus.FAILED, f"NWS request failed: {exc}", fetched_at),
            )

    async def _alerts_for_airport(self, airport: Airport, travel_date: date, fetched_at: datetime) -> list[Signal]:
        url = f"{self.source_url}/alerts/active"
        response = await self.client.get(url, params={"point": self._point(airport)})
        response.raise_for_status()
        features = response.json().get("features", [])
        relevance = operational_relevance(travel_date, fetched_at)
        signals: list[Signal] = []
        for feature in features:
            props = feature.get("properties", {})
            event = props.get("event") or "Weather alert"
            nws_severity = props.get("severity") or "Unknown"
            base = ALERT_SEVERITY.get(nws_severity, 0.35)
            severity = min(1.0, base * max(0.25, relevance))
            sent = props.get("sent") or props.get("effective")
            ends = props.get("ends") or props.get("expires")
            starts_at = self._parse_dt(sent)
            ends_at = self._parse_dt(ends)
            if not self._overlaps_travel_date(starts_at, ends_at, travel_date):
                continue
            raw_id = props.get("id") or f"{airport.iata_code}-{event}-{sent}"
            signals.append(
                Signal(
                    id=self._id("nws-alert", raw_id),
                    source=self.source_name,
                    category=SignalCategory.WEATHER_ALERT,
                    location=airport.iata_code,
                    severity=severity,
                    confidence=0.92 if relevance >= 0.55 else 0.65,
                    summary=f"{event} near {airport.iata_code}",
                    evidence=(props.get("headline") or props.get("description") or event)[:1200],
                    structured_data={
                        "event": event,
                        "severity": nws_severity,
                        "effective": sent or "",
                        "ends": ends or "",
                    },
                    full_evidence=props.get("description"),
                    observed_at=starts_at,
                    expires_at=ends_at,
                    fetched_at=fetched_at,
                    source_url=url,
                )
            )
        return signals

    async def _forecast_for_airport(self, airport: Airport, travel_date: date, fetched_at: datetime) -> list[Signal]:
        point = await self.client.get(f"{self.source_url}/points/{self._point(airport)}")
        point.raise_for_status()
        forecast_url = point.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return []
        forecast = await self.client.get(forecast_url)
        forecast.raise_for_status()
        periods = forecast.json().get("properties", {}).get("periods", [])
        relevant_periods = [period for period in periods if self._period_matches_travel_date(period, travel_date)]
        if not relevant_periods:
            return []
        text = "\n".join(self._format_period(period) for period in relevant_periods)
        lowered = text.lower()
        matched = [(word, score) for word, score in FORECAST_KEYWORDS.items() if word in lowered]
        if not matched:
            return []
        keyword, score = max(matched, key=lambda item: item[1])
        relevance = forecast_relevance(travel_date, fetched_at)
        summary = self._forecast_summary(airport, relevant_periods, keyword)
        return [
            Signal(
                id=self._id("nws-forecast", f"{airport.iata_code}-{travel_date}-{keyword}"),
                source=self.source_name,
                category=SignalCategory.FORECAST,
                location=airport.iata_code,
                severity=min(1.0, score * relevance),
                confidence=0.78 * relevance,
                summary=summary,
                evidence=text[:1200],
                structured_data={
                    "selected_periods": ", ".join(period.get("name", "") for period in relevant_periods if period.get("name")),
                    "travel_date": travel_date.isoformat(),
                    "trigger": keyword,
                },
                full_evidence="\n".join(self._format_period(period) for period in periods),
                observed_at=fetched_at,
                expires_at=None,
                fetched_at=fetched_at,
                source_url=forecast_url,
            )
        ]

    def _id(self, prefix: str, raw: str) -> str:
        return f"{prefix}-{sha1(raw.encode('utf-8')).hexdigest()[:12]}"

    def _point(self, airport: Airport) -> str:
        return f"{airport.latitude:.4f},{airport.longitude:.4f}"

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _period_matches_travel_date(self, period: dict, travel_date: date) -> bool:
        start = self._parse_dt(period.get("startTime"))
        end = self._parse_dt(period.get("endTime"))
        return self._overlaps_travel_date(start, end, travel_date)

    def _overlaps_travel_date(self, start: datetime | None, end: datetime | None, travel_date: date) -> bool:
        if start and end:
            return start.date() <= travel_date <= end.date()
        if start:
            return start.date() == travel_date
        if end:
            return end.date() == travel_date
        return False

    def _format_period(self, period: dict) -> str:
        name = period.get("name") or "Forecast period"
        short = period.get("shortForecast") or ""
        detailed = period.get("detailedForecast") or ""
        start = period.get("startTime") or ""
        end = period.get("endTime") or ""
        probability = period.get("probabilityOfPrecipitation", {}).get("value")
        pop = f" Precipitation chance: {probability}%." if probability is not None else ""
        return f"{name} ({start} to {end}): {short}. {detailed}{pop}".strip()

    def _forecast_summary(self, airport: Airport, periods: list[dict], keyword: str) -> str:
        highest_pop = max(
            (
                period.get("probabilityOfPrecipitation", {}).get("value")
                for period in periods
                if isinstance(period.get("probabilityOfPrecipitation", {}).get("value"), int)
            ),
            default=None,
        )
        period_text = " ".join(
            f"{period.get('shortForecast', '')} {period.get('detailedForecast', '')}".lower()
            for period in periods
        )
        if highest_pop is not None and any(word in period_text for word in PRECIPITATION_WORDS):
            return f"{highest_pop}% chance of precipitation near {airport.iata_code}"
        short_forecasts = [period.get("shortForecast") for period in periods if period.get("shortForecast")]
        if short_forecasts:
            return f"{short_forecasts[0]} near {airport.iata_code}"
        return f"Forecast concern near {airport.iata_code}: {keyword}"
