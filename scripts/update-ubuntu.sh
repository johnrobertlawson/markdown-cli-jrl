#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it with:"
  echo "  sudo apt update && sudo apt install -y git"
  exit 1
fi

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run from a git clone of markdown-cli-jrl." >&2
  exit 1
fi

git pull --ff-only
"$REPO_DIR/scripts/install-ubuntu.sh"
