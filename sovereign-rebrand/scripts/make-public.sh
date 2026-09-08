#!/usr/bin/env bash
# make-public.sh — Make repos public BEFORE pushing workflows
set -euo pipefail

TOKEN="${GITHUB_TOKEN:-$1}"
USER="toxicwind"

REPOS=("tau" "qed" "herd")

echo "=== MAKING REPOS PUBLIC ==="
echo "This must run BEFORE pushing workflows to avoid burning private credits"
echo ""

for repo in "${REPOS[@]}"; do
    echo "→ $repo"
    curl -s -X PATCH          -H "Authorization: token $TOKEN"          -H "Accept: application/vnd.github.v3+json"          -d '{"private":false}'          "https://api.github.com/repos/$USER/$repo" | jq -r '.html_url // .message'
done

echo ""
echo "✓ All repos public. Safe to push workflows now."
