from __future__ import annotations
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from database import get_db
from license import create_license

router = APIRouter(prefix="/checkout", tags=["checkout"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
PRICE_ID = os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")


class CreateSession(BaseModel):
    email: str
    name: str = ""


@router.post("/create")
async def create_checkout(data: CreateSession):
    if not stripe.api_key:
        raise HTTPException(400, "Stripe not configured")
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (data.email,)).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            (data.email, data.name),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (data.email,)).fetchone()
    conn.close()

    session = stripe.checkout.Session.create(
        customer_email=data.email,
        mode="subscription",
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        success_url="{host}/checkout/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="{host}/checkout/cancel",
        metadata={"user_id": str(user["id"])},
    )
    return {"url": session.url, "session_id": session.id}


@router.get("/success")
async def checkout_success(session_id: str):
    if not stripe.api_key:
        raise HTTPException(400, "Stripe not configured")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(400, str(e))

    user_id = int(session.metadata.get("user_id", 0))
    if not user_id:
        raise HTTPException(400, "Invalid session")

    sub_id = session.get("subscription")
    cust_id = session.get("customer")

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE subscriptions SET stripe_subscription_id = ?, stripe_customer_id = ?, tier = 'pro', status = 'active', updated_at = datetime('now') WHERE user_id = ?",
            (sub_id, cust_id, user_id),
        )
    else:
        conn.execute(
            "INSERT INTO subscriptions (user_id, stripe_subscription_id, stripe_customer_id, tier, status) VALUES (?, ?, ?, 'pro', 'active')",
            (user_id, sub_id, cust_id),
        )
    conn.commit()
    conn.close()

    create_license(user_id, "pro")
    return {"status": "ok", "message": "Pro subscription activated!"}


@router.get("/cancel")
async def checkout_cancel():
    return {"status": "cancelled"}
