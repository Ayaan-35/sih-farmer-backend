"""Runnable end-to-end verification for the Kisan Suraksha escrow prototype."""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_escrow_order_lifecycle() -> None:
    create_response = client.post(
        "/api/payment/create-order",
        json={
            "farmer_id": "FARMER_101",
            "buyer_id": "BUYER_202",
            "crop": "Tomato",
            "quantity_kg": 500,
            "total_amount": 12500,
        },
    )
    assert create_response.status_code == 201
    order = create_response.json()
    assert order["status"] == "ESCROW_LOCKED"
    assert order["dispatch_clearance"] is True
    assert len(order["verification_otp"]) == 4

    payout_response = client.post(
        "/api/payment/release-payout",
        json={"order_id": order["order_id"], "entered_otp": order["verification_otp"]},
    )
    assert payout_response.status_code == 200
    payout = payout_response.json()
    assert payout["status"] == "COMPLETED"
    assert payout["settlement_amount"] == 12500
    assert payout["payout_timestamp"]
    assert payout["settlement_reference"].startswith("UPI_SIM_")

    repeated_response = client.post(
        "/api/payment/release-payout",
        json={"order_id": order["order_id"], "entered_otp": order["verification_otp"]},
    )
    assert repeated_response.status_code == 409


def test_invalid_otp_does_not_release_payout() -> None:
    create_response = client.post(
        "/api/payment/create-order",
        json={
            "farmer_id": "FARMER_303",
            "buyer_id": "BUYER_404",
            "crop": "Onion",
            "quantity_kg": 100,
            "total_amount": 2200,
        },
    )
    order = create_response.json()

    payout_response = client.post(
        "/api/payment/release-payout",
        json={"order_id": order["order_id"], "entered_otp": "9999"},
    )
    assert payout_response.status_code == 400
    assert "Invalid handover OTP" in payout_response.json()["detail"]


if __name__ == "__main__":
    test_escrow_order_lifecycle()
    test_invalid_otp_does_not_release_payout()
    print("PASS: escrow lock -> OTP handover -> simulated payout release")
    print("PASS: invalid OTP and duplicate payout protections")
