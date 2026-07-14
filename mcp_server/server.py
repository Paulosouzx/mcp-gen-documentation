"""FastMCP server exposing generate_documentation. No business logic here —
every tool call delegates straight to core.generator.
"""

import os

from mcp.server.fastmcp import FastMCP

from core import generator as core_generator

mcp = FastMCP(
    name="generate-documentation-mcp",
    instructions=(
        "Turns a Git repository's uncommitted changes into a structured Markdown "
        "documentation skeleton (diffs + placeholders). The caller is expected to "
        "fill in the analysis/prose afterwards by editing the generated file."
    ),
)


@mcp.tool()
def generate_documentation(
    project_path: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    output_file: str = "documentation.md",
    language: str = "en",
    title: str | None = None,
    template: str = "default",
) -> dict:
    """Generate a Markdown documentation skeleton from the current Git changes.

    Args:
        project_path: Path to the Git repository. Defaults to the server's
            current working directory (the project Claude Code is running in).
        include: Glob patterns; only matching changed files are documented
            (e.g. ["*.py", "src/**"]). If omitted, all changed files match.
        exclude: Glob patterns to drop from the result (e.g. ["*.css"]),
            applied after include.
        output_file: Path (relative to project_path, unless absolute) for the
            generated Markdown file.
        language: Skeleton language, "en" or "pt".
        title: Document title. Defaults to a language-appropriate title.
        template: Template name to render (see templates/ directory).

    Returns:
        {"success": bool, "output_file": str | None, "files_processed": int,
         "files_ignored": int, "error": str (only on failure)}
    """
    result = core_generator.generate_documentation(
        project_path=project_path or os.getcwd(),
        include=include,
        exclude=exclude,
        output_file=output_file,
        language=language,
        title=title,
        template=template,
    )
    return result.to_dict()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
