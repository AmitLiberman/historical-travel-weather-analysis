from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

router = APIRouter()

metrics = {
    "/weather/monthly-profile": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
    "/travel/best-month": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
    "/travel/compare-cities": {"hits": 0, "errors": 0, "avg_time": 0, "max_time": 0, "min_time": float("inf")},
}


@router.get("/metrics")
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


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
