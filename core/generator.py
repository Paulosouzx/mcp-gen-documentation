"""Orchestrates diff collection, filtering, rendering and writing to disk.

This is the only module that owns business logic. cli/ and mcp_server/ are
thin adapters that call generate_documentation() and format its result.
"""

from core.filters import apply_filters
from core.git_diff import GitError, get_changed_files, get_current_branch, resolve_output_path
from core.models import DocumentationResult
from core.template_engine import TemplateEngineError, render

_DEFAULT_TITLES = {
    "en": "Documentation of changes",
    "pt": "Documentação das alterações",
}


def generate_documentation(
    project_path: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    output_file: str = "documentation.md",
    language: str = "en",
    title: str | None = None,
    template: str = "default",
) -> DocumentationResult:
    try:
        changed = get_changed_files(project_path)
    except GitError as exc:
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
