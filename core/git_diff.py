"""Git interaction: list changed files and pull their diffs via subprocess."""

import subprocess
from pathlib import Path

from core.models import ChangedFile


class GitError(RuntimeError):
    """Raised when the target directory is not a usable Git repository."""


def _run_git(project_path: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", project_path, *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def is_git_repo(project_path: str) -> bool:
    try:
        output = _run_git(project_path, "rev-parse", "--is-inside-work-tree")
    except GitError:
        return False
    return output.strip() == "true"


def get_current_branch(project_path: str) -> str:
    try:
        return _run_git(project_path, "branch", "--show-current").strip() or "HEAD"
    except GitError:
        return "HEAD"


def get_changed_files(project_path: str) -> list[ChangedFile]:
    """Return uncommitted changes (staged + unstaged), staged diff taking
    priority for files present in both sets — mirrors the original gendoc
    shell script's behavior."""
    if not is_git_repo(project_path):
        raise GitError(f"'{project_path}' is not a Git repository")

    staged_names = {
        line for line in _run_git(project_path, "diff", "--cached", "--name-only").splitlines() if line
    }
    unstaged_names = {
        line for line in _run_git(project_path, "diff", "--name-only").splitlines() if line
    }

    changed: list[ChangedFile] = []
    for path in sorted(staged_names | unstaged_names):
        staged = path in staged_names
        diff_args = ["diff", "--cached", "--", path] if staged else ["diff", "--", path]
        diff_text = _run_git(project_path, *diff_args)
        changed.append(ChangedFile(path=path, staged=staged, diff=diff_text))

    return changed


def resolve_output_path(project_path: str, output_file: str) -> Path:
    path = Path(output_file)
    if path.is_absolute():
        return path
    return Path(project_path) / path
