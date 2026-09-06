"""
===========================================================================
  test_mandi_features.py — Automated Integration Tests
  ─────────────────────────────────────────────────────
  Test 1: Direct MandiService unit tests (CSV-backed)
  Test 2: FastAPI live endpoint tests via TestClient
===========================================================================
"""

import sys
import json
import io

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Colour helpers for terminal output ───────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0


def report(label: str, success: bool, detail: str = ""):
    global passed, failed
    if success:
        passed += 1
        icon = f"{GREEN}✅{RESET}"
    else:
        failed += 1
        icon = f"{RED}❌{RESET}"
    print(f"  {icon} {label}")
    if detail:
        print(f"      {detail}")


# ═════════════════════════════════════════════════════════════
#  TEST 1 — Direct MandiService Tests
# ═════════════════════════════════════════════════════════════

print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
print(f"{BOLD}{CYAN}  TEST 1: Direct MandiService Unit Tests{RESET}")
print(f"{BOLD}{CYAN}{'═'*60}{RESET}\n")

from mandi_service import MandiService

svc = MandiService("mandi_data.csv")

# ── 1a. Nearby Mandis ────────────────────────────────────────
print(f"  {BOLD}▸ get_nearby_mandis(lat=18.5204, lon=73.8567, top_k=3){RESET}")
nearby = svc.get_nearby_mandis(farmer_lat=18.5204, farmer_lon=73.8567, top_k=3)

report(
    "Returns exactly 3 mandis",
    len(nearby) == 3,
    f"Got {len(nearby)} mandis",
)

first = nearby[0] if nearby else {}
report(
    "Nearest mandi is APMC Pune with distance 0.0 km",
    first.get("mandi_name") == "APMC Pune" and first.get("distance_km") == 0.0,
    f"Got: {first.get('mandi_name')} @ {first.get('distance_km')} km",
)

print(f"\n  {BOLD}Nearby Mandis Result:{RESET}")
for i, m in enumerate(nearby, 1):
    print(f"    {i}. {m['mandi_name']} ({m['district']}) — {m['distance_km']} km")

# ── 1b. Price Trends ─────────────────────────────────────────
print(f"\n  {BOLD}▸ get_price_trends('Tomato', 'Pune'){RESET}")
trend = svc.get_price_trends("Tomato", "Pune")

report(
    "latest_date is returned",
    "latest_date" in trend and trend["latest_date"] != "",
    f"latest_date = {trend.get('latest_date')}",
)

report(
    "current_modal_price_per_quintal is returned",
    "current_modal_price_per_quintal" in trend and isinstance(trend["current_modal_price_per_quintal"], (int, float)),
    f"current_modal_price_per_quintal = ₹{trend.get('current_modal_price_per_quintal')}",
)

report(
    "7_day_average_price is returned",
    "7_day_average_price" in trend and isinstance(trend["7_day_average_price"], (int, float)),
    f"7_day_average_price = ₹{trend.get('7_day_average_price')}",
)

report(
    "trend_status is returned",
    "trend_status" in trend and trend["trend_status"] in ("Upward", "Downward"),
    f"trend_status = {trend.get('trend_status')}",
)

print(f"\n  {BOLD}Price Trend Result:{RESET}")
for k, v in trend.items():
    print(f"    {k}: {v}")


# ═════════════════════════════════════════════════════════════
#  TEST 2 — FastAPI Live Endpoint Tests (TestClient)
# ═════════════════════════════════════════════════════════════

print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
print(f"{BOLD}{CYAN}  TEST 2: FastAPI Endpoint Tests (TestClient){RESET}")
print(f"{BOLD}{CYAN}{'═'*60}{RESET}\n")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── 2a. GET /api/nearby-mandis ───────────────────────────────
print(f"  {BOLD}▸ GET /api/nearby-mandis?lat=18.5204&lon=73.8567&top_k=3{RESET}")
resp_nearby = client.get("/api/nearby-mandis", params={"lat": 18.5204, "lon": 73.8567, "top_k": 3})

report(
    "Status code is 200",
    resp_nearby.status_code == 200,
    f"status_code = {resp_nearby.status_code}",
)

body_nearby = resp_nearby.json()
report(
    "Response contains 'nearby_mandis' list",
    "nearby_mandis" in body_nearby and isinstance(body_nearby["nearby_mandis"], list),
    f"Keys: {list(body_nearby.keys())}",
)

report(
    "Nearby Mandis endpoint returns 3 results",
    len(body_nearby.get("nearby_mandis", [])) == 3,
    f"Got {len(body_nearby.get('nearby_mandis', []))} results",
)

print(f"\n  {BOLD}Endpoint Response:{RESET}")
print(f"    {json.dumps(body_nearby, indent=4)}")

# ── 2b. GET /api/mandi-prices ───────────────────────────────
print(f"\n  {BOLD}▸ GET /api/mandi-prices?crop=Tomato&district=Pune{RESET}")
resp_prices = client.get("/api/mandi-prices", params={"crop": "Tomato", "district": "Pune"})

report(
    "Status code is 200",
    resp_prices.status_code == 200,
    f"status_code = {resp_prices.status_code}",
)

body_prices = resp_prices.json()
report(
    "Response contains price trend fields",
    all(k in body_prices for k in ["latest_date", "current_modal_price_per_quintal", "7_day_average_price", "trend_status"]),
    f"Keys: {list(body_prices.keys())}",
)

print(f"\n  {BOLD}Endpoint Response:{RESET}")
print(f"    {json.dumps(body_prices, indent=4)}")


# ═════════════════════════════════════════════════════════════
#  SUMMARY
# ═════════════════════════════════════════════════════════════

print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
total = passed + failed
if failed == 0:
    print(f"{BOLD}{GREEN}  🎉 ALL {total} TESTS PASSED{RESET}")
else:
    print(f"{BOLD}{RED}  ⚠️  {failed}/{total} TESTS FAILED{RESET}")
print(f"{BOLD}{CYAN}{'═'*60}{RESET}\n")

sys.exit(0 if failed == 0 else 1)
