# markdown-cli-jrl

Terminal-native Markdown viewer/editor for SSH and local terminals (no GUI or browser required).

## Install at a glance

- Available now (no clone):
  `python3 -m pip install --user "git+https://github.com/johnrobertlawson/markdown-cli-jrl.git"`
- After first PyPI publish:
  `python3 -m pip install --user markdown-cli-jrl`
- After conda-forge feedstock:
  `conda install -c conda-forge markdown-cli-jrl`

If `mdview` is not found after a `--user` install, add `~/.local/bin` to your `PATH`.

## Quick start

```bash
mdview README.md
mdview README.md --raw
mdview README.md --split
mdview README.md --edit
```

In-app keys: `q` quit, `v` view, `r` raw, `s` split, `e` edit, `?` help.

## Ubuntu server setup (clone + helper script)

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip
git clone https://github.com/johnrobertlawson/markdown-cli-jrl.git
cd markdown-cli-jrl
./scripts/install-ubuntu.sh
source .venv/bin/activate
mdview README.md
```

## Local development install

```bash
pip install -e .
pip install -e ".[dev]"
```

## What it does

- View mode: pretty rendered Markdown
- Raw mode: source with line numbers
- Split mode: raw + rendered with live reload on file changes
- Edit mode: opens `$EDITOR` with live preview

## Maintainers: publish to PyPI

1. In PyPI, configure Trusted Publishing for:
   - owner: `johnrobertlawson`
   - repo: `markdown-cli-jrl`
   - workflow: `publish-pypi.yml`
   - environment: `pypi`
2. In GitHub, create environment `pypi`.
3. Bump `version` in `pyproject.toml`.
4. Tag and push:

```bash
git tag v0.1.1
git push origin v0.1.1
```

This triggers `.github/workflows/publish-pypi.yml`.

## Requirements

- Python 3.8+
- Terminal with 256-color or truecolor support
