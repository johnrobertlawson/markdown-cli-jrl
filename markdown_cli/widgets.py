"""Custom widgets for markdown-cli-jrl."""

from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax

from textual.widgets import Markdown, Static


class TabQueueLine(Static):
    """Minimal tab strip with condensed labels for queued files."""

    DEFAULT_CSS = """
    TabQueueLine {
        width: 100%;
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    """

    SMALL_TAB_THRESHOLD = 4

    @staticmethod
    def _truncate_label(label: str, max_length: int) -> str:
        if len(label) <= max_length:
            return label
        return f"{label[: max_length - 1]}..."

    def update_tabs(self, filepaths: list[Path], active_index: int) -> None:
        count = len(filepaths)
        position = f"{active_index + 1}/{count}"

        if count <= self.SMALL_TAB_THRESHOLD:
            labels: list[str] = []
            for index, path in enumerate(filepaths):
                short_label = self._truncate_label(path.name, 18)
                if index == active_index:
                    labels.append(f"<{short_label}>")
                else:
                    labels.append(short_label)
            tabs_text = " | ".join(labels)
        else:
            active_name = self._truncate_label(filepaths[active_index].name, 24)
            queued_count = count - 1
            tabs_text = f"<{active_name}> | +{queued_count} queued"

        self.update(f" tabs {position}  {tabs_text}")


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

    def update_status(self, filename: str, mode: str, notice: str | None = None) -> None:
        mode_display = {
            "view": "👁  VIEW",
            "raw": "📄 RAW",
            "split": "📐 SPLIT",
            "edit": "✏️  EDIT",
        }
        text = f" {filename}  │  {mode_display.get(mode, mode.upper())}"
        if notice:
            text = f"{text}  │  {notice}"
        self.update(text)
