opencode-backend/
├── main.py              # FastAPI app with routes
├── database.py          # SQLite setup + schema
├── license.py           # License key generation & validation
├── routes/
│   ├── checkout.py      # Stripe checkout sessions
│   ├── webhooks.py      # Stripe event webhooks
│   └── license.py       # License validation API
├── pyproject.toml
├── requirements.txt
├── .env.example
└── render.yaml          # Deployment config (Render)
