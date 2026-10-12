# Climate Hazard Trend Analyzer

Full-stack web app that analyzes historical heatwave frequency and intensity for a chosen region, built for the Dygnify Ventures Full-Stack Developer case study.

**Scope:** heatwave only (working, well-reasoned analysis over a multi-hazard shell).

## Features

- Region selection via city/state search (Open-Meteo Geocoding) or Leaflet map click / lat-lon box
- Heatwave hazard (default / locked)
- Configurable year range (1940–2024, Open-Meteo archive limits)
- Time-series chart of yearly heatwave counts + 5-year rolling mean (Chart.js)
- Summary insight comparing early vs late periods, with OLS trend slope
- CSV export of yearly metrics
- Backend caching in MongoDB Atlas (in-memory fallback if Mongo is down)
- Input validation + per-IP rate limiting

## Architecture

```
React (Vite)  →  FastAPI  →  MongoDB Atlas (cache)
                    ↓
              Open-Meteo Historical + Geocoding APIs
```

| Layer | Stack |
|-------|--------|
| Frontend | React, TypeScript, Vite, Chart.js, Leaflet |
| Backend | FastAPI, pandas/numpy, scipy, httpx, slowapi |
| Database | MongoDB Atlas (NoSQL) via Motor |
| Weather | Open-Meteo Historical Weather API (ERA5-based archive) |

## Hazard logic

1. Fetch daily `temperature_2m_max` for the selected point and years.
2. Compute the **95th percentile** of Tmax over that full selected window.
3. Mark **hot days** where `tmax > P95`.
4. A **heatwave** is **3+ consecutive** hot calendar days.
5. Yearly metrics: event count, mean duration, mean intensity (`mean(tmax − P95)` over event days).
6. Trend: ordinary least squares of yearly event count vs year; report slope per decade and R².
7. Insight: percent change comparing the first vs last decade (or half-window if shorter).

## Assumptions

- Analysis uses a **point** query (city center, map click, or **bbox center**). It is not a true areal average.
- P95 is computed from the **selected period**, not a fixed WMO baseline (e.g. 1961–1990).
- Heatwave definition matches the brief’s example only (3-day / 95th percentile).
- Years with ≥30% missing daily values are flagged `low_confidence` but still included.
- Open-Meteo archive data is reanalysis-based (not station observations).

## Project layout

```
backend/          FastAPI app
  app/
    main.py
    routers/analyze.py
    services/     heatwave, trends, openmeteo
  tests/
frontend/         React + Vite SPA
render.yaml       Render Blueprint for the API
```

## Local setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- MongoDB Atlas URI (optional locally — API falls back to in-memory cache)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # or cp .env.example .env
# Edit .env: set MONGODB_URI and CORS_ORIGINS
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET http://localhost:8000/api/health`

### Frontend

```bash
cd frontend
npm install
copy .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`).

### Tests

```bash
cd backend
pytest -q
```

## API

### `POST /api/analyze`

```json
{
  "lat": 28.6139,
  "lon": 77.209,
  "start_year": 1990,
  "end_year": 2020,
  "label": "New Delhi, India"
}
```

Optional bbox fields `north`, `south`, `east`, `west` — analysis runs at the box center.

### `GET /api/geocode?q=Delhi`

### `GET /api/health`

## Deploy

Repo: https://github.com/jennymeshaiah09/climate-hazard-analyzer

### Backend (Render)

1. New **Web Service** → connect this GitHub repo.
2. Build: `pip install -r backend/requirements.txt`
3. Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars:
   - `MONGODB_URI` — Atlas connection string (optional; in-memory cache is used if Mongo is unreachable)
   - `MONGODB_DB=climate_hazard`
   - `CORS_ORIGINS` — your Vercel origin (or `*` for a quick demo)
   - `PYTHON_VERSION=3.12.8`
5. Or apply [`render.yaml`](render.yaml) as a Blueprint.

### Frontend (Vercel)

1. Import the repo; set **Root Directory** to `frontend`.
2. Framework preset: Vite. Build: `npm run build`, output: `dist`.
3. Env: `VITE_API_URL=https://<your-render-service>.onrender.com`
4. After deploy, set Render `CORS_ORIGINS` to the Vercel URL and redeploy the API.

### MongoDB Atlas

1. Create a free cluster and database user.
2. Allow network access from Render (`0.0.0.0/0` is typical on free tier).
3. Paste the connection string into `MONGODB_URI`.

**Deployed URLs:** add your Render API URL and Vercel app URL here after you create the services in the dashboards.

## What I would improve with more time

- Fixed climatology baseline (e.g. 1961–1990) and true gridded / areal averages
- Drought and heavy-rainfall hazard modules
- Mann–Kendall trend test and PDF report export
- Pre-warm popular cities; Redis for shared cache across instances
- Auth / saved analyses

## AI tools used

- **Cursor (Composer)** — scaffolded the monorepo, hazard logic, API, React UI, tests, and README from the case-study brief; iterative test fixes and deploy config.

## License

Case-study submission — not for republication of the confidential brief PDF.
