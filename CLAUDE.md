# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .                # Install (runtime)
pip install -e ".[dev]"         # Install with dev tools (pytest, ruff)
mdview README.md                # Run (also: --raw, --split, --edit, --theme light)
pytest                          # Run all tests
pytest path/to/test.py::name    # Run a single test
ruff check .                    # Lint
```

Ubuntu clone update flow: `git pull --ff-only && source .venv/bin/activate && python -m pip install --upgrade -e .`

## Architecture

CLI entrypoint `mdview` is defined in `pyproject.toml` and points to `markdown_cli.cli:main`.

**`cli.py`** — Click command that parses flags (`--raw`, `--split`, `--edit`, `--theme`), resolves one initial mode, and launches `MarkdownViewerApp`.

**`app.py`** — Textual app orchestrator. Composes layout: `Header`, `TabQueueLine`, raw pane + rendered pane in a `Horizontal`, `StatusLine`, `Footer`. Central reactive state is `mode_name`; the `watch_mode_name` callback controls pane visibility and status updates. `_refresh_content()` reads markdown from disk and synchronizes both panes. A background file watcher keeps content live.

**`widgets.py`** — Custom widgets:
- `SmartTableContent` / `SmartTable` / `SmartMarkdown` — override Textual's table rendering with content-proportional column widths (fr-based sizing by total content volume per column).
- `MarkdownRendered` — wraps `SmartMarkdown` for pretty rendering with improved tables.
- `MarkdownRaw` — uses Rich `Syntax(..., "markdown", line_numbers=True)` for source view.
- `StatusLine` — shows current file, mode, and update notices.
- `TabQueueLine` — tab strip that auto-summarizes when many files are queued.
- `FileTOC` — left sidebar listing `.md` files in the working directory with in-file heading navigation. Supports flat/nested scan toggle.

**`styles.tcss`** — Textual CSS for layout/border styling.

## Key conventions

- **Mode precedence** in CLI: `raw` > `split` > `edit` > `view` (default).
- **Pane IDs are stable**: `#raw-pane`, `#view-pane`, `#status`, `#file-toc`, `#tabs`. App queries widgets by these IDs.
- **All mode changes** flow through the `mode_name` reactive + `watch_mode_name`. Do not toggle widget visibility ad-hoc.
- **All content refresh** goes through `_refresh_content()` to keep raw and rendered panes synchronized.
- **Live reload** uses `watchfiles.watch` with a polling fallback on `ImportError`. File watcher runs in a daemon thread.
- **TUI suspend pattern**: `action_edit` and the upgrade action use `self.suspend()` so the terminal is cleanly handed to `$EDITOR` or `pip`.

## Non-obvious patterns

- **Vim "gg"**: `_pending_g` flag + timer (`GG_TIMEOUT_SECONDS = 0.6`). First `g` sets the flag; second within timeout jumps to top. Handled in `on_key()` before normal bindings.
- **Help overlay**: help is rendered markdown shown in the view pane. `_help_restore_mode` saves the mode before showing help; pressing `?`/`Esc` restores it.
- **Tab wrapping**: `active_index % len(filepaths)` for circular navigation. Discarding the last tab is prevented.
- **Scroll sync**: scroll actions operate on `_visible_panes()` so both panes scroll together in split mode.
- **Update check**: background thread queries PyPI JSON API at startup; `_is_newer_version()` compares semver tuples. Network errors are silently caught.
- **Smart tables**: `SmartTableContent` overrides `on_mount` to compute content volume per column and set `grid_columns` to fr-based scalars, replacing Textual's default auto-sizing.
- **FileTOC dual cursor**: `_in_headings` flag tracks whether the cursor is in the file list or the heading sub-list. `Enter` enters headings, `j`/`k` navigates, `Enter` again scrolls to the heading.
- **Iridescent palette**: dark theme uses texview's pastel colors (`#B388FF` lavender, `#82B1FF` periwinkle, etc.) for headings, status bar, tab bar. Light theme falls back to Textual defaults.

## Publishing

Version lives in `markdown_cli/__init__.py`. Tag with `v{VERSION}` and push; `.github/workflows/publish-pypi.yml` publishes to PyPI via trusted publishing.
