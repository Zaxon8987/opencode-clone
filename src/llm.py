from __future__ import annotations
import json
from typing import AsyncIterator
from src.config import provider, model, api_key
from src.tools.base import ToolRegistry

import httpx
from httpx_sse import aconnect_sse


class LLMError(Exception):
    pass


class LLM:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self._api_key = api_key()
        self._provider = provider()
        self._model = model()

    async def stream(self, messages: list[dict]) -> AsyncIterator[dict]:
        if self._provider == "anthropic":
            async for event in self._anthropic(messages):
                yield event
        else:
            async for event in self._openai(messages):
                yield event

    async def _anthropic(self, messages: list[dict]) -> AsyncIterator[dict]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        body = {
            "model": self._model,
            "max_tokens": 8192,
            "tools": self.registry.list_anthropic(),
            "messages": filtered,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=180) as client:
            async with aconnect_sse(
                client, "POST", "https://api.anthropic.com/v1/messages",
                headers=self._anthropic_headers(),
                json=body,
            ) as event_source:
                current_tool: dict | None = None
                tool_input_buf = ""

                async for sse in event_source.aiter_sse():
                    data = sse.json()

                    if sse.event == "content_block_start":
                        block = data.get("content_block", {})
                        if block.get("type") == "tool_use":
                            current_tool = {"id": block["id"], "name": block["name"]}
                            tool_input_buf = ""

                    elif sse.event == "content_block_delta":
                        delta = data.get("delta", {})
                        dt = delta.get("type")
                        if dt == "text_delta":
                            yield {"type": "text", "text": delta["text"]}
                        elif dt == "input_json_delta":
                            tool_input_buf += delta.get("partial_json", "")

                    elif sse.event == "content_block_stop" and current_tool:
                        inp = json.loads(tool_input_buf) if tool_input_buf.strip() else {}
                        result = await self.registry.call(current_tool["name"], **inp)
                        yield {
                            "type": "tool_call",
                            "id": current_tool["id"],
                            "name": current_tool["name"],
                            "input": inp,
                            "result": result.to_dict(),
                        }
                        current_tool = None
                        tool_input_buf = ""

                    elif sse.event == "message_stop":
                        break

    async def _openai(self, messages: list[dict]) -> AsyncIterator[dict]:
        body = {
            "model": self._model,
            "max_tokens": 8192,
            "tools": self.registry.list_openai(),
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self._openai_headers(),
                json=body,
            )
            data = r.json()
            if r.status_code != 200:
                raise LLMError(f"OpenAI error {r.status_code}: {data}")
            msg = data["choices"][0]["message"]
            if msg.get("content"):
                yield {"type": "text", "text": msg["content"]}
            for tc in msg.get("tool_calls") or []:
                args = json.loads(tc["function"]["arguments"])
                result = await self.registry.call(tc["function"]["name"], **args)
                yield {
                    "type": "tool_call",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": args,
                    "result": result.to_dict(),
                }

    def _anthropic_headers(self) -> dict:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _openai_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }
