from __future__ import annotations
import asyncio
import subprocess
from src.tools.base import Tool, ToolResult


def _run_sync(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", str(e)
    except FileNotFoundError:
        return -1, "", "git not found"


class Git(Tool):
    name = "git"
    description = "Run git commands: status, diff, log, add, commit, branch, checkout, push, pull, etc."
    input_schema = {
        "type": "object",
        "properties": {
            "args": {"type": "string", "description": "Git arguments (e.g. 'status', 'diff', 'log --oneline -5')"},
        },
        "required": ["args"],
    }

    async def run(self, args: str, **kwargs) -> ToolResult:
        cmd = ["git"] + args.split()
        denied = {"push --force", "push -f", "reset --hard", "clean -fd"}
        if any(d in args for d in denied):
            return ToolResult(success=False, error=f"Destructive git command denied: {args}")
        loop = asyncio.get_event_loop()
        rc, stdout, stderr = await loop.run_in_executor(None, _run_sync, cmd, None)
        if rc != 0:
            return ToolResult(success=False, data={"stdout": stdout, "stderr": stderr, "return_code": rc})
        return ToolResult(success=True, data={"stdout": stdout, "stderr": stderr})
