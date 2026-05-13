from __future__ import annotations
import json
from src.llm import LLM
from src.tools import (
    ToolRegistry, Bash, Read, Write, Edit, Glob, Grep,
    WebSearch, WebFetch, Git, Question,
)

SYSTEM_PROMPT = """You are opencode, an AI coding assistant that helps users with software engineering tasks.

You have access to these tools:
- **bash** — Execute shell commands (scripts, builds, git, any CLI)
- **read** — Read file contents
- **write** — Write/create files
- **edit** — Find-and-replace in files (exact match required)
- **glob** — Find files by pattern (e.g. '**/*.py')
- **grep** — Search file contents by regex
- **web_search** — Search the web for current information
- **web_fetch** — Fetch a URL and extract text
- **git** — Run git commands
- **question** — Ask the user for clarification

Rules:
1. Be concise and direct. Prefer action over explanation.
2. Read files before editing them.
3. After completing a task, summarize what was done concisely.
4. Never commit secrets or credentials.
5. When uncertain, ask the user with the question tool.
6. Run verification commands before claiming work is done.
7. Never make up information — use tools to verify.
"""

MAX_TURNS = 25


class Agent:
    def __init__(self) -> None:
        self.registry = ToolRegistry()
        self._register_tools()
        self.registry.set_tier_from_license()
        self.llm = LLM(self.registry)
        self.messages: list[dict] = []

    def _register_tools(self) -> None:
        for tool in [Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Git, Question]:
            self.registry.add(tool())

    def reset(self) -> None:
        self.messages = []
        self.registry.set_tier_from_license()

    def _build_system_prompt(self) -> str:
        tools = self.registry.list_anthropic()
        lines = ["You are opencode, an AI coding assistant that helps users with software engineering tasks.",
                 "",
                 "Available tools:"]
        for t in tools:
            lines.append(f"- **{t['name']}** — {t['description']}")
        lines.extend([
            "",
            "Rules:",
            "1. Be concise and direct. Prefer action over explanation.",
            "2. Read files before editing them.",
            "3. After completing a task, summarize what was done concisely.",
            "4. Never commit secrets or credentials.",
            "5. When uncertain, ask the user with the question tool.",
            "6. Run verification commands before claiming work is done.",
            "7. Never make up information — use tools to verify.",
        ])
        return "\n".join(lines)

    def add_system(self) -> None:
        prompt = self._build_system_prompt()
        if not any(m["role"] == "system" for m in self.messages):
            self.messages.insert(0, {"role": "system", "content": prompt})
        else:
            for m in self.messages:
                if m["role"] == "system":
                    m["content"] = prompt

    async def run(self, user_input: str) -> None:
        self.messages.append({"role": "user", "content": user_input})
        self.add_system()

        for turn in range(MAX_TURNS):
            text_parts: list[str] = []
            tool_calls: list[dict] = []

            async for event in self.llm.stream(self.messages):
                if event["type"] == "text":
                    text_parts.append(event["text"])
                elif event["type"] == "tool_call":
                    tool_calls.append(event)

                if event["type"] == "text":
                    print(event["text"], end="", flush=True)

            if text_parts:
                print()
                self.messages.append({"role": "assistant", "content": "".join(text_parts)})

            if not tool_calls:
                break

            for tc in tool_calls:
                name, inp, result = tc["name"], tc["input"], tc["result"]
                status = "\u2713" if result["type"] == "success" else "\u2717"
                print(f"\n[{status} {name}]")

                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": json.dumps(result),
                }
                self.messages.append({
                    "role": "user",
                    "content": [tool_result_block],
                })
        else:
            print("\n[Reached max turns]")
