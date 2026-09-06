"""
===========================================================================
  database.py — Supabase Client Initialisation
  ─────────────────────────────────────────────
  Loads credentials from .env and creates a single shared Supabase client
  that main.py imports.  This keeps database config separate from app logic.

  Supabase Table Schema Expected:
  ───────────────────────────────
  TABLE: crops
    id          SERIAL PRIMARY KEY
    name        TEXT UNIQUE NOT NULL        -- e.g. 'Tomato', 'Onion'

  TABLE: mandis
    id                      SERIAL PRIMARY KEY
    mandi_name              TEXT NOT NULL       -- e.g. 'Nashik APMC'
    district                TEXT NOT NULL       -- e.g. 'Nashik'
    distance_from_base_km   FLOAT NOT NULL      -- e.g. 15.0

  TABLE: mandi_prices
    id                  SERIAL PRIMARY KEY
    mandi_id            INT REFERENCES mandis(id)
    crop_id             INT REFERENCES crops(id)
    modal_price_per_kg  FLOAT NOT NULL          -- e.g. 22.0
===========================================================================
"""

import os
import logging

from dotenv import load_dotenv          # Reads .env file into os.environ
from supabase import create_client      # Official Supabase Python client

logger = logging.getLogger("sih26132")

# ── Load environment variables from .env ─────────────────────
# load_dotenv() searches for a .env file in the current directory
# (or any parent) and injects its key=value pairs into os.environ.
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ── Validate that credentials are present ────────────────────
# If the user forgot to fill in .env, we fail fast with a clear
# message rather than crashing later with a cryptic HTTP error.
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
        "See .env.example or the project README for details."
    )

if SUPABASE_KEY == "YAHAN_APNI_ANON_KEY_PASTE_KARO":
    logger.warning(
        "⚠️  SUPABASE_KEY is still the placeholder value! "
        "Paste your real anon key in .env before making database calls."
    )

# ── Create the Supabase client ───────────────────────────────
# This client is thread-safe and can be shared across requests.
# It communicates with Supabase via its REST (PostgREST) API.
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logger.info("✅ Supabase client initialised for %s", SUPABASE_URL)
