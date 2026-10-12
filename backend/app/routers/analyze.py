from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.cache import memory_get, memory_set
from app.config import get_settings
from app.db import get_cached_analysis, store_analysis
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    EventOut,
    GeocodeResult,
    RegionOut,
    TrendOut,
    YearMetricsOut,
)
from app.services.heatwave import analyze_heatwaves
from app.services.openmeteo import OpenMeteoError, fetch_daily_tmax, geocode_search
from app.services.trends import build_insight, compute_frequency_trend

router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)
_RATE = get_settings().rate_limit


def _cache_key(lat: float, lon: float, start_year: int, end_year: int) -> str:
    raw = f"{lat:.2f}:{lon:.2f}:{start_year}:{end_year}:heatwave"
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_point(body: AnalyzeRequest) -> tuple[float, float, dict[str, float] | None]:
    if body.north is not None and body.south is not None and body.east is not None and body.west is not None:
        lat = (body.north + body.south) / 2.0
        lon = (body.east + body.west) / 2.0
        bbox = {
            "north": body.north,
            "south": body.south,
            "east": body.east,
            "west": body.west,
        }
        return lat, lon, bbox
    return body.lat, body.lon, None


@router.get("/health")
async def health() -> dict[str, str]:
    from app.db import is_db_connected

    return {
        "status": "ok",
        "mongodb": "ok" if is_db_connected() else "unavailable",
    }


@router.get("/geocode", response_model=list[GeocodeResult])
@limiter.limit(_RATE)
async def geocode(request: Request, q: str = Query(..., min_length=1, max_length=100)) -> list[GeocodeResult]:
    try:
        results = await geocode_search(q)
    except OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [GeocodeResult(**item) for item in results]


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(_RATE)
async def analyze(request: Request) -> AnalyzeResponse:
    # Parse body from Request so slowapi's wrapper does not strip FastAPI body binding
    try:
        body = AnalyzeRequest.model_validate(await request.json())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON body") from exc

    lat, lon, bbox = _resolve_point(body)
    key = _cache_key(lat, lon, body.start_year, body.end_year)

    cached = None
    try:
        cached = await get_cached_analysis(key)
    except Exception:
        cached = memory_get(key)
    if cached is None:
        cached = memory_get(key)
    if cached:
        cached = dict(cached)
        cached["cached"] = True
        return AnalyzeResponse(**cached)

    try:
        dates, tmax = await fetch_daily_tmax(lat, lon, body.start_year, body.end_year)
    except OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not dates:
        raise HTTPException(status_code=404, detail="No weather observations for this request")

    try:
        threshold, events, metrics = analyze_heatwaves(dates, tmax)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    trend = compute_frequency_trend(metrics)
    insight = build_insight(metrics, trend, region_label=body.label)

    years_out: list[YearMetricsOut] = []
    for m, roll in zip(metrics, trend.rolling_mean_5yr):
        years_out.append(
            YearMetricsOut(
                year=m.year,
                event_count=m.event_count,
                mean_duration=m.mean_duration,
                mean_intensity=m.mean_intensity,
                hot_day_count=m.hot_day_count,
                low_confidence=m.low_confidence,
                missing_fraction=m.missing_fraction,
                rolling_mean_5yr=roll,
            )
        )

    # Cap sample events for payload size
    sample = sorted(events, key=lambda e: e.duration_days, reverse=True)[:25]
    events_out = [
        EventOut(
            start=e.start.isoformat(),
            end=e.end.isoformat(),
            duration_days=e.duration_days,
            mean_intensity=round(e.mean_intensity, 3),
            peak_tmax=round(e.peak_tmax, 2),
        )
        for e in sample
    ]

    result: dict[str, Any] = {
        "region": RegionOut(lat=round(lat, 4), lon=round(lon, 4), label=body.label, bbox=bbox).model_dump(),
        "hazard": "heatwave",
        "threshold_c": round(threshold, 2),
        "years": [y.model_dump() for y in years_out],
        "trend": TrendOut(
            slope_per_year=round(trend.slope_per_year, 4),
            slope_per_decade=round(trend.slope_per_decade, 4),
            r_squared=round(trend.r_squared, 4),
            p_value=round(trend.p_value, 4),
            direction=trend.direction,
        ).model_dump(),
        "insight": insight,
        "cached": False,
        "events_sample": [e.model_dump() for e in events_out],
        "data_source": (
            "Open-Meteo Historical Weather API (ERA5 reanalysis via archive-api.open-meteo.com)"
        ),
    }

    try:
        await store_analysis(key, result)
    except Exception:
        memory_set(key, result)
    else:
        memory_set(key, result)

    return AnalyzeResponse(**result)
