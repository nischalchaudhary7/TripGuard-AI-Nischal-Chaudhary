from pydantic import BaseModel, Field


class Airport(BaseModel):
    iata_code: str = Field(min_length=3, max_length=3)
    icao_code: str | None = None
    name: str
    city: str | None = None
    region: str | None = None
    country: str
    latitude: float
    longitude: float
    source_url: str

