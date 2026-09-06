# 🌾 SIH26132 — Farmer Market Linkages & Price Discovery Engine

> **Smart India Hackathon 2026** · Problem Statement SIH26132
> Built by Team to empower Maharashtra's farmers with data-driven mandi decisions.

---

## 📌 Core Problem Solved

Indian farmers often sell at the **nearest mandi** without knowing whether a slightly farther market could earn them significantly more. High prices at distant markets *look* attractive, but transport costs silently erode profits.

**Our engine solves this with one simple formula:**

```
Net Realisation = Gross Revenue − Distance-Based Logistics Cost
```

| Component | Formula |
|-----------|---------|
| **Gross Revenue** | `quantity_kg × modal_price_per_kg` |
| **Logistics Cost** | `distance_km × ₹4/km` (fixed truck-hire rate) |
| **Net Profit** | `Gross Revenue − Logistics Cost` |

The API evaluates **every reachable mandi**, ranks them by **net profit** (not just price), and generates a human-readable advisory explaining *why* the top choice is best — even if it doesn't have the highest per-kg rate.

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) |
| **Data Validation** | Pydantic v2 with strict Field constraints |
| **Database** | PostgreSQL via [Supabase](https://supabase.com/) (with in-memory fallback) |
| **Server** | Uvicorn (ASGI) |
| **API Docs** | Auto-generated Swagger UI at `/docs` |

---

## 🚀 Local Setup Instructions

### Prerequisites
- Python 3.10 or higher installed
- Git

### 1. Clone & Enter the Project

```bash
git clone <your-repo-url>
cd sih-farmer-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root (or edit the existing one):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

> **Note:** If you skip this step, the API will still work using built-in fallback data — perfect for local development without a database.

### 6. Run the Server

```bash
uvicorn main:app --reload
```

The server starts at **http://127.0.0.1:8000**

### 7. Open Interactive API Docs

Visit **http://127.0.0.1:8000/docs** in your browser to explore and test every endpoint via Swagger UI.

---

## 📡 API Documentation / Contract

### `GET /` — Health Check

```json
{
  "status": "active",
  "project": "SIH26132 Market Discovery Engine",
  "database": "Supabase PostgreSQL"
}
```

---

### `GET /api/crops` — List Available Crops

**Response:**
```json
{
  "source": "database",
  "crops": ["Onion", "Potato", "Soybean", "Tomato"]
}
```

---

### `GET /api/mandis` — List All Mandi Entries

**Response:**
```json
{
  "source": "database",
  "total": 18,
  "mandis": [
    {
      "id": 1,
      "mandi_name": "Nashik APMC",
      "district": "Nashik",
      "crop": "Tomato",
      "modal_price_per_kg": 22.0,
      "distance_from_base_km": 15.0
    }
  ]
}
```

---

### `POST /api/recommend` — 🚀 Core Recommendation Engine

**Request Body:**
```json
{
  "crop_name": "Tomato",
  "quantity_kg": 500,
  "max_distance_km": 200
}
```

**Response:**
```json
{
  "requested_crop": "Tomato",
  "total_quantity_kg": 500.0,
  "best_mandi": "Vashi APMC",
  "net_profit_at_best_mandi": 14860.0,
  "all_options": [
    {
      "mandi_name": "Vashi APMC",
      "district": "Mumbai",
      "price_per_kg": 31.0,
      "distance_km": 160.0,
      "gross_earnings": 15500.0,
      "transport_cost": 640.0,
      "net_profit": 14860.0,
      "is_viable": true
    },
    {
      "mandi_name": "Lasalgaon APMC",
      "district": "Nashik",
      "price_per_kg": 27.5,
      "distance_km": 45.0,
      "gross_earnings": 13750.0,
      "transport_cost": 180.0,
      "net_profit": 13570.0,
      "is_viable": true
    },
    {
      "mandi_name": "Nashik APMC",
      "district": "Nashik",
      "price_per_kg": 22.0,
      "distance_km": 15.0,
      "gross_earnings": 11000.0,
      "transport_cost": 60.0,
      "net_profit": 10940.0,
      "is_viable": true
    }
  ],
  "smart_advisory": "✅ Sell 500.0 kg at Vashi APMC (Mumbai).\n   Net profit: ₹14,860.00 (earning ₹31.0/kg, transport ₹640.00).\n   📊 Runner-up: Lasalgaon APMC (net ₹13,570.00, ₹1,290.00 less than the best)."
}
```

### Error Responses

| Status | Meaning | When |
|--------|---------|------|
| **404** | Crop not found | The requested crop doesn't exist in our APMC network |
| **400** | No mandis in range | Crop exists but all mandis exceed `max_distance_km` |
| **422** | Validation error | Invalid input (e.g. negative quantity, crop name too short) |
| **500** | Server error | Unexpected bug (clean JSON, no stack trace leaked) |

---

## 🔌 Team Workflow — Frontend Integration Guide

### For the React / Frontend Developer

The backend runs on `http://127.0.0.1:8000`. CORS is fully open (`*`), so you can call it from any `localhost` port.

#### Using `fetch` (vanilla JS)

```javascript
// Fetch available crops
const crops = await fetch("http://127.0.0.1:8000/api/crops")
  .then(res => res.json());

console.log(crops);
// { source: "database", crops: ["Onion", "Potato", "Soybean", "Tomato"] }
```

```javascript
// Get mandi recommendations
const response = await fetch("http://127.0.0.1:8000/api/recommend", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    crop_name: "Tomato",
    quantity_kg: 500,
    max_distance_km: 200
  })
});

const data = await response.json();
console.log(data.best_mandi);         // "Vashi APMC"
console.log(data.smart_advisory);     // Human-readable recommendation
console.log(data.all_options);        // Array of ranked mandis
```

#### Using `axios`

```javascript
import axios from "axios";

const API = "http://127.0.0.1:8000";

// GET crops
const { data: cropData } = await axios.get(`${API}/api/crops`);

// POST recommendation
const { data: recommendation } = await axios.post(`${API}/api/recommend`, {
  crop_name: "Onion",
  quantity_kg: 300,
  max_distance_km: 150
});
```

#### Key Fields for UI Rendering

| Field | Use in UI |
|-------|-----------|
| `best_mandi` | Highlight as the top recommendation card |
| `net_profit_at_best_mandi` | Show as the headline profit number |
| `all_options[]` | Render as a sortable comparison table |
| `all_options[].is_viable` | Grey out or flag loss-making mandis in red |
| `smart_advisory` | Display in a text box / advisory panel |

---

## 📂 Project Structure

```
sih-farmer-backend/
├── main.py              # FastAPI app — endpoints, validation, logic
├── database.py          # Supabase client initialisation
├── requirements.txt     # Python dependencies
├── .env                 # Supabase credentials (NOT committed)
├── .gitignore           # Excludes .env, __pycache__, .cursor/
└── README.md            # This file
```

---

## 🗄️ Database Schema (Supabase)

```sql
CREATE TABLE crops (
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE mandis (
    id                    SERIAL PRIMARY KEY,
    mandi_name            TEXT NOT NULL,
    district              TEXT NOT NULL,
    distance_from_base_km FLOAT NOT NULL
);

CREATE TABLE mandi_prices (
    id                 SERIAL PRIMARY KEY,
    mandi_id           INT REFERENCES mandis(id),
    crop_id            INT REFERENCES crops(id),
    modal_price_per_kg FLOAT NOT NULL
);
```

---

## 📝 License

This project is built for educational purposes as part of the **Smart India Hackathon 2026** programme.

---

<p align="center">
  <strong>Built with ❤️ for India's Farmers</strong><br>
  SIH 2026 · Problem Statement SIH26132
</p>
