from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.db import close_db, connect_db
from app.routers.analyze import limiter, router as analyze_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await connect_db()
    except Exception:
        # Allow API to start even if Mongo is temporarily unavailable;
        # analyze will fail cache ops but health reports mongodb status.
        pass
    yield
    await close_db()


settings = get_settings()
app = FastAPI(
    title="Climate Hazard Trend Analyzer",
    description="Heatwave frequency and intensity trends from Open-Meteo historical data.",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
origins = settings.cors_origin_list
allow_all = origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(analyze_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", settings.port))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
