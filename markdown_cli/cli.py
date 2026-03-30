"""CLI entry point for markdown-cli-jrl."""

import glob
from typing import Tuple

import click

from markdown_cli.app import MarkdownViewerApp


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=False)
@click.option("--raw", is_flag=True, help="Show raw markdown with line numbers")
@click.option("--split", "split_mode", is_flag=True, help="Side-by-side raw + rendered")
@click.option("--edit", "edit_mode", is_flag=True, help="Open $EDITOR with live preview")
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
    help="Color theme",
)
def main(
    files: Tuple[str, ...], raw: bool, split_mode: bool, edit_mode: bool, theme: str
) -> None:
    """View markdown files beautifully in the terminal."""
    if not files:
        files = tuple(sorted(glob.glob("*.md")))
        if not files:
            raise click.UsageError("No .md files found in current directory.")
    if raw:
        mode = "raw"
    elif split_mode:
        mode = "split"
    elif edit_mode:
        mode = "edit"
    else:
        mode = "view"

    app = MarkdownViewerApp(filepaths=list(files), initial_mode=mode, theme_name=theme)
    app.run()


if __name__ == "__main__":
    main()
