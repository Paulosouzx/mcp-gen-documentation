import subprocess
from pathlib import Path

from core.generator import generate_documentation


def test_generates_documentation_for_changed_files(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    result = generate_documentation(project_path=str(git_repo))

    assert result.success is True
    assert result.files_processed == 1
    assert result.files_ignored == 0
    output = Path(result.output_file)
    assert output.exists()
    content = output.read_text()
    assert "app.py" in content
    assert "Documentation of changes" in content
    assert "print('changed')" in content


def test_exclude_css_matches_original_script_behavior(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")
    (git_repo / "style.css").write_text("body { color: blue; }\n")

    result = generate_documentation(project_path=str(git_repo), exclude=["*.css"])

    assert result.files_processed == 1
    assert result.files_ignored == 1
    content = Path(result.output_file).read_text()
    assert "app.py" in content
    assert "style.css" not in content


def test_language_pt_uses_portuguese_template(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    result = generate_documentation(project_path=str(git_repo), language="pt")

    content = Path(result.output_file).read_text()
    assert "Documentação das alterações" in content
    assert "A preencher pela IA" in content


def test_custom_title_and_output_file(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    result = generate_documentation(
        project_path=str(git_repo),
        title="Custom Title",
        output_file="docs/custom.md",
    )

    assert result.success is True
    assert result.output_file.endswith("docs/custom.md")
    content = Path(result.output_file).read_text()
    assert content.startswith("Custom Title")


def test_no_changes_still_succeeds_with_zero_files(git_repo):
    result = generate_documentation(project_path=str(git_repo))

    assert result.success is True
    assert result.files_processed == 0
    assert result.files_ignored == 0


def test_non_git_directory_returns_failure(tmp_path):
    plain_dir = tmp_path / "not-a-repo"
    plain_dir.mkdir()

    result = generate_documentation(project_path=str(plain_dir))

    assert result.success is False
    assert result.error is not None


def test_unknown_template_returns_failure(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    result = generate_documentation(project_path=str(git_repo), template="does-not-exist")

    assert result.success is False
    assert "does-not-exist" in result.error


def test_mode_defaults_to_working_tree_for_backward_compat(git_repo):
    (git_repo / "app.py").write_text("print('changed')\n")

    default_result = generate_documentation(project_path=str(git_repo))
    explicit_result = generate_documentation(project_path=str(git_repo), mode="working_tree")

    assert default_result.to_dict() == explicit_result.to_dict()
    assert Path(default_result.output_file).read_text() == Path(explicit_result.output_file).read_text()


def test_mode_commit_documents_a_single_commit(git_repo):
    (git_repo / "app.py").write_text("print('committed change')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "second commit"], check=True)

    result = generate_documentation(project_path=str(git_repo), mode="commit")

    assert result.success is True
    assert result.files_processed == 1
    content = Path(result.output_file).read_text()
    assert "app.py" in content
    assert "committed change" in content


def test_mode_commit_with_explicit_hash(git_repo):
    (git_repo / "app.py").write_text("print('v2')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "v2"], check=True)
    second_hash = subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (git_repo / "app.py").write_text("print('v3')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "v3"], check=True)

    result = generate_documentation(project_path=str(git_repo), mode="commit", commit_hash=second_hash)

    content = Path(result.output_file).read_text()
    assert "v2" in content
    assert "v3" not in content


def test_mode_branch_documents_diff_against_base(git_repo):
    subprocess.run(["git", "-C", str(git_repo), "branch", "base"], check=True)
    (git_repo / "app.py").write_text("print('feature work')\n")
    subprocess.run(["git", "-C", str(git_repo), "commit", "-aq", "-m", "feature commit"], check=True)

    result = generate_documentation(project_path=str(git_repo), mode="branch", base_branch="base")

    assert result.success is True
    assert result.files_processed == 1
    content = Path(result.output_file).read_text()
    assert "feature work" in content


def test_mode_branch_unknown_base_returns_failure(git_repo):
    result = generate_documentation(project_path=str(git_repo), mode="branch", base_branch="does-not-exist")

    assert result.success is False
    assert result.error is not None
