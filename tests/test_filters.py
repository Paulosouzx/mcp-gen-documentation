from core.filters import apply_filters
from core.models import ChangedFile


def _cf(path: str) -> ChangedFile:
    return ChangedFile(path=path, staged=False, diff=f"diff for {path}")


def test_no_filters_keeps_everything():
    files = [_cf("app.py"), _cf("style.css")]
    kept, ignored = apply_filters(files)
    assert kept == files
    assert ignored == []


def test_exclude_by_extension():
    files = [_cf("app.py"), _cf("style.css")]
    kept, ignored = apply_filters(files, exclude=["*.css"])
    assert [f.path for f in kept] == ["app.py"]
    assert [f.path for f in ignored] == ["style.css"]


def test_include_restricts_to_matching():
    files = [_cf("app.py"), _cf("style.css"), _cf("readme.md")]
    kept, ignored = apply_filters(files, include=["*.py"])
    assert [f.path for f in kept] == ["app.py"]
    assert {f.path for f in ignored} == {"style.css", "readme.md"}


def test_include_and_exclude_combined():
    files = [_cf("src/app.py"), _cf("src/app.test.py"), _cf("style.css")]
    kept, ignored = apply_filters(files, include=["src/*"], exclude=["*.test.py"])
    assert [f.path for f in kept] == ["src/app.py"]


def test_glob_matches_nested_basename():
    files = [_cf("assets/compiled/style.css")]
    kept, ignored = apply_filters(files, exclude=["*.css"])
    assert kept == []
    assert len(ignored) == 1
