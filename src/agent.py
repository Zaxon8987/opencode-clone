from __future__ import annotations
import json
from src.llm import LLM
from src.context import SessionContext
from src.tools import (
    ToolRegistry,
    Bash, Read, Write, Edit, Glob, Grep,
    WebSearch, WebFetch, Git, Question,
    TodoWrite, Verify, Spawn,
    GitHub, LoadSkill, ListSkills, ProjectInfo,
    Learn, Recall,
)

MAX_TURNS = 25


class Agent:
    def __init__(self) -> None:
        self.ctx = SessionContext()
        self.registry = ToolRegistry()
        self._register_tools()
        self.registry.set_tier_from_license()
        self.llm = LLM(self.registry)
        self.messages: list[dict] = []

    def _register_tools(self) -> None:
        for tool in [
            Bash, Read, Write, Edit, Glob, Grep,
            WebSearch, WebFetch, Git, Question,
            TodoWrite, Verify, Spawn,
            GitHub, LoadSkill, ListSkills, ProjectInfo,
            Learn, Recall,
        ]:
            self.registry.add(tool())

    def reset(self) -> None:
        self.messages = []
        self.registry.set_tier_from_license()

    def _build_system_prompt(self) -> str:
        tools = self.registry.list_anthropic()
        lines = [
            "You are opencode, an AI coding assistant that helps users with software engineering tasks.",
            "",
            "Available tools:",
        ]
        for t in tools:
            lines.append(f"- **{t['name']}** — {t['description']}")
        lines.extend([
            "",
            "Rules:",
            "1. Be concise and direct. Prefer action over explanation.",
            "2. Read files before editing them.",
            "3. Use the todo tool to track progress on multi-step tasks.",
            "4. After changing code, use the verify tool to run tests/lint.",
            "5. For independent tasks, use the spawn tool to parallelize.",
            "6. Use load_skill for domain-specific work (security, DB, deploy).",
            "7. Use recall before starting to check past learnings.",
            "8. Use project_info on startup to understand the codebase.",
            "9. Use github for PRs, issues, and CI operations.",
            "10. Never commit secrets or credentials.",
            "11. When uncertain, ask the user with the question tool.",
            "12. Never make up information — use tools to verify.",
            "13. If something fails twice, try a different approach.",
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
        consecutive_failures = 0

        for turn in range(MAX_TURNS):
            if self.ctx.is_in_fix_loop():
                print("\n[Recovery: multiple failures detected. Switching approaches.]")
                self.messages.append({
                    "role": "user",
                    "content": "Previous attempts have failed multiple times. Take a step back and try a fundamentally different approach. Do not repeat the same failing strategy.",
                })
                self.ctx.reset_errors()

            text_parts: list[str] = []
            tool_calls: list[dict] = []

            async for event in self.llm.stream(self.messages):
                if event["type"] == "text":
                    text_parts.append(event["text"])
                    if not self.ctx.terse:
                        print(event["text"], end="", flush=True)
                elif event["type"] == "tool_call":
                    tool_calls.append(event)

            if text_parts and self.ctx.terse:
                summary = "".join(text_parts)[:200]
                print(f"\n[{summary}]\n", end="")

            if text_parts:
                print() if not self.ctx.terse else None
                self.messages.append({"role": "assistant", "content": "".join(text_parts)})

            if not tool_calls:
                break

            for tc in tool_calls:
                name = tc["name"]
                result = tc["result"]
                status = "\u2713" if result["type"] == "success" else "\u2717"

                if not self.ctx.terse:
                    print(f"\n[{status} {name}]")

                if result["type"] == "success":
                    consecutive_failures = 0
                    self.ctx.reset_errors()
                else:
                    consecutive_failures += 1
                    self.ctx.add_error(f"{name}: {result.get('error', 'unknown')}")

                if name in ("write", "edit"):
                    path = tc["input"].get("file_path", tc["input"].get("path", ""))
                    if path:
                        self.ctx.touch_file(path)

                tool_block = {
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": json.dumps(result),
                }
                self.messages.append({
                    "role": "user",
                    "content": [tool_block],
                })
        else:
            print("\n[Reached max turns]")

        self.ctx.conversation_summary.append({
            "input": user_input[:100],
            "tools_used": len([m for m in self.messages if m["role"] == "user" and isinstance(m.get("content"), list)]),
            "turns": turn + 1,
        })
        self.ctx.conversation_summary = self.ctx.conversation_summary[-20:]
        self.ctx.save()
