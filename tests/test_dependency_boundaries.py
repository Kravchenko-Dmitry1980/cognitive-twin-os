"""Tests for Phase 1 dependency boundaries."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_DEPENDENCY_NAMES = {
    "aiohttp",
    "anthropic",
    "autogen",
    "chromadb",
    "crewai",
    "faiss-cpu",
    "fastapi",
    "httpx",
    "langchain",
    "llama-index",
    "openai",
    "pinecone",
    "pinecone-client",
    "qdrant-client",
    "requests",
    "sqlalchemy",
    "starlette",
    "uvicorn",
    "weaviate-client",
}

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "anthropic",
    "autogen",
    "chromadb",
    "crewai",
    "faiss",
    "fastapi",
    "httpx",
    "langchain",
    "llama_index",
    "openai",
    "pinecone",
    "qdrant_client",
    "requests",
    "sqlalchemy",
    "starlette",
    "urllib",
    "uvicorn",
    "weaviate",
}


def _normalized_dependency_name(requirement: str) -> str:
    name = requirement.split(";", 1)[0]
    for separator in ("[", "<", ">", "=", "!", "~"):
        name = name.split(separator, 1)[0]
    return name.strip().lower().replace("_", "-")


def test_project_dependencies_do_not_include_forbidden_runtime_dependencies() -> None:
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    dependencies = {
        _normalized_dependency_name(requirement)
        for requirement in project.get("dependencies", [])
    }
    optional_dependencies = {
        _normalized_dependency_name(requirement)
        for requirements in project.get("optional-dependencies", {}).values()
        for requirement in requirements
    }

    assert dependencies.isdisjoint(FORBIDDEN_DEPENDENCY_NAMES)
    assert optional_dependencies.isdisjoint(FORBIDDEN_DEPENDENCY_NAMES)


def test_source_does_not_import_forbidden_runtime_dependencies() -> None:
    imported_roots: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
