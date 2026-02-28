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

Keys: `q` quit, `v` view, `r` raw, `s` split, `e` edit, `?` help.

## Ubuntu server quick setup

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip
git clone https://github.com/johnrobertlawson/markdown-cli-jrl.git
cd markdown-cli-jrl
./scripts/install-ubuntu.sh
source .venv/bin/activate
mdview README.md
```

## Maintainers

```bash
git tag v0.1.1 && git push origin v0.1.1
```

PyPI publish runs from `.github/workflows/publish-pypi.yml` on `v*` tags after Trusted Publishing is configured for `johnrobertlawson/markdown-cli-jrl` and environment `pypi`.

## Requirements

- Python 3.8+
- Terminal with 256-color or truecolor support
