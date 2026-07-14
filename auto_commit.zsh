#!/bin/zsh
set -euo pipefail

# Always run from the repository root, not from src/ or any other subdirectory.
SCRIPT_DIR=${0:A:h}
cd "$SCRIPT_DIR"

# Cron jobs often run with a minimal PATH. Keep the common Homebrew and system
# locations available so git can be found reliably.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
LOG_FILE="${TMPDIR:-/tmp}/github_action-auto_commit.log"
exec >>"$LOG_FILE" 2>&1

current_time=$(date +"%Y-%m-%d %H:%M:%S")

git add -A

if git diff --cached --quiet; then
  echo "Nothing staged after git add."
  exit 0
fi

echo "Changes detected. Committing..."

git commit -m "Auto commit at $current_time"
git push
