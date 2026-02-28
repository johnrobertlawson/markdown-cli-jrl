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

### pip install from PyPI (after first release)

```bash
python3 -m pip install --user markdown-cli-jrl
```

### pip install from GitHub (available now, no clone)

```bash
# Replace <owner>/<repo> with your GitHub path
python3 -m pip install --user "git+https://github.com/<owner>/<repo>.git"

# Optional: pin to a tag
python3 -m pip install --user "git+https://github.com/<owner>/<repo>.git@v0.1.0"
```

If `mdview` is not found after install, add `~/.local/bin` to your `PATH`.

### Local/dev install

```bash
# From the repo root:
pip install -e .

# Or with dev dependencies:
pip install -e ".[dev]"
```

### Ubuntu server quick install (clone + helper script)

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip
git clone <your-repo-url>
cd markdown-cli-jrl
./scripts/install-ubuntu.sh
source .venv/bin/activate
mdview README.md
```

### Conda / conda-forge

```bash
# Use conda env + pip today
conda create -n mdview python=3.11 pip -y
conda activate mdview
python -m pip install markdown-cli-jrl
```

If the package is not yet on PyPI, use:

```bash
python -m pip install "git+https://github.com/<owner>/<repo>.git"
```

Once a conda-forge feedstock is published, install with:

```bash
conda install -c conda-forge markdown-cli-jrl
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

## Publishing to PyPI (maintainers)

1. Create a PyPI account and add a trusted publisher for this repository:
   - Owner: `<owner>`
   - Repository: `<repo>`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi`
2. In GitHub, create an environment named `pypi` for this repo.
3. Bump `version` in `pyproject.toml`.
4. Create and push a version tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

The publish workflow uploads the package to PyPI, after which users can run:

```bash
python3 -m pip install --user markdown-cli-jrl
```

## Requirements

- Python 3.8+
- A terminal with 256-color or truecolor support (most modern terminals)
- Works on: macOS Terminal, iTerm2, Termius, any SSH session

## Future

- Go port for single-binary distribution
