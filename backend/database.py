from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "data" / "opencode.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            google_id TEXT UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            stripe_subscription_id TEXT UNIQUE,
            stripe_customer_id TEXT,
            tier TEXT NOT NULL DEFAULT 'free',
            status TEXT NOT NULL DEFAULT 'active',
            current_period_start TEXT,
            current_period_end TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            key TEXT UNIQUE NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            active BOOLEAN NOT NULL DEFAULT 1,
            expires_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS feature_flags (
            tier TEXT NOT NULL,
            feature TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT 1,
            PRIMARY KEY (tier, feature)
        );
    """)

    default_features = {
        "free": ["read", "write", "glob", "grep", "question"],
        "pro": [
            "read", "write", "edit", "glob", "grep",
            "bash", "web_search", "web_fetch", "git", "question",
            "priority_support",
        ],
    }
    for tier, features in default_features.items():
        for feature in features:
            conn.execute(
                "INSERT OR IGNORE INTO feature_flags (tier, feature, enabled) VALUES (?, ?, 1)",
                (tier, feature),
            )
    conn.commit()
    conn.close()
