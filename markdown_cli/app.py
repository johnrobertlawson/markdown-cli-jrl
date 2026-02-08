"""Main Textual application for markdown-cli-jrl."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from threading import Thread

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from markdown_cli.widgets import MarkdownRendered, MarkdownRaw, StatusLine


class MarkdownViewerApp(App):
    """A terminal-native markdown viewer with multiple display modes."""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("v", "switch_mode('view')", "View"),
        Binding("r", "switch_mode('raw')", "Raw"),
        Binding("s", "switch_mode('split')", "Split"),
        Binding("e", "edit", "Edit"),
        Binding("question_mark", "help", "Help"),
    ]

    mode_name: reactive[str] = reactive("view")

    def __init__(
        self,
        filepath: str,
        initial_mode: str = "view",
        theme_name: str = "dark",
    ) -> None:
        super().__init__()
        self.filepath = Path(filepath).resolve()
        self.initial_mode = initial_mode
        self._theme_name = theme_name
        self._watcher_thread: Thread | None = None
        self._watching = False

    @property
    def markdown_content(self) -> str:
        """Read the current file contents."""
        try:
            return self.filepath.read_text(encoding="utf-8")
        except Exception as e:
            return f"*Error reading file:* {e}"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            yield MarkdownRaw(id="raw-pane")
            yield MarkdownRendered(id="view-pane")
        yield StatusLine(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"mdview — {self.filepath.name}"
        self.mode_name = self.initial_mode
        self._refresh_content()
        self._start_watcher()

    def watch_mode_name(self, new_mode: str) -> None:
        """React to mode changes by showing/hiding panes."""
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        view_pane = self.query_one("#view-pane", MarkdownRendered)
        status = self.query_one("#status", StatusLine)

        if new_mode == "view":
            raw_pane.display = False
            view_pane.display = True
        elif new_mode == "raw":
            raw_pane.display = True
            view_pane.display = False
        elif new_mode in ("split", "edit"):
            raw_pane.display = True
            view_pane.display = True

        status.update_status(self.filepath.name, new_mode)

    def _refresh_content(self) -> None:
        """Reload file and update both panes."""
        content = self.markdown_content
        self.query_one("#raw-pane", MarkdownRaw).update_content(content)
        self.query_one("#view-pane", MarkdownRendered).update_content(content)

    def _start_watcher(self) -> None:
        """Watch the file for changes in a background thread."""
        self._watching = True

        def _watch() -> None:
            try:
                from watchfiles import watch

                for _changes in watch(str(self.filepath)):
                    if not self._watching:
                        break
                    self.call_from_thread(self._refresh_content)
            except ImportError:
                # watchfiles not installed — fall back to polling
                import time

                last_mtime = self.filepath.stat().st_mtime
                while self._watching:
                    time.sleep(1)
                    try:
                        mtime = self.filepath.stat().st_mtime
                        if mtime != last_mtime:
                            last_mtime = mtime
                            self.call_from_thread(self._refresh_content)
                    except FileNotFoundError:
                        break

        self._watcher_thread = Thread(target=_watch, daemon=True)
        self._watcher_thread.start()

    def action_switch_mode(self, mode: str) -> None:
        self.mode_name = mode

    def action_edit(self) -> None:
        """Open the file in $EDITOR."""
        editor = os.environ.get("EDITOR", "vim")
        self.mode_name = "edit"

        def _run_editor() -> None:
            with self.suspend():
                subprocess.run([editor, str(self.filepath)])

        # Run editor — file watcher will pick up changes
        self.call_later(_run_editor)

    def action_help(self) -> None:
        """Toggle help overlay."""
        help_text = (
            "## Keybindings\n\n"
            "| Key | Action |\n"
            "|-----|--------|\n"
            "| q | Quit |\n"
            "| v | View mode |\n"
            "| r | Raw mode |\n"
            "| s | Split mode |\n"
            "| e | Open in $EDITOR |\n"
            "| ? | This help |\n"
        )
        view_pane = self.query_one("#view-pane", MarkdownRendered)
        view_pane.update_content(help_text)
        raw_pane = self.query_one("#raw-pane", MarkdownRaw)
        raw_pane.display = False
        view_pane.display = True

    def on_unmount(self) -> None:
        self._watching = False
