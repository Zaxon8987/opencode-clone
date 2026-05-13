from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any

FREE_TOOLS = {"read", "write", "glob", "grep", "question"}
PRO_TOOLS = {"bash", "edit", "web_search", "web_fetch", "git"}


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        if self.success:
            return {"type": "success", "data": self.data}
        return {"type": "error", "error": self.error}

    def __bool__(self) -> bool:
        return self.success


class Tool(ABC):
    name: str = ""
    description: str = ""
    input_schema: dict = field(default_factory=dict)
    pro: bool = False

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        ...

    def to_anthropic(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._allowed_tools: set[str] | None = None

    def add(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def set_tier(self, tier: str) -> None:
        if tier == "pro":
            self._allowed_tools = None
        else:
            self._allowed_tools = FREE_TOOLS

    def set_tier_from_license(self) -> None:
        from src.license import get_license
        lic = get_license()
        if lic and lic.get("valid"):
            self._allowed_tools = None
        else:
            self._allowed_tools = FREE_TOOLS

    def _visible_tools(self) -> list[Tool]:
        if self._allowed_tools is None:
            return list(self._tools.values())
        return [t for t in self._tools.values() if t.name in self._allowed_tools]

    def list_anthropic(self) -> list[dict]:
        return [t.to_anthropic() for t in self._visible_tools()]

    def list_openai(self) -> list[dict]:
        return [t.to_openai() for t in self._visible_tools()]

    async def call(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        if self._allowed_tools is not None and name not in self._allowed_tools:
            return ToolResult(success=False, error=f"Tool '{name}' requires Pro license. Use /license <key> to activate.")
        return await tool.run(**kwargs)
