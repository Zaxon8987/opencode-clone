from __future__ import annotations
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from database import get_db
from license import create_license

router = APIRouter(prefix="/webhook", tags=["webhook"])
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


@router.post("/stripe")
async def stripe_webhook(request: Request):
    if not endpoint_secret:
        raise HTTPException(500, "Webhook secret not configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(400, str(e))

    event_type = event["type"]
    data = event["data"]["object"]
    conn = get_db()

    if event_type == "checkout.session.completed":
        user_id = int(data.get("metadata", {}).get("user_id", 0))
        if user_id:
            create_license(user_id, "pro")
            conn.execute(
                "INSERT OR REPLACE INTO subscriptions (user_id, stripe_subscription_id, stripe_customer_id, tier, status) VALUES (?, ?, ?, 'pro', 'active')",
                (user_id, data.get("subscription"), data.get("customer")),
            )
            conn.commit()

    elif event_type == "customer.subscription.deleted":
        sub_id = data["id"]
        conn.execute(
            "UPDATE subscriptions SET status = 'canceled', tier = 'free', updated_at = datetime('now') WHERE stripe_subscription_id = ?",
            (sub_id,),
        )
        user_row = conn.execute(
            "SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ?", (sub_id,)
        ).fetchone()
        if user_row:
            conn.execute(
                "UPDATE licenses SET active = 0 WHERE user_id = ? AND tier = 'pro'",
                (user_row["user_id"],),
            )
        conn.commit()

    elif event_type == "invoice.paid":
        sub_id = data.get("subscription")
        if sub_id:
            conn.execute(
                "UPDATE subscriptions SET status = 'active', updated_at = datetime('now') WHERE stripe_subscription_id = ?",
                (sub_id,),
            )
            user_row = conn.execute(
                "SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ?", (sub_id,)
            ).fetchone()
            if user_row:
                conn.execute(
                    "UPDATE licenses SET active = 1 WHERE user_id = ? AND tier = 'pro'",
                    (user_row["user_id"],),
                )
        conn.commit()

    conn.close()
    return {"status": "ok"}
