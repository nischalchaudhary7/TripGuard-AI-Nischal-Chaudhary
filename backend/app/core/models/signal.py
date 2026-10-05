from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class SignalCategory(StrEnum):
    WEATHER_ALERT = "WEATHER_ALERT"
    FORECAST = "FORECAST"
    AVIATION_WEATHER = "AVIATION_WEATHER"
    FAA_OPERATIONAL = "FAA_OPERATIONAL"
    AIRPORT_STATUS = "AIRPORT_STATUS"


class Signal(BaseModel):
    id: str
    source: str
    category: SignalCategory
    location: str
    severity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    evidence: str
    structured_data: dict[str, str] = Field(default_factory=dict)
    raw_data: str | None = None
    full_evidence: str | None = None
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    fetched_at: datetime
    source_url: str

    @field_validator("id", "source", "location", "summary", "evidence", "source_url")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value
