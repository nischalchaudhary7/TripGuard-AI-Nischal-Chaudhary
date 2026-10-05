from datetime import UTC, date, datetime
from hashlib import sha1
import xml.etree.ElementTree as ET

from app.config import Settings
from app.connectors.base import BaseConnector, ConnectorResult
from app.core.models.airport import Airport
from app.core.models.signal import Signal, SignalCategory
from app.core.models.source import SourceStatus
from app.utils.time_horizon import operational_relevance


class FAAConnector(BaseConnector):
    source_name = "FAA NAS Status"
    source_url = "https://nasstatus.faa.gov/"

    def __init__(self, client, settings: Settings):
        super().__init__(client)
        self.settings = settings

    async def fetch(self, airports: list[Airport], travel_date: date) -> ConnectorResult:
        fetched_at = datetime.now(UTC)
        if not self.settings.faa_nas_status_url:
            return ConnectorResult(
                signals=[],
                coverage=self.coverage(
                    SourceStatus.UNAVAILABLE,
                    "No stable documented FAA NAS JSON endpoint is configured; FAA operational data was not fabricated.",
                    fetched_at,
                ),
            )
        try:
            response = await self.client.get(self.settings.faa_nas_status_url)
            response.raise_for_status()
            signals = self._parse_airport_status(response.text, airports, travel_date, fetched_at)
            return ConnectorResult(
                signals=signals,
                coverage=self.coverage(
                    SourceStatus.AVAILABLE,
                    f"Fetched FAA NAS Status XML and found {len(signals)} relevant airport events.",
                    fetched_at,
                ),
            )
        except Exception as exc:
            return ConnectorResult(
                signals=[],
                coverage=self.coverage(SourceStatus.FAILED, f"Configured FAA endpoint failed: {exc}", fetched_at),
            )

    def _parse_airport_status(
        self,
        xml_text: str,
        airports: list[Airport],
        travel_date: date,
        fetched_at: datetime,
    ) -> list[Signal]:
        root = ET.fromstring(xml_text)
        wanted = {airport.iata_code for airport in airports}
        signals: list[Signal] = []
        relevance = operational_relevance(travel_date, fetched_at)
        if relevance < 0.5:
            return []

        for delay_type in root.findall(".//Delay_type"):
            event_type = self._text(delay_type.find("Name")) or "FAA airport event"
            for airport_node in delay_type.findall(".//Airport"):
                code = self._text(airport_node.find("ARPT"))
                if code not in wanted:
                    continue
                reason = self._text(airport_node.find("Reason"))
                start = self._text(airport_node.find("Start"))
                end = self._text(airport_node.find("End"))
                avg_delay = self._text(airport_node.find("Avg"))
                scope = self._text(airport_node.find("Scope"))
                evidence_parts = [part for part in [avg_delay, reason, scope, start, end] if part]
                evidence = "; ".join(evidence_parts) or event_type
                severity = self._severity(event_type, evidence) * relevance
                if severity < 0.25:
                    continue
                raw = ET.tostring(airport_node, encoding="unicode")
                signals.append(
                    Signal(
                        id=f"faa-nas-{sha1((code + event_type + evidence).encode('utf-8')).hexdigest()[:12]}",
                        source=self.source_name,
                        category=SignalCategory.FAA_OPERATIONAL,
                        location=code,
                        severity=min(1.0, severity),
                        confidence=0.9,
                        summary=f"{event_type} reported at {code}",
                        evidence=evidence[:1200],
                        structured_data={
                            "event": event_type,
                            "airport": code,
                            "average_delay": avg_delay,
                            "reason": reason,
                            "scope": scope,
                            "start": start,
                            "end": end,
                        },
                        raw_data=raw,
                        observed_at=fetched_at,
                        fetched_at=fetched_at,
                        source_url=self.settings.faa_nas_status_url or self.source_url,
                    )
                )
        return signals

    def _text(self, node) -> str:
        return (node.text or "").strip() if node is not None else ""

    def _severity(self, event_type: str, evidence: str) -> float:
        text = f"{event_type} {evidence}".lower()
        if "ground stop" in text or "airport closure" in text:
            return 0.9
        if "ground delay" in text:
            return 0.75
        if "departure delay" in text or "arrival delay" in text:
            return 0.55
        return 0.4
