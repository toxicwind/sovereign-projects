#!/usr/bin/env bash
# update-settings.sh — Configure GitHub repo settings
set -euo pipefail

TOKEN="${GITHUB_TOKEN:-$1}"
USER="toxicwind"

update_repo() {
    local repo=$1
    local topics=$2
    local homepage=$3
    local upstream=$4

    echo "Updating $repo..."

    curl -s -X PATCH          -H "Authorization: token $TOKEN"          -H "Accept: application/vnd.github.v3+json"          -d "{\"has_issues\":true,\"has_projects\":true,\"has_wiki\":true,\"has_discussions\":true,\"homepage\":\"$homepage\",\"topics\":$topics}"          https://api.github.com/repos/$USER/$repo | jq -r '.html_url // .message'

    curl -s -X POST          -H "Authorization: token $TOKEN"          -H "Accept: application/vnd.github.v3+json"          -d "{\"name\":\"UPSTREAM_URL\",\"value\":\"$upstream\"}"          https://api.github.com/repos/$USER/$repo/actions/variables | jq -r '.name // .message'
}

update_repo "tau" '["ai-agent","llm","polyglot","autonomous","sovereign","typescript","bun"]' "https://tau.dev" "https://github.com/earendil-works/pi.git"
update_repo "qed" '["ai-editor","autonomous","rust","gpu","mcp","sovereign"]' "https://qed.dev" "https://github.com/zed-industries/zed.git"
update_repo "herd" '["llm","inference","gateway","orchestration","go","vllm","sglang","sovereign"]' "https://herd.dev" "https://github.com/mostlygeek/llama-swap.git"

echo "✓ All repos configured"
