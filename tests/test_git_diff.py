import subprocess

import pytest

from core.git_diff import (
    GitError,
    get_branch_diff,
    get_commit_diff,
    get_current_branch,
    get_working_tree_diff,
    is_git_repo,
)


def test_is_git_repo_true_for_repo(git_repo):
    assert is_git_repo(str(git_repo)) is True


def test_is_git_repo_false_for_non_repo(tmp_path):
    plain_dir = tmp_path / "not-a-repo"
    plain_dir.mkdir()
    assert is_git_repo(str(plain_dir)) is False


def test_get_current_branch(git_repo):
    assert get_current_branch(str(git_repo)) == "main"


def test_get_working_tree_diff_detects_unstaged(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    changed = get_working_tree_diff(str(git_repo))

    assert len(changed) == 1
    assert changed[0].path == "app.py"
    assert changed[0].staged is False
    assert "changed" in changed[0].diff


def test_get_working_tree_diff_prefers_staged_diff(git_repo):
    (git_repo / "app.py").write_text("print('staged version')\n")
    subprocess.run(["git", "-C", str(git_repo), "add", "app.py"], check=True, capture_output=True)
    (git_repo / "app.py").write_text("print('staged version')\nprint('more')\n")

    changed = get_working_tree_diff(str(git_repo))

    assert len(changed) == 1
    assert changed[0].staged is True
    assert "staged version" in changed[0].diff
    assert "more" not in changed[0].diff


def test_get_working_tree_diff_raises_for_non_repo(tmp_path):
    plain_dir = tmp_path / "not-a-repo"
    plain_dir.mkdir()
    with pytest.raises(GitError):
        get_working_tree_diff(str(plain_dir))


def test_get_commit_diff_defaults_to_head(git_repo):
    (git_repo / "app.py").write_text("print('committed change')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "second commit"], check=True)

    changed = get_commit_diff(str(git_repo))

    assert len(changed) == 1
    assert changed[0].path == "app.py"
    assert "committed change" in changed[0].diff


def test_get_commit_diff_with_explicit_hash(git_repo):
    (git_repo / "app.py").write_text("print('v2')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "v2"], check=True)
    second_hash = subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()

    (git_repo / "app.py").write_text("print('v3')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "v3"], check=True)

    changed = get_commit_diff(str(git_repo), second_hash)

    assert len(changed) == 1
    assert "v2" in changed[0].diff
    assert "v3" not in changed[0].diff


def test_get_commit_diff_root_commit(git_repo):
    root_hash = subprocess.run(
        ["git", "-C", str(git_repo), "rev-list", "--max-parents=0", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    changed = get_commit_diff(str(git_repo), root_hash)

    assert {f.path for f in changed} == {"app.py", "style.css"}


def test_get_commit_diff_raises_for_unknown_hash(git_repo):
    with pytest.raises(GitError):
        get_commit_diff(str(git_repo), "deadbeef")


def test_get_branch_diff(git_repo):
    subprocess.run(["git", "-C", str(git_repo), "branch", "base"], check=True)
    (git_repo / "app.py").write_text("print('feature work')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "feature commit"], check=True)

    changed = get_branch_diff(str(git_repo), base_branch="base")

    assert len(changed) == 1
    assert changed[0].path == "app.py"
    assert "feature work" in changed[0].diff


def test_get_branch_diff_raises_for_unknown_base(git_repo):
    with pytest.raises(GitError):
        get_branch_diff(str(git_repo), base_branch="does-not-exist")
