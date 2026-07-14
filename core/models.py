from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChangedFile:
    """A single file changed in the repository, with its diff text."""

    path: str
    staged: bool
    diff: str


@dataclass(frozen=True)
class DocumentationResult:
    """Outcome of a generate_documentation call."""

    success: bool
    output_file: str | None = None
    files_processed: int = 0
    files_ignored: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        data = {
            "success": self.success,
            "output_file": self.output_file,
            "files_processed": self.files_processed,
            "files_ignored": self.files_ignored,
        }
        if self.error is not None:
            data["error"] = self.error
        return data
