from __future__ import annotations
import os
import re
from pathlib import Path
from src.tools.base import Tool, ToolResult

WORKSPACE = Path.cwd()


def _safe(path_str: str) -> Path | None:
    p = (WORKSPACE / path_str).resolve()
    try:
        p.relative_to(WORKSPACE)
    except ValueError:
        return None
    return p


class Read(Tool):
    name = "read"
    description = "Read a file's contents. Supports line offset and limit for large files."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "offset": {"type": "integer", "description": "Starting line number (1-indexed)"},
            "limit": {"type": "integer", "description": "Max lines to read"},
        },
        "required": ["file_path"],
    }

    async def run(self, file_path: str, offset: int | None = None, limit: int | None = None, **kwargs) -> ToolResult:
        fp = _safe(file_path)
        if not fp:
            return ToolResult(success=False, error="Access denied: path outside workspace")
        if not fp.exists():
            return ToolResult(success=False, error=f"File not found: {file_path}")
        if fp.is_dir():
            return ToolResult(success=False, error=f"Is a directory: {file_path}")
        try:
            text = fp.read_text(encoding="utf-8")
            lines = text.splitlines(keepends=True)
            total = len(lines)
            start = (offset - 1) if offset and offset > 0 else 0
            end = start + limit if limit else total
            content = "".join(lines[start:end])
            return ToolResult(success=True, data={
                "content": content, "total_lines": total,
                "start_line": start + 1, "end_line": min(end, total),
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class Write(Tool):
    name = "write"
    description = "Write content to a file. Creates parent directories if needed. Overwrites existing files."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to write to"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["file_path", "content"],
    }

    async def run(self, file_path: str, content: str, **kwargs) -> ToolResult:
        fp = _safe(file_path)
        if not fp:
            return ToolResult(success=False, error="Access denied: path outside workspace")
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            return ToolResult(success=True, data=f"Written {len(content)} bytes to {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class Edit(Tool):
    name = "edit"
    description = "Find and replace exact text in a file. The old_string must match exactly (including indentation)."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "old_string": {"type": "string", "description": "Text to replace (must match exactly)"},
            "new_string": {"type": "string", "description": "Replacement text"},
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def run(self, file_path: str, old_string: str, new_string: str, **kwargs) -> ToolResult:
        fp = _safe(file_path)
        if not fp:
            return ToolResult(success=False, error="Access denied: path outside workspace")
        if not fp.exists():
            return ToolResult(success=False, error=f"File not found: {file_path}")
        try:
            text = fp.read_text(encoding="utf-8")
            if old_string not in text:
                return ToolResult(success=False, error="old_string not found in file")
            if text.count(old_string) > 1:
                return ToolResult(success=False, error="Multiple matches. Provide more context.")
            new_text = text.replace(old_string, new_string, 1)
            fp.write_text(new_text, encoding="utf-8")
            return ToolResult(success=True, data=f"Edited {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class Glob(Tool):
    name = "glob"
    description = "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts'). Sorted by modification time."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to search"},
            "path": {"type": "string", "description": "Root directory (defaults to workspace)"},
        },
        "required": ["pattern"],
    }

    async def run(self, pattern: str, path: str | None = None, **kwargs) -> ToolResult:
        root = _safe(path) if path else WORKSPACE
        if not root:
            return ToolResult(success=False, error="Access denied: path outside workspace")
        try:
            files = sorted(
                [str(p.relative_to(WORKSPACE)) for p in root.rglob(pattern) if p.is_file()],
                key=lambda f: -os.path.getmtime(WORKSPACE / f),
            )
            return ToolResult(success=True, data=files)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class Grep(Tool):
    name = "grep"
    description = "Search file contents with a regex pattern. Returns matching file paths and line numbers."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search"},
            "include": {"type": "string", "description": "File pattern filter (e.g. '*.py')"},
            "path": {"type": "string", "description": "Root directory"},
        },
        "required": ["pattern"],
    }

    async def run(self, pattern: str, include: str | None = None, path: str | None = None, **kwargs) -> ToolResult:
        root = _safe(path) if path else WORKSPACE
        if not root:
            return ToolResult(success=False, error="Access denied: path outside workspace")
        try:
            matches = []
            for p in root.rglob(include or "*"):
                if not p.is_file():
                    continue
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if re.search(pattern, line):
                        rel = str(p.relative_to(WORKSPACE))
                        matches.append(f"{rel}:{i}: {line.strip()[:200]}")
            return ToolResult(success=True, data=matches)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
