from __future__ import annotations
import asyncio
import subprocess
import sys
from pathlib import Path
from src.tools.base import Tool, ToolResult


class Spawn(Tool):
    name = "spawn"
    description = "Launch a sub-agent to handle an independent task in parallel. Use for multi-file changes, independent research, or parallel work."
    input_schema = {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "The task for the sub-agent to complete"},
            "timeout": {"type": "integer", "description": "Max seconds to wait for the sub-agent", "default": 120},
        },
        "required": ["task"],
    }

    async def run(self, task: str, timeout: int = 120, **kwargs) -> ToolResult:
        root = Path(__file__).parent.parent.parent
        main_py = root / "main.py"
        if not main_py.exists():
            return ToolResult(success=False, error=f"main.py not found at {main_py}")
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, str(main_py), task,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(root),
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=min(timeout, 300))
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, data={
                    "error": f"Sub-agent timed out after {timeout}s",
                })
            out = stdout.decode(errors="replace")[:15000]
            err = stderr.decode(errors="replace")[:5000]
            return ToolResult(
                success=proc.returncode == 0,
                data={"stdout": out, "stderr": err, "return_code": proc.returncode},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
