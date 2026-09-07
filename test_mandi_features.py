import os
from fastapi.testclient import TestClient
from mandi_service import MandiService
from ai_buyer_service import filter_buyers, ask_gemini_advisory
from main import app

client = TestClient(app)
CSV_FILE = "mandi_data.csv"

def test_all_features():
    print("\n============================================================")
    print("  SIH26132 FULL INTEGRATION TEST SUITE (14 TESTS)")
    print("============================================================")

    assert os.path.exists(CSV_FILE), "mandi_data.csv missing!"
    service = MandiService(CSV_FILE)

    # 1. Mandi Service Logic Tests
    nearby_pune = service.get_nearby_mandis(18.5204, 73.8567, top_k=3)
    assert len(nearby_pune) == 3
    assert nearby_pune[0]["mandi_name"] == "APMC Pune" and nearby_pune[0]["distance_km"] == 0.0
    print("✅ Test 1 Passed: Nearby Mandi returned 0.0 km")

    nearby_5 = service.get_nearby_mandis(18.5204, 73.8567, top_k=5)
    assert len(nearby_5) == 5
    print("✅ Test 2 Passed: Top-K returned 5 mandis")

    distances = [m["distance_km"] for m in nearby_5]
    assert distances == sorted(distances)
    print("✅ Test 3 Passed: Distances strictly ascending")

    trend_tomato = service.get_price_trends("Tomato", "Pune")
    assert "current_modal_price_per_quintal" in trend_tomato
    assert "7_day_average_price" in trend_tomato
    print(f"✅ Test 4 Passed: 7-Day Trend computed ({trend_tomato['trend_status']})")

    if trend_tomato["current_modal_price_per_quintal"] >= trend_tomato["7_day_average_price"]:
        assert trend_tomato["trend_status"] == "Upward"
    else:
        assert trend_tomato["trend_status"] == "Downward"
    print("✅ Test 5 Passed: Trend direction logic consistent")

    trend_case = service.get_price_trends("toMAto", "pUNe")
    assert "error" not in trend_case
    print("✅ Test 6 Passed: Case-insensitive query works")

    trend_fake = service.get_price_trends("Pineapple", "Antarctica")
    assert "error" in trend_fake
    print("✅ Test 7 Passed: Invalid crop handled gracefully")

    # 2. FastAPI Endpoints Tests
    res8 = client.get("/api/nearby-mandis?lat=18.5204&lon=73.8567&top_k=3")
    assert res8.status_code == 200
    res8_data = res8.json()
    mandis_list = res8_data.get("nearby_mandis", res8_data if isinstance(res8_data, list) else [])
    assert len(mandis_list) == 3
    print("✅ Test 8 Passed: GET /api/nearby-mandis returned 200 OK")

    res9 = client.get("/api/mandi-prices?crop=Tomato&district=Pune")
    assert res9.status_code == 200
    print("✅ Test 9 Passed: GET /api/mandi-prices returned 200 OK")

    res10 = client.get("/api/mandi-prices?crop=Avocado&district=Pune")
    assert res10.status_code == 404
    print("✅ Test 10 Passed: GET /api/mandi-prices returned 404 for invalid crop")

    res11 = client.get("/api/nearby-mandis?lat=invalid_coord&lon=73.8567")
    assert res11.status_code == 422
    print("✅ Test 11 Passed: Schema validation returned 422")

    # 3. Buyer & Advisory Tests
    buyers = filter_buyers(crop="Tomato", quantity=100, district="Nashik")
    assert len(buyers) > 0
    print(f"✅ Test 12 Passed: Found {len(buyers)} buyers in Nashik")

    res13 = client.get("/api/buyer-matches?crop=Tomato&quantity=100&district=Nashik")
    assert res13.status_code == 200
    print("✅ Test 13 Passed: GET /api/buyer-matches returned 200 OK")

    res14 = client.post("/api/advisory-bot", json={
        "user_message": "kya mujhe abhi bechna chahiye?",
        "crop": "Tomato",
        "district": "Pune"
    })
    assert res14.status_code == 200
    assert "advice" in res14.json()
    print("✅ Test 14 Passed: POST /api/advisory-bot returned 200 OK with advice")

    print("============================================================")
    print("🎉 ALL 14 TESTS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    test_all_features()