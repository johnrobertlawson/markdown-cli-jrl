"""Main Textual application for markdown-cli-jrl."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from threading import Thread
from urllib.error import URLError
from urllib.request import urlopen

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Footer, Header

from markdown_cli import __version__
from markdown_cli.widgets import MarkdownRendered, MarkdownRaw, StatusLine, TabQueueLine


def _version_numbers(version: str) -> tuple[int, ...]:
    numbers = tuple(int(part) for part in re.findall(r"\d+", version))
    return numbers or (0,)


def _is_newer_version(candidate: str, current: str) -> bool:
    candidate_numbers = _version_numbers(candidate)
    current_numbers = _version_numbers(current)
    width = max(len(candidate_numbers), len(current_numbers))
    candidate_numbers += (0,) * (width - len(candidate_numbers))
    current_numbers += (0,) * (width - len(current_numbers))
    return candidate_numbers > current_numbers


class MarkdownViewerApp(App):
    """A terminal-native markdown viewer with multiple display modes."""

    CSS_PATH = "styles.tcss"
    GG_TIMEOUT_SECONDS = 0.6
    UPDATE_CHECK_TIMEOUT_SECONDS = 2.5
    PACKAGE_NAME = "markdown-cli-jrl"
    UPDATE_CHECK_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
    HELP_STATUS_NOTE = "HELP (?/Esc to close)"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("v", "switch_mode('view')", "View"),
        Binding("r", "switch_mode('raw')", "Raw"),
        Binding("s", "switch_mode('split')", "Split"),
        Binding("e", "edit", "Edit"),
        Binding("right,l", "next_tab", "Next Tab"),
        Binding("left,h", "previous_tab", "Prev Tab"),
        Binding("x,d", "discard_tab", "Discard Tab"),
        Binding("j,down", "line_down", "Line Down"),
        Binding("k,up", "line_up", "Line Up"),
        Binding("pageup,ctrl+u", "page_up", "Page Up"),
        Binding("pagedown,ctrl+d", "page_down", "Page Down"),
        Binding("G", "jump_bottom", "Bottom"),
        Binding("exclamation_mark", "install_update", "Install Update"),
        Binding("question_mark", "help", "Help"),
        Binding("escape", "close_help", "Close Help"),
    ]

    mode_name: reactive[str] = reactive("view")

    def __init__(
        self,
        filepaths: list[str],
        initial_mode: str = "view",
        theme_name: str = "dark",
    ) -> None:
        super().__init__()
        self.filepaths = [Path(filepath).resolve() for filepath in filepaths]
        self.active_index = 0
        self.initial_mode = initial_mode
        self._theme_name = theme_name
        self._watcher_thread: Thread | None = None
        self._watching = False
        self._pending_g = False
        self._pending_g_timer: Timer | None = None
        self._update_available_version: str | None = None
        self._help_active = False
        self._help_restore_mode = initial_mode

    @property
    def markdown_content(self) -> str:
        """Read the current file contents."""
        try:
            return self.active_filepath.read_text(encoding="utf-8")
        except Exception as e:
            return f"*Error reading file:* {e}"

    @property
    def active_filepath(self) -> Path:
        return self.filepaths[self.active_index]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TabQueueLine(id="tabs")
        with Horizontal(id="main-container"):
            yield MarkdownRaw(id="raw-pane")
            yield MarkdownRendered(id="view-pane")
        yield StatusLine(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"mdview — {self.active_filepath.name}"
        self.mode_name = self.initial_mode
        self._refresh_tabs()
        self._refresh_content()
        self._start_watcher()
        self._start_update_check()

    def watch_mode_name(self, new_mode: str) -> None:
        """React to mode changes by showing/hiding panes."""
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        view_pane = self.query_one("#view-pane", MarkdownRendered)

        if new_mode == "view":
            raw_pane.display = False
            view_pane.display = True
        elif new_mode == "raw":
            raw_pane.display = True
            view_pane.display = False
        elif new_mode in ("split", "edit"):
            raw_pane.display = True
            view_pane.display = True

        self._refresh_status()

    def _refresh_content(self) -> None:
        """Reload file and update both panes."""
        content = self.markdown_content
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        view_pane = self.query_one("#view-pane", MarkdownRendered)
        raw_pane.update_content(content)
        if not self._help_active:
            view_pane.update_content(content)
        self._refresh_status()
        self._refresh_tabs()

    def _refresh_tabs(self) -> None:
        tabs = self.query_one("#tabs", TabQueueLine)
        tabs.update_tabs(self.filepaths, self.active_index)

    def _start_watcher(self) -> None:
        """Watch the file for changes in a background thread."""
        self._watching = True

        def _watch() -> None:
            try:
                from watchfiles import watch

                watch_paths = [str(path) for path in self.filepaths]
                for _changes in watch(*watch_paths):
                    if not self._watching:
                        break
                    self.call_from_thread(self._refresh_content)
            except ImportError:
                # watchfiles not installed — fall back to polling
                import time

                last_mtimes = {path: path.stat().st_mtime for path in self.filepaths}
                while self._watching:
                    time.sleep(1)
                    for path in list(last_mtimes):
                        try:
                            mtime = path.stat().st_mtime
                        except FileNotFoundError:
                            self.call_from_thread(self._refresh_content)
                            continue
                        if mtime != last_mtimes[path]:
                            last_mtimes[path] = mtime
                            self.call_from_thread(self._refresh_content)

        self._watcher_thread = Thread(target=_watch, daemon=True)
        self._watcher_thread.start()

    def _start_update_check(self) -> None:
        """Check for a newer published version in a background thread."""

        def _check() -> None:
            latest_version = self._fetch_latest_version()
            if latest_version is None:
                return
            if _is_newer_version(latest_version, __version__):
                self.call_from_thread(self._set_update_available, latest_version)

        Thread(target=_check, daemon=True).start()

    def _fetch_latest_version(self) -> str | None:
        try:
            with urlopen(
                self.UPDATE_CHECK_URL, timeout=self.UPDATE_CHECK_TIMEOUT_SECONDS
            ) as response:
                payload = response.read().decode("utf-8")
        except (OSError, TimeoutError, URLError):
            return None

        try:
            metadata = json.loads(payload)
        except json.JSONDecodeError:
            return None

        info = metadata.get("info")
        if not isinstance(info, dict):
            return None
        latest = info.get("version")
        if not isinstance(latest, str):
            return None
        return latest

    def _set_update_available(self, latest_version: str) -> None:
        self._update_available_version = latest_version
        self._refresh_status()
        self.notify(f"Update available: v{latest_version} (press ! to install).")

    def _refresh_status(self) -> None:
        status = self.query_one("#status", StatusLine)
        update_note = None
        if self._update_available_version is not None:
            update_note = f"v{self._update_available_version} available (! to install)"
        if self._help_active:
            if update_note is None:
                update_note = self.HELP_STATUS_NOTE
            else:
                update_note = f"{self.HELP_STATUS_NOTE} | {update_note}"
        status.update_status(self.active_filepath.name, self.mode_name, update_note)

    def action_switch_mode(self, mode: str) -> None:
        self._help_active = False
        self.mode_name = mode
        self._refresh_content()

    def _clear_pending_g(self) -> None:
        self._pending_g = False
        if self._pending_g_timer is not None:
            self._pending_g_timer.stop()
            self._pending_g_timer = None

    def on_key(self, event: events.Key) -> None:
        if event.key == "g":
            if self._pending_g:
                self._clear_pending_g()
                self.action_jump_top()
            else:
                self._pending_g = True
                if self._pending_g_timer is not None:
                    self._pending_g_timer.stop()
                self._pending_g_timer = self.set_timer(
                    self.GG_TIMEOUT_SECONDS, self._clear_pending_g
                )
            event.stop()
            return
        self._clear_pending_g()

    def _visible_panes(self) -> list[MarkdownRaw | MarkdownRendered]:
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        view_pane = self.query_one("#view-pane", MarkdownRendered)
        panes: list[MarkdownRaw | MarkdownRendered] = []
        if raw_pane.display:
            panes.append(raw_pane)
        if view_pane.display:
            panes.append(view_pane)
        return panes

    def action_line_up(self) -> None:
        """Scroll the visible pane(s) up by one line."""
        for pane in self._visible_panes():
            pane.scroll_up(animate=False)

    def action_line_down(self) -> None:
        """Scroll the visible pane(s) down by one line."""
        for pane in self._visible_panes():
            pane.scroll_down(animate=False)

    def action_page_up(self) -> None:
        """Scroll the visible pane(s) one page up."""
        for pane in self._visible_panes():
            pane.scroll_page_up(animate=False)

    def action_page_down(self) -> None:
        """Scroll the visible pane(s) one page down."""
        for pane in self._visible_panes():
            pane.scroll_page_down(animate=False)

    def action_jump_top(self) -> None:
        """Jump to the top of visible pane(s)."""
        for pane in self._visible_panes():
            pane.scroll_home(animate=False)

    def action_jump_bottom(self) -> None:
        """Jump to the bottom of visible pane(s)."""
        for pane in self._visible_panes():
            pane.scroll_end(animate=False)

    def action_install_update(self) -> None:
        """Install an available update and exit on success."""
        if self._update_available_version is None:
            self.notify("No update available.")
            return

        install_command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            self.PACKAGE_NAME,
        ]
        target_version = self._update_available_version

        def _run_upgrade() -> None:
            with self.suspend():
                print(
                    f"Updating {self.PACKAGE_NAME} from v{__version__} to v{target_version}..."
                )
                result = subprocess.run(install_command, check=False)
            if result.returncode == 0:
                self.exit()
            else:
                self.notify(f"Update failed (exit code {result.returncode}).")

        self.call_later(_run_upgrade)

    def action_edit(self) -> None:
        """Open the file in $EDITOR."""
        editor = os.environ.get("EDITOR", "vim")
        self.mode_name = "edit"

        def _run_editor() -> None:
            with self.suspend():
                subprocess.run([editor, str(self.active_filepath)])

        # Run editor — file watcher will pick up changes
        self.call_later(_run_editor)

    def _switch_to_tab(self, new_index: int) -> None:
        self.active_index = new_index % len(self.filepaths)
        self.title = f"mdview — {self.active_filepath.name}"
        self._refresh_content()

    def action_next_tab(self) -> None:
        """Move to the next queued file tab."""
        self._switch_to_tab(self.active_index + 1)

    def action_previous_tab(self) -> None:
        """Move to the previous queued file tab."""
        self._switch_to_tab(self.active_index - 1)

    def action_discard_tab(self) -> None:
        """Discard current tab and move to the next one."""
        if len(self.filepaths) == 1:
            self.notify("Can't discard the last remaining tab.")
            return
        discarded = self.active_filepath.name
        del self.filepaths[self.active_index]
        if self.active_index >= len(self.filepaths):
            self.active_index = 0
        self.title = f"mdview — {self.active_filepath.name}"
        self._refresh_content()
        self.notify(f"Discarded tab: {discarded}")

    def action_help(self) -> None:
        """Toggle help overlay."""
        if self._help_active:
            self.action_close_help()
            return
        self._help_active = True
        self._help_restore_mode = self.mode_name
        help_text = (
            "## Keybindings\n\n"
            "| Key | Action |\n"
            "|-----|--------|\n"
            "| q | Quit |\n"
            "| v | View mode |\n"
            "| r | Raw mode |\n"
            "| s | Split mode |\n"
            "| e | Open in $EDITOR |\n"
            "| Right / l | Next tab |\n"
            "| Left / h | Previous tab |\n"
            "| x / d | Discard current tab |\n"
            "| k / Up | Scroll up one line |\n"
            "| j / Down | Scroll down one line |\n"
            "| PgUp / Ctrl+U | Page up |\n"
            "| PgDn / Ctrl+D | Page down |\n"
            "| gg | Jump to top |\n"
            "| G | Jump to bottom |\n"
            "| ! | Install available update |\n"
            "| ? | Toggle help |\n"
            "| Esc | Close help |\n"
        )
        view_pane = self.query_one("#view-pane", MarkdownRendered)
        view_pane.update_content(help_text)
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        raw_pane.display = False
        view_pane.display = True
        self._refresh_status()

    def action_close_help(self) -> None:
        """Close help and restore prior mode content."""
        if not self._help_active:
            return
        self._help_active = False
        self.mode_name = self._help_restore_mode
        self._refresh_content()

    def on_unmount(self) -> None:
        self._watching = False
        if self._pending_g_timer is not None:
            self._pending_g_timer.stop()
