"""Renders the Markdown skeleton from a Jinja2 template plus changed-file data."""

import importlib.resources as resources

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.models import ChangedFile


class TemplateEngineError(RuntimeError):
    """Raised when the requested template/language combination doesn't exist."""


def _environment() -> Environment:
    templates_dir = resources.files("templates")
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render(template: str, language: str, title: str, branch: str, files: list[ChangedFile]) -> str:
    filename = f"{template}_{language}.md.j2"
    env = _environment()
    try:
        tpl = env.get_template(filename)
    except TemplateNotFound as exc:
        raise TemplateEngineError(
            f"no template found for template='{template}', language='{language}' "
            f"(expected templates/{filename})"
        ) from exc

    return tpl.render(title=title, branch=branch, files=files)
