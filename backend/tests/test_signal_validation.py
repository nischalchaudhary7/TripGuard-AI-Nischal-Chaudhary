from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.models.signal import Signal, SignalCategory


def test_signal_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        Signal(
            id="bad",
            source="source",
            category=SignalCategory.FORECAST,
            location="DFW",
            severity=1.5,
            confidence=0.5,
            summary="summary",
            evidence="evidence",
            fetched_at=datetime.now(UTC),
            source_url="https://example.com",
        )

