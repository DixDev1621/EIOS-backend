# EIOS Backend -- FastAPI service

Real-data backend for the India Environmental Intelligence OS (Tamil Nadu build).
No mock data, no placeholder endpoints: every response is computed from a live
public data provider or an on-the-fly-trained model.

## Data sources (all real)

| Domain | Provider | Key required? |
|---|---|---|
| Air quality (PM2.5, PM10, NO2, SO2, CO, O3) | [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) | No |
| Weather (temp, humidity, wind, rain, forecast) | [Open-Meteo Forecast API](https://open-meteo.com/en/docs) | No |
| Historical training data | [Open-Meteo Historical/Archive API](https://open-meteo.com/en/docs/historical-weather-api) | No |
| Active fires / crop burning | [NASA FIRMS](https://firms.modis.gov/api/) | Yes (free, instant) |
| Auth, database, storage | [Supabase](https://supabase.com) | Yes (free tier) |

AQI is computed with the **official CPCB National AQI breakpoint formula**
(`app/services/aqi_calculator.py`), not a third-party AQI number, so it matches
what Indian government dashboards report.

## Quick start

```bash
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in the values, see below
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger docs of every endpoint.

The API works with **zero keys configured** for AQI/weather (Open-Meteo needs
none). Fire alerts and Supabase-backed features (auth, persisted alerts) need
their respective keys -- see `docs/API_KEYS_SETUP.md` in the project root.

## Architecture

```
app/
  core/           settings, JWT auth, rate limiting, logging, cache
  data/           TN district reference dataset (real, sourced)
  services/       Open-Meteo, NASA FIRMS, AQI calculator, ML forecasting,
                  health score, recommendation engine, AI chat/query logic
  routers/        REST endpoints, grouped by resource
  schemas/        Pydantic request/response models
  db/             Supabase client factory
  main.py         FastAPI app, middleware, router registration
```

## Key design decisions

- **Deterministic "AI chat"**: `/api/v1/ai/*` answers officer questions
  (why is a district polluted, traffic-reduction scenarios, vulnerable
  districts) by composing real data, not by generating free text with an
  LLM -- every number in the answer is traceable back to a live source.
  This matters for anything an official might act on.
- **Forecasting is trained on real data, on demand**: `ml_service.py` fetches
  60 days of real historical PM2.5/weather for a district, trains an
  XGBoost model with time-series cross-validation, and reports SHAP-based
  reason codes plus a confidence score derived from cross-validated error
  -- never a hardcoded confidence number.
- **Health Score is a documented composite**, not a raw measurement --
  the formula and every input are returned in the response for audit.
- **Graceful degradation**: if `NASA_FIRMS_MAP_KEY` or Supabase credentials
  are missing, those specific features report `configured: false` / return
  503s with a clear message, instead of silently fabricating data.

## Running tests

```bash
pytest
```

## Docker

```bash
docker build -t eios-backend .
docker run -p 8000:8000 --env-file .env eios-backend
```
