# markdown-cli-jrl Copilot Instructions

## Build, test, and lint commands

- Install package (runtime): `pip install -e .`
- Install package with dev tools: `pip install -e ".[dev]"`
- Run tests: `pytest`
- Run a single test: `pytest path/to/test_file.py::test_name`
- Lint: `ruff check .`
- Run the app locally: `mdview README.md` (or pass `--raw`, `--split`, `--edit`)

## High-level architecture

- `pyproject.toml` defines the CLI entrypoint: `mdview = markdown_cli.cli:main`.
- `markdown_cli/cli.py` parses flags (`--raw`, `--split`, `--edit`, `--theme`), resolves one initial mode, and launches `MarkdownViewerApp`.
- `markdown_cli/app.py` is the Textual app orchestrator:
  - Composes the layout (`Header`, `Footer`, `StatusLine`, raw pane, rendered pane).
  - Uses reactive state `mode_name`; `watch_mode_name` controls pane visibility and status updates.
  - Reads markdown from disk, updates both panes through `_refresh_content`, and keeps content live via a background file watcher.
  - Opens `$EDITOR` in `action_edit` using `self.suspend()` so terminal editing works cleanly.
- `markdown_cli/widgets.py` defines pane/widget behavior:
  - `MarkdownRendered` wraps Textual `Markdown` for prettified rendering.
  - `MarkdownRaw` uses Rich `Syntax(..., "markdown", line_numbers=True)` for source view.
  - `StatusLine` renders current file + mode in the bottom bar.
- `markdown_cli/styles.tcss` owns layout/border styling for `#main-container`, `#raw-pane`, and `#view-pane`.

## Key conventions in this repo

- Mode selection precedence in CLI is: `raw` > `split` > `edit` > `view` (default).
- Keep pane IDs stable (`#raw-pane`, `#view-pane`, `#status`); `app.py` queries widgets by these IDs.
- Any mode-related behavior should flow through `mode_name` + `watch_mode_name`, not ad-hoc widget toggles.
- File content refresh should go through `_refresh_content()` so raw and rendered views stay synchronized.
- Live reload is expected: use the existing watcher pattern (`watchfiles.watch`, with polling fallback on `ImportError`) for file-change behavior.
