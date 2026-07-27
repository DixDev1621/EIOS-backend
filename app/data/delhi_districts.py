"""
NCT of Delhi district reference dataset.

IMPORTANT: Delhi's district boundaries were reorganized from 11 to 13
districts by the Delhi Cabinet in December 2025, effective 1 January 2026
(dissolving Shahdara; creating Old Delhi, Central North Delhi and Outer
North Delhi). This file reflects the NEW 13-district structure.

Population/area figures are the last officially published (pre-reorg)
district figures for the 10 districts that carried over with the same
core territory; the 3 brand-new districts (Central North Delhi, Old Delhi,
Outer North Delhi) do not yet have separately published Census figures
since they were only just carved out, so their population/area fields are
left as `None` rather than estimated -- consistent with this project's
"no fabricated data" rule. Coordinates are the named sub-division/tehsil
headquarters town for each district and should be treated as
representative sampling points, not precise centroids.
"""

from typing import TypedDict, Optional


class District(TypedDict):
    code: str
    name: str
    headquarters: str
    lat: float
    lon: float
    area_km2: Optional[float]
    population: Optional[int]


DL_DISTRICTS: list[District] = [
    {"code": "DL-CTR", "name": "Central Delhi", "headquarters": "Karol Bagh", "lat": 28.6519, "lon": 77.1909, "area_km2": 23.0, "population": 578671},
    {"code": "DL-CNR", "name": "Central North Delhi", "headquarters": "Model Town", "lat": 28.7041, "lon": 77.1900, "area_km2": None, "population": None},
    {"code": "DL-EST", "name": "East Delhi", "headquarters": "Gandhi Nagar", "lat": 28.6508, "lon": 77.2773, "area_km2": 49.0, "population": 1707725},
    {"code": "DL-NDL", "name": "New Delhi", "headquarters": "New Delhi", "lat": 28.6139, "lon": 77.2090, "area_km2": 35.0, "population": 133713},
    {"code": "DL-NTH", "name": "North Delhi", "headquarters": "Burari", "lat": 28.7460, "lon": 77.1025, "area_km2": 59.0, "population": 883418},
    {"code": "DL-NEA", "name": "North East Delhi", "headquarters": "Yamuna Vihar", "lat": 28.6935, "lon": 77.2926, "area_km2": 56.0, "population": 2240749},
    {"code": "DL-NWT", "name": "North West Delhi", "headquarters": "Rohini", "lat": 28.7041, "lon": 77.1025, "area_km2": 234.4, "population": 3651261},
    {"code": "DL-OLD", "name": "Old Delhi", "headquarters": "Chandni Chowk", "lat": 28.6562, "lon": 77.2410, "area_km2": None, "population": None},
    {"code": "DL-ONT", "name": "Outer North Delhi", "headquarters": "Narela", "lat": 28.8386, "lon": 77.0921, "area_km2": None, "population": None},
    {"code": "DL-STH", "name": "South Delhi", "headquarters": "Saket", "lat": 28.5245, "lon": 77.1855, "area_km2": 249.0, "population": 2733752},
    {"code": "DL-SES", "name": "South East Delhi", "headquarters": "Kalkaji", "lat": 28.5494, "lon": 77.2500, "area_km2": 102.0, "population": 637775},
    {"code": "DL-SWT", "name": "South West Delhi", "headquarters": "Dwarka", "lat": 28.5921, "lon": 77.0460, "area_km2": 421.0, "population": 2292363},
    {"code": "DL-WST", "name": "West Delhi", "headquarters": "Janakpuri", "lat": 28.6219, "lon": 77.0878, "area_km2": 131.0, "population": 2531583},
]

DL_STATE = {
    "code": "DL",
    "name": "Delhi (NCT)",
    "capital": "New Delhi",
    "lat": 28.6139,
    "lon": 77.2090,
    "area_km2": 1483.0,
    "population": 16787941,
    "district_count": 13,
}
