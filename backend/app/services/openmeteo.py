"""Open-Meteo Historical Weather + Geocoding clients."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings

HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


class OpenMeteoError(Exception):
    """Raised when Open-Meteo returns an error or unusable payload."""


async def fetch_daily_tmax(
    lat: float,
    lon: float,
    start_year: int,
    end_year: int,
    client: httpx.AsyncClient | None = None,
) -> tuple[list[date], list[float | None]]:
    settings = get_settings()
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max",
        "timezone": "UTC",
    }

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds)

    try:
        response = await client.get(HISTORICAL_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise OpenMeteoError("Failed to fetch historical weather from Open-Meteo") from exc
    finally:
        if owns_client:
            await client.aclose()

    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    temps = daily.get("temperature_2m_max") or []
    if not times or len(times) != len(temps):
        raise OpenMeteoError("Open-Meteo returned incomplete daily temperature data")

    dates = [date.fromisoformat(t) for t in times]
    tmax: list[float | None] = [None if v is None else float(v) for v in temps]
    return dates, tmax


async def geocode_search(
    query: str,
    count: int = 8,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    q = query.strip()
    if not q:
        return []

    params = {"name": q, "count": count, "language": "en", "format": "json"}
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds)

    try:
        response = await client.get(GEOCODE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise OpenMeteoError("Failed to geocode location via Open-Meteo") from exc
    finally:
        if owns_client:
            await client.aclose()

    results = payload.get("results") or []
    out: list[dict[str, Any]] = []
    for item in results:
        out.append(
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "admin1": item.get("admin1"),
                "lat": item.get("latitude"),
                "lon": item.get("longitude"),
                "label": _format_label(item),
            }
        )
    return out


def _format_label(item: dict[str, Any]) -> str:
    parts = [item.get("name"), item.get("admin1"), item.get("country")]
    return ", ".join(str(p) for p in parts if p)
