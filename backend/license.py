from __future__ import annotations
import secrets
from database import get_db


def generate_key() -> str:
    return "oc-" + secrets.token_hex(16)


def create_license(user_id: int, tier: str, expires_at: str | None = None) -> dict:
    key = generate_key()
    conn = get_db()
    conn.execute(
        "INSERT INTO licenses (user_id, key, tier, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, key, tier, expires_at),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM licenses WHERE key = ?", (key,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def validate_license(key: str) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT l.*, u.email, u.name FROM licenses l JOIN users u ON l.user_id = u.id WHERE l.key = ?",
        (key,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    lic = dict(row)
    if not lic["active"]:
        return None
    return lic


def get_features_for_tier(tier: str) -> list[str]:
    conn = get_db()
    rows = conn.execute(
        "SELECT feature FROM feature_flags WHERE tier = ? AND enabled = 1",
        (tier,),
    ).fetchall()
    conn.close()
    return [r["feature"] for r in rows]
