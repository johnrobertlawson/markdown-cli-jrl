# markdown-cli-jrl

A terminal-native markdown viewer and editor. Renders markdown beautifully in
the terminal — no GUI, no browser, no X forwarding required. Works over SSH on
headless Ubuntu and locally on macOS.

## Features

- **View mode** — Pretty-rendered markdown (styled headers, code blocks with
  syntax highlighting, formatted lists/tables). No line numbers, no hash
  symbols — just clean reading.
- **Raw mode** — Source markdown with line numbers, like `cat -n`.
- **Split mode** — Side-by-side (or top/bottom) raw source and rendered output
  with live updates as the file changes on disk.
- **Edit mode** — Opens your `$EDITOR` alongside a live-updating rendered
  preview.

## Install

```bash
# From the repo root:
pip install -e .

# Or with dev dependencies:
pip install -e ".[dev]"
```

## Usage

```bash
# View mode (default)
mdview README.md

# Raw mode
mdview README.md --raw

# Split mode
mdview README.md --split

# Edit mode (opens $EDITOR + live preview)
mdview README.md --edit
```

## Keybindings (in TUI modes)

| Key   | Action                        |
|-------|-------------------------------|
| `q`   | Quit                          |
| `v`   | Switch to view mode           |
| `r`   | Switch to raw mode            |
| `s`   | Switch to split mode          |
| `e`   | Open in $EDITOR (edit mode)   |
| `?`   | Show help                     |

## Requirements

- Python 3.8+
- A terminal with 256-color or truecolor support (most modern terminals)
- Works on: macOS Terminal, iTerm2, Termius, any SSH session

## Future

- Go port for single-binary distribution
