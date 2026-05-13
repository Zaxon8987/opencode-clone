from __future__ import annotations
from pathlib import Path
from src.tools.base import Tool, ToolResult

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


class LoadSkill(Tool):
    name = "load_skill"
    description = "Load a specialized skill for a specific domain. Available skills: security-audit, database-design, deploy-check, react-testing, api-design."
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "enum": ["security-audit", "database-design", "deploy-check", "react-testing", "api-design"],
                "description": "Skill name",
            },
        },
        "required": ["name"],
    }

    async def run(self, name: str, **kwargs) -> ToolResult:
        path = SKILLS_DIR / f"{name}.md"
        if not path.exists():
            return ToolResult(success=False, error=f"Skill '{name}' not found. Available: security-audit, database-design, deploy-check, react-testing, api-design")
        content = path.read_text(encoding="utf-8")
        return ToolResult(success=True, data={"name": name, "instructions": content})


class ListSkills(Tool):
    name = "list_skills"
    description = "List all available skills that can be loaded."
    input_schema = {
        "type": "object",
        "properties": {},
    }

    async def run(self, **kwargs) -> ToolResult:
        if not SKILLS_DIR.exists():
            return ToolResult(success=True, data=[])
        skills = []
        for f in sorted(SKILLS_DIR.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            desc = ""
            for line in content.splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
            skills.append({"name": f.stem, "description": desc})
        return ToolResult(success=True, data=skills)
