"""Thin CLI adapter around core.generator. No business logic here."""

import argparse
import json
import os
import sys

from core.generator import generate_documentation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gendoc-mcp",
        description="Generate a Markdown documentation skeleton from Git changes.",
    )
    parser.add_argument("--project-path", default=os.getcwd(), help="Path to the Git repository (default: cwd)")
    parser.add_argument("--include", nargs="*", default=None, help="Glob patterns to include, e.g. *.py src/*")
    parser.add_argument("--exclude", nargs="*", default=None, help="Glob patterns to exclude, e.g. *.css")
    parser.add_argument("--output-file", default="documentation.md", help="Output Markdown file path")
    parser.add_argument("--language", default="en", choices=["en", "pt"], help="Skeleton language")
    parser.add_argument("--title", default=None, help="Document title")
    parser.add_argument("--template", default="default", help="Template name (see templates/)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    result = generate_documentation(
        project_path=args.project_path,
        include=args.include,
        exclude=args.exclude,
        output_file=args.output_file,
        language=args.language,
        title=args.title,
        template=args.template,
    )

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
