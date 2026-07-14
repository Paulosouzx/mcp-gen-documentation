"""Orchestrates diff collection, filtering, rendering and writing to disk.

This is the only module that owns business logic. cli/ and mcp_server/ are
thin adapters that call generate_documentation() and format its result.
"""

from typing import Literal

from core.filters import apply_filters
from core.git_diff import (
    GitError,
    get_branch_diff,
    get_commit_diff,
    get_current_branch,
    get_working_tree_diff,
    resolve_output_path,
)
from core.models import DocumentationResult
from core.template_engine import TemplateEngineError, render

_DEFAULT_TITLES = {
    "en": "Documentation of changes",
    "pt": "Documentação das alterações",
}

Mode = Literal["working_tree", "commit", "branch"]


def _get_diff(
    project_path: str,
    mode: Mode,
    commit_hash: str | None,
    base_branch: str,
):
    if mode == "working_tree":
        return get_working_tree_diff(project_path)
    if mode == "commit":
        return get_commit_diff(project_path, commit_hash)
    if mode == "branch":
        return get_branch_diff(project_path, base_branch)
    raise ValueError(f"unknown mode '{mode}'")


def generate_documentation(
    project_path: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    output_file: str = "documentation.md",
    language: str = "en",
    title: str | None = None,
    template: str = "default",
    mode: Mode = "working_tree",
    commit_hash: str | None = None,
    base_branch: str = "origin/main",
) -> DocumentationResult:
    try:
        changed = _get_diff(project_path, mode, commit_hash, base_branch)
    except (GitError, ValueError) as exc:
        return DocumentationResult(success=False, error=str(exc))

    kept, ignored = apply_filters(changed, include, exclude)
    resolved_title = title or _DEFAULT_TITLES.get(language, _DEFAULT_TITLES["en"])
    branch = get_current_branch(project_path)

    try:
        content = render(template, language, title=resolved_title, branch=branch, files=kept)
    except TemplateEngineError as exc:
        return DocumentationResult(success=False, error=str(exc))

    output_path = resolve_output_path(project_path, output_file)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return DocumentationResult(success=False, error=str(exc))

    return DocumentationResult(
        success=True,
        output_file=str(output_path),
        files_processed=len(kept),
        files_ignored=len(ignored),
    )
