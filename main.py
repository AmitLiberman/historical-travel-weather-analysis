from fastapi import FastAPI
from routers import travel, weather, metrics

app = FastAPI()

app.include_router(travel.router)
app.include_router(weather.router)
app.include_router(metrics.router)
app.add_middleware(metrics.MetricsMiddleware)
