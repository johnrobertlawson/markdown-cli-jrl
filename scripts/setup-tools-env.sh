#!/usr/bin/env bash
set -euo pipefail

TOOLS_ENV_NAME="${TOOLS_ENV_NAME:-tools}"

usage() {
  cat <<EOF
Usage: ./scripts/setup-tools-env.sh [--pull]

Create or refresh the dedicated "${TOOLS_ENV_NAME}" conda environment for mdview,
install this repo there in editable mode, and write a small mdview shim into
~/.local/bin so it works from any directory in new shells without activating
the environment.

Options:
  --pull    Run "git pull --ff-only" in this repo before reinstalling
  -h, --help
EOF
}

find_conda_bin() {
  if [[ -n "${CONDA_EXE:-}" && -x "${CONDA_EXE}" ]]; then
    printf '%s\n' "${CONDA_EXE}"
    return 0
  fi

  if command -v conda >/dev/null 2>&1; then
    command -v conda
    return 0
  fi

  for candidate in \
    "$HOME/miniforge3/bin/conda" \
    "$HOME/mambaforge/bin/conda" \
    "/opt/homebrew/Caskroom/miniforge/base/bin/conda"
  do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

pull_latest=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      pull_latest=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

CONDA_BIN="$(find_conda_bin)" || {
  echo "Could not find conda. Install Miniforge or add conda to PATH." >&2
  exit 1
}

SOLVER_BIN="$CONDA_BIN"
if command -v mamba >/dev/null 2>&1; then
  SOLVER_BIN="$(command -v mamba)"
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_NAME="markdown-cli-jrl"
CONDA_BASE="$("$CONDA_BIN" info --base)"
TOOLS_PREFIX="$CONDA_BASE/envs/${TOOLS_ENV_NAME}"
TOOLS_BIN="${TOOLS_PREFIX}/bin"
LOCAL_BIN="${HOME}/.local/bin"

run_in_tools() {
  "$CONDA_BIN" run --no-capture-output -n "$TOOLS_ENV_NAME" "$@"
}

run_tools_python() {
  run_in_tools python -I "$@"
}

validate_runtime_deps() {
  run_tools_python - <<PY
from importlib import metadata

package_name = "${PACKAGE_NAME}"
dist = metadata.distribution(package_name)
missing = []
seen = set()

for requirement in dist.metadata.get_all("Requires-Dist") or []:
    normalized = requirement.split(";", 1)[0]
    for separator in ("[", " ", "<", ">", "=", "!", "~", "("):
        normalized = normalized.split(separator, 1)[0]
    normalized = normalized.strip()
    if not normalized or normalized in seen:
        continue
    seen.add(normalized)
    try:
        metadata.version(normalized)
    except metadata.PackageNotFoundError:
        missing.append(normalized)

if missing:
    raise SystemExit(
        "Missing runtime dependencies in the tools env: "
        + ", ".join(sorted(missing))
    )
PY
}

if (( pull_latest )); then
  git -C "$REPO_DIR" pull --ff-only
fi

if [[ ! -d "$TOOLS_PREFIX" ]]; then
  "$SOLVER_BIN" create -y -n "$TOOLS_ENV_NAME" python=3.12 pip
fi

run_tools_python - <<'PY'
import sys

if sys.version_info < (3, 8):
    raise SystemExit("The tools environment must use Python 3.8 or newer.")
PY

run_tools_python -m pip install --isolated --upgrade -e "$REPO_DIR"
validate_runtime_deps

mkdir -p "$LOCAL_BIN"
TMP_SHIM="$(mktemp "${LOCAL_BIN}/mdview.XXXXXX")"
cat > "$TMP_SHIM" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${TOOLS_BIN}/python" -I -m markdown_cli.cli "\$@"
EOF
chmod +x "$TMP_SHIM"
mv "$TMP_SHIM" "${LOCAL_BIN}/mdview"
"${LOCAL_BIN}/mdview" --help >/dev/null

echo
echo "mdview is ready."
echo "  env:    ${TOOLS_ENV_NAME}"
echo "  binary: ${TOOLS_BIN}/python -I -m markdown_cli.cli"
echo "  shim:   ${LOCAL_BIN}/mdview"

case ":$PATH:" in
  *":${LOCAL_BIN}:"*)
    echo "Run: mdview README.md"
    ;;
  *)
    echo "Add ${LOCAL_BIN} to your PATH if mdview is not found in a new shell."
    ;;
esac

echo "Re-run ./scripts/setup-tools-env.sh --pull to refresh after pulling the repo."
