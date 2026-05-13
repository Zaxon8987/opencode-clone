#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_env, api_key
from src.license import get_license, save_license, remove_license, validate_online, is_pro
from src.context import SessionContext

load_env()


def check_key() -> None:
    if not api_key():
        print("Error: No API key found.")
        print("Copy .env.example to .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        sys.exit(1)


def show_banner() -> None:
    ctx = SessionContext()
    lic = get_license()
    tier = lic["tier"].upper() if lic and lic.get("valid") else "FREE"
    print(f"opencode — AI coding assistant [{tier}]")
    summary = ctx.summary()
    if summary:
        print(f"  {summary}")
    if tier == "FREE":
        print("  Upgrade to Pro: /license <key>")
    print("/help for commands\n")


def show_help() -> None:
    print("""
Commands:
  /exit, /quit          Exit
  /reset                Reset conversation
  /license <key>        Activate a license key
  /plan                 Show current plan + allowed tools
  /todo                 Show task list
  /todo add <task>      Add a task
  /todo done <id>       Mark task complete
  /terse                Toggle compact output mode
  /ctx                  Show session context
  /save                 Save session state
  /help                 Show this help
""")


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

        cmd = inp.lower()

        if cmd in ("/exit", "/quit"):
            break

        if cmd == "/help":
            show_help()
            continue

        if cmd == "/reset":
            agent.reset()
            SessionContext().reset()
            print("Session reset.\n")
            continue

        if cmd.startswith("/license"):
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
                print(f"Invalid: {result.get('error', 'Unknown error')}")
            continue

        if cmd == "/plan":
            lic = get_license()
            if lic and lic.get("valid"):
                print(f"Plan: {lic['tier'].upper()}")
                print(f"Tools: {', '.join(sorted(lic.get('features', [])))}")
            else:
                print("Plan: FREE")
                print("Tools: read, write, glob, grep, question")
            continue

        if cmd == "/todo":
            ctx = SessionContext()
            if not ctx.todos:
                print("No tasks.")
            else:
                for t in ctx.todos:
                    icons = {"pending": "O", "in_progress": ">", "completed": "x", "cancelled": "-"}
                    icon = icons.get(t["status"], "?")
                    print(f"  {icon} #{t['id']} {t['content']} [{t['priority']}]")
            continue

        if cmd.startswith("/todo add"):
            parts = inp.split(None, 2)
            if len(parts) < 3:
                print("Usage: /todo add <task>")
                continue
            ctx = SessionContext()
            todo = ctx.add_todo(parts[2])
            print(f"Task #{todo['id']} added.")
            continue

        if cmd.startswith("/todo done"):
            parts = inp.split(None, 2)
            if len(parts) < 3:
                print("Usage: /todo done <id>")
                continue
            try:
                tid = int(parts[2])
                ctx = SessionContext()
                if ctx.update_todo(tid, "completed"):
                    print(f"Task #{tid} completed.")
                else:
                    print(f"Task #{tid} not found.")
            except ValueError:
                print("ID must be a number.")
            continue

        if cmd == "/terse":
            ctx = SessionContext()
            ctx.terse = not ctx.terse
            ctx.save()
            print(f"Terse mode: {'ON' if ctx.terse else 'OFF'}")
            continue

        if cmd == "/ctx":
            ctx = SessionContext()
            print(f"Files touched ({len(ctx.files_touched)}): {', '.join(ctx.files_touched[-5:])}")
            print(f"Errors: {ctx.error_count}")
            print(f"Terse: {ctx.terse}")
            print(f"Tasks: {len(ctx.todos)} total, {sum(1 for t in ctx.todos if t['status'] == 'completed')} done")
            continue

        if cmd == "/save":
            agent.ctx.save()
            print("Session saved.")
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
