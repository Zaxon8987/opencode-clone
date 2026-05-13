from __future__ import annotations
import json
import re
import os
from urllib.parse import unquote, quote
import httpx
from src.tools.base import Tool, ToolResult


class WebSearch(Tool):
    name = "web_search"
    description = "Search the web for current information. Returns titles, URLs, and snippets."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Number of results (max 10)", "default": 5},
        },
        "required": ["query"],
    }

    async def run(self, query: str, count: int = 5, **kwargs) -> ToolResult:
        count = min(count, 10)
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if api_key:
            return await self._firecrawl(query, count, api_key)
        return await self._ddg(query, count)

    async def _firecrawl(self, query: str, count: int, key: str) -> ToolResult:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {key}"},
                json={"query": query, "pageSize": count},
            )
            if r.status_code != 200:
                return ToolResult(success=False, error=f"Search error {r.status_code}")
            data = r.json()
            results = []
            for item in (data.get("data") or [])[:count]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                })
            return ToolResult(success=True, data=results)

    async def _ddg(self, query: str, count: int) -> ToolResult:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            r = await c.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            if r.status_code != 200:
                return ToolResult(success=False, error=f"DuckDuckGo error {r.status_code}")
            results = []
            for m in re.finditer(
                r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
                r.text, re.DOTALL,
            ):
                href = m.group(1)
                if "&uddg=" in href:
                    url = unquote(href.split("&uddg=")[1].split("&")[0])
                else:
                    url = unquote(re.sub(r"^//", "", href))
                title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                snippet = re.sub(r"<[^>]+>", "", m.group(3)).strip()
                results.append({"title": title, "url": url, "snippet": snippet})
                if len(results) >= count:
                    break
            return ToolResult(success=True, data=results)


class WebFetch(Tool):
    name = "web_fetch"
    description = "Fetch a URL and extract its text content. Useful for reading articles or documentation."
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        },
        "required": ["url"],
    }

    async def run(self, url: str, **kwargs) -> ToolResult:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            try:
                r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            except httpx.HTTPError as e:
                return ToolResult(success=False, error=str(e))
            text = re.sub(r"<script[^>]*>.*?</script>", "", r.text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()[:10000]
            return ToolResult(success=True, data=text)
