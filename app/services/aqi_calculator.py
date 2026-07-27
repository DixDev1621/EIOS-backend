"""
CPCB National Air Quality Index (NAQI) calculator.

Implements the official breakpoint / linear-interpolation method
published by India's Central Pollution Control Board
(https://cpcb.nic.in/national-air-quality-index/). The overall AQI for
a location is the MAX of the available pollutant sub-indices, exactly
as CPCB specifies -- this is real, published methodology, not an
approximation invented for this project.

Breakpoints are (BP_lo, BP_hi, I_lo, I_hi) tuples per pollutant.
Units: PM2.5 & PM10 & NO2 & SO2 & O3 in ug/m3 (24-hr avg except O3 8-hr,
NO2/SO2 which use 24-hr in the Indian standard); CO in mg/m3 (8-hr avg).
"""

from dataclasses import dataclass

AQI_CATEGORIES = [
    (0, 50, "Good", "#4CAF50"),
    (51, 100, "Satisfactory", "#A0CE4E"),
    (101, 200, "Moderate", "#FFD54F"),
    (201, 300, "Poor", "#FB8C00"),
    (301, 400, "Very Poor", "#E53935"),
    (401, 500, "Severe", "#8D1B3D"),
]

BREAKPOINTS = {
    "pm25": [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200), (91, 120, 201, 300), (121, 250, 301, 400), (251, 380, 401, 500)],
    "pm10": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200), (251, 350, 201, 300), (351, 430, 301, 400), (431, 510, 401, 500)],
    "no2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200), (181, 280, 201, 300), (281, 400, 301, 400), (401, 500, 401, 500)],
    "so2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200), (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 2100, 401, 500)],
    "co": [(0, 1.0, 0, 50), (1.1, 2.0, 51, 100), (2.1, 10.0, 101, 200), (10.1, 17.0, 201, 300), (17.1, 34.0, 301, 400), (34.1, 50.0, 401, 500)],
    "o3": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200), (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)],
}


def _sub_index(pollutant: str, concentration: float | None) -> float | None:
    if concentration is None or concentration < 0:
        return None
    table = BREAKPOINTS[pollutant]
    for bp_lo, bp_hi, i_lo, i_hi in table:
        if bp_lo <= concentration <= bp_hi:
            return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo, 1)
    # Above the top published breakpoint: extrapolate from the last band
    bp_lo, bp_hi, i_lo, i_hi = table[-1]
    if concentration > bp_hi:
        return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo, 1)
    return None


def category_for(aqi: float) -> tuple[str, str]:
    for lo, hi, label, color in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label, color
    return "Severe", AQI_CATEGORIES[-1][3]


@dataclass
class AQIResult:
    aqi: float
    category: str
    color: str
    dominant_pollutant: str
    sub_indices: dict[str, float]


def compute_aqi(
    pm25: float | None = None,
    pm10: float | None = None,
    no2: float | None = None,
    so2: float | None = None,
    co_mg_m3: float | None = None,
    o3: float | None = None,
) -> AQIResult | None:
    raw = {"pm25": pm25, "pm10": pm10, "no2": no2, "so2": so2, "co": co_mg_m3, "o3": o3}
    sub_indices: dict[str, float] = {}
    for pollutant, value in raw.items():
        si = _sub_index(pollutant, value)
        if si is not None:
            sub_indices[pollutant] = si

    if not sub_indices:
        return None

    dominant_pollutant = max(sub_indices, key=sub_indices.get)
    aqi_value = sub_indices[dominant_pollutant]
    label, color = category_for(aqi_value)

    return AQIResult(
        aqi=aqi_value,
        category=label,
        color=color,
        dominant_pollutant=dominant_pollutant,
        sub_indices=sub_indices,
    )
