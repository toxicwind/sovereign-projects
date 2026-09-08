#!/usr/bin/env python3
"""fast-push.py — Memory-aware parallel GitHub API pusher
Usage: python3 fast-push.py <folder> <repo> [branch]
"""
import os, sys, requests, base64, concurrent.futures, psutil, time, json

def main():
    folder = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3] if len(sys.argv) > 3 else 'main'
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')

    if not token:
        print("ERROR: GITHUB_TOKEN or GH_TOKEN not set")
        sys.exit(1)

    base_url = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    # Memory-aware concurrency
    mem = psutil.virtual_memory()
    concurrency = max(5, min(50, int(mem.available / 50_000_000)))
    print(f"Memory: {mem.available/1e9:.1f}GB, concurrency: {concurrency}")

    start = time.time()

    # Get existing files
    r = requests.get(f"{base_url}/git/trees/{branch}?recursive=1", headers=headers, timeout=15)
    existing = set()
    if r.status_code == 200:
        for item in r.json().get('tree', []):
            if item['type'] == 'blob':
                existing.add(item['path'])
    print(f"Existing: {len(existing)} in {time.time()-start:.2f}s")

    # Collect missing files
    uploads = []
    for root, dirs, files in os.walk(folder):
        if '.git' in root:
            continue
        for f in files:
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, folder)
            if rel not in existing:
                with open(fp, 'rb') as file:
                    uploads.append((rel, file.read()))

    print(f"Missing: {len(uploads)} in {time.time()-start:.2f}s")
    if not uploads:
        print("All files up to date!")
        return

    def upload(args):
        path, content = args
        try:
            r = requests.put(
                f"{base_url}/contents/{path}",
                headers=headers,
                json={"message": f"auto: {path}", "content": base64.b64encode(content).decode(), "branch": branch},
                timeout=30
            )
            return (path, r.status_code in (200, 201), r.status_code)
        except Exception as e:
            return (path, False, str(e)[:100])

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(upload, uploads))

    ok = sum(1 for r in results if r[1])
    fail = len(results) - ok
    print(f"Uploaded: {ok}, Failed: {fail} in {time.time()-start:.1f}s")

    for r in results:
        if not r[1]:
            print(f"  FAIL: {r[0]}: {r[2]}")

    if fail > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
