from __future__ import annotations
import asyncio
import subprocess
import json
from src.tools.base import Tool, ToolResult


def _gh(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", str(e)
    except FileNotFoundError:
        return -1, "", "gh CLI not found. Install: https://cli.github.com"


class GitHub(Tool):
    name = "github"
    description = "GitHub operations: create/list PRs, issues, reviews, check CI, manage releases."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "pr_create", "pr_list", "pr_view", "pr_merge", "pr_comment",
                    "issue_create", "issue_list", "issue_view", "issue_comment",
                    "ci_view", "release_create", "repo_info",
                ],
                "description": "Action to perform",
            },
            "title": {"type": "string", "description": "Title for PR/issue/release"},
            "body": {"type": "string", "description": "Body content for PR/issue/release"},
            "number": {"type": "integer", "description": "PR or issue number"},
            "state": {"type": "string", "description": "Filter: open/closed/all"},
            "label": {"type": "string", "description": "Label to filter by"},
            "tag": {"type": "string", "description": "Git tag for release"},
            "base": {"type": "string", "description": "Base branch for PR"},
            "head": {"type": "string", "description": "Head branch for PR"},
        },
        "required": ["action"],
    }

    async def run(self, action: str, **kwargs) -> ToolResult:
        loop = asyncio.get_event_loop()

        if action == "pr_create":
            title = kwargs.get("title", "")
            body = kwargs.get("body", "")
            base = kwargs.get("base", "main")
            head = kwargs.get("head", "")
            if not title or not head:
                return ToolResult(success=False, error="title and head required")
            rc, out, err = await loop.run_in_executor(
                None, _gh,
                ["pr", "create", "--title", title, "--body", body, "--base", base, "--head", head],
            )
            return ToolResult(success=rc == 0, data={"url": out.strip(), "stderr": err} if rc == 0 else {"error": err, "stdout": out})

        if action == "pr_list":
            state = kwargs.get("state", "open")
            label = kwargs.get("label", "")
            args = ["pr", "list", "--state", state, "--json", "number,title,state,author,createdAt,headRefName,baseRefName,url"]
            if label:
                args.extend(["--label", label])
            rc, out, err = await loop.run_in_executor(None, _gh, args)
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            prs = json.loads(out) if out else []
            return ToolResult(success=True, data=prs)

        if action == "pr_view":
            num = kwargs.get("number")
            if not num:
                return ToolResult(success=False, error="number required")
            rc, out, err = await loop.run_in_executor(
                None, _gh,
                ["pr", "view", str(num), "--json", "number,title,body,state,author,createdAt,mergedAt,additions,deletions,files,comments,reviews,url"],
            )
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            return ToolResult(success=True, data=json.loads(out))

        if action == "pr_merge":
            num = kwargs.get("number")
            if not num:
                return ToolResult(success=False, error="number required")
            rc, out, err = await loop.run_in_executor(
                None, _gh, ["pr", "merge", str(num), "--squash"],
            )
            return ToolResult(success=rc == 0, data={"message": out.strip(), "stderr": err} if rc == 0 else {"error": err})

        if action == "pr_comment":
            num = kwargs.get("number")
            body = kwargs.get("body", "")
            if not num or not body:
                return ToolResult(success=False, error="number and body required")
            rc, out, err = await loop.run_in_executor(
                None, _gh, ["pr", "comment", str(num), "--body", body],
            )
            return ToolResult(success=rc == 0, data={"message": out.strip()} if rc == 0 else {"error": err})

        if action == "issue_create":
            title = kwargs.get("title", "")
            body = kwargs.get("body", "")
            label = kwargs.get("label", "")
            if not title:
                return ToolResult(success=False, error="title required")
            args = ["issue", "create", "--title", title, "--body", body]
            if label:
                args.extend(["--label", label])
            rc, out, err = await loop.run_in_executor(None, _gh, args)
            return ToolResult(success=rc == 0, data={"url": out.strip()} if rc == 0 else {"error": err})

        if action == "issue_list":
            state = kwargs.get("state", "open")
            label = kwargs.get("label", "")
            args = ["issue", "list", "--state", state, "--json", "number,title,state,author,createdAt,labels,url"]
            if label:
                args.extend(["--label", label])
            rc, out, err = await loop.run_in_executor(None, _gh, args)
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            return ToolResult(success=True, data=json.loads(out) if out else [])

        if action == "issue_view":
            num = kwargs.get("number")
            if not num:
                return ToolResult(success=False, error="number required")
            rc, out, err = await loop.run_in_executor(
                None, _gh, ["issue", "view", str(num), "--json", "number,title,body,state,author,createdAt,comments,url"],
            )
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            return ToolResult(success=True, data=json.loads(out))

        if action == "issue_comment":
            num = kwargs.get("number")
            body = kwargs.get("body", "")
            if not num or not body:
                return ToolResult(success=False, error="number and body required")
            rc, out, err = await loop.run_in_executor(
                None, _gh, ["issue", "comment", str(num), "--body", body],
            )
            return ToolResult(success=rc == 0, data={"message": out.strip()} if rc == 0 else {"error": err})

        if action == "ci_view":
            branch = kwargs.get("head") or kwargs.get("base", "main")
            rc, out, err = await loop.run_in_executor(
                None, _gh,
                ["run", "list", "--branch", branch, "--json", "databaseId,displayTitle,status,conclusion,updatedAt,url", "--limit", "10"],
            )
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            return ToolResult(success=True, data=json.loads(out) if out else [])

        if action == "release_create":
            tag = kwargs.get("tag", "")
            title = kwargs.get("title", "")
            body = kwargs.get("body", "")
            if not tag:
                return ToolResult(success=False, error="tag required")
            args = ["release", "create", tag, "--title", title or tag, "--notes", body]
            rc, out, err = await loop.run_in_executor(None, _gh, args)
            return ToolResult(success=rc == 0, data={"url": out.strip()} if rc == 0 else {"error": err})

        if action == "repo_info":
            rc, out, err = await loop.run_in_executor(
                None, _gh, ["repo", "view", "--json", "name,owner,description,url,defaultBranch,primaryLanguage,languages,issues,pullRequests"],
            )
            if rc != 0:
                return ToolResult(success=False, data={"error": err})
            return ToolResult(success=True, data=json.loads(out))

        return ToolResult(success=False, error=f"Unknown action: {action}")
