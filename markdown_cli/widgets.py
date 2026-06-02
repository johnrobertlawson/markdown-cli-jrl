"""Custom widgets for markdown-cli-jrl."""

from __future__ import annotations

import re
from pathlib import Path

from rich.syntax import Syntax

from textual.css.scalar import Scalar, Unit
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Markdown, Static, TextArea
from textual.widgets._markdown import (
    MarkdownTable,
    MarkdownTableContent,
)


class TabQueueLine(Static):
    """Minimal tab strip with condensed labels for queued files."""

    DEFAULT_CSS = """
    TabQueueLine {
        width: 100%;
        height: 1;
        padding: 0 1;
        &:dark {
            background: #1A0033;
            color: #B388FF;
        }
        &:light {
            background: $panel;
            color: $text-muted;
        }
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


class SmartTableContent(MarkdownTableContent):
    """Table content with content-proportional column widths."""

    def on_mount(self) -> None:
        super().on_mount()
        num_cols = len(self.headers)
        if num_cols == 0:
            return
        # Use the widest cell in each column (header or any row) as the weight.
        # This reflects actual display need rather than total row-volume, so a
        # column with many short entries doesn't shrink columns that have a few
        # wide ones.
        max_widths: list[float] = []
        for col in range(num_cols):
            col_max = len(self.headers[col].plain)
            for row in self.rows:
                if col < len(row):
                    col_max = max(col_max, len(row[col].plain))
            max_widths.append(float(max(col_max, 1)))

        # Floor: each column gets at least half of an equal share, so no column
        # is squeezed to invisibility when one column has unusually wide cells.
        equal_share = sum(max_widths) / num_cols
        floor = max(1.0, equal_share * 0.5)
        weights = [max(floor, w) for w in max_widths]

        self.styles.grid_columns = tuple(
            Scalar(w, Unit.FRACTION, Unit.WIDTH) for w in weights
        )


class SmartTable(MarkdownTable):
    """Table block that uses content-proportional column sizing."""

    def compose(self):
        headers, rows = self._get_headers_and_rows()
        self._headers = headers
        self._rows = rows
        yield SmartTableContent(headers, rows)


class SmartMarkdown(Markdown):
    """Markdown widget with smarter table rendering."""

    BLOCKS = {**Markdown.BLOCKS, "table_open": SmartTable}


class MarkdownRendered(Static):
    """Pretty-rendered markdown pane using Textual's Markdown widget.

    Hosts an inline-edit TextArea that swaps in over the rendered Markdown
    when the user presses `i`. Mirrors texview's TexPreview inline editor.
    """

    DEFAULT_CSS = """
    MarkdownRendered {
        width: 1fr;
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
    }
    MarkdownRendered TextArea {
        width: 1fr;
        height: 1fr;
    }
    """

    class InlineSaved(Message):
        def __init__(self, path: Path, content: str) -> None:
            super().__init__()
            self.path = path
            self.content = content

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._md_widget: SmartMarkdown | None = None
        self._editor: TextArea | None = None
        self._edit_path: Path | None = None
        self._edit_original: str = ""
        self.editing: bool = False

    def on_mount(self) -> None:
        self._md_widget = SmartMarkdown("")
        self.mount(self._md_widget)
        ta = TextArea(
            "",
            show_line_numbers=True,
            soft_wrap=True,
            tab_behavior="indent",
            id="inline-md-editor",
        )
        ta.display = False
        ta.can_focus = False  # don't steal focus while hidden
        self.mount(ta)
        self._editor = ta

    def update_content(self, content: str) -> None:
        if self._md_widget is not None:
            self._md_widget.update(content)

    def begin_inline_edit(self, path: Path) -> None:
        if self._editor is None or self._md_widget is None:
            return
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return
        self._edit_path = path
        self._edit_original = text
        self._editor.load_text(text)
        self._md_widget.display = False
        self._editor.display = True
        self._editor.can_focus = True
        self.editing = True
        self._editor.focus()

    def end_inline_edit(self, save: bool = True) -> tuple[bool, str]:
        if self._editor is None or self._md_widget is None or not self.editing:
            return False, ""
        text = self._editor.text
        saved = False
        if save and self._edit_path is not None and text != self._edit_original:
            self._edit_path.write_text(text, encoding="utf-8")
            self.post_message(self.InlineSaved(self._edit_path, text))
            self._edit_original = text
            saved = True
        self._editor.display = False
        self._editor.can_focus = False
        self._md_widget.display = True
        self.editing = False
        return saved, text

    def save_inline(self) -> bool:
        if self._editor is None or not self.editing or self._edit_path is None:
            return False
        text = self._editor.text
        if text == self._edit_original:
            return False
        self._edit_path.write_text(text, encoding="utf-8")
        self._edit_original = text
        self.post_message(self.InlineSaved(self._edit_path, text))
        return True

    @property
    def inline_dirty(self) -> bool:
        if not self.editing or self._editor is None:
            return False
        return self._editor.text != self._edit_original


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
        padding: 0 1;
        &:dark {
            background: #1A0033;
            color: #B388FF;
        }
        &:light {
            background: $accent;
            color: $text;
        }
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


class FileTOC(Widget):
    """Left sidebar: directory listing of .md files with in-file headings."""

    _PALETTE = [
        "#B388FF", "#82B1FF", "#80D8FF", "#EA80FC", "#CE93D8",
        "#F48FB1", "#90CAF9", "#B39DDB", "#80CBC4", "#7986CB",
    ]
    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)

    DEFAULT_CSS = """
    FileTOC {
        width: 32;
        min-width: 24;
        max-width: 44;
        overflow-y: auto;
        display: none;
        &:dark {
            border-right: solid #4A148C;
        }
        &:light {
            border-right: solid $accent;
        }
    }
    """

    active_index: reactive[int] = reactive(0)

    class FileSelected(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    class HeadingSelected(Message):
        def __init__(self, heading_id: str) -> None:
            super().__init__()
            self.heading_id = heading_id

    def __init__(self, root: Path, **kw) -> None:
        super().__init__(**kw)
        self.root = root
        self.nested = False
        self.files: list[Path] = []
        self.headings: list[tuple[int, str, str]] = []  # (level, text, id)
        self._active_file: Path | None = None
        self._in_headings = False  # cursor is in heading sub-list
        self._heading_index = 0

    def on_mount(self) -> None:
        self.mount(Static(id="toc-list"))
        self.scan()

    def scan(self) -> None:
        if self.nested:
            found = sorted(self.root.rglob("*.md"))
        else:
            found = sorted(self.root.glob("*.md"))
        self.files = found
        self.active_index = min(self.active_index, max(0, len(self.files) - 1))
        self._refresh()

    def set_active_file(self, path: Path) -> None:
        """Update heading list when the viewed file changes."""
        self._active_file = path
        self._parse_headings(path)
        self._refresh()

    def _parse_headings(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            self.headings = []
            return
        self.headings = []
        for match in self._HEADING_RE.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            slug = re.sub(r"[^\w\s-]", "", text.lower())
            slug = re.sub(r"[\s]+", "-", slug).strip("-")
            self.headings.append((level, text, slug))

    def toggle_nested(self) -> None:
        self.nested = not self.nested
        self.scan()

    def watch_active_index(self, _old: int, _new: int) -> None:
        self._in_headings = False
        self._heading_index = 0
        self._refresh()

    def cursor_down(self) -> None:
        if self._in_headings:
            if self._heading_index < len(self.headings) - 1:
                self._heading_index += 1
                self._refresh()
            else:
                # Move to next file
                self._in_headings = False
                if self.active_index < len(self.files) - 1:
                    self.active_index += 1
        else:
            if self.active_index < len(self.files) - 1:
                self.active_index += 1

    def cursor_up(self) -> None:
        if self._in_headings:
            if self._heading_index > 0:
                self._heading_index -= 1
                self._refresh()
            else:
                self._in_headings = False
                self._refresh()
        else:
            if self.active_index > 0:
                self.active_index -= 1

    def select(self) -> None:
        if self._in_headings and self.headings:
            _, _, slug = self.headings[self._heading_index]
            self.post_message(self.HeadingSelected(slug))
        elif self.files:
            self.post_message(self.FileSelected(self.files[self.active_index]))

    def enter_headings(self) -> None:
        """Move cursor into the heading sub-list."""
        if self.headings and not self._in_headings:
            self._in_headings = True
            self._heading_index = 0
            self._refresh()

    def _refresh(self) -> None:
        try:
            widget = self.query_one("#toc-list", Static)
        except Exception:
            return
        lines: list[str] = []
        mode = "nested" if self.nested else "flat"
        lines.append(f"[dim] .md files ({mode})[/dim]")
        lines.append("[dim]" + "\u2500" * 28 + "[/dim]")

        for i, path in enumerate(self.files):
            color = self._PALETTE[i % len(self._PALETTE)]
            if self.nested:
                try:
                    label = str(path.relative_to(self.root))
                except ValueError:
                    label = path.name
            else:
                label = path.name
            label = label[:26]
            marker = "\u25b8" if i == self.active_index and not self._in_headings else " "
            if i == self.active_index and not self._in_headings:
                line = f"[bold reverse {color}] {marker} {label:<26s} [/bold reverse {color}]"
            else:
                line = f"[{color}] {marker} {label:<26s}[/{color}]"
            lines.append(line)

            # Show headings under the active file
            if self._active_file and path == self._active_file and self.headings:
                for hi, (level, text, _slug) in enumerate(self.headings):
                    indent = "  " * level
                    htext = text[:24 - level * 2]
                    hcolor = self._PALETTE[(i + hi + 1) % len(self._PALETTE)]
                    hmarker = "\u25b8" if self._in_headings and hi == self._heading_index else " "
                    if self._in_headings and hi == self._heading_index:
                        hline = f"[bold reverse {hcolor}]   {hmarker}{indent}{htext}[/bold reverse {hcolor}]"
                    else:
                        hline = f"[dim {hcolor}]   {hmarker}{indent}{htext}[/dim {hcolor}]"
                    lines.append(hline)

        if not self.files:
            lines.append("[dim] (no .md files found)[/dim]")

        widget.update("\n".join(lines))
