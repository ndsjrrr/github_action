#!/bin/zsh
set -euo pipefail

# Always run from the repository root, not from src/ or any other subdirectory.
SCRIPT_DIR=${0:A:h}
cd "$SCRIPT_DIR"

# Cron jobs often run with a minimal PATH. Keep the common Homebrew and system
# locations available so git can be found reliably.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

current_time=$(date +"%Y-%m-%d %H:%M:%S")

if git diff --quiet && git diff --cached --quiet; then
  echo "No changes detected."
  exit 0
fi

echo "Changes detected. Committing..."
git add -A

if git diff --cached --quiet; then
  echo "Nothing staged after git add."
  exit 0
fi

git commit -m "Auto commit at $current_time"
git push
