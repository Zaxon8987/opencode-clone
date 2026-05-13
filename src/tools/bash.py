from __future__ import annotations
import asyncio
import os
import subprocess
from src.tools.base import Tool, ToolResult


DENIED_PREFIXES = (
    "rm -rf /", "rm -rf ~", "rm -rf .", "mkfs", "dd if=",
    ":(){", "> /dev/sda", "fork()", "chmod 777 /",
)


class Bash(Tool):
    name = "bash"
    description = "Execute a shell command and capture output. Use for running scripts, builds, git, or any CLI tool."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (max 300)", "default": 30},
            "workdir": {"type": "string", "description": "Working directory relative to current"},
        },
        "required": ["command"],
    }

    async def run(self, command: str, timeout: int = 30, workdir: str | None = None, **kwargs) -> ToolResult:
        for prefix in DENIED_PREFIXES:
            if command.strip().startswith(prefix):
                return ToolResult(success=False, error=f"Destructive command denied: {prefix}")
        cwd = None
        if workdir:
            from pathlib import Path
            resolved = (Path.cwd() / workdir).resolve()
            try:
                resolved.relative_to(Path.cwd())
            except ValueError:
                return ToolResult(success=False, error="Access denied: workdir outside workspace")
            cwd = str(resolved)
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy(),
                shell=True,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=min(timeout, 300))
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, error=f"Command timed out after {timeout}s")
            out = stdout.decode(errors="replace")[:50000]
            err = stderr.decode(errors="replace")[:20000]
            if proc.returncode != 0:
                return ToolResult(success=False, data={
                    "return_code": proc.returncode, "stdout": out, "stderr": err,
                })
            return ToolResult(success=True, data={
                "return_code": proc.returncode, "stdout": out, "stderr": err,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))
