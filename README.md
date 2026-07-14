# Generate-documentation-MCP

MCP server for Claude Code that turns a Git repository's uncommitted changes
into a structured Markdown documentation skeleton — diffs, file list and
placeholders — ready for Claude Code to fill in with the actual analysis.

This is a **standalone product**, not an evolution of
[Generate-documentation-IA](https://github.com/Paulosouzx/Generate-documentation-IA).
That project's `gendoc` shell script was used only as a reference for the
skeleton format; this repo does not reuse its code.

## Design

- **No AI API calls.** All language understanding ("ignore CSS files",
  "document this in Portuguese") happens in Claude Code, which translates the
  request into structured parameters. The MCP server only executes them:
  reads Git diffs, applies include/exclude filters, renders a template, and
  writes the file.
- **`core/` owns all logic.** `cli/` and `mcp_server/` are thin adapters that
  call `core.generator.generate_documentation()` and format its result —
  neither contains business rules.
- **Skeleton, not final prose.** The generated Markdown mirrors the original
  script's workflow: diffs are embedded with `[To be filled by AI]`
  placeholders. After calling the tool, Claude Code edits the output file
  directly to fill in the analysis.

```
core/          diff collection, filtering, template rendering, file writing
cli/           argparse wrapper around core, for local/manual use
mcp_server/    FastMCP server exposing the generate_documentation tool
templates/     Jinja2 skeleton templates (default_en.md.j2, default_pt.md.j2)
tests/         pytest suite (uses real throwaway Git repos via subprocess)
```

> Note: the MCP-facing package is named `mcp_server/`, not `mcp/`, because
> `mcp` is the name of the official MCP SDK this project depends on — a
> top-level `mcp/` package in this repo would shadow it on import.

## The `generate_documentation` tool

Parameters:

| Name           | Type         | Default          | Meaning                                              |
|----------------|--------------|------------------|-------------------------------------------------------|
| `project_path` | string       | server cwd       | Git repository to analyze                             |
| `include`      | string[]     | none (= all)     | Glob patterns; only matching changed files are kept    |
| `exclude`      | string[]     | none             | Glob patterns to drop, applied after `include`         |
| `output_file`  | string       | `documentation.md` | Output path, relative to `project_path` unless absolute |
| `language`     | `"en"`\|`"pt"` | `"en"`         | Skeleton language                                      |
| `title`        | string       | language default | Document title                                        |
| `template`     | string       | `"default"`      | Template name, resolved as `templates/{template}_{language}.md.j2` |

Returns:

```json
{
  "success": true,
  "output_file": "/path/to/documentation.md",
  "files_processed": 12,
  "files_ignored": 3
}
```

On failure (`success: false`), a `error` field explains what went wrong (not a
Git repo, unknown template, unwritable path).

Diff scope matches the original script: staged + unstaged uncommitted
changes, staged diff taking priority for files with both.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/Paulosouzx/Generate-documentation-MCP.git
cd Generate-documentation-MCP
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the `gendoc-mcp` (CLI) and `gendoc-mcp-server` (MCP server)
console scripts into `.venv/bin/`.

### Registering with Claude Code

Register it once, at user scope, so it's available in every project:

```bash
claude mcp add --scope user --transport stdio gendoc -- \
  /absolute/path/to/Generate-documentation-MCP/.venv/bin/gendoc-mcp-server
```

Verify it's registered:

```bash
claude mcp list
```

or run `/mcp` inside a Claude Code session.

### Using it

Inside any Git repository, in Claude Code:

> "Document the changes on this branch, ignoring CSS files, in Portuguese."

Claude Code interprets that and calls the tool with something like:

```json
{"exclude": ["*.css"], "language": "pt"}
```

The MCP server writes `documentation.md` with the diffs and placeholders;
Claude Code then edits that file in place to fill in the actual analysis.

## Development

```bash
pip install -e ".[dev]"
pytest
```

CLI usage (no Claude Code needed), useful for manual testing:

```bash
gendoc-mcp --project-path . --exclude "*.css" --language pt
```

## Adding a new tool

Add the core function in `core/`, then expose it with a new `@mcp.tool()`
function in `mcp_server/server.py` that calls it — no logic in the server
itself. Add a matching CLI subcommand in `cli/` if useful for manual/local
use.
