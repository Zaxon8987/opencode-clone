from __future__ import annotations
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes.checkout import router as checkout_router
from routes.webhooks import router as webhook_router
from routes.license import router as license_router

app = FastAPI(title="opencode license server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(checkout_router)
app.include_router(webhook_router)
app.include_router(license_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"name": "opencode license server", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


def serve() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    serve()
