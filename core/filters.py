"""Include/exclude glob filtering over a list of changed files."""

import fnmatch
from pathlib import PurePosixPath

from core.models import ChangedFile


def _matches(path: str, patterns: list[str]) -> bool:
    basename = PurePosixPath(path).name
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(basename, pattern) for pattern in patterns)


def apply_filters(
    files: list[ChangedFile],
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> tuple[list[ChangedFile], list[ChangedFile]]:
    """Split files into (kept, ignored) based on include/exclude glob patterns.

    include: if given, only files matching at least one pattern survive.
    exclude: files matching any pattern are dropped, applied after include.
    """
    kept = files
    if include:
        kept = [f for f in kept if _matches(f.path, include)]
    if exclude:
        kept = [f for f in kept if not _matches(f.path, exclude)]

    ignored = [f for f in files if f not in kept]
    return kept, ignored
