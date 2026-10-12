from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings


class AnalyzeRequest(BaseModel):
    lat: float = Field(..., description="Latitude of the analysis point")
    lon: float = Field(..., description="Longitude of the analysis point")
    start_year: int
    end_year: int
    label: str | None = Field(default=None, max_length=200)
    north: float | None = None
    south: float | None = None
    east: float | None = None
    west: float | None = None
    hazard: Literal["heatwave"] = "heatwave"

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90.0 <= v <= 90.0:
            raise ValueError("lat must be between -90 and 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180.0 <= v <= 180.0:
            raise ValueError("lon must be between -180 and 180")
        return v

    @model_validator(mode="after")
    def validate_years_and_bbox(self) -> AnalyzeRequest:
        settings = get_settings()
        if self.start_year < settings.min_year or self.end_year > settings.max_year:
            raise ValueError(
                f"Years must be within {settings.min_year}–{settings.max_year}"
            )
        if self.start_year > self.end_year:
            raise ValueError("start_year must be <= end_year")
        if self.end_year - self.start_year + 1 > settings.max_year_span:
            raise ValueError(f"Year span cannot exceed {settings.max_year_span} years")

        bbox = [self.north, self.south, self.east, self.west]
        if any(v is not None for v in bbox) and not all(v is not None for v in bbox):
            raise ValueError("Provide all of north, south, east, west or none")
        if all(v is not None for v in bbox):
            assert self.north is not None and self.south is not None
            assert self.east is not None and self.west is not None
            if self.south >= self.north:
                raise ValueError("south must be < north")
            if not (-90 <= self.south <= 90 and -90 <= self.north <= 90):
                raise ValueError("bbox latitudes out of range")
            if not (-180 <= self.west <= 180 and -180 <= self.east <= 180):
                raise ValueError("bbox longitudes out of range")
        return self


class YearMetricsOut(BaseModel):
    year: int
    event_count: int
    mean_duration: float | None
    mean_intensity: float | None
    hot_day_count: int
    low_confidence: bool
    missing_fraction: float
    rolling_mean_5yr: float | None = None


class TrendOut(BaseModel):
    slope_per_year: float
    slope_per_decade: float
    r_squared: float
    p_value: float
    direction: str


class EventOut(BaseModel):
    start: str
    end: str
    duration_days: int
    mean_intensity: float
    peak_tmax: float


class RegionOut(BaseModel):
    lat: float
    lon: float
    label: str | None = None
    bbox: dict[str, float] | None = None


class AnalyzeResponse(BaseModel):
    region: RegionOut
    hazard: str
    threshold_c: float
    years: list[YearMetricsOut]
    trend: TrendOut
    insight: str
    cached: bool
    events_sample: list[EventOut]
    data_source: str = (
        "Open-Meteo Historical Weather API (ERA5 reanalysis via archive-api.open-meteo.com)"
    )


class GeocodeResult(BaseModel):
    name: str | None
    country: str | None
    admin1: str | None
    lat: float
    lon: float
    label: str


class HealthResponse(BaseModel):
    status: str
    mongodb: str
