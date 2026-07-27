"""
Kerala district reference dataset -- 14 districts, confirmed against the
Wikipedia "List of districts of Kerala" and Government of Kerala district
portal (igod.gov.in) as of this build. Population figures are 2011 Census
(Kerala's district list has been stable since 1984, unlike some northern
states with recent reorganizations).

Same shape as app/data/tn_districts.py -- see that file for field docs.
"""

from typing import TypedDict


class District(TypedDict):
    code: str
    name: str
    headquarters: str
    lat: float
    lon: float
    area_km2: float
    population: int


KL_DISTRICTS: list[District] = [
    {"code": "KL-TVM", "name": "Thiruvananthapuram", "headquarters": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366, "area_km2": 2192.0, "population": 3301427},
    {"code": "KL-KLM", "name": "Kollam", "headquarters": "Kollam", "lat": 8.8932, "lon": 76.6141, "area_km2": 2491.0, "population": 2635375},
    {"code": "KL-PTA", "name": "Pathanamthitta", "headquarters": "Pathanamthitta", "lat": 9.2648, "lon": 76.7870, "area_km2": 2652.0, "population": 1197412},
    {"code": "KL-ALP", "name": "Alappuzha", "headquarters": "Alappuzha", "lat": 9.4981, "lon": 76.3388, "area_km2": 1414.0, "population": 2127789},
    {"code": "KL-KTM", "name": "Kottayam", "headquarters": "Kottayam", "lat": 9.5916, "lon": 76.5222, "area_km2": 2203.0, "population": 1974551},
    {"code": "KL-IDK", "name": "Idukki", "headquarters": "Painavu", "lat": 9.8455, "lon": 76.9744, "area_km2": 4358.0, "population": 1108974},
    {"code": "KL-EKM", "name": "Ernakulam", "headquarters": "Kakkanad (Kochi)", "lat": 9.9816, "lon": 76.3312, "area_km2": 3068.0, "population": 3282388},
    {"code": "KL-TSR", "name": "Thrissur", "headquarters": "Thrissur", "lat": 10.5276, "lon": 76.2144, "area_km2": 3032.0, "population": 3121200},
    {"code": "KL-PKD", "name": "Palakkad", "headquarters": "Palakkad", "lat": 10.7867, "lon": 76.6548, "area_km2": 4482.0, "population": 2809934},
    {"code": "KL-MLP", "name": "Malappuram", "headquarters": "Malappuram", "lat": 11.0510, "lon": 76.0711, "area_km2": 3550.0, "population": 4112920},
    {"code": "KL-KKD", "name": "Kozhikode", "headquarters": "Kozhikode", "lat": 11.2588, "lon": 75.7804, "area_km2": 2345.0, "population": 3086293},
    {"code": "KL-WYD", "name": "Wayanad", "headquarters": "Kalpetta", "lat": 11.6085, "lon": 76.0837, "area_km2": 2131.0, "population": 817420},
    {"code": "KL-KNR", "name": "Kannur", "headquarters": "Kannur", "lat": 11.8745, "lon": 75.3704, "area_km2": 2966.0, "population": 2523003},
    {"code": "KL-KSD", "name": "Kasaragod", "headquarters": "Kasaragod", "lat": 12.4996, "lon": 74.9869, "area_km2": 1992.0, "population": 1307375},
]

KL_STATE = {
    "code": "KL",
    "name": "Kerala",
    "capital": "Thiruvananthapuram",
    "lat": 8.5241,
    "lon": 76.9366,
    "area_km2": 38863.0,
    "population": 33406061,
    "district_count": 14,
}
