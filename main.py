from fastapi import FastAPI, Query, HTTPException, Request
from open_metro_services import GeocodingService, WeatherService
import time

app = FastAPI()

metrics = {
    "/weather/monthly-profile": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
    "/travel/best-month": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
    "/travel/compare-cities": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
}


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    route = request.url.path
    if route not in metrics:
        return await call_next(request)

    start_time = time.time()
    metrics[route]["hits"] += 1
    try:
        response = await call_next(request)
    except Exception as e:
        metrics[route]["errors"] += 1
        raise e
    finally:
        process_time = time.time() - start_time
        current_metrics = metrics[route]
        current_metrics["avg_time"] = (
                (current_metrics["avg_time"] * (current_metrics["hits"] - 1) + process_time)
                / current_metrics["hits"]
        )
        current_metrics["max_time"] = max(current_metrics["max_time"], process_time)
        current_metrics["min_time"] = min(current_metrics["min_time"], process_time)

    return response


@app.get("/weather/monthly-profile")
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


@app.get("/travel/best-month")
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


@app.get("/travel/compare-cities")
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


@app.get("/metrics")
async def get_metrics():
    result = {
        "routes": {}
    }

    for route, data in metrics.items():
        route_data = {
            "hits": data["hits"],
            "errors": data["errors"],
            "avg_time": round(data["avg_time"], 4),
            "max_time": round(data["max_time"], 4),
            "min_time": round(data["min_time"], 4) if data["min_time"] != float("inf") else 0,
        }
        result["routes"][route] = route_data

    return result
