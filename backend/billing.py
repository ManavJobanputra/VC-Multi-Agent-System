import hmac
import hashlib
import logging
import uuid

import razorpay

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from db import get_conn
from user_auth import grant_credits

logger = logging.getLogger(__name__)

# Pay-per-session credit packs. Priced in INR (Razorpay's native currency).
CREDIT_PACKS = {
    "single": {"credits": 1, "amount_inr": 749, "label": "1 session"},
    "five": {"credits": 5, "amount_inr": 2499, "label": "5 sessions"},
    "fifteen": {"credits": 15, "amount_inr": 5999, "label": "15 sessions"},
}


def _client() -> razorpay.Client:
    if not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
        raise RuntimeError("Razorpay is not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET missing).")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_order(email: str, pack: str) -> dict:
    if pack not in CREDIT_PACKS:
        raise ValueError(f"Unknown credit pack: {pack}")

    pack_info = CREDIT_PACKS[pack]
    client = _client()

    order = client.order.create({
        "amount": pack_info["amount_inr"] * 100,  # Razorpay takes paise
        "currency": "INR",
        "notes": {"email": email, "pack": pack},
    })

    payment_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO payments (id, email, razorpay_order_id, pack, amount_inr, credits_granted, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'created')",
            (payment_id, email, order["id"], pack, pack_info["amount_inr"], pack_info["credits"]),
        )

    return {
        "order_id": order["id"],
        "amount": pack_info["amount_inr"] * 100,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "pack": pack,
    }


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    if not RAZORPAY_WEBHOOK_SECRET:
        logger.warning("RAZORPAY_WEBHOOK_SECRET not set - rejecting webhook.")
        return False
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def handle_payment_captured(order_id: str, payment_id: str) -> None:
    """Grants credits for the order tied to this webhook event, exactly
    once - re-deliveries of the same event are a no-op since the payment
    row is only ever moved from 'created' to 'captured' the first time."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT email, credits_granted, status FROM payments WHERE razorpay_order_id = ?",
            (order_id,),
        ).fetchone()

        if row is None:
            logger.warning(f"Webhook for unknown order_id {order_id}")
            return

        if row["status"] == "captured":
            return  # already processed, avoid double-granting credits

        conn.execute(
            "UPDATE payments SET status = 'captured', razorpay_payment_id = ? WHERE razorpay_order_id = ?",
            (payment_id, order_id),
        )
        email = row["email"]
        credits = row["credits_granted"]

    grant_credits(email, credits)
    logger.info(f"Granted {credits} credit(s) to {email} for order {order_id}")
