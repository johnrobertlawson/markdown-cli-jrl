# CLAUDE.md

Dense notes for Claude Code. Optimized for AI reader, not humans.

## Install flows — two supported, pick by host

- **venv flow** (`scripts/install-ubuntu.sh`) — `.venv/` + `pip install -e .`. Update: `git pull --ff-only && source .venv/bin/activate && pip install --upgrade -e .`.
- **conda `tools` flow** (`scripts/setup-tools-env.sh`) — creates conda env `tools`, pip-installs editable, writes `~/.local/bin/mdview` shim that invokes `~/miniforge3/envs/tools/bin/python -I -m markdown_cli.cli`. Update: `./scripts/setup-tools-env.sh --pull`. No env activation needed at call time.

Dev extras: `pip install -e ".[dev]"` → pytest + ruff. Run: `pytest`, `ruff check .`.

## Install gotchas (encountered, keep)

- **Half-formed `.venv` on fresh Ubuntu**: without `python3-venv`+`python3-pip` apt packages, `python3 -m venv .venv` still writes `pyvenv.cfg` and python symlinks but no `pip` / `activate`. Looks installed, isn't. Delete and retry after `sudo apt install python3-venv python3-pip`, or switch to conda flow.
- **`setup-tools-env.sh:99` bug — `validate_runtime_deps` counts extras as runtime deps.** It splits `Requires-Dist` on `;` but doesn't check for `extra == "..."`, so `[dev]` deps (`pytest`, `ruff`) are flagged missing. `set -euo pipefail` aborts before the shim step. Workarounds: (a) install `[dev]` first so validation sees them present, (b) proper fix: skip requirements whose marker contains `extra ==`.
- **Conda discovery** in `setup-tools-env.sh`: `$CONDA_EXE` → PATH → hardcoded `$HOME/miniforge3` / `$HOME/mambaforge` / homebrew path. System-wide `/opt/miniforge3` is NOT found. Per-user miniforge is the intended install.
- **`conda run` output masks `set -e` exits** — validation failure showed as `ERROR conda.cli.main_run:execute`; real cause was the python heredoc raising.

## Architecture

CLI entrypoint `mdview` → `markdown_cli.cli:main` (see `pyproject.toml`).

- **`cli.py`** — Click parser (`--raw`, `--split`, `--edit`, `--theme`), resolves one initial mode, launches `MarkdownViewerApp`. Mode precedence: `raw` > `split` > `edit` > `view`.
- **`app.py`** — Textual app. Layout: `Header`, `TabQueueLine`, raw pane + rendered pane in `Horizontal`, `StatusLine`, `Footer`. Central reactive: `mode_name`; `watch_mode_name` controls pane visibility + status. `_refresh_content()` syncs both panes from disk. `watchfiles.watch` daemon thread drives live reload (polling fallback on `ImportError`); shutdown uses `stop_event=self._watch_stop` — without it the Rust thread parks in a syscall during teardown and glibc aborts with `FATAL: exception not rethrown` on `q`.
- **`widgets.py`** — `SmartTableContent`/`SmartTable`/`SmartMarkdown`: fr-based column sizing by per-column content volume (replaces Textual auto-sizing). `MarkdownRendered` wraps `SmartMarkdown` and hosts an inline-edit `TextArea` that swaps in over the rendered Markdown (`i` enter, `Esc` save+rerender, `Ctrl+S` save-without-exit); the hidden TextArea has `can_focus = False` so it doesn't steal initial focus. `MarkdownRaw`: Rich `Syntax(..., "markdown", line_numbers=True)`. `StatusLine`, `TabQueueLine` (auto-summarizes when many files), `FileTOC` (sidebar, flat/nested toggle, dual-cursor via `_in_headings`).
- **`styles.tcss`** — Textual CSS.

## Invariants — don't break

- Mode changes flow through `mode_name` reactive → `watch_mode_name`. No ad-hoc visibility toggles.
- Content refresh goes through `_refresh_content()`; both panes stay in sync. `_refresh_content` short-circuits when `MarkdownRendered.editing` is True so the watcher (which fires on inline-save) and the disk reload don't clobber the in-flight buffer.
- Tab switch (`_switch_to_tab`) saves+exits any in-flight inline edit before changing files.
- Pane IDs stable: `#raw-pane`, `#view-pane`, `#status`, `#file-toc`, `#tabs`.
- `action_edit` and upgrade action use `self.suspend()` before handing terminal to `$EDITOR` / `pip`.

## Non-obvious patterns

- **Vim `gg`**: `_pending_g` + `GG_TIMEOUT_SECONDS = 0.6`, handled in `on_key()` before bindings.
- **Help overlay**: rendered markdown in view pane. `_help_restore_mode` saves mode; `?`/`Esc` restores.
- **Tab wrapping**: `active_index % len(filepaths)`. Cannot discard last tab.
- **Scroll sync**: `_visible_panes()` drives scroll actions so split mode scrolls together.
- **Update check**: background thread hits PyPI JSON at startup; `_is_newer_version()` compares semver tuples; network errors swallowed.
- **Smart tables**: `SmartTableContent.on_mount` computes per-column content volume → fr-based `grid_columns`.
- **FileTOC dual cursor**: `_in_headings` tracks whether cursor is in file list or heading sub-list. `Enter` enters / scrolls to heading; `j`/`k` navigates.
- **Iridescent palette (dark only)**: `#B388FF` lavender, `#82B1FF` periwinkle, `#7986CB` indigo, `#4A148C` borders, `#1A0033` status bars. Light theme uses Textual defaults.
- **Esc precedence**: `action_escape` exits inline-edit first (saving), then closes help; old `close_help` binding still exists and is reachable via the same path.

## Sibling repo: texview (`../texview/`)

Shares Textual+Rich foundation, iridescent palette, keybindings (`t`/`n`/`j`/`k`/`gg`/`G`/`v`/`r`/`s`/`e`/`i`/`?`/`q`, plus `Space`/`PgDn`/`PgUp` for paging and `Ctrl+S` for inline-save), and widget patterns (`FileTOC`, `StatusLine`, inline-edit-over-render). When changing shortcuts or aesthetics here, check if texview needs the same change.

## Publishing

Version: `markdown_cli/__init__.py`. Tag `v{VERSION}` + push → `.github/workflows/publish-pypi.yml` publishes via PyPI trusted publishing.
