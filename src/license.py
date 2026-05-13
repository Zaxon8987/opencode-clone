from __future__ import annotations
import os
import json
from pathlib import Path

LICENSE_FILE = Path.cwd() / ".session" / "license.json"
LICENSE_SERVER = os.environ.get("LICENSE_SERVER_URL", "http://localhost:8000")

FREE_TOOLS = {"read", "write", "glob", "grep", "question"}
PRO_TOOLS = {"bash", "edit", "web_search", "web_fetch", "git"}


def get_license() -> dict | None:
    if LICENSE_FILE.exists():
        try:
            return json.loads(LICENSE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_license(data: dict) -> None:
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(json.dumps(data, indent=2))


def remove_license() -> None:
    LICENSE_FILE.unlink(missing_ok=True)


def cached_features() -> list[str]:
    lic = get_license()
    if lic and lic.get("valid"):
        return lic.get("features", [])
    return list(FREE_TOOLS)


def is_tool_allowed(tool_name: str) -> bool:
    lic = get_license()
    if not lic or not lic.get("valid"):
        return tool_name in FREE_TOOLS
    return tool_name in lic.get("features", [])


def is_pro() -> bool:
    lic = get_license()
    return bool(lic and lic.get("valid") and lic.get("tier") == "pro")


async def validate_online(key: str) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{LICENSE_SERVER}/license/validate", json={"key": key})
        if r.status_code == 200:
            return r.json()
        return {"valid": False, "error": r.json().get("detail", "Validation failed")}
