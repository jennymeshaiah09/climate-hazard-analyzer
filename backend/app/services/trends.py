"""Trend analysis and human-readable insight strings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats

from app.services.heatwave import YearlyMetrics


@dataclass(frozen=True)
class TrendResult:
    slope_per_year: float
    slope_per_decade: float
    r_squared: float
    p_value: float
    direction: str
    rolling_mean_5yr: list[float | None]


def rolling_mean(values: Sequence[float], window: int = 5) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
            continue
        chunk = values[i + 1 - window : i + 1]
        out.append(float(np.mean(chunk)))
    return out


def compute_frequency_trend(metrics: Sequence[YearlyMetrics]) -> TrendResult:
    years = np.asarray([m.year for m in metrics], dtype=float)
    counts = np.asarray([m.event_count for m in metrics], dtype=float)
    rolling = rolling_mean([float(c) for c in counts], window=5)

    if len(years) < 2 or np.all(counts == counts[0]):
        return TrendResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            r_squared=0.0,
            p_value=1.0,
            direction="stable",
            rolling_mean_5yr=rolling,
        )

    slope, _intercept, r_value, p_value, _stderr = stats.linregress(years, counts)
    slope_per_decade = float(slope * 10)
    r_squared = float(r_value**2)

    # Treat near-zero slopes as stable for messaging
    if abs(slope_per_decade) < 0.05 or p_value > 0.1:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return TrendResult(
        slope_per_year=float(slope),
        slope_per_decade=slope_per_decade,
        r_squared=r_squared,
        p_value=float(p_value),
        direction=direction,
        rolling_mean_5yr=rolling,
    )


def build_insight(
    metrics: Sequence[YearlyMetrics],
    trend: TrendResult,
    region_label: str | None = None,
) -> str:
    if not metrics:
        return "Not enough data to summarize heatwave trends for this region."

    start_year = metrics[0].year
    end_year = metrics[-1].year
    place = f" in {region_label}" if region_label else " in this region"

    # Compare first vs last decade (or half-period if shorter)
    span = end_year - start_year + 1
    window = 10 if span >= 20 else max(3, span // 2)

    early = [m.event_count for m in metrics if m.year < start_year + window]
    late = [m.event_count for m in metrics if m.year > end_year - window]

    if not early or not late:
        return (
            f"Heatwave frequency{place} averages {np.mean([m.event_count for m in metrics]):.1f} "
            f"events/year over {start_year}–{end_year}."
        )

    early_mean = float(np.mean(early))
    late_mean = float(np.mean(late))

    if early_mean == 0 and late_mean == 0:
        return (
            f"No heatwave events were detected{place} under the 3-day / 95th-percentile "
            f"definition across {start_year}–{end_year}."
        )

    if early_mean == 0:
        return (
            f"Heatwaves appeared{place} in later years ({end_year - window + 1}–{end_year}: "
            f"{late_mean:.1f} events/year) after near-zero frequency in {start_year}–"
            f"{start_year + window - 1}. Linear trend: {trend.slope_per_decade:+.2f} "
            f"events/decade."
        )

    pct_change = ((late_mean - early_mean) / early_mean) * 100
    abs_pct = abs(pct_change)

    if abs_pct < 5:
        verb = "changed little"
        detail = f"about {early_mean:.1f} to {late_mean:.1f} events/year"
    elif pct_change > 0:
        verb = f"increased by about {abs_pct:.0f}%"
        detail = f"{early_mean:.1f} to {late_mean:.1f} events/year"
    else:
        verb = f"decreased by about {abs_pct:.0f}%"
        detail = f"{early_mean:.1f} to {late_mean:.1f} events/year"

    return (
        f"Heatwave frequency{place} {verb} comparing {start_year}–{start_year + window - 1} "
        f"to {end_year - window + 1}–{end_year} ({detail}). "
        f"OLS slope: {trend.slope_per_decade:+.2f} events/decade "
        f"(R²={trend.r_squared:.2f})."
    )
