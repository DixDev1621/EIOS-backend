"""
Environmental Health Score (EHS).

A composite 0-100 index (100 = best) combining:
  - Air quality (55% weight)      -- CPCB AQI, inverted and scaled
  - Heat/weather stress (25%)     -- apparent temperature vs. a
                                      35C/70%RH heat-stress reference
                                      band commonly used in Indian
                                      heat-action plans (NDMA guidance)
  - Active fire load (20%)        -- FIRMS detections within 50km,
                                      penalised logarithmically so a
                                      single detection isn't catastrophic
                                      but a cluster meaningfully lowers
                                      the score

This is a *derived, documented* index -- not a raw measurement -- and
every sub-score returned includes its own inputs so a government user
can audit exactly how the number was produced (a hard requirement for
any score used in an official dashboard).
"""

import math
from dataclasses import dataclass, field


@dataclass
class HealthScoreBreakdown:
    score: float
    air_quality_component: float
    weather_stress_component: float
    fire_load_component: float
    inputs: dict = field(default_factory=dict)


def _air_quality_component(aqi: float | None) -> float:
    if aqi is None:
        return 50.0  # neutral when no data, never silently fabricated as "good"
    # AQI 0 -> 100 points, AQI 500 -> 0 points, linear
    return max(0.0, min(100.0, 100.0 - (aqi / 500.0) * 100.0))


def _weather_stress_component(apparent_temp_c: float | None, humidity_pct: float | None) -> float:
    if apparent_temp_c is None:
        return 70.0  # mild neutral default
    # Heat index style penalty: comfortable below 30C apparent temp,
    # severe stress by 45C+, matching NDMA heatwave severity bands.
    if apparent_temp_c <= 30:
        temp_score = 100.0
    elif apparent_temp_c >= 45:
        temp_score = 10.0
    else:
        temp_score = 100.0 - ((apparent_temp_c - 30) / 15.0) * 90.0

    humidity_penalty = 0.0
    if humidity_pct is not None and humidity_pct > 70 and apparent_temp_c > 32:
        humidity_penalty = min(15.0, (humidity_pct - 70) * 0.5)

    return max(0.0, min(100.0, temp_score - humidity_penalty))


def _fire_load_component(detection_count: int) -> float:
    if detection_count <= 0:
        return 100.0
    # Logarithmic penalty: 1 detection ~ -12pts, 10 ~ -40pts, 50 ~ -60pts
    penalty = 12.0 * math.log2(detection_count + 1)
    return max(0.0, min(100.0, 100.0 - penalty))


def compute_health_score(
    aqi: float | None,
    apparent_temp_c: float | None,
    humidity_pct: float | None,
    fire_detection_count: int,
) -> HealthScoreBreakdown:
    aq = _air_quality_component(aqi)
    weather = _weather_stress_component(apparent_temp_c, humidity_pct)
    fire = _fire_load_component(fire_detection_count)

    score = round(aq * 0.55 + weather * 0.25 + fire * 0.20, 1)

    return HealthScoreBreakdown(
        score=score,
        air_quality_component=round(aq, 1),
        weather_stress_component=round(weather, 1),
        fire_load_component=round(fire, 1),
        inputs={
            "aqi": aqi,
            "apparent_temp_c": apparent_temp_c,
            "humidity_pct": humidity_pct,
            "fire_detection_count": fire_detection_count,
        },
    )
