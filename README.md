# 🏛️ SIH 2026 — Smart Market Discovery & Price Intelligence Backend

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Vectorized-013243?logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458?logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

> **Problem Statement SIH26132** — A production-ready backend that helps Maharashtra farmers discover the most profitable APMC Mandi for selling their crops, powered by real-time database queries, geospatial analytics, and price trend intelligence.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Local Setup](#-local-setup)
- [Testing](#-testing)
- [Environment Variables](#-environment-variables)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                        (main.py)                                │
├──────────────────┬──────────────────┬───────────────────────────┤
│  Cloud Database  │  Geolocation &   │   Recommendation          │
│  Layer           │  Analytics       │   Engine                  │
│                  │  Service         │                           │
│  • Supabase      │                  │  • Net realisation calc   │
│    PostgreSQL    │  • Haversine GPS │  • Revenue − Transport    │
│  • Real-time     │    proximity     │  • Distance-based cost    │
│    crop/mandi    │  • 7-day price   │  • Smart advisory         │
│    listings      │    trend window  │    generation             │
│  • PostgREST     │  • Offline CSV   │  • Viability flagging     │
│    joins         │    dataset       │                           │
├──────────────────┼──────────────────┼───────────────────────────┤
│  database.py     │ mandi_service.py │  main.py (POST /recommend)│
│                  │ mandi_data.csv   │                           │
└──────────────────┴──────────────────┴───────────────────────────┘
```

### 1. Cloud Database Layer — `database.py`

- Connects to **Supabase PostgreSQL** via the official Python SDK.
- Credentials loaded from `.env` using `python-dotenv`.
- Exposes a shared `supabase` client imported by the application layer.
- Tables: `crops`, `mandis`, `mandi_prices` (with foreign key joins).

### 2. Geolocation & Analytics Service — `mandi_service.py`

| Feature | Detail |
|---------|--------|
| **Nearest Mandi Discovery** | Haversine formula with **NumPy vectorization** computes great-circle distances from the farmer's GPS coordinates to all APMC mandis in the dataset. |
| **Price Trend Analysis** | 7-day rolling window on `modal_price` per quintal. Computes current price, 7-day average, and classifies momentum as **Upward** or **Downward**. |
| **Offline Dataset** | `mandi_data.csv` — 15 APMC mandi records across 5 districts, 4 crops (Tomato, Onion, Cotton, Banana) with geo-coordinates and time-series prices. |

### 3. Recommendation Engine — `main.py`

- Computes **net realization** = `(Quantity × Price/kg) − (Distance × ₹4/km transport)`.
- Ranks all mandis within the farmer's travel radius by net profit.
- Flags loss-making routes (`is_viable = false`) where transport exceeds revenue.
- Generates a human-readable **Smart Advisory** paragraph explaining the recommendation.
- Falls back gracefully from Supabase → in-memory mock data if the DB is unreachable.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI | Async REST API with auto-generated OpenAPI docs |
| **ASGI Server** | Uvicorn | High-performance async server |
| **Validation** | Pydantic | Request/response schema enforcement |
| **Database** | Supabase (PostgreSQL) | Cloud-hosted relational data with PostgREST |
| **Geospatial** | NumPy | Vectorized haversine distance computation |
| **Analytics** | Pandas | Time-series price trend analysis |
| **Config** | python-dotenv | Secure credential management via `.env` |
| **Testing** | httpx + TestClient | FastAPI endpoint integration testing |

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Health check — service status | None |
| `GET` | `/api/crops` | List all available crops | None |
| `GET` | `/api/mandis` | List all Supabase mandi records | None |
| `POST` | `/api/recommend` | Compute the most profitable mandi for a crop + quantity | None |
| `GET` | `/api/nearby-mandis?lat={lat}&lon={lon}&top_k={k}` | Geospatial nearest mandi discovery (haversine) | None |
| `GET` | `/api/mandi-prices?crop={crop}&district={district}` | Price trends — latest price, 7-day avg, momentum | None |
| `GET` | `/docs` | Interactive Swagger UI documentation | None |
| `GET` | `/redoc` | ReDoc API documentation | None |

### Example Requests

#### 🔍 Find Nearest Mandis

```bash
curl "http://127.0.0.1:8000/api/nearby-mandis?lat=18.5204&lon=73.8567&top_k=3"
```

```json
{
  "farmer_location": { "lat": 18.5204, "lon": 73.8567 },
  "top_k": 3,
  "nearby_mandis": [
    { "mandi_name": "APMC Pune", "district": "pune", "distance_km": 0.0 },
    { "mandi_name": "APMC Shirur", "district": "pune", "distance_km": 64.59 },
    { "mandi_name": "APMC Baramati", "district": "pune", "distance_km": 86.38 }
  ]
}
```

#### 📈 Get Price Trends

```bash
curl "http://127.0.0.1:8000/api/mandi-prices?crop=Tomato&district=Pune"
```

```json
{
  "crop": "Tomato",
  "district": "Pune",
  "latest_date": "2026-09-01",
  "current_modal_price_per_quintal": 2500.0,
  "7_day_average_price": 2533.33,
  "trend_status": "Downward"
}
```

#### 🚀 Get Best Mandi Recommendation

```bash
curl -X POST "http://127.0.0.1:8000/api/recommend" \
  -H "Content-Type: application/json" \
  -d '{"crop_name": "Tomato", "quantity_kg": 500, "max_distance_km": 200}'
```

---

## 📁 Project Structure

```
sih-farmer-backend/
├── main.py                   # FastAPI app — endpoints, recommendation engine
├── database.py               # Supabase client initialization
├── mandi_service.py          # Geolocation + price analytics service
├── mandi_data.csv            # Offline APMC mandi dataset (15 records)
├── test_mandi_features.py    # Automated integration test suite
├── requirements.txt          # Python dependencies
├── .env                      # Supabase credentials (not committed)
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## 🚀 Local Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### 1. Clone the repository

```bash
git clone https://github.com/Ayaan-35/sih-farmer-backend.git
cd sih-farmer-backend
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the project root (or update the existing one):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 4. Start the development server

```bash
uvicorn main:app --reload
```

The API will be available at:
- **Base URL:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## 🧪 Testing

### Automated Test Suite

Run all 11 integration tests (service-layer + HTTP endpoint verification):

```bash
python test_mandi_features.py
```

**Expected output:**

```
════════════════════════════════════════════════════════════
  TEST 1: Direct MandiService Unit Tests
════════════════════════════════════════════════════════════

  ✅ Returns exactly 3 mandis
  ✅ Nearest mandi is APMC Pune with distance 0.0 km
  ✅ latest_date is returned
  ✅ current_modal_price_per_quintal is returned
  ✅ 7_day_average_price is returned
  ✅ trend_status is returned

════════════════════════════════════════════════════════════
  TEST 2: FastAPI Endpoint Tests (TestClient)
════════════════════════════════════════════════════════════

  ✅ Status code is 200
  ✅ Response contains 'nearby_mandis' list
  ✅ Nearby Mandis endpoint returns 3 results
  ✅ Status code is 200
  ✅ Response contains price trend fields

════════════════════════════════════════════════════════════
  🎉 ALL 11 TESTS PASSED
════════════════════════════════════════════════════════════
```

### Manual Testing

Start the server and open these URLs in your browser:

| Test | URL |
|------|-----|
| Nearby Mandis (Pune) | `http://127.0.0.1:8000/api/nearby-mandis?lat=18.5204&lon=73.8567&top_k=3` |
| Price Trend (Tomato/Pune) | `http://127.0.0.1:8000/api/mandi-prices?crop=Tomato&district=Pune` |
| Price Trend (Onion/Nashik) | `http://127.0.0.1:8000/api/mandi-prices?crop=Onion&district=Nashik` |
| Swagger Docs | `http://127.0.0.1:8000/docs` |

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Your Supabase anon/public API key |

> ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

---

## 📄 License

This project is developed as part of **Smart India Hackathon 2026** (Problem Statement SIH26132).

---

<p align="center">
  Built with ❤️ for Indian Farmers
</p>
