from __future__ import annotations
import asyncio
import subprocess
from src.tools.base import Tool, ToolResult


class Verify(Tool):
    name = "verify"
    description = "Run a verification command (tests, lint, typecheck, build) and report the result. Use this before declaring work complete."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The verification command to run (e.g. 'pytest', 'npm test', 'ruff check .')"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60},
        },
        "required": ["command"],
    }

    async def run(self, command: str, timeout: int = 60, **kwargs) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=min(timeout, 120))
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, data={
                    "verdict": "TIMEOUT",
                    "message": f"Verification timed out after {timeout}s",
                })
            out = stdout.decode(errors="replace")[:5000]
            err = stderr.decode(errors="replace")[:5000]
            passed = proc.returncode == 0
            return ToolResult(
                success=passed,
                data={
                    "verdict": "PASS" if passed else "FAIL",
                    "return_code": proc.returncode,
                    "stdout": out,
                    "stderr": err,
                    "message": "All checks passed" if passed else f"Exit code {proc.returncode}",
                },
            )
        except Exception as e:
            return ToolResult(success=False, data={"verdict": "ERROR", "message": str(e)})
