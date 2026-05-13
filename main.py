#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_env, api_key
from src.license import get_license, save_license, remove_license, validate_online, is_pro

load_env()


def check_key() -> None:
    if not api_key():
        print("Error: No API key found.")
        print("Copy .env.example to .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        sys.exit(1)


def show_banner() -> None:
    lic = get_license()
    tier = lic["tier"].upper() if lic and lic.get("valid") else "FREE"
    print(f"opencode — AI coding assistant [{tier}]")
    if tier == "FREE":
        print("Upgrade to Pro: set a license key with /license <key>")
    print()


async def repl() -> None:
    from src.agent import Agent

    agent = Agent()
    show_banner()

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
        if inp.lower().startswith("/license"):
            parts = inp.split(None, 1)
            if len(parts) < 2:
                print("Usage: /license <key>")
                continue
            key = parts[1].strip()
            result = await validate_online(key)
            if result.get("valid"):
                save_license(result)
                print(f"License activated! Tier: {result['tier'].upper()}")
                agent.registry.set_tier(result.get("tier", "free"))
            else:
                print(f"License invalid: {result.get('error', 'Unknown error')}")
            continue
        if inp.lower() == "/plan":
            lic = get_license()
            if lic and lic.get("valid"):
                tier = lic["tier"].upper()
                features = lic.get("features", [])
                print(f"Plan: {tier}")
                print(f"Tools: {', '.join(sorted(features))}")
            else:
                print("Plan: FREE")
                print("Tools: read, write, glob, grep, question")
            continue

        agent.registry.set_tier_from_license()
        await agent.run(inp)
        print()


async def single(prompt: str) -> None:
    from src.agent import Agent

    agent = Agent()
    agent.registry.set_tier_from_license()
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
