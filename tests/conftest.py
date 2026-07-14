import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def git_repo(tmp_path) -> Path:
    """A throwaway Git repo with one committed file, ready for callers to
    add staged/unstaged changes on top of."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")

    (repo / "app.py").write_text("print('hello')\n")
    (repo / "style.css").write_text("body { color: red; }\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "initial commit")

    return repo
