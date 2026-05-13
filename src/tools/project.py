from __future__ import annotations
import json
from pathlib import Path
from src.tools.base import Tool, ToolResult


DETECTORS: list[tuple[str, list[str], str]] = [
    ("python", ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"], "Python"),
    ("node", ["package.json", "yarn.lock", "pnpm-lock.yaml"], "Node.js"),
    ("go", ["go.mod", "go.sum"], "Go"),
    ("rust", ["Cargo.toml", "Cargo.lock"], "Rust"),
    ("ruby", ["Gemfile", "Gemfile.lock"], "Ruby"),
    ("php", ["composer.json", "composer.lock"], "PHP"),
    ("elixir", ["mix.exs"], "Elixir"),
    ("java", ["pom.xml", "build.gradle", "build.gradle.kts"], "Java"),
    ("docker", ["Dockerfile", "docker-compose.yml"], "Docker"),
    ("terraform", ["*.tf", "*.tfvars"], "Terraform"),
    ("rusty", ["Cargo.toml"], "Rust"),
]


class ProjectInfo(Tool):
    name = "project_info"
    description = "Detect project stack, languages, frameworks, and configuration. Run this on startup for context."
    input_schema = {
        "type": "object",
        "properties": {},
    }

    async def run(self, **kwargs) -> ToolResult:
        root = Path.cwd()
        info = {
            "name": root.name,
            "languages": [],
            "frameworks": [],
            "config_files": {},
            "readme": "",
        }

        for lang_id, files, label in DETECTORS:
            for pattern in files:
                matched = list(root.glob(pattern))
                if matched:
                    if label not in info["languages"]:
                        info["languages"].append(label)
                    f = matched[0]
                    info["config_files"][f.name] = self._read_safe(f, 20)

        package_json = root / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                frameworks = {
                    "react": "React", "next": "Next.js", "vue": "Vue.js",
                    "nuxt": "Nuxt", "svelte": "Svelte", "angular": "Angular",
                    "express": "Express", "fastify": "Fastify", "nest": "NestJS",
                    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
                    "spring": "Spring Boot", "rails": "Ruby on Rails",
                    "tailwindcss": "Tailwind CSS", "shadcn": "shadcn/ui",
                }
                for key, name in frameworks.items():
                    if any(key in k for k in deps):
                        info["frameworks"].append(name)
            except Exception:
                pass

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "django" in content:
                info["frameworks"].append("Django")
            if "fastapi" in content:
                info["frameworks"].append("FastAPI")
            if "flask" in content:
                info["frameworks"].append("Flask")

        readme_files = list(root.glob("README.md")) + list(root.glob("README.rst"))
        if readme_files:
            info["readme"] = self._read_safe(readme_files[0], 15)

        info["frameworks"] = list(set(info["frameworks"]))
        return ToolResult(success=True, data=info)

    def _read_safe(self, path: Path, lines: int) -> str:
        try:
            text = path.read_text(encoding="utf-8")
            return "\n".join(text.splitlines()[:lines])
        except Exception:
            return ""
