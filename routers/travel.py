from fastapi import APIRouter, Query, HTTPException

from services.geocoding import GeocodingService
from services.weather import WeatherService

router = APIRouter()


@router.get("/travel/best-month")
async def best_month(city: str, min_temp: int, max_temp: int):
    latitude, longitude = await get_coordinates(city)

    weather_service = WeatherService(latitude, longitude)
    weather_data = await fetch_weather_data(weather_service)

    best_month, total_diff, max_temp_diff, min_temp_diff = weather_service.find_best_month(weather_data,
                                                                                           max_temp,
                                                                                           min_temp)
    return {
        "city": city,
        "best_month": int(best_month),
        "min_temp_diff": round(float(min_temp_diff), 2),
        "max_temp_diff": round(float(max_temp_diff), 2),
        "overall_diff": round(float(total_diff), 2)
    }


@router.get("/travel/compare-cities")
async def compare_cities(cities: str, month: int = Query(..., ge=1, le=12)):
    # Validate input
    city_names = cities.split(",")
    if not (2 <= len(city_names) <= 5):
        raise HTTPException(status_code=400, detail="Number of cities must be between 2 and 5")

    # Fetch coordinates
    coordinates = await get_coordinates(city_names)
    latitudes = [float(coord["latitude"]) for coord in coordinates.values()]
    longitudes = [float(coord["longitude"]) for coord in coordinates.values()]

    # Fetch weather data
    weather_service = WeatherService(latitudes, longitudes)
    weather_data = await fetch_weather_data(weather_service)

    # Prepare the result
    result = {"month": month}
    for i, data in enumerate(weather_data):
        city = list(coordinates.keys())[i]
        result[city] = weather_service.calculate_average_temps(data, month)

    return result


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
