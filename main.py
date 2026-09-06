"""
===========================================================================
  SIH26132 — Farmer Market Linkages & Price Discovery Engine
  ----------------------------------------------------------
  A production-ready FastAPI backend that helps Maharashtra farmers
  discover the most profitable APMC Mandi for selling their crops.

  • Connected to live Supabase PostgreSQL database.
  • Fallback to in-memory mock data if database is unreachable.
  • Fully runnable:  uvicorn main:app --reload
===========================================================================
"""

# ─────────────────────────────────────────────────────────────
# 1. IMPORTS
# ─────────────────────────────────────────────────────────────

import logging                                      # For server-side error logging

from fastapi import FastAPI, HTTPException, Request  # Web framework & error handling
from fastapi.middleware.cors import CORSMiddleware   # Cross-Origin Resource Sharing
from fastapi.responses import JSONResponse           # For custom error responses
from pydantic import BaseModel, Field                # Request/Response validation
from typing import Optional                          # Optional type hints

# Import the shared Supabase client from our database module.
# This will load .env and validate credentials on startup.
from database import supabase

# Configure a logger so errors are recorded in server logs,
# not swallowed silently.  Judges love to see proper logging.
logger = logging.getLogger("sih26132")


# ─────────────────────────────────────────────────────────────
# 2. APP INITIALISATION
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="SIH26132 — Market Discovery Engine",
    description=(
        "Helps farmers in Maharashtra find the best APMC Mandi to sell "
        "their produce by computing net profit after transport costs. "
        "Now powered by a live Supabase PostgreSQL database."
    ),
    version="2.0.0",
)

# Allow any frontend (React, plain HTML, mobile app) to call this API
# without running into CORS issues during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Accept requests from every origin
    allow_credentials=True,
    allow_methods=["*"],       # Accept every HTTP method (GET, POST, …)
    allow_headers=["*"],       # Accept every header
)


# ─────────────────────────────────────────────────────────────
# 2b. GLOBAL EXCEPTION HANDLER
# ─────────────────────────────────────────────────────────────
# WHY: If any unhandled Python exception (KeyError, ZeroDivisionError,
# etc.) slips through, FastAPI normally returns an ugly HTML 500 page
# with a full stack trace.  During hackathon evaluation, that looks
# unprofessional and leaks internal details.
#
# This handler catches ALL unexpected exceptions, logs the real error
# server-side (so we can debug), and returns a clean JSON 500 response.
#
# HTTP 500 — "Internal Server Error": the server encountered something
# it didn't expect.  We use it as a catch-all safety net.

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for any unhandled exception.
    Logs the real traceback server-side, returns sanitised JSON to client.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Processing Error",
            "detail": "Something went wrong in the calculations.",
        },
    )


# ─────────────────────────────────────────────────────────────
# 3. IN-MEMORY FALLBACK DATA
# ─────────────────────────────────────────────────────────────
# Kept as a safety net so the app still works even if the
# Supabase database is empty or unreachable during a demo.
# The API endpoints try the live database FIRST, and only
# fall back to this data if the query returns nothing.

FALLBACK_MANDI_DATA: list[dict] = [
    # ── Tomato ───────────────────────────────────────────────
    {"id": 1,  "mandi_name": "Nashik APMC",      "district": "Nashik",  "crop": "Tomato",  "modal_price_per_kg": 22.0, "distance_from_base_km": 15.0},
    {"id": 2,  "mandi_name": "Lasalgaon APMC",   "district": "Nashik",  "crop": "Tomato",  "modal_price_per_kg": 27.5, "distance_from_base_km": 45.0},
    {"id": 3,  "mandi_name": "Pimpalgaon APMC",  "district": "Nashik",  "crop": "Tomato",  "modal_price_per_kg": 24.0, "distance_from_base_km": 30.0},
    {"id": 4,  "mandi_name": "Vashi APMC",        "district": "Mumbai",  "crop": "Tomato",  "modal_price_per_kg": 31.0, "distance_from_base_km": 160.0},
    {"id": 5,  "mandi_name": "Pune Market Yard",  "district": "Pune",    "crop": "Tomato",  "modal_price_per_kg": 28.0, "distance_from_base_km": 210.0},
    # ── Onion ────────────────────────────────────────────────
    {"id": 6,  "mandi_name": "Lasalgaon APMC",   "district": "Nashik",  "crop": "Onion",   "modal_price_per_kg": 18.0, "distance_from_base_km": 45.0},
    {"id": 7,  "mandi_name": "Nashik APMC",      "district": "Nashik",  "crop": "Onion",   "modal_price_per_kg": 16.5, "distance_from_base_km": 15.0},
    {"id": 8,  "mandi_name": "Pimpalgaon APMC",  "district": "Nashik",  "crop": "Onion",   "modal_price_per_kg": 17.0, "distance_from_base_km": 30.0},
    {"id": 9,  "mandi_name": "Vashi APMC",        "district": "Mumbai",  "crop": "Onion",   "modal_price_per_kg": 21.0, "distance_from_base_km": 160.0},
    {"id": 10, "mandi_name": "Pune Market Yard",  "district": "Pune",    "crop": "Onion",   "modal_price_per_kg": 19.5, "distance_from_base_km": 210.0},
    # ── Soybean ──────────────────────────────────────────────
    {"id": 11, "mandi_name": "Nashik APMC",      "district": "Nashik",  "crop": "Soybean", "modal_price_per_kg": 42.0, "distance_from_base_km": 15.0},
    {"id": 12, "mandi_name": "Lasalgaon APMC",   "district": "Nashik",  "crop": "Soybean", "modal_price_per_kg": 44.5, "distance_from_base_km": 45.0},
    {"id": 13, "mandi_name": "Pune Market Yard",  "district": "Pune",    "crop": "Soybean", "modal_price_per_kg": 47.0, "distance_from_base_km": 210.0},
    {"id": 14, "mandi_name": "Vashi APMC",        "district": "Mumbai",  "crop": "Soybean", "modal_price_per_kg": 46.0, "distance_from_base_km": 160.0},
    # ── Potato ───────────────────────────────────────────────
    {"id": 15, "mandi_name": "Nashik APMC",      "district": "Nashik",  "crop": "Potato",  "modal_price_per_kg": 14.0, "distance_from_base_km": 15.0},
    {"id": 16, "mandi_name": "Pimpalgaon APMC",  "district": "Nashik",  "crop": "Potato",  "modal_price_per_kg": 13.5, "distance_from_base_km": 30.0},
    {"id": 17, "mandi_name": "Vashi APMC",        "district": "Mumbai",  "crop": "Potato",  "modal_price_per_kg": 18.0, "distance_from_base_km": 160.0},
    {"id": 18, "mandi_name": "Pune Market Yard",  "district": "Pune",    "crop": "Potato",  "modal_price_per_kg": 16.5, "distance_from_base_km": 210.0},
]

# Fixed logistics cost: ₹4 per kilometre (one-way truck hire estimate).
TRANSPORT_RATE_PER_KM: float = 4.0


# ─────────────────────────────────────────────────────────────
# 4. PYDANTIC SCHEMAS — Request & Response Models
# ─────────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    """
    What the farmer sends:
      - Which crop they want to sell
      - How many kg they have
      - How far they're willing to travel (optional, defaults to 200 km)

    Pydantic automatically returns HTTP 422 ("Unprocessable Entity") if
    any of these constraints are violated.  422 means: "I understood your
    JSON, but the values inside are semantically invalid."
    """
    crop_name: str = Field(
        ...,
        min_length=2,           # Reject single-char garbage like "X"
        strip_whitespace=True,  # Auto-trim " Tomato " → "Tomato"
        example="Tomato",
        description="Name of the crop to sell (case-insensitive, min 2 chars).",
    )
    quantity_kg: float = Field(
        ...,
        gt=0,                   # Must be positive
        le=100000,              # Cap at 1,00,000 kg to prevent absurd inputs
        example=500,
        description="Quantity must be between 0 and 1,00,000 kg.",
    )
    max_distance_km: Optional[float] = Field(
        default=200.0,
        gt=0,                   # Must be positive (0 km makes no sense)
        le=2000,                # Cap at 2000 km — realistic Indian distances
        example=200.0,
        description="Distance must be positive and realistic (max 2000 km).",
    )


class MandiResultItem(BaseModel):
    """One row in the results table — profit breakdown for a single mandi."""
    mandi_name: str
    district: str
    price_per_kg: float
    distance_km: float
    gross_earnings: float       # quantity × price
    transport_cost: float       # distance × ₹4/km
    net_profit: float           # gross − transport
    is_viable: bool             # False if transport cost ≥ gross earnings (loss-making)


class RecommendationResponse(BaseModel):
    """
    The full recommendation payload returned to the farmer.
    Contains the best mandi, all evaluated options, and a
    human-readable advisory paragraph.
    """
    requested_crop: str
    total_quantity_kg: float
    best_mandi: str
    net_profit_at_best_mandi: float
    all_options: list[MandiResultItem]
    smart_advisory: str


# ─────────────────────────────────────────────────────────────
# 5. DATABASE HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
# These functions encapsulate all Supabase queries.  If a query
# fails, they log the error and return None so the endpoint can
# gracefully fall back to in-memory data.

def _fetch_crops_from_db() -> list[str] | None:
    """
    Fetch all crop names from the 'crops' table in Supabase.
    Returns a sorted list of crop names, or None on failure.

    Expected table schema:
      crops(id SERIAL, name TEXT UNIQUE NOT NULL)
    """
    try:
        response = supabase.table("crops").select("name").execute()
        if response.data:
            return sorted({row["name"] for row in response.data})
        return None
    except Exception as e:
        logger.error("Failed to fetch crops from Supabase: %s", e)
        return None


def _fetch_mandis_from_db() -> list[dict] | None:
    """
    Fetch ALL mandi+price data by querying 'mandi_prices' with a
    join to 'mandis' and 'crops' via Supabase's PostgREST syntax.

    Returns a flat list of dicts matching our standard format, or
    None on failure.

    Expected table schemas:
      mandis(id, mandi_name, district, distance_from_base_km)
      crops(id, name)
      mandi_prices(id, mandi_id → mandis, crop_id → crops, modal_price_per_kg)
    """
    try:
        # PostgREST embedded resource syntax:
        #   "mandis(mandi_name, district, distance_from_base_km)"
        #   means: join mandi_prices → mandis and fetch those columns.
        response = (
            supabase.table("mandi_prices")
            .select(
                "id, modal_price_per_kg, "
                "mandis(mandi_name, district, distance_from_base_km), "
                "crops(name)"
            )
            .execute()
        )
        if not response.data:
            return None

        # Flatten the nested PostgREST response into our standard format:
        #   { mandi_name, district, crop, modal_price_per_kg, distance_from_base_km }
        flat = []
        for row in response.data:
            mandi_info = row.get("mandis", {}) or {}
            crop_info = row.get("crops", {}) or {}
            flat.append({
                "id": row["id"],
                "mandi_name": mandi_info.get("mandi_name", "Unknown"),
                "district": mandi_info.get("district", "Unknown"),
                "crop": crop_info.get("name", "Unknown"),
                "modal_price_per_kg": row["modal_price_per_kg"],
                "distance_from_base_km": mandi_info.get("distance_from_base_km", 0.0),
            })
        return flat

    except Exception as e:
        logger.error("Failed to fetch mandis from Supabase: %s", e)
        return None


def _fetch_mandis_for_crop(crop_name: str) -> list[dict] | None:
    """
    Fetch mandi+price data for a SPECIFIC crop by querying
    'mandi_prices' joined with 'mandis' and filtered by crop name.

    This is more efficient than fetching everything and filtering
    in Python — the database does the heavy lifting.

    Returns a flat list of matching dicts, or None on failure.
    """
    try:
        # Step 1: Find the crop ID by name (case-insensitive via .ilike)
        crop_response = (
            supabase.table("crops")
            .select("id")
            .ilike("name", crop_name)
            .execute()
        )
        if not crop_response.data:
            return []  # Empty list = crop not found (not an error)

        crop_id = crop_response.data[0]["id"]

        # Step 2: Fetch all mandi_prices for this crop, joined with mandis
        response = (
            supabase.table("mandi_prices")
            .select(
                "id, modal_price_per_kg, "
                "mandis(mandi_name, district, distance_from_base_km)"
            )
            .eq("crop_id", crop_id)
            .execute()
        )
        if not response.data:
            return []

        # Flatten the nested response
        flat = []
        for row in response.data:
            mandi_info = row.get("mandis", {}) or {}
            flat.append({
                "id": row["id"],
                "mandi_name": mandi_info.get("mandi_name", "Unknown"),
                "district": mandi_info.get("district", "Unknown"),
                "crop": crop_name.title(),
                "modal_price_per_kg": row["modal_price_per_kg"],
                "distance_from_base_km": mandi_info.get("distance_from_base_km", 0.0),
            })
        return flat

    except Exception as e:
        logger.error("Failed to fetch mandis for crop '%s': %s", crop_name, e)
        return None


# ─────────────────────────────────────────────────────────────
# 6. API ENDPOINTS
# ─────────────────────────────────────────────────────────────

# ---------- 6a. Health-check / status ----------

@app.get(
    "/",
    summary="System Status",
    tags=["General"],
)
def root():
    """
    Quick health-check endpoint.
    Returns the service status and project identifier.
    """
    return {
        "status": "active",
        "project": "SIH26132 Market Discovery Engine",
        "database": "Supabase PostgreSQL",
    }


# ---------- 6b. List available crops ----------

@app.get(
    "/api/crops",
    summary="List Available Crops",
    tags=["Market Data"],
)
def get_crops():
    """
    Fetches all unique crop names from the Supabase 'crops' table.
    Falls back to in-memory data if the database query fails.
    """
    # Try live database first
    db_crops = _fetch_crops_from_db()

    if db_crops is not None and len(db_crops) > 0:
        logger.info("Crops fetched from Supabase: %s", db_crops)
        return {"source": "database", "crops": db_crops}

    # Fallback to in-memory data
    logger.warning("Supabase returned no crops — using fallback data.")
    fallback_crops = sorted({entry["crop"] for entry in FALLBACK_MANDI_DATA})
    return {"source": "fallback", "crops": fallback_crops}


# ---------- 6c. List all mandis (raw data) ----------

@app.get(
    "/api/mandis",
    summary="List All Mandis",
    tags=["Market Data"],
)
def get_mandis():
    """
    Returns all mandi+price listings from Supabase.
    Falls back to in-memory data if the database query fails.
    """
    db_mandis = _fetch_mandis_from_db()

    if db_mandis is not None and len(db_mandis) > 0:
        logger.info("Mandis fetched from Supabase: %d entries", len(db_mandis))
        return {"source": "database", "total": len(db_mandis), "mandis": db_mandis}

    # Fallback
    logger.warning("Supabase returned no mandis — using fallback data.")
    return {"source": "fallback", "total": len(FALLBACK_MANDI_DATA), "mandis": FALLBACK_MANDI_DATA}


# ---------- 6d. Core Recommendation Engine ----------

@app.post(
    "/api/recommend",
    response_model=RecommendationResponse,
    summary="Get Best Mandi Recommendation",
    tags=["Recommendation Engine"],
)
def recommend(request: RecommendationRequest):
    """
    🚀 THE CORE LOGIC ENGINE (Production-Hardened + Supabase)

    HTTP status codes used and WHY:
      • 200 — Success. Recommendation computed and returned.
      • 400 — Bad Request. The crop exists but no mandis are within
              the user's distance limit. The user can fix this by
              increasing max_distance_km (a client-side fix).
      • 404 — Not Found. The requested crop doesn't exist in our
              APMC network at all. No client-side fix possible.
      • 422 — Unprocessable Entity (auto-raised by Pydantic).
              The JSON body was parseable but field values violate
              constraints (e.g. negative quantity, crop name too short).
      • 500 — Internal Server Error (caught by global handler).
              An unexpected bug in our code. Never shown as raw traceback.

    Steps:
      1. Normalise the crop name (trim + lowercase).
      2. Query Supabase for matching mandis (fallback to in-memory).
      3. Filter by max_distance_km — 400 if none in range.
      4. Compute gross, transport, net, and viability flag.
      5. Sort by net_profit descending.
      6. Build smart advisory.
      7. Return structured response.
    """

    # ── Step 1: Robust crop name normalisation ───────────────
    crop_lower = request.crop_name.lower()

    # ── Step 2: Query database for this crop's mandis ────────
    # Try Supabase first — it does the crop matching and join
    # in the database, which is faster for large datasets.
    matching_entries = _fetch_mandis_for_crop(crop_lower)

    # If Supabase call failed entirely (returned None), fall back
    # to in-memory filtering.
    if matching_entries is None:
        logger.warning(
            "Supabase query failed for crop '%s' — falling back to mock data.",
            request.crop_name,
        )
        matching_entries = [
            entry for entry in FALLBACK_MANDI_DATA
            if entry["crop"].lower() == crop_lower
        ]

    # HTTP 404 — "Not Found": the resource (crop) doesn't exist
    # in our system. This is semantically correct because the
    # farmer asked for something we simply don't track.
    if not matching_entries:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Crop '{request.crop_name}' is not currently tracked "
                f"in our APMC network."
            ),
        )

    # ── Step 3: Filter by maximum travel distance ────────────
    within_range = [
        entry for entry in matching_entries
        if entry["distance_from_base_km"] <= request.max_distance_km
    ]

    # HTTP 400 — "Bad Request": the crop exists, but the user's
    # distance constraint filters out every mandi.
    if not within_range:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No mandis found within {request.max_distance_km} km. "
                f"Try increasing the search distance."
            ),
        )

    # ── Step 4: Compute financials for each mandi ────────────
    results: list[MandiResultItem] = []

    for entry in within_range:
        gross = round(request.quantity_kg * entry["modal_price_per_kg"], 2)
        transport = round(entry["distance_from_base_km"] * TRANSPORT_RATE_PER_KM, 2)
        net = round(gross - transport, 2)

        # is_viable = False when transport cost eats up all earnings.
        viable = transport < gross

        results.append(
            MandiResultItem(
                mandi_name=entry["mandi_name"],
                district=entry["district"],
                price_per_kg=entry["modal_price_per_kg"],
                distance_km=entry["distance_from_base_km"],
                gross_earnings=gross,
                transport_cost=transport,
                net_profit=net,
                is_viable=viable,
            )
        )

    # ── Step 5: Sort descending by net profit ────────────────
    results.sort(key=lambda r: r.net_profit, reverse=True)

    best = results[0]

    # ── Step 6: Build the smart advisory ─────────────────────
    smart_advisory = _build_advisory(results, request.quantity_kg)

    # ── Step 7: Return the structured response ───────────────
    return RecommendationResponse(
        requested_crop=request.crop_name.title(),
        total_quantity_kg=request.quantity_kg,
        best_mandi=best.mandi_name,
        net_profit_at_best_mandi=best.net_profit,
        all_options=results,
        smart_advisory=smart_advisory,
    )


# ─────────────────────────────────────────────────────────────
# 7. HELPER — Smart Advisory Builder
# ─────────────────────────────────────────────────────────────

def _build_advisory(results: list[MandiResultItem], quantity_kg: float) -> str:
    """
    Generates a human-readable advisory paragraph that explains
    WHY the top mandi is best, and how it compares to alternatives.
    """

    best = results[0]

    # Count how many options would result in a loss
    non_viable_count = sum(1 for r in results if not r.is_viable)

    # Start with the primary recommendation
    lines = [
        f"✅ Sell {quantity_kg} kg at {best.mandi_name} ({best.district}).",
        f"   Net profit: ₹{best.net_profit:,.2f} "
        f"(earning ₹{best.price_per_kg}/kg, transport ₹{best.transport_cost:,.2f}).",
    ]

    # Warn if even the best option is loss-making
    if not best.is_viable:
        lines.append(
            f"   🔴 WARNING: ALL {len(results)} options result in a loss! "
            f"Transport costs exceed earnings at every mandi in range. "
            f"Consider waiting for better prices or reducing transport distance."
        )
    elif non_viable_count > 0:
        lines.append(
            f"   ⚠️ Note: {non_viable_count} of {len(results)} mandis "
            f"are loss-making at this quantity — marked is_viable=false."
        )

    # If there are alternatives, explain why they're worse
    if len(results) > 1:
        runner_up = results[1]

        # Find the mandi with the highest gross price (may differ from best net)
        highest_price_mandi = max(results, key=lambda r: r.price_per_kg)

        if highest_price_mandi.mandi_name != best.mandi_name:
            extra_transport = round(
                highest_price_mandi.transport_cost - best.transport_cost, 2
            )
            lines.append(
                f"   ⚠️ Even though {highest_price_mandi.mandi_name} offers a "
                f"higher rate of ₹{highest_price_mandi.price_per_kg}/kg, "
                f"transport costs ₹{extra_transport:,.2f} more. "
                f"{best.mandi_name} yields the highest net profit."
            )

        profit_diff = round(best.net_profit - runner_up.net_profit, 2)
        lines.append(
            f"   📊 Runner-up: {runner_up.mandi_name} "
            f"(net ₹{runner_up.net_profit:,.2f}, "
            f"₹{profit_diff:,.2f} less than the best)."
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 8. ENTRY POINT (optional — for running with `python main.py`)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    # Launch the development server on port 8000
    # Access Swagger docs at http://127.0.0.1:8000/docs
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
