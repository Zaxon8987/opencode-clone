from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any


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

    def add(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_anthropic(self) -> list[dict]:
        return [t.to_anthropic() for t in self._tools.values()]

    def list_openai(self) -> list[dict]:
        return [t.to_openai() for t in self._tools.values()]

    async def call(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        return await tool.run(**kwargs)
