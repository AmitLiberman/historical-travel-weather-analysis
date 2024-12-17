from aiohttp import ClientSession
import asyncio


class GeocodingService:
    def __init__(self):
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"

    async def get_coordinates(self, city: str):
        """Fetches coordinates of a city."""

        async with ClientSession() as session:
            async with session.get(self.geocode_url, params={'name': city, 'count': 1}) as response:
                data = await response.json()
                if 'results' not in data or not data['results']:
                    raise Exception(f"City '{city}' not found.")

                return data['results'][0]['latitude'], data['results'][0]['longitude']

    async def fetch_coordinates_for_multiple_cities(self, cities: list):
        """Fetches coordinates of list of cities"""

        tasks = [self.get_coordinates(city) for city in cities]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        coordinates = {}
        for city, result in zip(cities, results):
            if isinstance(result, Exception):
                raise Exception(result)
            else:
                coordinates[city] = {"latitude": result[0], "longitude": result[1]}
        return coordinates
