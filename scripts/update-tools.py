#!/usr/bin/env python3
"""Update agent-tools binaries from upstream GitHub releases.

Reads tools-manifest.json. For each tool:
  1. Fetch the latest release of `repo`.
  2. Match a release asset against `asset_glob` (preferring amd64/x64 over arm/i386).
  3. If the release tag matches the recorded version (.tool-versions.json), skip.
  4. Download the asset. If `zip`, extract and locate the .exe via `exe_glob`;
     otherwise use the downloaded file directly.
  5. Write the canonical `name` (hyphens/version/platform suffix already stripped
     to the clean tool name) into the repo working tree.
  6. Record the new version.

The script prints a summary of changed tools and exits 0. It does NOT commit —
the calling workflow commits any changes. Only tools whose version changed are
touched, so unchanged releases produce no diff (no empty commits, no churn).

Usage:
  python3 scripts/update-tools.py [--dry-run]
Requires env: GH_TOKEN (GitHub token for API auth + 5000/hr rate limit).
"""
import os, sys, json, fnmatch, io, zipfile, hashlib, urllib.request, urllib.error

MANIFEST = "tools-manifest.json"
VERSIONS = ".tool-versions.json"
TOKEN = os.environ.get("GH_TOKEN", "")

def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-tools-updater",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def pick_asset(assets, glob):
    """Match assets by glob; prefer x64/amd64, avoid arm/i386/386 where possible."""
    matches = [a for a in assets if fnmatch.fnmatch(a["name"].lower(), glob.lower())]
    if not matches:
        return None
    # rank: amd64/x64 first, then anything, penalize arm/386
    def score(a):
        n = a["name"].lower()
        bad = 0
        if "arm64" in n or "aarch64" in n or "armv" in n: bad += 2
        if "-386" in n or "i386" in n or "i686" in n: bad += 2
        return bad
    matches.sort(key=score)
    return matches[0]

def download(url, dest):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
        "User-Agent": "agent-tools-updater",
    })
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        for chunk in iter(lambda: r.read(1 << 20), b""):
            f.write(chunk)

def find_exe_in_zip(zip_path, exe_glob):
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        # prefer exact glob match (case-insensitive), prefer .exe
        lowered = {n.lower(): n for n in names}
        hits = [real for low, real in lowered.items() if fnmatch.fnmatch(low, exe_glob.lower()) and low.endswith(".exe")]
        if not hits:
            # fallback: any single .exe at any depth
            hits = [n for n in names if n.lower().endswith(".exe")]
        if not hits:
            return None
        # pick the shortest path (top-level binary preferred)
        hits.sort(key=lambda n: (len(n), n))
        chosen = hits[0]
        data = z.read(chosen)
        return chosen, data

def main():
    dry = "--dry-run" in sys.argv
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)

    manifest = json.load(open(MANIFEST))["tools"]
    versions = {}
    if os.path.exists(VERSIONS):
        versions = json.load(open(VERSIONS))

    changed = []
    skipped = []
    failed = []

    for t in manifest:
        name = t["name"]
        repo = t["repo"]
        try:
            rel = api(f"https://api.github.com/repos/{repo}/releases/latest")
            if "tag_name" not in rel:
                failed.append((name, repo, "no releases (404/empty)"))
                continue
            tag = rel["tag_name"]
            if versions.get(name) == tag and os.path.exists(name):
                skipped.append((name, tag))
                continue
            asset = pick_asset(rel.get("assets", []), t["asset_glob"])
            if not asset:
                failed.append((name, repo, f"no asset matching {t['asset_glob']}"))
                continue
            tmp = f".tmp-{name}"
            download(asset["browser_download_url"], tmp)
            if t.get("zip"):
                found = find_exe_in_zip(tmp, t.get("exe_glob", f"**/{name}"))
                os.remove(tmp)
                if not found:
                    failed.append((name, repo, f"no .exe inside zip matching {t.get('exe_glob')}"))
                    continue
                inner, data = found
                with open(name, "wb") as f:
                    f.write(data)
            else:
                # direct exe asset — just rename
                os.replace(tmp, name)
            versions[name] = tag
            changed.append((name, tag, asset["name"]))
        except Exception as e:
            failed.append((name, repo, str(e)[:120]))

    if not dry:
        with open(VERSIONS, "w") as f:
            json.dump(versions, f, indent=2, sort_keys=True)
            f.write("\n")  # trailing newline keeps the file byte-stable across no-op runs

    print("=== agent-tools update summary ===")
    print(f"changed: {len(changed)}")
    for n, tag, asset in changed:
        print(f"  ✓ {n:20} -> {tag}  ({asset})")
    print(f"skipped (already current): {len(skipped)}")
    for n, tag in skipped:
        print(f"  · {n:20} == {tag}")
    print(f"failed: {len(failed)}")
    for n, repo, reason in failed:
        print(f"  ✗ {n:20} [{repo}] {reason}")
    # exit code: 0 always (failures are non-fatal; we still commit any successes)
    return 0

if __name__ == "__main__":
    sys.exit(main())
