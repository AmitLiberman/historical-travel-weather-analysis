from fastapi import APIRouter, Query, HTTPException

from services.geocoding import GeocodingService
from services.weather import WeatherService


router = APIRouter()


@router.get("/travel/best-month")
async def best_month(city: str, min_temp: int, max_temp: int):
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
    city_names = cities.split(',')

    if not (2 <= len(city_names) <= 5):
        raise HTTPException(status_code=400, detail="Number of cities must be between 2 and 5")

    geocoding_service = GeocodingService()
    try:
        coordinates = await geocoding_service.fetch_coordinates_for_multiple_cities(city_names)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    latitudes = [float(coord["latitude"]) for coord in coordinates.values()]
    longitudes = [float(coord["longitude"]) for coord in coordinates.values()]
    weather_service = WeatherService(latitudes, longitudes)

    try:
        weather_data = await weather_service.fetch_weather_data()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weather data: {str(e)}"
        )

    result = {"month": month}

    for i, data in enumerate(weather_data):
        city = list(coordinates.keys())[i]
        max_temp_avg, min_temp_avg = weather_service.average_month_temperature(data, month)
        result[city] = {
            "min_temp_avg": round(min_temp_avg, 2),
            "max_temp_avg": round(max_temp_avg, 2)
        }

    return result
