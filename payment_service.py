"""In-memory escrow workflow used by the Kisan Suraksha demo."""

from __future__ import annotations

from datetime import datetime, timezone
from secrets import randbelow, token_hex
from threading import Lock


class EscrowOrderNotFoundError(ValueError):
    """Raised when an order ID is not present in the simulated ledger."""


class PayoutAlreadyReleasedError(ValueError):
    """Raised when an already-completed order is redeemed again."""


class InvalidHandoverOtpError(ValueError):
    """Raised when the supplied handover OTP does not match the order."""


class PaymentService:
    """Simulate escrow holds and one-time OTP-authorised farmer payouts.

    This is intentionally an in-memory prototype: all orders are lost when
    the API process restarts and no real bank or UPI transfer is attempted.
    """

    def __init__(self) -> None:
        self._orders: dict[str, dict] = {}
        self._lock = Lock()

    def create_escrow_order(
        self,
        farmer_id: str,
        buyer_id: str,
        crop: str,
        quantity_kg: float,
        total_amount: float,
    ) -> dict:
        """Lock buyer funds and issue the farmer's handover OTP."""
        order_id = f"ORDER_{token_hex(6).upper()}"
        verification_otp = f"{randbelow(10_000):04d}"
        created_at = self._timestamp()
        order = {
            "order_id": order_id,
            "farmer_id": farmer_id,
            "buyer_id": buyer_id,
            "crop": crop,
            "quantity_kg": quantity_kg,
            "total_amount": total_amount,
            "verification_otp": verification_otp,
            "status": "ESCROW_LOCKED",
            "created_at": created_at,
            "payout_timestamp": None,
        }

        with self._lock:
            self._orders[order_id] = order

        return {
            **order,
            "message": "Escrow funds locked. Produce dispatch is cleared.",
            "dispatch_clearance": True,
        }

    def verify_and_release_payout(self, order_id: str, entered_otp: str) -> dict:
        """Release an escrowed payout after the OTP handover check."""
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                raise EscrowOrderNotFoundError("Escrow order not found.")
            if order["status"] == "COMPLETED":
                raise PayoutAlreadyReleasedError(
                    "Payout has already been released for this order."
                )
            if entered_otp != order["verification_otp"]:
                raise InvalidHandoverOtpError(
                    "Invalid handover OTP. Payout was not released."
                )

            payout_timestamp = self._timestamp()
            order["status"] = "COMPLETED"
            order["payout_timestamp"] = payout_timestamp

            return {
                "order_id": order_id,
                "status": order["status"],
                "farmer_id": order["farmer_id"],
                "settlement_amount": order["total_amount"],
                "payout_timestamp": payout_timestamp,
                "message": "OTP verified. Instant UPI/direct-to-bank payout released to farmer.",
                "settlement_reference": f"UPI_SIM_{token_hex(5).upper()}",
            }

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
