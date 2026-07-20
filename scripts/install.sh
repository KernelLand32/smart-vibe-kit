#!/usr/bin/env bash
# Cross-platform Smart Vibe Kit installer (Unix wrapper → install.py).
# Usage:
#   ./scripts/install.sh
#   ./scripts/install.sh all user
#   ./scripts/install.sh agents user
#   ./scripts/install.sh cursor project /path/to/repo
#   ./scripts/install.sh --list
#   ./scripts/install.sh --uninstall agents user
# Env:
#   ALSO_LEGACY_CLAUDE_COMMAND=1
#   NO_BACKUP=1
#   SVK_LINK=1
#   SVK_WHAT_IF=1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_PY="$SCRIPT_DIR/install.py"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  elif command -v python >/dev/null 2>&1; then
    echo python
  else
    echo ""
  fi
}

PY="$(find_python)"
if [[ -z "$PY" ]]; then
  echo "Python 3 is required. Install python3 and re-run." >&2
  exit 1
fi

# Flag-style invocation: ./install.sh --list | --uninstall …
if [[ "${1:-}" == --* ]]; then
  exec "$PY" "$INSTALL_PY" "$@"
fi

TARGET="${1:-all}"
SCOPE="${2:-user}"
PROJECT_ROOT="${3:-$(pwd)}"

ARGS=(--target "$TARGET" --scope "$SCOPE" --project-root "$PROJECT_ROOT")
[[ "${ALSO_LEGACY_CLAUDE_COMMAND:-0}" == "1" ]] && ARGS+=(--also-legacy-claude-command)
[[ "${NO_BACKUP:-0}" == "1" ]] && ARGS+=(--no-backup)
[[ "${SVK_LINK:-0}" == "1" ]] && ARGS+=(--link)
[[ "${SVK_WHAT_IF:-0}" == "1" ]] && ARGS+=(--what-if)

echo "→ $PY $INSTALL_PY ${ARGS[*]}"
exec "$PY" "$INSTALL_PY" "${ARGS[@]}"
