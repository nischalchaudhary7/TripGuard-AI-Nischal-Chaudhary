from datetime import date

from app.connectors.base import BaseConnector, ConnectorResult
from app.core.models.airport import Airport
from app.core.models.signal import Signal
from app.core.models.source import SourceCoverage


class SignalCollectionService:
    def __init__(self, connectors: list[BaseConnector]):
        self.connectors = connectors

    async def collect(self, airports: list[Airport], travel_date: date) -> tuple[list[Signal], list[SourceCoverage]]:
        signals: list[Signal] = []
        coverage: list[SourceCoverage] = []
        for connector in self.connectors:
            result: ConnectorResult = await connector.fetch(airports, travel_date)
            signals.extend(result.signals)
            coverage.append(result.coverage)
        return signals, coverage

