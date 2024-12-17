from fastapi import APIRouter, Query, HTTPException

from services.geocoding import GeocodingService
from services.weather import WeatherService

router = APIRouter()


@router.get("/weather/monthly-profile")
async def monthly_profile(city: str, month: int = Query(..., ge=1, le=12)):
    latitude, longitude = await get_coordinates(city)

    weather_service = WeatherService(latitude, longitude)
    weather_data = await fetch_weather_data(weather_service)

    max_temp_avg, min_temp_avg = weather_service.average_month_temperature(weather_data, month)
    return {
        "city": city,
        "month": month,
        "min_temp_avg": round(float(min_temp_avg), 2),
        "max_temp_avg": round(float(max_temp_avg), 2)
    }


async def get_coordinates(city_names):
    geocoding_service = GeocodingService()
    try:
        if isinstance(city_names, list):
            return await geocoding_service.fetch_coordinates_for_multiple_cities(city_names)
        return await geocoding_service.get_coordinates(city_names)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


async def fetch_weather_data(weather_service):
    try:
        return await weather_service.fetch_weather_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")
