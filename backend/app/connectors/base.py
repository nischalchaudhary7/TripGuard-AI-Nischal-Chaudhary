from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import httpx

from app.core.models.airport import Airport
from app.core.models.signal import Signal
from app.core.models.source import SourceCoverage, SourceStatus


@dataclass
class ConnectorResult:
    signals: list[Signal]
    coverage: SourceCoverage


class ConnectorError(Exception):
    pass


class BaseConnector(ABC):
    source_name: str
    source_url: str

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def coverage(self, status: SourceStatus, message: str, fetched_at=None) -> SourceCoverage:
        return SourceCoverage(
            source=self.source_name,
            status=status,
            fetched_at=fetched_at,
            message=message,
            source_url=self.source_url,
        )

    @abstractmethod
    async def fetch(self, airports: list[Airport], travel_date: date) -> ConnectorResult:
        raise NotImplementedError

