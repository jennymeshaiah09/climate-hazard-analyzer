from datetime import date, timedelta

import numpy as np

from app.services.heatwave import analyze_heatwaves, compute_p95_threshold, find_heatwave_events
from app.services.trends import build_insight, compute_frequency_trend, rolling_mean


def _series_with_heatwave():
    """Synthetic series: mostly cool so P95 stays low; one 4-day spike above it."""
    start = date(2000, 1, 1)
    n = 100
    dates = [start + timedelta(days=i) for i in range(n)]
    tmax = [30.0] * n
    for i in range(50, 54):
        tmax[i] = 45.0
    return dates, tmax


def test_p95_threshold():
    values = list(range(100))
    assert compute_p95_threshold(values) == np.percentile(values, 95)


def test_find_heatwave_requires_three_days():
    dates, tmax = _series_with_heatwave()
    threshold = compute_p95_threshold(tmax)
    events = find_heatwave_events(dates, tmax, threshold, min_consecutive=3)
    assert len(events) == 1
    assert events[0].duration_days == 4
    assert events[0].start == date(2000, 2, 20)


def test_two_day_spike_not_heatwave():
    dates, tmax = _series_with_heatwave()
    tmax = list(tmax)
    for i in range(50, 54):
        tmax[i] = 30.0
    tmax[5] = 50.0
    tmax[6] = 50.0
    threshold = compute_p95_threshold(tmax)
    events = find_heatwave_events(dates, tmax, threshold, min_consecutive=3)
    assert events == []


def test_analyze_yearly_metrics():
    dates, tmax = _series_with_heatwave()
    threshold, events, metrics = analyze_heatwaves(dates, tmax)
    assert threshold >= 30.0
    assert len(events) == 1
    assert len(metrics) == 1
    assert metrics[0].event_count == 1
    assert metrics[0].mean_duration == 4


def test_rolling_mean():
    assert rolling_mean([1, 2, 3, 4, 5], window=5) == [None, None, None, None, 3.0]


def test_trend_and_insight_increasing():
    from app.services.heatwave import YearlyMetrics

    metrics = [
        YearlyMetrics(y, c, None, None, 0, False, 0.0)
        for y, c in zip(range(1990, 2000), [0, 0, 1, 0, 1, 2, 2, 3, 3, 4])
    ]
    trend = compute_frequency_trend(metrics)
    assert trend.direction in {"increasing", "stable"}
    insight = build_insight(metrics, trend, region_label="Test City")
    assert "Test City" in insight
    assert "Heatwave" in insight
