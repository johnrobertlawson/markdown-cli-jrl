#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install it with:"
  echo "  sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "python3-venv is required. Install it with:"
  echo "  sudo apt update && sudo apt install -y python3-venv"
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

echo
echo "Install complete."
echo "Activate the environment with: source .venv/bin/activate"
echo "Then run: mdview README.md"
