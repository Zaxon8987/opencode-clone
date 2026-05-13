from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

SESSION_DIR = Path.cwd() / ".session"
FILE = SESSION_DIR / "context.json"


class SessionContext:
    def __init__(self) -> None:
        self.todos: list[dict] = []
        self.files_touched: list[str] = []
        self.recent_errors: list[str] = []
        self.error_count: int = 0
        self.terse: bool = False
        self.conversation_summary: list[dict] = []
        self._load()

    def _path(self) -> Path:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        return FILE

    def _load(self) -> None:
        p = self._path()
        if p.exists():
            try:
                data = json.loads(p.read_text())
                self.todos = data.get("todos", [])
                self.files_touched = data.get("files_touched", [])
                self.recent_errors = data.get("recent_errors", [])
                self.error_count = data.get("error_count", 0)
                self.terse = data.get("terse", False)
                self.conversation_summary = data.get("conversation_summary", [])
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        data = {
            "todos": self.todos,
            "files_touched": self.files_touched,
            "recent_errors": self.recent_errors,
            "error_count": self.error_count,
            "terse": self.terse,
            "conversation_summary": self.conversation_summary,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._path().write_text(json.dumps(data, indent=2))

    def touch_file(self, path: str) -> None:
        if path not in self.files_touched:
            self.files_touched.append(path)
            self.files_touched = self.files_touched[-50:]
            self.save()

    def add_error(self, error: str) -> None:
        self.recent_errors.append(error)
        self.recent_errors = self.recent_errors[-10:]
        self.error_count += 1
        self.save()

    def reset_errors(self) -> None:
        self.recent_errors = []
        self.error_count = 0
        self.save()

    def add_todo(self, content: str, priority: str = "medium") -> dict:
        tid = max([t["id"] for t in self.todos], default=0) + 1
        todo = {
            "id": tid,
            "content": content,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.todos.append(todo)
        self.save()
        return todo

    def update_todo(self, tid: int, status: str | None = None) -> bool:
        for t in self.todos:
            if t["id"] == tid:
                if status:
                    t["status"] = status
                self.save()
                return True
        return False

    def is_in_fix_loop(self) -> bool:
        return self.error_count >= 4

    def summary(self) -> str:
        lines = []
        pending = sum(1 for t in self.todos if t["status"] == "pending")
        completed = sum(1 for t in self.todos if t["status"] == "completed")
        if self.todos:
            lines.append(f"Tasks: {completed}/{len(self.todos)} done, {pending} pending")
        if self.files_touched:
            lines.append(f"Files touched: {len(self.files_touched)}")
        if self.error_count > 0:
            lines.append(f"Errors: {self.error_count}")
        return " | ".join(lines) if lines else ""

    def reset(self) -> None:
        self.todos = []
        self.files_touched = []
        self.recent_errors = []
        self.error_count = 0
        self.conversation_summary = []
        self.save()
