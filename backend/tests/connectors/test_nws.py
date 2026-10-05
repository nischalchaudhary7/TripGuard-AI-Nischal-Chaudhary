from datetime import UTC, date, datetime

from app.connectors.nws import NWSConnector
from app.core.models.airport import Airport


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeClient:
    async def get(self, url, params=None):
        if url.endswith("/points/32.8998,-97.0403"):
            return FakeResponse({"properties": {"forecast": "https://forecast.example/dfw"}})
        if url == "https://forecast.example/dfw":
            return FakeResponse(
                {
                    "properties": {
                        "periods": [
                            {
                                "name": "Sunday Night",
                                "startTime": "2026-10-04T18:00:00-05:00",
                                "endTime": "2026-10-04T23:59:00-05:00",
                                "shortForecast": "Thunderstorms",
                                "detailedForecast": "Thunderstorms likely.",
                                "probabilityOfPrecipitation": {"value": 80},
                            },
                            {
                                "name": "Monday",
                                "startTime": "2026-10-05T06:00:00-05:00",
                                "endTime": "2026-10-05T18:00:00-05:00",
                                "shortForecast": "Rain Showers",
                                "detailedForecast": "Rain showers possible.",
                                "probabilityOfPrecipitation": {"value": 70},
                            },
                        ]
                    }
                }
            )
        raise AssertionError(f"unexpected URL {url}")


def airport():
    return Airport(
        iata_code="DFW",
        icao_code="KDFW",
        name="Dallas Fort Worth International Airport",
        city="Dallas-Fort Worth",
        region="TX",
        country="US",
        latitude=32.8998,
        longitude=-97.0403,
        source_url="https://ourairports.com",
    )


async def test_forecast_signal_uses_only_selected_travel_date_periods():
    connector = NWSConnector(FakeClient())

    signals = await connector._forecast_for_airport(airport(), date(2026, 10, 5), datetime(2026, 10, 3, tzinfo=UTC))

    assert len(signals) == 1
    signal = signals[0]
    assert signal.summary == "70% chance of precipitation near DFW"
    assert "Monday" in signal.evidence
    assert "Sunday Night" not in signal.evidence
    assert "Thunderstorms" not in signal.evidence
    assert "Sunday Night" in signal.full_evidence
