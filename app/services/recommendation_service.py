"""
Recommendation engine.

Deliberately rule-based rather than free-text LLM generation: every
recommendation below traces to a published, citable public-health
threshold (CPCB AQI categories, WHO Air Quality Guidelines 2021, NDMA
Heat Action Plan bands). This is what makes recommendations trustworthy
enough for a government-facing tool -- an official can audit exactly
which rule fired and why, rather than trusting an opaque generative
response.
"""

from dataclasses import dataclass


@dataclass
class Recommendation:
    audience: str
    severity: str  # info | advisory | warning | emergency
    action: str
    basis: str


def recommendations_for_aqi(aqi: float, category: str) -> list[Recommendation]:
    recs: list[Recommendation] = []

    if aqi <= 50:
        recs.append(Recommendation(
            audience="General public",
            severity="info",
            action="Air quality is good. Normal outdoor activity is safe for all groups.",
            basis="CPCB AQI category: Good (0-50)",
        ))
    elif aqi <= 100:
        recs.append(Recommendation(
            audience="General public",
            severity="info",
            action="Air quality is satisfactory. Unusually sensitive individuals should consider "
                   "reducing prolonged outdoor exertion.",
            basis="CPCB AQI category: Satisfactory (51-100)",
        ))
    elif aqi <= 200:
        recs.append(Recommendation(
            audience="Sensitive groups (children, elderly, respiratory/cardiac conditions)",
            severity="advisory",
            action="Reduce prolonged or heavy outdoor exertion, especially near traffic corridors.",
            basis="CPCB AQI category: Moderate (101-200)",
        ))
    elif aqi <= 300:
        recs.append(Recommendation(
            audience="Sensitive groups",
            severity="warning",
            action="Avoid outdoor physical activity. Keep windows closed during peak traffic hours.",
            basis="CPCB AQI category: Poor (201-300)",
        ))
        recs.append(Recommendation(
            audience="Pollution Control Board / District administration",
            severity="warning",
            action="Consider activating GRAP-equivalent construction-dust and open-burning "
                   "enforcement measures for this district.",
            basis="CPCB Graded Response Action Plan triggers at Poor and above",
        ))
    elif aqi <= 400:
        recs.append(Recommendation(
            audience="General public",
            severity="warning",
            action="Avoid all outdoor physical activity. Sensitive groups should remain indoors.",
            basis="CPCB AQI category: Very Poor (301-400)",
        ))
        recs.append(Recommendation(
            audience="District administration",
            severity="warning",
            action="Issue a public health advisory and consider school outdoor-activity restrictions.",
            basis="WHO Air Quality Guidelines 2021 short-term exposure risk thresholds",
        ))
    else:
        recs.append(Recommendation(
            audience="General public",
            severity="emergency",
            action="Stay indoors. Use air purification where available. Avoid all outdoor exertion.",
            basis="CPCB AQI category: Severe (401-500)",
        ))
        recs.append(Recommendation(
            audience="District Collector / Pollution Control Board",
            severity="emergency",
            action="Consider emergency measures: halt construction activity, restrict heavy vehicle "
                   "entry, and issue a public emergency health advisory.",
            basis="CPCB Graded Response Action Plan -- Severe+ tier",
        ))

    return recs


def recommendations_for_heat(apparent_temp_c: float) -> list[Recommendation]:
    recs: list[Recommendation] = []
    if apparent_temp_c >= 45:
        recs.append(Recommendation(
            audience="General public",
            severity="emergency",
            action="Extreme heat. Avoid outdoor exposure between 12pm-4pm. Stay hydrated.",
            basis="NDMA Heat Action Plan: Red / Extreme Danger band (>=45C apparent temperature)",
        ))
    elif apparent_temp_c >= 40:
        recs.append(Recommendation(
            audience="Outdoor workers, elderly, children",
            severity="warning",
            action="Limit strenuous outdoor work to early morning/evening hours; ensure ORS/water access.",
            basis="NDMA Heat Action Plan: Orange / Danger band (40-45C apparent temperature)",
        ))
    elif apparent_temp_c >= 35:
        recs.append(Recommendation(
            audience="General public",
            severity="advisory",
            action="Stay hydrated and avoid prolonged midday sun exposure.",
            basis="NDMA Heat Action Plan: Yellow / Caution band (35-40C apparent temperature)",
        ))
    return recs


def recommendations_for_fires(detection_count: int) -> list[Recommendation]:
    if detection_count == 0:
        return []
    if detection_count < 5:
        severity = "advisory"
        action = "Isolated thermal anomalies detected nearby; monitor for smoke and localized PM2.5 spikes."
    else:
        severity = "warning"
        action = ("A cluster of active fire/thermal detections was found nearby, consistent with "
                   "crop residue burning or a forest fire. Expect elevated PM2.5 downwind and "
                   "consider field verification.")
    return [Recommendation(
        audience="Pollution Control Board / Forest Department",
        severity=severity,
        action=action,
        basis="NASA FIRMS active fire detections (VIIRS, last 48 hours)",
    )]
