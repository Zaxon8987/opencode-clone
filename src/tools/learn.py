from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from src.tools.base import Tool, ToolResult

LEARNINGS_FILE = Path.cwd() / ".session" / "learnings.json"


def _load() -> list[dict]:
    if LEARNINGS_FILE.exists():
        try:
            return json.loads(LEARNINGS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(data: list[dict]) -> None:
    LEARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEARNINGS_FILE.write_text(json.dumps(data, indent=2))


class Learn(Tool):
    name = "learn"
    description = "Store a pattern, convention, or insight for future sessions. Use this when you discover something useful."
    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Short name for this learning (e.g. 'commit-style', 'error-pattern-xyz')"},
            "value": {"type": "string", "description": "What you learned — be specific and actionable"},
            "category": {
                "type": "string",
                "enum": ["pattern", "convention", "fix", "architecture", "process", "other"],
                "description": "Category of learning",
                "default": "pattern",
            },
        },
        "required": ["key", "value"],
    }

    async def run(self, key: str, value: str, category: str = "pattern", **kwargs) -> ToolResult:
        data = _load()
        existing = next((d for d in data if d["key"] == key), None)
        now = datetime.now(timezone.utc).isoformat()
        entry = {"key": key, "value": value, "category": category, "updated_at": now}
        if existing:
            existing.update(entry)
        else:
            data.append(entry)
        _save(data)
        return ToolResult(success=True, data=f"Learned: {key}")


class Recall(Tool):
    name = "recall"
    description = "Search past learnings for patterns, conventions, or fixes. Call this before starting work."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term to find relevant learnings"},
            "category": {
                "type": "string",
                "enum": ["pattern", "convention", "fix", "architecture", "process", "other"],
                "description": "Filter by category",
            },
        },
    }

    async def run(self, query: str = "", category: str | None = None, **kwargs) -> ToolResult:
        data = _load()
        if not data:
            return ToolResult(success=True, data="No learnings stored yet.")
        results = []
        for d in data:
            if category and d.get("category") != category:
                continue
            if query and query.lower() not in d["key"].lower() and query.lower() not in d["value"].lower():
                continue
            results.append(d)
        if results:
            lines = []
            for r in results:
                lines.append(f"[{r['category']}] {r['key']}: {r['value']}")
            return ToolResult(success=True, data="\n".join(lines))
        return ToolResult(success=True, data=f"No learnings found for '{query}'")
