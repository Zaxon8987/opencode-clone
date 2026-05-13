#!/usr/bin/env python3
"""Create Stripe product and price for opencode Pro subscription."""
import os
import stripe

stripe.api_key = input("Enter your Stripe secret key (sk_test_...): ").strip()

# Create product
product = stripe.Product.create(
    name="opencode Pro",
    description="Monthly subscription for opencode AI coding assistant — all 19 tools, priority support",
)
print(f"Product created: {product.id}")

# Create monthly price
price = stripe.Price.create(
    product=product.id,
    unit_amount=999,  # $9.99
    currency="usd",
    recurring={"interval": "month"},
    nickname="Pro Monthly",
)
print(f"Price created: {price.id}")
print(f"\nAdd these to your backend/.env:")
print(f"STRIPE_PRICE_PRO_MONTHLY={price.id}")
