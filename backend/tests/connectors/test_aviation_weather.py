from datetime import UTC, date, datetime

from app.connectors.aviation_weather import AviationWeatherConnector
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
        return FakeResponse([{"rawOb": "KDFW 030053Z 18015G30KT 1SM TSRA BKN008"}])


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


async def test_metar_is_not_used_as_future_predictive_signal():
    connector = AviationWeatherConnector(FakeClient())

    signals = await connector._metar("KDFW", airport(), date(2026, 10, 4), datetime(2026, 10, 3, tzinfo=UTC))

    assert signals == []


async def test_metar_decodes_structured_fields_for_today():
    connector = AviationWeatherConnector(FakeClient())

    signals = await connector._metar("KDFW", airport(), date(2026, 10, 3), datetime(2026, 10, 3, tzinfo=UTC))

    assert len(signals) == 1
    assert signals[0].raw_data
    assert signals[0].structured_data["visibility"] == "1 statute miles"
    assert signals[0].structured_data["wind"] == "180 degrees at 15 kt, gusting 30 kt"
    assert signals[0].structured_data["cloud_ceiling"] == "BKN at 800 ft"
