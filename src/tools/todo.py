from __future__ import annotations
from src.tools.base import Tool, ToolResult
from src.context import SessionContext


class TodoWrite(Tool):
    name = "todo"
    description = "Create, update, or list tasks. Use this for multi-step work to track progress."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "update", "list", "summary"],
                "description": "Action: create a task, update its status, list all, or get a summary",
            },
            "content": {"type": "string", "description": "Task description (required for create)"},
            "task_id": {"type": "integer", "description": "Task ID (required for update)"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "cancelled"],
                "description": "New status (for update)",
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Task priority",
            },
        },
        "required": ["action"],
    }

    async def run(self, action: str, content: str | None = None, task_id: int | None = None, status: str | None = None, priority: str = "medium", **kwargs) -> ToolResult:
        ctx = SessionContext()

        if action == "create":
            if not content:
                return ToolResult(success=False, error="content required for create")
            todo = ctx.add_todo(content, priority)
            return ToolResult(success=True, data=f"Task #{todo['id']}: {todo['content']} [{todo['priority']}]")

        if action == "update":
            if task_id and status:
                if ctx.update_todo(task_id, status):
                    return ToolResult(success=True, data=f"Task #{task_id} -> {status}")
                return ToolResult(success=False, error=f"Task #{task_id} not found")
            return ToolResult(success=False, error="task_id and status required for update")

        if action == "list":
            if not ctx.todos:
                return ToolResult(success=True, data="No tasks")
            lines = []
            for t in ctx.todos:
                icon = {"pending": "\u25cb", "in_progress": "\u25b6", "completed": "\u2713", "cancelled": "\u2717"}.get(t["status"], "?")
                lines.append(f"{icon} #{t['id']} {t['content']} [{t['priority']}]")
            return ToolResult(success=True, data="\n".join(lines))

        if action == "summary":
            total = len(ctx.todos)
            done = sum(1 for t in ctx.todos if t["status"] == "completed")
            pending = sum(1 for t in ctx.todos if t["status"] in ("pending", "in_progress"))
            return ToolResult(success=True, data=f"{done}/{total} tasks done, {pending} remaining")

        return ToolResult(success=False, error=f"Unknown action: {action}")
