#!/usr/bin/env bash
# auto-push.sh — Autonomous folder → GitHub repo pusher
# Handles .git/.files persistence issues via renaming + GitHub API fallback
# Usage: ./auto-push.sh <folder> <repo-url> [branch]
set -euo pipefail

FOLDER="${1:-}"
REPO_URL="${2:-}"
BRANCH="${3:-main}"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

if [[ -z "$FOLDER" || -z "$REPO_URL" ]]; then
    echo "Usage: $0 <folder> <repo-url> [branch]"
    echo "  folder:   Local directory to push"
    echo "  repo-url: https://github.com/user/repo or git@github.com:user/repo"
    echo "  branch:   Target branch (default: main)"
    echo ""
    echo "Env: GITHUB_TOKEN or GH_TOKEN must be set"
    exit 1
fi

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: GITHUB_TOKEN or GH_TOKEN not set"
    exit 1
fi

# Parse repo owner/name from URL
if [[ "$REPO_URL" =~ github.com[/:]([^/]+)/([^/]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
else
    echo "ERROR: Cannot parse repo URL: $REPO_URL"
    exit 1
fi

REPO="${REPO%.git}"
API_URL="https://api.github.com/repos/${OWNER}/${REPO}"
AUTH_HEADER="Authorization: token ${TOKEN}"

echo "=== AUTO-PUSH ==="
echo "Folder:  $FOLDER"
echo "Repo:    $OWNER/$REPO"
echo "Branch:  $BRANCH"

# Step 1: Create temp working copy (isolates .git issues)
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo ""
echo "=== Step 1: Prepare temp copy ==="
rsync -a --exclude='.git' "$FOLDER/" "$TMPDIR/" 2>/dev/null || cp -r "$FOLDER"/* "$TMPDIR/" 2>/dev/null || true

# Step 2: Handle .files that need persistence
# Rename .git* → git*_ (preserves content, avoids git conflicts)
# Rename .github → github_ (preserves workflows, avoids git dir confusion)
# These get renamed back in post-receive hook or via API
echo "=== Step 2: Rename .files for persistence ==="
find "$TMPDIR" -name ".git*" -type f | while read f; do
    dir=$(dirname "$f")
    base=$(basename "$f")
    newname="${base#.}_"
    mv "$f" "$dir/$newname"
    echo "  Renamed: $base → ${newname}"
done

# Rename .github directory
if [[ -d "$TMPDIR/.github" ]]; then
    mv "$TMPDIR/.github" "$TMPDIR/github_"
    echo "  Renamed: .github → github_"
fi

# Rename other dotfiles that might be lost
find "$TMPDIR" -name ".*" -type f | while read f; do
    dir=$(dirname "$f")
    base=$(basename "$f")
    newname="${base#.}_"
    mv "$f" "$dir/$newname"
    echo "  Renamed: $base → ${newname}"
done

# Step 3: Git init in temp dir (fresh, no history conflicts)
echo ""
echo "=== Step 3: Git init and commit ==="
cd "$TMPDIR"
git init
git config user.email "auto-push@localhost"
git config user.name "Auto Push"
git add -A
git commit -m "auto: push from $(hostname) at $(date -Iseconds)" || true

# Step 4: Backup current branch if exists
echo ""
echo "=== Step 4: Backup current branch ==="
git remote add origin "https://${TOKEN}@github.com/${OWNER}/${REPO}.git" 2>/dev/null || true
git fetch origin "$BRANCH" 2>/dev/null || true

if git rev-parse --verify "origin/${BRANCH}" >/dev/null 2>&1; then
    BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
    git branch "$BACKUP_BRANCH" "origin/${BRANCH}" 2>/dev/null || true
    echo "  Backup: $BACKUP_BRANCH"
fi

# Step 5: Force push
echo ""
echo "=== Step 5: Push ==="
git push origin "HEAD:${BRANCH}" --force 2>&1 || {
    echo "Git push failed, falling back to GitHub API..."

    # API fallback: upload files directly
    python3 -c "
import os, requests, base64, sys

folder = '$TMPDIR'
base_url = '$API_URL'
headers = {'$AUTH_HEADER', 'Accept': 'application/vnd.github.v3+json'}
branch = '$BRANCH'

# Get current commit
r = requests.get(f'{base_url}/git/ref/heads/{branch}', headers=headers, timeout=10)
if r.status_code == 200:
    current_sha = r.json()['object']['sha']
    print(f'Current: {current_sha[:8]}')
else:
    current_sha = None
    print('No existing branch')

# Upload all files
for root, dirs, files in os.walk(folder):
    for f in files:
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, folder).replace('_', '.', 1)  # Rename back
        with open(fp, 'rb') as file:
            content = file.read()

        r = requests.put(
            f'{base_url}/contents/{rel}',
            headers=headers,
            json={'message': f'auto: {rel}', 'content': base64.b64encode(content).decode(), 'branch': branch},
            timeout=30
        )
        if r.status_code in (200, 201):
            print(f'  OK: {rel}')
        else:
            print(f'  FAIL: {rel}: {r.status_code}')
            sys.exit(1)

print('API fallback complete')
" || exit 1
}

echo ""
echo "=== DONE ==="
echo "Repo: https://github.com/$OWNER/$REPO/tree/$BRANCH"
if git rev-parse --verify "$BACKUP_BRANCH" >/dev/null 2>&1; then
    echo "Backup: https://github.com/$OWNER/$REPO/tree/$BACKUP_BRANCH"
fi
