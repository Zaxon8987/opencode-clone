#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_env, api_key

load_env()


def check_key() -> None:
    if not api_key():
        print("Error: No API key found.")
        print("Copy .env.example to .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        sys.exit(1)


async def repl() -> None:
    from src.agent import Agent

    agent = Agent()
    print("opencode — AI coding assistant. Type /exit to quit.\n")

    while True:
        try:
            inp = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not inp:
            continue
        if inp.lower() in ("/exit", "/quit"):
            break
        if inp.lower() == "/reset":
            agent.reset()
            print("Session reset.\n")
            continue

        await agent.run(inp)
        print()


async def single(prompt: str) -> None:
    from src.agent import Agent

    agent = Agent()
    await agent.run(prompt)


def main() -> None:
    check_key()
    prompt = " ".join(sys.argv[1:])
    if prompt:
        asyncio.run(single(prompt))
    else:
        try:
            asyncio.run(repl())
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
