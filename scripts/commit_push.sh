#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/commit_push.sh -m "<subject>" [-d "<description>"] [--no-push]

Description:
  Stage all changes, create one commit, and push current branch to origin.

Examples:
  scripts/commit_push.sh -m "docs: update AGENTS"
  scripts/commit_push.sh -m "feat(api): add health route" -d "Add endpoint and tests."
  scripts/commit_push.sh -m "chore: snapshot WIP" --no-push
EOF
}

subject=""
description=""
no_push=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message)
      subject="${2:-}"
      shift 2
      ;;
    -d|--description)
      description="${2:-}"
      shift 2
      ;;
    --no-push)
      no_push=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$subject" ]]; then
  echo "Missing commit subject." >&2
  usage
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repository." >&2
  exit 1
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to commit."
  exit 1
fi

branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  echo "Could not detect current branch." >&2
  exit 1
fi

git add -A
if [[ -n "$description" ]]; then
  git commit -m "$subject" -m "$description"
else
  git commit -m "$subject"
fi

if [[ "$no_push" -eq 0 ]]; then
  git push origin "$branch"
  echo "Pushed to origin/$branch"
else
  echo "Commit created on $branch (push skipped)."
fi
