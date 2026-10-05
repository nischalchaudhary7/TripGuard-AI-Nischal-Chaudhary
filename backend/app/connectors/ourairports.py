import csv
from io import StringIO

import httpx

from app.config import Settings
from app.core.models.airport import Airport
from app.utils.errors import AirportResolutionError


class OurAirportsResolver:
    source_name = "OurAirports"

    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self.client = client
        self.settings = settings
        self._airports: list[Airport] | None = None

    async def load_airports(self) -> list[Airport]:
        if self._airports is not None:
            return self._airports

        try:
            response = await self.client.get(self.settings.ourairports_csv_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AirportResolutionError(f"OurAirports airport dataset could not be loaded: {exc}") from exc
        rows = csv.DictReader(StringIO(response.text))
        airports: list[Airport] = []
        for row in rows:
            iata = (row.get("iata_code") or "").strip().upper()
            if not iata or row.get("iso_country") != "US":
                continue
            if row.get("type") not in {"large_airport", "medium_airport"}:
                continue
            try:
                airports.append(
                    Airport(
                        iata_code=iata,
                        icao_code=(row.get("ident") or "").strip().upper() or None,
                        name=(row.get("name") or iata).strip(),
                        city=(row.get("municipality") or "").strip() or None,
                        region=(row.get("iso_region") or "").replace("US-", "") or None,
                        country="US",
                        latitude=float(row["latitude_deg"]),
                        longitude=float(row["longitude_deg"]),
                        source_url=self.settings.ourairports_csv_url,
                    )
                )
            except (KeyError, ValueError):
                continue
        self._airports = airports
        return airports

    async def resolve(self, query: str) -> Airport:
        normalized = query.strip().upper()
        if not normalized:
            raise AirportResolutionError("Airport or city is required.")

        airports = await self.load_airports()
        for airport in airports:
            if airport.iata_code == normalized or airport.icao_code == normalized:
                return airport

        city_matches = [
            airport
            for airport in airports
            if airport.city and normalized in airport.city.upper()
        ]
        if city_matches:
            return sorted(city_matches, key=lambda airport: (airport.city or "", airport.name))[0]

        name_matches = [
            airport
            for airport in airports
            if normalized in airport.name.upper()
        ]
        if name_matches:
            return sorted(name_matches, key=lambda airport: airport.name)[0]

        raise AirportResolutionError(f"Could not resolve '{query}' to a U.S. airport.")
