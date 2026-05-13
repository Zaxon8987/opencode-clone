from __future__ import annotations
import json
import sys
from src.tools.base import Tool, ToolResult


class Question(Tool):
    name = "question"
    description = "Ask the user a question when you need clarification, a decision, or confirmation before proceeding."
    input_schema = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question to ask the user"},
        },
        "required": ["question"],
    }

    async def run(self, question: str, **kwargs) -> ToolResult:
        print(f"\n\u2794 {question}")
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return ToolResult(success=False, error="User cancelled input")
        return ToolResult(success=True, data=answer)
