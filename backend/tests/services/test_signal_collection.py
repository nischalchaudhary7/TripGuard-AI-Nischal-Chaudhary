from datetime import date

from app.connectors.base import ConnectorResult
from app.core.models.source import SourceCoverage, SourceStatus
from app.services.signal_collection import SignalCollectionService


class FailingButGracefulConnector:
    async def fetch(self, airports, travel_date):
        return ConnectorResult(
            signals=[],
            coverage=SourceCoverage(source="Broken Source", status=SourceStatus.FAILED, message="failed"),
        )


async def test_collection_keeps_failed_source_as_coverage():
    service = SignalCollectionService([FailingButGracefulConnector()])
    signals, coverage = await service.collect([], date(2026, 10, 3))
    assert signals == []
    assert coverage[0].status == SourceStatus.FAILED

