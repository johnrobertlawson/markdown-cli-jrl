# markdown-cli-jrl

Terminal-native Markdown viewer/editor for SSH and local terminals (no GUI/browser).

## TL;DR install

```bash
# Works today (no clone)
python3 -m pip install --user "git+https://github.com/johnrobertlawson/markdown-cli-jrl.git"

# After first PyPI release
python3 -m pip install --user markdown-cli-jrl

# After conda-forge feedstock
conda install -c conda-forge markdown-cli-jrl
```

If `mdview` is not found after `--user` install, add `~/.local/bin` to your `PATH`.

## Run

```bash
mdview README.md
mdview README.md --raw
mdview README.md --split
mdview README.md --edit
```

Keys: `q` quit, `v` view, `r` raw, `s` split, `e` edit, `PgUp`/`Ctrl+U` page up, `PgDn`/`Ctrl+D` page down, `?` help.
Extra navigation: `j`/Down scrolls down one line, `k`/Up scrolls up one line, `gg` jumps to top, `G` jumps to bottom.
Update shortcut: on startup, mdview performs a quick update check (best effort); if a newer version is available, press `!` to run an in-place `pip install --upgrade markdown-cli-jrl` and exit on success.

## Ubuntu server quick setup

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip
git clone https://github.com/johnrobertlawson/markdown-cli-jrl.git
cd markdown-cli-jrl
./scripts/install-ubuntu.sh
source .venv/bin/activate
mdview README.md
```

## Ubuntu: updating an existing installation

If you installed from a clone with `.venv`:

```bash
cd markdown-cli-jrl
git pull --ff-only
source .venv/bin/activate
python -m pip install --upgrade -e .
```

If you installed with `--user`:

```bash
python3 -m pip install --user --upgrade markdown-cli-jrl
```

## Maintainers

```bash
VERSION=$(python3 -c "import markdown_cli; print(markdown_cli.__version__)")
git tag "v${VERSION}" && git push origin "v${VERSION}"
```

PyPI publish runs from `.github/workflows/publish-pypi.yml` on `v*` tags after Trusted Publishing is configured for `johnrobertlawson/markdown-cli-jrl` and environment `pypi`.

## Next TODOs

- Dog-food v0.5.1 in daily SSH usage and tune colors + update UX behavior based on that run.

## Requirements

- Python 3.8+
- Terminal with 256-color or truecolor support
