import subprocess

import pytest

from core.git_diff import GitError, get_changed_files, get_current_branch, is_git_repo


def test_is_git_repo_true_for_repo(git_repo):
    assert is_git_repo(str(git_repo)) is True


def test_is_git_repo_false_for_non_repo(tmp_path):
    plain_dir = tmp_path / "not-a-repo"
    plain_dir.mkdir()
    assert is_git_repo(str(plain_dir)) is False


def test_get_current_branch(git_repo):
    assert get_current_branch(str(git_repo)) == "main"


def test_get_changed_files_detects_unstaged(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    changed = get_changed_files(str(git_repo))

    assert len(changed) == 1
    assert changed[0].path == "app.py"
    assert changed[0].staged is False
    assert "changed" in changed[0].diff


def test_get_changed_files_prefers_staged_diff(git_repo):
    (git_repo / "app.py").write_text("print('staged version')\n")
    subprocess.run(["git", "-C", str(git_repo), "add", "app.py"], check=True, capture_output=True)
    (git_repo / "app.py").write_text("print('staged version')\nprint('more')\n")

    changed = get_changed_files(str(git_repo))

    assert len(changed) == 1
    assert changed[0].staged is True
    assert "staged version" in changed[0].diff
    assert "more" not in changed[0].diff


def test_get_changed_files_raises_for_non_repo(tmp_path):
    plain_dir = tmp_path / "not-a-repo"
    plain_dir.mkdir()
    with pytest.raises(GitError):
        get_changed_files(str(plain_dir))
