import os
from pathlib import Path

ROOT = Path.cwd()
SESSION_DIR = ROOT / ".session"


def load_env() -> None:
    dotenv_path = ROOT / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


def provider() -> str:
    return "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"


def model() -> str:
    return os.environ.get("AGENT_MODEL", "claude-sonnet-4-20250514")
