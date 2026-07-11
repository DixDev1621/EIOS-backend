import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.aqi_calculator import compute_aqi, category_for

def test_good_air_quality():
    r = compute_aqi(pm25=10, pm10=20)
    assert r.category == "Good"
    assert r.aqi <= 50

def test_severe_air_quality():
    r = compute_aqi(pm25=300)
    assert r.category == "Severe"
    assert r.aqi > 400

def test_dominant_pollutant_selection():
    # NO2 breakpoint gives a higher sub-index than PM2.5 here
    r = compute_aqi(pm25=10, no2=300)
    assert r.dominant_pollutant == "no2"

def test_no_data_returns_none():
    assert compute_aqi() is None

def test_category_boundaries():
    assert category_for(50)[0] == "Good"
    assert category_for(51)[0] == "Satisfactory"
    assert category_for(500)[0] == "Severe"

if __name__ == "__main__":
    test_good_air_quality()
    test_severe_air_quality()
    test_dominant_pollutant_selection()
    test_no_data_returns_none()
    test_category_boundaries()
    print("ALL AQI TESTS PASSED")
