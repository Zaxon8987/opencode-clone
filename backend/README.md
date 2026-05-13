# opencode License Server

FastAPI backend for subscription management and license key validation.

## Setup

```bash
cd backend
cp .env.example .env
```

### 1. Get your Stripe keys

1. Go to https://dashboard.stripe.com/apikeys
2. Copy **Secret key** (`sk_test_...`) into `.env` as `STRIPE_SECRET_KEY`
3. Your **Publishable key** (`pk_test_...`) goes in `web/checkout.html`

### 2. Create a product and price

```bash
python3 setup_stripe.py
# Enter your sk_test_... key when prompted
# Copy the price_xxx ID into .env as STRIPE_PRICE_PRO_MONTHLY
```

### 3. Set up webhook (for local dev)

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe listen --forward-to localhost:8000/webhook/stripe
# Copy the whsec_... secret into .env as STRIPE_WEBHOOK_SECRET
```

### 4. Run the server

```bash
uvicorn main:app --reload --port 8000
```

### 5. Open checkout page

Open `web/checkout.html` in a browser and subscribe.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/checkout/create` | POST | Create Stripe Checkout session |
| `/checkout/success` | GET | License activation callback |
| `/checkout/cancel` | GET | Cancelled checkout |
| `/webhook/stripe` | POST | Stripe event webhooks |
| `/license/validate` | POST | Validate a license key |
| `/license/features/{tier}` | GET | Get allowed tools for tier |
| `/health` | GET | Health check |

## Deploy

Deploy to Render/Railway/Fly:
- Set all env vars from `.env`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set `LICENSE_SERVER_URL` in the CLI `.env` to your deployed URL
