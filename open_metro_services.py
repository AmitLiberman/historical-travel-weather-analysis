from aiohttp import ClientSession
import pandas as pd
from datetime import datetime
import asyncio
from fastapi import HTTPException


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


class WeatherService:
    def __init__(self,
                 latitude: float | list[float],
                 longitude: float | list[float],
                 start_date: datetime = datetime(2018, 1, 1),
                 end_date: datetime = datetime(2023, 12, 31)):
        self.weather_url = "https://archive-api.open-meteo.com/v1/archive"
        self.latitude = [latitude] if isinstance(latitude, float) else latitude
        self.longitude = [longitude] if isinstance(longitude, float) else longitude
        self.start_date = start_date
        self.end_date = end_date

    async def fetch_weather_data(self):
        """Fetches historical weather data for a given location."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": self.start_date.date().isoformat(),
            "end_date": self.end_date.date().isoformat(),
            "daily": ["temperature_2m_max", "temperature_2m_min"]
        }

        async with ClientSession() as session:
            async with session.get(self.weather_url, params=params) as response:
                return await response.json()

    @staticmethod
    def average_month_temperature(data: dict, month: int):
        """Calculates average max and min temperatures for a given month."""
        df = pd.DataFrame(data['daily'])
        df['time'] = pd.to_datetime(df['time'])
        month_data = df[df["time"].dt.month == month]
        if month_data.empty:
            raise ValueError(f"No data available for month {month}.")
        return month_data["temperature_2m_max"].mean(), month_data["temperature_2m_min"].mean()

    def find_best_month(self, data: dict, max_temp: float, min_temp: float):
        """
        Finds the best month based on the smallest total difference.
        """
        monthly_averages = self._preprocess_monthly_data(data, max_temp, min_temp)
        best_row = monthly_averages.loc[monthly_averages['total_diff'].idxmin()]

        best_month = best_row['month']
        total_diff = best_row['total_diff']
        max_temp_diff = best_row['max_temp_diff']
        min_temp_diff = best_row['min_temp_diff']

        return best_month, total_diff, max_temp_diff, min_temp_diff

    @staticmethod
    def _preprocess_monthly_data(data: dict, max_temp: float, min_temp: float) -> pd.DataFrame:
        """
        Preprocesses the input data to compute monthly averages and differences.
        """
        df = pd.DataFrame(data['daily'])
        df['time'] = pd.to_datetime(df['time'])
        df['month'] = df['time'].dt.month

        # Compute monthly averages
        monthly_averages = df.groupby('month').agg({
            'temperature_2m_max': 'mean',
            'temperature_2m_min': 'mean'
        }).reset_index()

        # Calculate differences
        monthly_averages['max_temp_diff'] = abs(monthly_averages['temperature_2m_max'] - max_temp)
        monthly_averages['min_temp_diff'] = abs(monthly_averages['temperature_2m_min'] - min_temp)
        monthly_averages['total_diff'] = monthly_averages['max_temp_diff'] + monthly_averages['min_temp_diff']

        return monthly_averages
