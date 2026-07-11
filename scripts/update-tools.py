#!/usr/bin/env python3
"""Update agent-tools binaries from upstream GitHub releases.

Reads tools-manifest.json. For each tool:
  1. Fetch the latest release of `repo`.
  2. Match a release asset against `asset_glob` (preferring amd64/x64 over arm/i386).
  3. If the release tag matches the recorded version (.tool-versions.json) and the
     output file(s) exist, skip — avoids re-downloading unchanged releases.
  4. Download the asset. If `zip`, extract each output (matching its `exe_glob`) and
     rename to the canonical `name`; if `tar`, extract from a .tar.gz similarly;
     otherwise the downloaded file IS the output.
  5. Store the output(s):
       - storage "tree"   (default): write into the repo working tree (committed by
         the calling workflow). Used for tools <=100 MB.
       - storage "release": upload as an asset on THIS repo's `large-binaries`
         GitHub release (deleting any prior asset of the same name first). Used for
         tools >100 MB that GitHub refuses in normal git. Requires GITHUB_REPOSITORY
         and a token with contents:write.
  6. Record the new version under every output name.

A tool may produce several `outputs` from one zip (e.g. uv -> uv.exe/uvw.exe/uvx.exe;
ngrep -> ngrep.exe/pcre2-8.dll). Single-output tools just use `name` + `exe_glob`.

The script prints a summary and exits 0 (failures are non-fatal so partial success
still commits). It does NOT commit; the workflow commits tree changes.

Usage:
  python3 scripts/update-tools.py [--dry-run]
Env: GH_TOKEN (GitHub token), GITHUB_REPOSITORY (e.g. "DrOlu/agent-tools",
     auto-set in Actions; set it locally to seed release assets).
"""
import os, sys, json, fnmatch, io, zipfile, tarfile, hashlib, urllib.request, urllib.error, urllib.parse

MANIFEST = "tools-manifest.json"
VERSIONS = ".tool-versions.json"
TOKEN = os.environ.get("GH_TOKEN", "")
THIS_REPO = os.environ.get("GITHUB_REPOSITORY", "")          # e.g. "DrOlu/agent-tools"
LARGE_RELEASE_TAG = "large-binaries"                          # rolling release for >100MB files

def _headers(extra=None):
    h = {
        "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-tools-updater",
    }
    if extra:
        h.update(extra)
    return h

def api(url, method="GET", data=None, extra_headers=None, raw=False, timeout=120):
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
    req = urllib.request.Request(url, method=method, data=body, headers=_headers(extra_headers))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        if raw:
            return r.status, b
        if not b:
            return r.status, None
        return r.status, json.loads(b)

def api_create_release(repo, tag, commitish="main"):
    body = {
        "tag_name": tag,
        "name": "Large binaries (auto-updated)",
        "body": "Binaries larger than GitHub's 100 MB per-file limit (opencode.exe, "
                "omp.exe, usql.exe) live here as release assets. They are kept in sync "
                "with upstream releases by the daily update-tools workflow. Download "
                "them with install-agent-tools.bat.",
        "target_commitish": commitish,
        "draft": False,
        "prerelease": False,
    }
    _, d = api(f"https://api.github.com/repos/{repo}/releases", method="POST", data=body)
    return d

def get_or_create_release(repo, tag):
    """Return the release dict for `tag`, creating it if missing."""
    try:
        _, d = api(f"https://api.github.com/repos/{repo}/releases/tags/{tag}")
        return d
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return api_create_release(repo, tag)
        raise

def upload_release_asset(repo, release, filename, filebytes):
    """Upload (replacing any existing same-named asset) to a release."""
    # delete existing asset of the same name
    for a in release.get("assets", []):
        if a["name"] == filename:
            api(f"https://api.github.com/repos/{repo}/releases/assets/{a['id']}", method="DELETE")
            break
    # the upload_url looks like: https://uploads.github.com/repos/OWNER/REPO/releases/REL_ID/assets{?name,label}
    upload_url = release["upload_url"].split("{")[0]
    params = urllib.parse.urlencode({"name": filename})
    url = f"{upload_url}?{params}"
    status, d = api(url, method="POST", data=filebytes,
                    extra_headers={"Content-Type": "application/octet-stream"},
                    timeout=900)
    return d

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
    with urllib.request.urlopen(req, timeout=900) as r, open(dest, "wb") as f:
        for chunk in iter(lambda: r.read(1 << 20), b""):
            f.write(chunk)

def read_from_zip(zip_path, member_glob, want_ext=None):
    """Return (member_name, bytes) for the zip entry matching member_glob.

    Handles both nested (`ripgrep-15.../rg.exe`) and top-level (`ngrep.exe`)
    entries: `**/foo` matches basename `foo` at any depth including the root.
    """
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        g = member_glob.lower()
        basename_glob = g[3:] if g.startswith("**/") else g.rsplit("/", 1)[-1]
        def ok(n):
            nl = n.lower()
            if want_ext and not nl.endswith(want_ext):
                return False
            if fnmatch.fnmatch(nl, g):                       # full-path match (nested)
                return True
            return fnmatch.fnmatch(nl.rsplit("/", 1)[-1], basename_glob)  # basename match (top-level)
        hits = [n for n in names if ok(n)]
        if not hits:                                           # fallback: any matching ext
            hits = [n for n in names if (not want_ext or n.lower().endswith(want_ext))]
        if not hits:
            return None
        hits.sort(key=lambda n: (len(n), n))   # prefer top-level
        chosen = hits[0]
        return chosen, z.read(chosen)

def read_from_tar(tar_path, member_glob, want_ext=None):
    """Return (member_name, bytes) for the tar.gz entry matching member_glob.

    Mirrors read_from_zip but for .tar.gz archives (e.g. spiceai releases).
    """
    with tarfile.open(tar_path, "r:gz") as t:
        names = t.getnames()
        g = member_glob.lower()
        basename_glob = g[3:] if g.startswith("**/") else g.rsplit("/", 1)[-1]
        def ok(n):
            nl = n.lower()
            if want_ext and not nl.endswith(want_ext):
                return False
            if fnmatch.fnmatch(nl, g):
                return True
            return fnmatch.fnmatch(nl.rsplit("/", 1)[-1], basename_glob)
        hits = [n for n in names if ok(n)]
        if not hits:
            hits = [n for n in names if (not want_ext or n.lower().endswith(want_ext))]
        if not hits:
            return None
        hits.sort(key=lambda n: (len(n), n))
        chosen = hits[0]
        f = t.extractfile(chosen)
        if f is None:
            return None
        return chosen, f.read()

def tool_outputs(t):
    """Normalize a manifest entry to a list of {exe_glob, name} outputs and a storage mode."""
    if "outputs" in t:
        outs = [{"exe_glob": o.get("exe_glob", f"**/{o['name']}"), "name": o["name"]} for o in t["outputs"]]
    else:
        outs = [{"exe_glob": t.get("exe_glob", f"**/{t['name']}"), "name": t["name"]}]
    storage = t.get("storage", "tree")
    return outs, storage

def main():
    dry = "--dry-run" in sys.argv
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)

    manifest = json.load(open(MANIFEST))["tools"]
    versions = {}
    if os.path.exists(VERSIONS):
        versions = json.load(open(VERSIONS))

    # lazily fetch the large-binaries release once (only if a release-storage tool needs it)
    large_release = {"_obj": None}
    def large_release_obj():
        if large_release["_obj"] is None:
            if not THIS_REPO:
                raise RuntimeError("GITHUB_REPOSITORY env var is required to manage release assets")
            large_release["_obj"] = get_or_create_release(THIS_REPO, LARGE_RELEASE_TAG)
        return large_release["_obj"]

    changed = []
    skipped = []
    failed = []

    def save_versions():
        with open(VERSIONS, "w") as f:
            json.dump(versions, f, indent=2, sort_keys=True)
            f.write("\n")  # trailing newline keeps the file byte-stable across no-op runs

    for t in manifest:
        outs, storage = tool_outputs(t)
        primary = outs[0]["name"]
        repo = t["repo"]
        try:
            rel = api(f"https://api.github.com/repos/{repo}/releases/latest")[1]
            if not rel or "tag_name" not in rel:
                failed.append((primary, repo, "no releases (404/empty)"))
                continue
            tag = rel["tag_name"]
            # skip if already at this tag AND all tree outputs exist on disk
            already = versions.get(primary) == tag
            if already and (storage == "release" or all(os.path.exists(o["name"]) for o in outs)):
                skipped.append((primary, tag))
                continue
            asset = pick_asset(rel.get("assets", []), t["asset_glob"])
            if not asset:
                failed.append((primary, repo, f"no asset matching {t['asset_glob']}"))
                continue

            if dry:
                changed.append((primary, tag, asset["name"] + " [dry-run]"))
                continue

            tmp = f".tmp-{primary}"
            download(asset["browser_download_url"], tmp)

            # produce each output's bytes
            produced = []   # (name, bytes)
            if t.get("zip"):
                for o in outs:
                    want_ext = ".dll" if o["name"].endswith(".dll") else ".exe"
                    found = read_from_zip(tmp, o["exe_glob"], want_ext=want_ext)
                    if not found:
                        # fallback: any .exe/.dll at any depth for this output
                        found = read_from_zip(tmp, f"**/*{want_ext}", want_ext=want_ext)
                    if not found:
                        failed.append((o["name"], repo, f"no file inside zip matching {o['exe_glob']}"))
                        break
                    produced.append((o["name"], found[1]))
                os.remove(tmp)
                if len(produced) != len(outs):
                    continue   # a missing output was already recorded as failed
            elif t.get("tar"):
                for o in outs:
                    want_ext = ".dll" if o["name"].endswith(".dll") else ".exe"
                    found = read_from_tar(tmp, o["exe_glob"], want_ext=want_ext)
                    if not found:
                        found = read_from_tar(tmp, f"**/*{want_ext}", want_ext=want_ext)
                    if not found:
                        failed.append((o["name"], repo, f"no file inside tar matching {o['exe_glob']}"))
                        break
                    produced.append((o["name"], found[1]))
                os.remove(tmp)
                if len(produced) != len(outs):
                    continue
            elif t.get("store_archive"):
                # Multi-file self-contained deployment (e.g. .NET app with 600+ DLLs).
                # Upload the entire archive as a release asset — no extraction.
                produced = [(outs[0]["name"], open(tmp, "rb").read())]
                os.remove(tmp)
            else:
                # single non-zip asset — the downloaded file is the (single) output
                produced = [(outs[0]["name"], open(tmp, "rb").read())]
                os.remove(tmp)

            # store the outputs
            if storage == "release":
                rel_obj = large_release_obj()
                for name, data in produced:
                    upload_release_asset(THIS_REPO, rel_obj, name, data)
                    # refresh cached release asset list so the next delete sees prior uploads
                    rel_obj = get_or_create_release(THIS_REPO, LARGE_RELEASE_TAG)
                large_release["_obj"] = rel_obj
            else:
                for name, data in produced:
                    with open(name, "wb") as f:
                        f.write(data)

            for o in outs:
                versions[o["name"]] = tag
            save_versions()  # incremental: survives a timeout mid-run
            changed.append((primary, tag, asset["name"]))
        except Exception as e:
            failed.append((primary, repo, str(e)[:160]))

    if not dry:
        save_versions()  # final flush (no-op if every tool already saved)

    print("=== agent-tools update summary ===")
    print(f"changed: {len(changed)}")
    for n, tag, asset in changed:
        print(f"  + {n:20} -> {tag}  ({asset})")
    print(f"skipped (already current): {len(skipped)}")
    for n, tag in skipped:
        print(f"  . {n:20} == {tag}")
    print(f"failed: {len(failed)}")
    for n, repo, reason in failed:
        print(f"  x {n:20} [{repo}] {reason}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
