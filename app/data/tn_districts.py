"""
Tamil Nadu district reference dataset.

Source: Government of Tamil Nadu district portals (tn.gov.in) and the
2011 Census of India district tables (population figures are the most
recent full decadal census; TN's 2021 Census was postponed nationally).
Headquarters coordinates are the town/city centroid of each district's
administrative headquarters, used as the sampling point for all live
environmental data (air quality, weather, fire detections).

This is reference/master data, not observational data. Every "live" field
served by the API (AQI, PM2.5, temperature, wind, etc.) is fetched at
request time from real external providers keyed off the lat/lon here.

Fields:
    code           3-letter TN administrative code
    name           Official district name
    headquarters   Headquarters town/city
    lat, lon       Headquarters coordinates (WGS84)
    area_km2       District area in square kilometres
    population     2011 Census population
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


TN_DISTRICTS: list[District] = [
    {"code": "ARI", "name": "Ariyalur", "headquarters": "Ariyalur", "lat": 11.1401, "lon": 79.0782, "area_km2": 2027.6, "population": 754894},
    {"code": "CHG", "name": "Chengalpattu", "headquarters": "Chengalpattu", "lat": 12.6921, "lon": 79.9753, "area_km2": 2802.6, "population": 2556244},
    {"code": "CHN", "name": "Chennai", "headquarters": "Chennai", "lat": 13.0827, "lon": 80.2707, "area_km2": 462.3, "population": 6748026},
    {"code": "COI", "name": "Coimbatore", "headquarters": "Coimbatore", "lat": 11.0168, "lon": 76.9558, "area_km2": 4950.7, "population": 3458045},
    {"code": "CUD", "name": "Cuddalore", "headquarters": "Cuddalore", "lat": 11.7480, "lon": 79.7714, "area_km2": 3870.0, "population": 2605914},
    {"code": "DHA", "name": "Dharmapuri", "headquarters": "Dharmapuri", "lat": 12.1277, "lon": 78.1580, "area_km2": 4735.7, "population": 1506843},
    {"code": "DIN", "name": "Dindigul", "headquarters": "Dindigul", "lat": 10.3673, "lon": 77.9803, "area_km2": 6289.1, "population": 2159775},
    {"code": "ERO", "name": "Erode", "headquarters": "Erode", "lat": 11.3410, "lon": 77.7172, "area_km2": 6036.0, "population": 2251744},
    {"code": "KAL", "name": "Kallakurichi", "headquarters": "Kallakurichi", "lat": 11.7401, "lon": 78.9597, "area_km2": 3440.8, "population": 1370281},
    {"code": "KAC", "name": "Kancheepuram", "headquarters": "Kancheepuram", "lat": 12.8342, "lon": 79.7036, "area_km2": 1800.2, "population": 1166401},
    {"code": "KAY", "name": "Kanyakumari", "headquarters": "Nagercoil", "lat": 8.1780, "lon": 77.4346, "area_km2": 1729.2, "population": 1870374},
    {"code": "KAR", "name": "Karur", "headquarters": "Karur", "lat": 10.9601, "lon": 78.0766, "area_km2": 3022.3, "population": 1064493},
    {"code": "KRI", "name": "Krishnagiri", "headquarters": "Krishnagiri", "lat": 12.5186, "lon": 78.2137, "area_km2": 5414.4, "population": 1883731},
    {"code": "MAD", "name": "Madurai", "headquarters": "Madurai", "lat": 9.9252, "lon": 78.1198, "area_km2": 3846.4, "population": 3038252},
    {"code": "MAY", "name": "Mayiladuthurai", "headquarters": "Mayiladuthurai", "lat": 11.1017, "lon": 79.6521, "area_km2": 1237.1, "population": 918356},
    {"code": "NAG", "name": "Nagapattinam", "headquarters": "Nagapattinam", "lat": 10.7657, "lon": 79.8424, "area_km2": 1459.0, "population": 697069},
    {"code": "NAM", "name": "Namakkal", "headquarters": "Namakkal", "lat": 11.2189, "lon": 78.1674, "area_km2": 3573.4, "population": 1726601},
    {"code": "NIL", "name": "Nilgiris", "headquarters": "Udagamandalam (Ooty)", "lat": 11.4102, "lon": 76.6950, "area_km2": 2452.5, "population": 735394},
    {"code": "PER", "name": "Perambalur", "headquarters": "Perambalur", "lat": 11.2342, "lon": 78.8807, "area_km2": 1836.6, "population": 565223},
    {"code": "PUD", "name": "Pudukkottai", "headquarters": "Pudukkottai", "lat": 10.3813, "lon": 78.8213, "area_km2": 4847.8, "population": 1618345},
    {"code": "RAM", "name": "Ramanathapuram", "headquarters": "Ramanathapuram", "lat": 9.3639, "lon": 78.8395, "area_km2": 4243.1, "population": 1353445},
    {"code": "RAN", "name": "Ranipet", "headquarters": "Ranipet", "lat": 12.9249, "lon": 79.3308, "area_km2": 2234.3, "population": 1210277},
    {"code": "SAL", "name": "Salem", "headquarters": "Salem", "lat": 11.6643, "lon": 78.1460, "area_km2": 5245.0, "population": 3482056},
    {"code": "SIV", "name": "Sivaganga", "headquarters": "Sivaganga", "lat": 9.8433, "lon": 78.4809, "area_km2": 4086.0, "population": 1339101},
    {"code": "TEN", "name": "Tenkasi", "headquarters": "Tenkasi", "lat": 8.9598, "lon": 77.3152, "area_km2": 2916.1, "population": 1407627},
    {"code": "THA", "name": "Thanjavur", "headquarters": "Thanjavur", "lat": 10.7870, "lon": 79.1378, "area_km2": 3396.6, "population": 2405890},
    {"code": "THE", "name": "Theni", "headquarters": "Theni", "lat": 10.0104, "lon": 77.4768, "area_km2": 3066.0, "population": 1245899},
    {"code": "THO", "name": "Thoothukudi", "headquarters": "Thoothukudi", "lat": 8.7642, "lon": 78.1348, "area_km2": 4621.0, "population": 1750176},
    {"code": "TIC", "name": "Tiruchirappalli", "headquarters": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047, "area_km2": 4407.0, "population": 2722290},
    {"code": "TIN", "name": "Tirunelveli", "headquarters": "Tirunelveli", "lat": 8.7139, "lon": 77.7567, "area_km2": 3842.4, "population": 1665253},
    {"code": "TIA", "name": "Tirupathur", "headquarters": "Tirupattur", "lat": 12.4967, "lon": 78.5734, "area_km2": 1792.9, "population": 1111812},
    {"code": "TIP", "name": "Tiruppur", "headquarters": "Tiruppur", "lat": 11.1085, "lon": 77.3411, "area_km2": 5186.3, "population": 2479052},
    {"code": "TAL", "name": "Tiruvallur", "headquarters": "Tiruvallur", "lat": 13.1231, "lon": 79.9120, "area_km2": 3444.2, "population": 3728104},
    {"code": "TAN", "name": "Tiruvannamalai", "headquarters": "Tiruvannamalai", "lat": 12.2253, "lon": 79.0747, "area_km2": 6191.0, "population": 2464875},
    {"code": "TAR", "name": "Tiruvarur", "headquarters": "Tiruvarur", "lat": 10.7727, "lon": 79.6367, "area_km2": 2161.0, "population": 1264277},
    {"code": "VEL", "name": "Vellore", "headquarters": "Vellore", "lat": 12.9165, "lon": 79.1325, "area_km2": 2222.1, "population": 1614242},
    {"code": "VIL", "name": "Viluppuram", "headquarters": "Viluppuram", "lat": 11.9401, "lon": 79.4861, "area_km2": 3725.5, "population": 2093003},
    {"code": "VIR", "name": "Virudhunagar", "headquarters": "Virudhunagar", "lat": 9.5810, "lon": 77.9624, "area_km2": 4288.0, "population": 1942288},
]

TN_STATE = {
    "code": "TN",
    "name": "Tamil Nadu",
    "capital": "Chennai",
    "lat": 11.1271,
    "lon": 78.6569,
    "area_km2": 130058.0,
    "population": 72147030,
    "district_count": 38,
}


def get_district_by_code(code: str) -> District | None:
    code = code.upper()
    for d in TN_DISTRICTS:
        if d["code"] == code:
            return d
    return None


def get_district_by_name(name: str) -> District | None:
    name = name.strip().lower()
    for d in TN_DISTRICTS:
        if d["name"].lower() == name:
            return d
    return None


def search_districts(query: str) -> list[District]:
    q = query.strip().lower()
    return [d for d in TN_DISTRICTS if q in d["name"].lower() or q in d["headquarters"].lower()]
