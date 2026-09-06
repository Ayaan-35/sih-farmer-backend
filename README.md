# SIH26132 — Market Discovery & Price Intelligence Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.1%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![NumPy](https://img.shields.io/badge/NumPy-Vectorized%20math-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20analysis-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
![License](https://img.shields.io/badge/License-Not%20specified-lightgrey)

**Market Discovery & Price Intelligence Engine** is the backend for Smart India Hackathon 2026 problem statement **SIH26132**. It helps farmers identify viable APMC markets by combining GPS-based mandi discovery, historical modal-price momentum, and a net-realization calculation that accounts for transport costs.

Instead of recommending the mandi with only the highest listed price, the engine ranks options by expected net profit. This supports more practical decisions: where to sell, whether a farther market is worthwhile, and whether current price movement is upward or downward.

## Core Features

### Geospatial nearest-mandi discovery

`MandiService.get_nearby_mandis()` uses the vectorized `haversine_np()` implementation to calculate great-circle distances from a farmer's latitude and longitude to APMC GPS coordinates in `mandi_data.csv`. It groups market locations, sorts them by `distance_km`, and returns the nearest requested number of mandis.

### Seven-day rolling price trend engine

`MandiService.get_price_trends()` filters historical records by crop and district, identifies the newest modal price, and compares it with the average modal price in the preceding seven-day window. The response reports an `Upward` trend when the current price is greater than or equal to the rolling average; otherwise it reports `Downward`.

### Net realization optimizer

`POST /api/recommend` evaluates eligible mandi listings for a crop and calculates:

```text
gross_earnings = quantity_kg × modal_price_per_kg
transport_cost = distance_km × ₹4
net_profit     = gross_earnings − transport_cost
```

The endpoint returns every eligible option sorted by net profit, marks loss-making routes with `is_viable: false`, and provides a plain-language advisory. The transport rate is currently a fixed one-way estimate of **₹4 per kilometre**.

### Cloud data layer with fallback

The application reads crop and mandi-price data from Supabase PostgreSQL through the Supabase client. If a database query fails or returns no records, the relevant listing endpoints and recommendation flow use the built-in in-memory fallback dataset, preserving a dependable demo path.

## Architecture

```text
Client / Frontend
        │
        ▼
FastAPI routes + Pydantic validation
        ├──────────────► Supabase PostgreSQL (live crop and mandi data)
        │                         │
        │                         └── failure / empty-result fallback
        ▼
MandiService ─────────► mandi_data.csv (GPS and historical modal prices)
        │
        ├── NumPy Haversine distance calculations
        └── Pandas seven-day price analysis
```

## API Contract

Interactive OpenAPI documentation is available at [`/docs`](http://127.0.0.1:8000/docs) while the service is running.

| Method | Endpoint | Query / body payload | Response summary |
| --- | --- | --- | --- |
| `GET` | `/` | None | Service status, project identifier, and database label. |
| `GET` | `/api/crops` | None | Available crop names from Supabase or fallback data. |
| `GET` | `/api/mandis` | None | All mandi-price listings, source (`database` or `fallback`), and total count. |
| `POST` | `/api/recommend` | JSON: `crop_name` (2+ chars), `quantity_kg` (>0, ≤100000), optional `max_distance_km` (>0, ≤2000; default 200). | Best mandi, net profit, ranked options, viability flags, and advisory. Returns `404` for an untracked crop and `400` when no market meets the distance limit. |
| `GET` | `/api/nearby-mandis` | `lat` (float), `lon` (float), optional `top_k` (integer 1–20; default 3). | Farmer coordinates plus nearest mandi records with GPS coordinates and `distance_km`. |
| `GET` | `/api/mandi-prices` | `crop` (2+ chars), `district` (2+ chars). | Latest modal price, seven-day average, latest record date, and `Upward` / `Downward` trend. Returns `404` if no matching historical record exists. |
| `GET` | `/docs` | None | Swagger UI generated from the FastAPI OpenAPI schema. |

### Recommendation request example

```json
{
  "crop_name": "Tomato",
  "quantity_kg": 500,
  "max_distance_km": 200
}
```

### Validation and errors

- FastAPI/Pydantic returns `422 Unprocessable Entity` when route or request-body constraints are invalid, such as missing coordinates, `top_k` outside 1–20, or a non-positive quantity.
- `GET /api/mandi-prices` returns `404 Not Found` when the requested crop/district pair has no CSV history.
- `POST /api/recommend` returns `404 Not Found` for an untracked crop and `400 Bad Request` when the crop exists but no mandi is within the requested distance.

## Sample Responses

### `GET /api/nearby-mandis?lat=18.5204&lon=73.8567&top_k=3`

```json
{
  "farmer_location": { "lat": 18.5204, "lon": 73.8567 },
  "top_k": 3,
  "nearby_mandis": [
    { "mandi_name": "APMC Pune", "district": "pune", "latitude": 18.5204, "longitude": 73.8567, "distance_km": 0.0 },
    { "mandi_name": "APMC Shirur", "district": "pune", "latitude": 18.8272, "longitude": 74.3773, "distance_km": 64.59 },
    { "mandi_name": "APMC Baramati", "district": "pune", "latitude": 18.1517, "longitude": 74.577, "distance_km": 86.38 }
  ]
}
```

### `GET /api/mandi-prices?crop=Tomato&district=Pune`

```json
{
  "crop": "Tomato",
  "district": "Pune",
  "latest_date": "2026-09-01",
  "current_modal_price_per_quintal": 2700.0,
  "7_day_average_price": 2562.5,
  "trend_status": "Upward"
}
```

> Sample values are representative of the CSV-backed API response; the exact result follows the records currently present in `mandi_data.csv`.

## Repository Structure

```text
sih-farmer-backend/
├── database.py               # Supabase client initialization and configuration
├── main.py                   # FastAPI app, routes, schemas, fallback data, optimizer
├── mandi_service.py          # Haversine and CSV-backed mandi/price service
├── mandi_data.csv            # Historical APMC coordinates and modal-price records
├── test_mandi_features.py    # Service and FastAPI endpoint integration tests
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables (do not commit secrets)
└── README.md                 # Project documentation
```

## Prerequisites

- Python 3.12 or newer
- A Supabase project for live crop and mandi data (optional for local fallback mode)
- Git

## Installation and Local Run

```bash
git clone https://github.com/Ayaan-35/sih-farmer-backend.git
cd sih-farmer-backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies and configure local environment variables:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key
```

`SUPABASE_URL` and `SUPABASE_KEY` are required for live Supabase reads. Do not commit `.env` files or production credentials. The current code can serve fallback mandi data when live data is unavailable.

Start the API:

```bash
uvicorn main:app --reload
```

The API is then available at `http://127.0.0.1:8000`, with interactive documentation at `http://127.0.0.1:8000/docs`.

## Automated Testing

The test script checks the CSV-backed `MandiService` and the FastAPI endpoints through `TestClient`.

```bash
python test_mandi_features.py
```

It verifies nearby-mandi ranking, price-trend response fields, and successful responses from `/api/nearby-mandis` and `/api/mandi-prices`.

## Deploying to Render

1. Push this repository to GitHub and create a Supabase project/table setup used by the backend.
2. In [Render](https://render.com/), select **New +** → **Web Service** and connect the GitHub repository.
3. Choose a Python runtime, then set the build command:

   ```bash
   pip install -r requirements.txt
   ```

4. Set the start command:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

5. Add these environment variables in Render's service settings:

   | Variable | Purpose |
   | --- | --- |
   | `SUPABASE_URL` | Supabase project URL used by the database client. |
   | `SUPABASE_KEY` | Supabase API key authorized for the required read operations. |

6. Deploy the service, open its generated URL followed by `/docs`, and exercise the health check plus core endpoints.

For a secure production deployment, keep credentials exclusively in Render environment settings, limit the Supabase key to the least privilege required, and configure the application's CORS allowlist for the deployed frontend origin before public release.

## Technology Stack

- **FastAPI + Uvicorn** — API framework and ASGI server
- **Pydantic** — request validation and response contracts
- **Supabase PostgreSQL** — live market and crop data
- **NumPy** — vectorized Haversine distance calculations
- **Pandas** — CSV loading and rolling historical price analysis
- **python-dotenv** — local environment-variable loading

## SIH Demo Flow

1. Call `/api/nearby-mandis` with a farmer's GPS location to show nearby APMCs.
2. Call `/api/mandi-prices` for a crop and district to explain recent price momentum.
3. Submit the farmer's crop, quantity, and travel limit to `/api/recommend`.
4. Show that the selected mandi maximizes net realization after transport—not merely the posted price.

---

Built for **Smart India Hackathon 2026** — SIH26132.
