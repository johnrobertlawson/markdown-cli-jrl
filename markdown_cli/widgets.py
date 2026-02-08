"""Custom widgets for markdown-cli-jrl."""

from __future__ import annotations

from rich.syntax import Syntax
from rich.text import Text

from textual.widgets import Static, MarkdownViewer, Markdown


class MarkdownRendered(Static):
    """Pretty-rendered markdown pane using Textual's Markdown widget."""

    DEFAULT_CSS = """
    MarkdownRendered {
        width: 1fr;
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._md_widget: Markdown | None = None

    def on_mount(self) -> None:
        self._md_widget = Markdown("")
        self.mount(self._md_widget)

    def update_content(self, content: str) -> None:
        if self._md_widget is not None:
            self._md_widget.update(content)


class MarkdownRaw(Static):
    """Raw markdown source with line numbers."""

    DEFAULT_CSS = """
    MarkdownRaw {
        width: 1fr;
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
    }
    """

    def update_content(self, content: str) -> None:
        syntax = Syntax(
            content,
            "markdown",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        self.update(syntax)


class StatusLine(Static):
    """Bottom status bar showing file name and current mode."""

    DEFAULT_CSS = """
    StatusLine {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    def update_status(self, filename: str, mode: str) -> None:
        mode_display = {
            "view": "👁  VIEW",
            "raw": "📄 RAW",
            "split": "📐 SPLIT",
            "edit": "✏️  EDIT",
        }
        self.update(f" {filename}  │  {mode_display.get(mode, mode.upper())}")
