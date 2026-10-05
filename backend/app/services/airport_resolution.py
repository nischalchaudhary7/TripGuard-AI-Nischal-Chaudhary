from app.connectors.ourairports import OurAirportsResolver
from app.core.models.airport import Airport


class AirportResolutionService:
    def __init__(self, resolver: OurAirportsResolver):
        self.resolver = resolver

    async def resolve_pair(self, origin: str, destination: str) -> tuple[Airport, Airport]:
        return await self.resolver.resolve(origin), await self.resolver.resolve(destination)

