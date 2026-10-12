"""Heatwave detection and yearly rollups.

Definition (from case study example):
- Hot day: daily maximum temperature above the 95th percentile for the series
- Heatwave event: 3 or more consecutive hot days
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HeatwaveEvent:
    start: date
    end: date
    duration_days: int
    mean_intensity: float
    peak_tmax: float


@dataclass(frozen=True)
class YearlyMetrics:
    year: int
    event_count: int
    mean_duration: float | None
    mean_intensity: float | None
    hot_day_count: int
    low_confidence: bool
    missing_fraction: float


def _is_missing(value: float | None) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value))


def compute_p95_threshold(tmax: Sequence[float | None]) -> float:
    values = np.asarray([v for v in tmax if not _is_missing(v)], dtype=float)
    if values.size == 0:
        raise ValueError("No valid temperature observations to compute P95")
    return float(np.percentile(values, 95))


def find_heatwave_events(
    dates: Sequence[date],
    tmax: Sequence[float | None],
    threshold: float,
    min_consecutive: int = 3,
) -> list[HeatwaveEvent]:
    if len(dates) != len(tmax):
        raise ValueError("dates and tmax must be the same length")

    events: list[HeatwaveEvent] = []
    run_start: int | None = None
    run_temps: list[float] = []

    def close_run(end_idx: int) -> None:
        nonlocal run_start, run_temps
        if run_start is None:
            return
        duration = end_idx - run_start + 1
        if duration >= min_consecutive:
            intensity = float(np.mean([t - threshold for t in run_temps]))
            events.append(
                HeatwaveEvent(
                    start=dates[run_start],
                    end=dates[end_idx],
                    duration_days=duration,
                    mean_intensity=intensity,
                    peak_tmax=float(max(run_temps)),
                )
            )
        run_start = None
        run_temps = []

    for i, (d, t) in enumerate(zip(dates, tmax)):
        is_hot = not _is_missing(t) and float(t) > threshold
        if is_hot:
            if run_start is None:
                run_start = i
                run_temps = [float(t)]
            else:
                prev = dates[i - 1]
                if (d - prev).days == 1:
                    run_temps.append(float(t))
                else:
                    close_run(i - 1)
                    run_start = i
                    run_temps = [float(t)]
        elif run_start is not None:
            close_run(i - 1)

    if run_start is not None:
        close_run(len(dates) - 1)

    return events


def analyze_heatwaves(
    dates: Sequence[date],
    tmax: Sequence[float | None],
    min_consecutive: int = 3,
    missing_threshold: float = 0.30,
) -> tuple[float, list[HeatwaveEvent], list[YearlyMetrics]]:
    threshold = compute_p95_threshold(tmax)
    events = find_heatwave_events(dates, tmax, threshold, min_consecutive=min_consecutive)

    frame = pd.DataFrame({"date": list(dates), "tmax": list(tmax)})
    frame["year"] = frame["date"].map(lambda d: d.year)
    frame["is_hot"] = [
        (not _is_missing(v) and float(v) > threshold) for v in frame["tmax"]
    ]

    by_year: dict[int, list[HeatwaveEvent]] = {}
    for ev in events:
        by_year.setdefault(ev.start.year, []).append(ev)

    metrics: list[YearlyMetrics] = []
    for year, group in frame.groupby("year", sort=True):
        raw = list(group["tmax"])
        total_days = len(raw)
        missing = sum(1 for v in raw if _is_missing(v))
        missing_fraction = missing / total_days if total_days else 1.0
        year_events = by_year.get(int(year), [])
        metrics.append(
            YearlyMetrics(
                year=int(year),
                event_count=len(year_events),
                mean_duration=(
                    float(np.mean([e.duration_days for e in year_events])) if year_events else None
                ),
                mean_intensity=(
                    float(np.mean([e.mean_intensity for e in year_events])) if year_events else None
                ),
                hot_day_count=int(group["is_hot"].sum()),
                low_confidence=missing_fraction >= missing_threshold,
                missing_fraction=float(missing_fraction),
            )
        )

    return threshold, events, metrics
