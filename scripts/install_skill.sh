#!/usr/bin/env bash
set -eu

SKILL_NAME="audit-korean-startup-grant"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/skills/$SKILL_NAME"
DEST_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
DEST_DIR="$DEST_ROOT/$SKILL_NAME"
VALIDATOR="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "Missing skill source: $SOURCE_DIR/SKILL.md" >&2
  exit 1
fi

mkdir -p "$DEST_ROOT"

if [ -e "$DEST_DIR" ]; then
  BACKUP_DIR="$DEST_DIR.backup.$(date +%Y%m%d%H%M%S)"
  mv "$DEST_DIR" "$BACKUP_DIR"
  echo "Backed up existing install to $BACKUP_DIR"
fi

cp -R "$SOURCE_DIR" "$DEST_DIR"
find "$DEST_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +

echo "Installed $SKILL_NAME to $DEST_DIR"

if [ -f "$VALIDATOR" ]; then
  python3 "$VALIDATOR" "$DEST_DIR"
else
  echo "Skipped validation: validator not found at $VALIDATOR"
fi

echo "Restart Codex or open a new session, then use: Use \$audit-korean-startup-grant ..."
