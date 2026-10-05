from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SourceStatus(StrEnum):
    AVAILABLE = "available"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class SourceCoverage(BaseModel):
    source: str
    status: SourceStatus
    fetched_at: datetime | None = None
    message: str
    source_url: str | None = None

