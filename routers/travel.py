from fastapi import APIRouter, Query, HTTPException

from services.geocoding import GeocodingService
from services.weather import WeatherService


router = APIRouter()

@router.get("/weather/monthly-profile")
async def monthly_profile(city: str, month: int = Query(..., ge=1, le=12)):
    geocoding_service = GeocodingService()
    try:
        latitude, longitude = await geocoding_service.get_coordinates(city)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    weather_service = WeatherService(latitude, longitude)
    try:
        weather_data = await weather_service.fetch_weather_data()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Could not get weather data")

    max_temp_avg, min_temp_avg = weather_service.average_month_temperature(weather_data, month)
    return {
        "city": city,
        "month": month,
        "min_temp_avg": round(float(min_temp_avg), 2),
        "max_temp_avg": round(float(max_temp_avg), 2)
    }
