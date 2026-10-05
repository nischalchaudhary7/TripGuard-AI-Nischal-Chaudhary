import re
from datetime import UTC, date, datetime
from hashlib import sha1

from app.connectors.base import BaseConnector, ConnectorResult
from app.core.models.airport import Airport
from app.core.models.signal import Signal, SignalCategory
from app.core.models.source import SourceStatus
from app.utils.time_horizon import days_until_travel, operational_relevance


class AviationWeatherConnector(BaseConnector):
    source_name = "Aviation Weather Center"
    source_url = "https://aviationweather.gov/api/data"

    async def fetch(self, airports: list[Airport], travel_date: date) -> ConnectorResult:
        fetched_at = datetime.now(UTC)
        try:
            signals: list[Signal] = []
            for airport in airports:
                station = airport.icao_code or f"K{airport.iata_code}"
                signals.extend(await self._metar(station, airport, travel_date, fetched_at))
                signals.extend(await self._taf(station, airport, travel_date, fetched_at))
            return ConnectorResult(
                signals=signals,
                coverage=self.coverage(SourceStatus.AVAILABLE, "Fetched METAR/TAF data where available.", fetched_at),
            )
        except Exception as exc:
            return ConnectorResult(
                signals=[],
                coverage=self.coverage(SourceStatus.FAILED, f"AWC request failed: {exc}", fetched_at),
            )

    async def _metar(self, station: str, airport: Airport, travel_date: date, fetched_at: datetime) -> list[Signal]:
        url = f"{self.source_url}/metar"
        response = await self.client.get(url, params={"ids": station, "format": "json", "taf": "false"})
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return []
        if travel_date != fetched_at.date():
            return []
        raw = rows[0].get("rawOb") or rows[0].get("raw_text") or str(rows[0])
        severity = self._weather_text_severity(raw) * operational_relevance(travel_date, fetched_at)
        if severity < 0.25:
            return []
        decoded = self._decode_aviation_weather(raw)
        return [self._signal("awc-metar", station, airport, raw, severity, fetched_at, url, decoded, "METAR")]

    async def _taf(self, station: str, airport: Airport, travel_date: date, fetched_at: datetime) -> list[Signal]:
        url = f"{self.source_url}/taf"
        response = await self.client.get(url, params={"ids": station, "format": "json"})
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return []
        row = rows[0]
        if not self._taf_relevant_to_travel_date(row, travel_date):
            return []
        raw = row.get("rawTAF") or row.get("raw_text") or str(row)
        severity = self._weather_text_severity(raw) * max(0.25, operational_relevance(travel_date, fetched_at))
        if severity < 0.25:
            return []
        decoded = self._decode_aviation_weather(raw)
        return [self._signal("awc-taf", station, airport, raw, severity, fetched_at, url, decoded, "TAF")]

    def _signal(
        self,
        prefix: str,
        station: str,
        airport: Airport,
        raw: str,
        severity: float,
        fetched_at: datetime,
        url: str,
        decoded: dict[str, str],
        report_type: str,
    ) -> Signal:
        title = self._title(airport, decoded, report_type)
        return Signal(
            id=f"{prefix}-{sha1((station + raw).encode('utf-8')).hexdigest()[:12]}",
            source=self.source_name,
            category=SignalCategory.AVIATION_WEATHER,
            location=airport.iata_code,
            severity=min(1.0, severity),
            confidence=0.82,
            summary=title,
            evidence=self._evidence(decoded),
            structured_data=decoded,
            raw_data=raw,
            observed_at=fetched_at,
            expires_at=None,
            fetched_at=fetched_at,
            source_url=url,
        )

    def _weather_text_severity(self, text: str) -> float:
        upper = text.upper()
        if any(token in upper for token in ["+TS", "TORNADO", "FC", "SQ"]):
            return 0.9
        if any(token in upper for token in ["TS", "+SN", "FZRA", "BLSN", "LLWS"]):
            return 0.72
        if any(token in upper for token in ["IFR", "LIFR", "FG", "SN", "RA", "G35", "G40"]):
            return 0.5
        if any(token in upper for token in ["MVFR", "BR", "SHRA", "G25", "G30"]):
            return 0.3
        return 0.0

    def _taf_relevant_to_travel_date(self, row: dict, travel_date: date) -> bool:
        starts = self._parse_dt(row.get("validTimeFrom") or row.get("valid_time_from") or row.get("validFrom"))
        ends = self._parse_dt(row.get("validTimeTo") or row.get("valid_time_to") or row.get("validTo"))
        if starts and ends:
            return starts.date() <= travel_date <= ends.date()
        if starts:
            return starts.date() <= travel_date
        if ends:
            return travel_date <= ends.date()
        return days_until_travel(travel_date) <= 1

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        if isinstance(value, int | float):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(timestamp, UTC)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _decode_aviation_weather(self, raw: str) -> dict[str, str]:
        decoded: dict[str, str] = {}
        visibility = re.search(r"\b(P?\d+(?:/\d+)?|\d+\s+\d/\d)SM\b", raw)
        wind = re.search(r"\b(\d{3}|VRB)(\d{2,3})(G\d{2,3})?KT\b", raw)
        ceiling = re.search(r"\b(BKN|OVC|VV)(\d{3})\b", raw)
        weather_tokens = [token for token in re.findall(r"\b[-+]?(?:TS|RA|SN|FZRA|FG|BR|SHRA|BLSN|SQ|FC)\b", raw)]
        conditions = []

        if visibility:
            decoded["visibility"] = visibility.group(0).replace("SM", " statute miles")
        if wind:
            direction = "variable" if wind.group(1) == "VRB" else f"{wind.group(1)} degrees"
            gust = f", gusting {wind.group(3)[1:]} kt" if wind.group(3) else ""
            decoded["wind"] = f"{direction} at {wind.group(2)} kt{gust}"
        if weather_tokens:
            decoded["precipitation_weather"] = ", ".join(dict.fromkeys(weather_tokens))
        if ceiling:
            decoded["cloud_ceiling"] = f"{ceiling.group(1)} at {int(ceiling.group(2)) * 100} ft"
        if any(token in raw.upper() for token in ["IFR", "LIFR"]):
            conditions.append("IFR/LIFR mentioned")
        if "LLWS" in raw.upper():
            conditions.append("low-level wind shear")
        if any(token in raw.upper() for token in ["+TS", "FC", "SQ"]):
            conditions.append("significant convective weather")
        if conditions:
            decoded["important_aviation_conditions"] = ", ".join(conditions)
        return decoded

    def _title(self, airport: Airport, decoded: dict[str, str], report_type: str) -> str:
        ceiling = self._ceiling_feet(decoded.get("cloud_ceiling"))
        if ceiling is not None and ceiling <= 1000:
            return f"Low cloud ceiling reported at {airport.iata_code}"
        if self._visibility_miles(decoded.get("visibility")) is not None and self._visibility_miles(decoded.get("visibility")) < 6:
            return f"Reduced visibility reported at {airport.iata_code}"
        if decoded.get("precipitation_weather"):
            return f"{report_type} reports {decoded['precipitation_weather']} at {airport.iata_code}"
        if decoded.get("wind"):
            return f"Aviation winds reported at {airport.iata_code}"
        return f"{report_type} aviation weather concern at {airport.iata_code}"

    def _evidence(self, decoded: dict[str, str]) -> str:
        if not decoded:
            return "Aviation weather report contains operational weather terms."
        labels = {
            "visibility": "Visibility",
            "wind": "Wind",
            "precipitation_weather": "Weather",
            "cloud_ceiling": "Cloud ceiling",
            "important_aviation_conditions": "Important aviation conditions",
        }
        return "; ".join(f"{labels.get(key, key)}: {value}" for key, value in decoded.items())

    def _visibility_miles(self, value: str | None) -> float | None:
        if not value:
            return None
        token = value.split()[0]
        try:
            if token.startswith("P"):
                token = token[1:]
            if "/" in token:
                numerator, denominator = token.split("/", 1)
                return float(numerator) / float(denominator)
            return float(token)
        except ValueError:
            return None

    def _ceiling_feet(self, value: str | None) -> int | None:
        if not value:
            return None
        match = re.search(r"(\d+) ft", value)
        return int(match.group(1)) if match else None
