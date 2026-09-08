#!/usr/bin/env bash
# sovereign-rebrand.sh — Rebrand forks to sovereign primary repos
set -euo pipefail

TOKEN="${GITHUB_TOKEN:-$1}"
USER="toxicwind"

TAU="tau"
QED="qed"
HERD="herd"

TAU_UPSTREAM="https://github.com/earendil-works/pi.git"
QED_UPSTREAM="https://github.com/zed-industries/zed.git"
HERD_UPSTREAM="https://github.com/mostlygeek/llama-swap.git"

echo "=== SOVEREIGN REBRAND ==="

create_repo() {
    local old_name=$1
    local new_name=$2
    local upstream=$3
    local description=$4

    echo ""
    echo "=== $old_name → $new_name ==="

    curl -s -H "Authorization: token $TOKEN"          -H "Accept: application/vnd.github.v3+json"          -X POST          -d "{\"name\":\"$new_name\",\"description\":\"$description\",\"private\":false,\"has_issues\":true,\"has_projects\":true,\"has_wiki\":true,\"has_discussions\":true}"          https://api.github.com/user/repos | jq -r '.html_url // .message'

    git clone --mirror https://github.com/$USER/$old_name.git /tmp/$old_name-mirror
    cd /tmp/$old_name-mirror
    git remote set-url origin https://github.com/$USER/$new_name.git
    git push --mirror
    git remote add upstream $upstream

    echo "✓ $new_name ready"
}

create_repo "pi" "$TAU" "$TAU_UPSTREAM" "τ (tau) — The sovereign agent framework. Multi-language, multi-model, fully autonomous."
create_repo "zed" "$QED" "$QED_UPSTREAM" "QED — The definitive AI-native code editor. Proof complete."
create_repo "llama-swap" "$HERD" "$HERD_UPSTREAM" "Herd — Orchestrate fleets of LLM inference engines."

echo ""
echo "=== NEXT STEPS ==="
echo "1. Copy LICENSE, README.md, .github/workflows/ to each repo"
echo "2. Run ./scripts/make-public.sh"
echo "3. Set repository variables: UPSTREAM_URL"
echo "4. Add topics via GitHub UI or API"
echo "5. Cut first release: git tag v1.0.0 && git push origin v1.0.0"
