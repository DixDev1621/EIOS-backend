"""
National registry -- the generalization point that turns this from a
Tamil-Nadu-only build into an all-India platform.

Two tiers, deliberately kept separate and honestly labeled:

1. INDIA_STATES: all 28 states + 8 union territories (36 total), with
   real capital-city coordinates, area and population, used to power the
   national home page and state-level navigation for the *whole country*.

2. LIVE_DISTRICT_DATASETS: states for which this build additionally ships
   full district-level reference data (headquarters coordinates), which
   is what unlocks live AQI/weather/forecast/health-score/recommendation
   endpoints per district. Adding a new state to this tier means adding a
   `<state>_districts.py` file following the exact shape of
   `tn_districts.py` and registering it here -- no other code changes
   required, because every router/service already operates generically
   on `(lat, lon)` and a flat district list.

Only 3 states are in tier 2 in this build (Tamil Nadu, Kerala, Delhi) --
see docs/ROADMAP.md for why full district-level coverage of all 36
states/UTs (roughly 800 districts) was not hand-fabricated in one pass,
and the exact recipe for adding the rest with verified data.
"""

from typing import TypedDict, Optional

from app.data import tn_districts, kerala_districts, delhi_districts


class StateSummary(TypedDict):
    code: str
    name: str
    capital: str
    lat: float
    lon: float
    area_km2: float
    population: int
    is_union_territory: bool
    district_data_available: bool


# Real, well-established figures: capital coordinates (unambiguous,
# stable facts) and 2011 Census area/population (the last full decadal
# census; the 2021 Census was postponed nationally and has not yet been
# conducted). Newer UTs created after 2011 (Telangana in 2014, J&K/Ladakh
# split in 2019) use the most recently published administrative figures
# for those specific units.
INDIA_STATES: list[StateSummary] = [
    {"code": "AP", "name": "Andhra Pradesh", "capital": "Amaravati", "lat": 16.5062, "lon": 80.6480, "area_km2": 162970.0, "population": 49386799, "is_union_territory": False, "district_data_available": False},
    {"code": "AR", "name": "Arunachal Pradesh", "capital": "Itanagar", "lat": 27.0844, "lon": 93.6053, "area_km2": 83743.0, "population": 1383727, "is_union_territory": False, "district_data_available": False},
    {"code": "AS", "name": "Assam", "capital": "Dispur", "lat": 26.1433, "lon": 91.7898, "area_km2": 78438.0, "population": 31205576, "is_union_territory": False, "district_data_available": False},
    {"code": "BR", "name": "Bihar", "capital": "Patna", "lat": 25.5941, "lon": 85.1376, "area_km2": 94163.0, "population": 104099452, "is_union_territory": False, "district_data_available": False},
    {"code": "CT", "name": "Chhattisgarh", "capital": "Raipur", "lat": 21.2514, "lon": 81.6296, "area_km2": 135192.0, "population": 25545198, "is_union_territory": False, "district_data_available": False},
    {"code": "GA", "name": "Goa", "capital": "Panaji", "lat": 15.4909, "lon": 73.8278, "area_km2": 3702.0, "population": 1458545, "is_union_territory": False, "district_data_available": False},
    {"code": "GJ", "name": "Gujarat", "capital": "Gandhinagar", "lat": 23.2156, "lon": 72.6369, "area_km2": 196244.0, "population": 60439692, "is_union_territory": False, "district_data_available": False},
    {"code": "HR", "name": "Haryana", "capital": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "area_km2": 44212.0, "population": 25351462, "is_union_territory": False, "district_data_available": False},
    {"code": "HP", "name": "Himachal Pradesh", "capital": "Shimla", "lat": 31.1048, "lon": 77.1734, "area_km2": 55673.0, "population": 6864602, "is_union_territory": False, "district_data_available": False},
    {"code": "JH", "name": "Jharkhand", "capital": "Ranchi", "lat": 23.3441, "lon": 85.3096, "area_km2": 79716.0, "population": 32988134, "is_union_territory": False, "district_data_available": False},
    {"code": "KA", "name": "Karnataka", "capital": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "area_km2": 191791.0, "population": 61095297, "is_union_territory": False, "district_data_available": False},
    {"code": "KL", "name": "Kerala", "capital": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366, "area_km2": 38863.0, "population": 33406061, "is_union_territory": False, "district_data_available": True},
    {"code": "MP", "name": "Madhya Pradesh", "capital": "Bhopal", "lat": 23.2599, "lon": 77.4126, "area_km2": 308245.0, "population": 72626809, "is_union_territory": False, "district_data_available": False},
    {"code": "MH", "name": "Maharashtra", "capital": "Mumbai", "lat": 19.0760, "lon": 72.8777, "area_km2": 307713.0, "population": 112374333, "is_union_territory": False, "district_data_available": False},
    {"code": "MN", "name": "Manipur", "capital": "Imphal", "lat": 24.8170, "lon": 93.9368, "area_km2": 22327.0, "population": 2855794, "is_union_territory": False, "district_data_available": False},
    {"code": "ML", "name": "Meghalaya", "capital": "Shillong", "lat": 25.5788, "lon": 91.8933, "area_km2": 22429.0, "population": 2966889, "is_union_territory": False, "district_data_available": False},
    {"code": "MZ", "name": "Mizoram", "capital": "Aizawl", "lat": 23.7271, "lon": 92.7176, "area_km2": 21081.0, "population": 1097206, "is_union_territory": False, "district_data_available": False},
    {"code": "NL", "name": "Nagaland", "capital": "Kohima", "lat": 25.6751, "lon": 94.1086, "area_km2": 16579.0, "population": 1978502, "is_union_territory": False, "district_data_available": False},
    {"code": "OR", "name": "Odisha", "capital": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245, "area_km2": 155707.0, "population": 41974218, "is_union_territory": False, "district_data_available": False},
    {"code": "PB", "name": "Punjab", "capital": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "area_km2": 50362.0, "population": 27743338, "is_union_territory": False, "district_data_available": False},
    {"code": "RJ", "name": "Rajasthan", "capital": "Jaipur", "lat": 26.9124, "lon": 75.7873, "area_km2": 342239.0, "population": 68548437, "is_union_territory": False, "district_data_available": False},
    {"code": "SK", "name": "Sikkim", "capital": "Gangtok", "lat": 27.3389, "lon": 88.6065, "area_km2": 7096.0, "population": 610577, "is_union_territory": False, "district_data_available": False},
    {"code": "TN", "name": "Tamil Nadu", "capital": "Chennai", "lat": 13.0827, "lon": 80.2707, "area_km2": 130058.0, "population": 72147030, "is_union_territory": False, "district_data_available": True},
    {"code": "TG", "name": "Telangana", "capital": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "area_km2": 112077.0, "population": 35003674, "is_union_territory": False, "district_data_available": False},
    {"code": "TR", "name": "Tripura", "capital": "Agartala", "lat": 23.8315, "lon": 91.2868, "area_km2": 10486.0, "population": 3673917, "is_union_territory": False, "district_data_available": False},
    {"code": "UP", "name": "Uttar Pradesh", "capital": "Lucknow", "lat": 26.8467, "lon": 80.9462, "area_km2": 240928.0, "population": 199812341, "is_union_territory": False, "district_data_available": False},
    {"code": "UT", "name": "Uttarakhand", "capital": "Dehradun", "lat": 30.3165, "lon": 78.0322, "area_km2": 53483.0, "population": 10086292, "is_union_territory": False, "district_data_available": False},
    {"code": "WB", "name": "West Bengal", "capital": "Kolkata", "lat": 22.5726, "lon": 88.3639, "area_km2": 88752.0, "population": 91276115, "is_union_territory": False, "district_data_available": False},
    # --- Union Territories ---
    {"code": "AN", "name": "Andaman and Nicobar Islands", "capital": "Port Blair", "lat": 11.6234, "lon": 92.7265, "area_km2": 8249.0, "population": 380581, "is_union_territory": True, "district_data_available": False},
    {"code": "CH", "name": "Chandigarh", "capital": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "area_km2": 114.0, "population": 1055450, "is_union_territory": True, "district_data_available": False},
    {"code": "DN", "name": "Dadra and Nagar Haveli and Daman and Diu", "capital": "Daman", "lat": 20.3974, "lon": 72.8328, "area_km2": 603.0, "population": 585764, "is_union_territory": True, "district_data_available": False},
    {"code": "DL", "name": "Delhi (NCT)", "capital": "New Delhi", "lat": 28.6139, "lon": 77.2090, "area_km2": 1483.0, "population": 16787941, "is_union_territory": True, "district_data_available": True},
    {"code": "JK", "name": "Jammu and Kashmir", "capital": "Srinagar (summer) / Jammu (winter)", "lat": 34.0837, "lon": 74.7973, "area_km2": 42241.0, "population": 12267032, "is_union_territory": True, "district_data_available": False},
    {"code": "LA", "name": "Ladakh", "capital": "Leh", "lat": 34.1526, "lon": 77.5770, "area_km2": 59146.0, "population": 274289, "is_union_territory": True, "district_data_available": False},
    {"code": "LD", "name": "Lakshadweep", "capital": "Kavaratti", "lat": 10.5669, "lon": 72.6420, "area_km2": 32.0, "population": 64473, "is_union_territory": True, "district_data_available": False},
    {"code": "PY", "name": "Puducherry", "capital": "Puducherry", "lat": 11.9416, "lon": 79.8083, "area_km2": 490.0, "population": 1247953, "is_union_territory": True, "district_data_available": False},
]


def get_state(code: str) -> Optional[StateSummary]:
    code = code.upper()
    for s in INDIA_STATES:
        if s["code"] == code:
            return s
    return None


def list_states() -> list[StateSummary]:
    return INDIA_STATES


# ---------------------------------------------------------------------
# Tier 2: states/UTs with full live district-level datasets wired in.
# To add a state here: create app/data/<state>_districts.py following
# the exact shape of tn_districts.py, import it below, add its entry to
# this dict, and flip `district_data_available` to True for its code in
# INDIA_STATES above.
# ---------------------------------------------------------------------
LIVE_DISTRICT_DATASETS: dict[str, list[dict]] = {
    "TN": tn_districts.TN_DISTRICTS,
    "KL": kerala_districts.KL_DISTRICTS,
    "DL": delhi_districts.DL_DISTRICTS,
}

LIVE_STATE_DETAIL: dict[str, dict] = {
    "TN": tn_districts.TN_STATE,
    "KL": kerala_districts.KL_STATE,
    "DL": delhi_districts.DL_STATE,
}


def all_live_districts() -> list[dict]:
    """Every district across every state with live data, flattened, each
    tagged with its owning state code for disambiguation (a few district
    names repeat across states, e.g. Hamirpur exists in both HP and UP --
    only relevant once more states are added, but we tag from day one)."""
    flattened: list[dict] = []
    for state_code, districts in LIVE_DISTRICT_DATASETS.items():
        for d in districts:
            flattened.append({**d, "state_code": state_code})
    return flattened


def get_district_by_code(code: str) -> Optional[dict]:
    code = code.upper()
    for d in all_live_districts():
        if d["code"].upper() == code:
            return d
    return None


def get_district_by_name(name: str) -> Optional[dict]:
    name = name.strip().lower()
    for d in all_live_districts():
        if d["name"].lower() == name:
            return d
    return None


def search_all(query: str) -> dict:
    """Search across states (all 36) and live districts (currently TN/KL/DL)."""
    q = query.strip().lower()
    if not q:
        return {"states": [], "districts": []}

    matched_states = [s for s in INDIA_STATES if q in s["name"].lower()]
    matched_districts = [
        d for d in all_live_districts()
        if q in d["name"].lower() or q in d["headquarters"].lower()
    ]
    return {"states": matched_states, "districts": matched_districts}
