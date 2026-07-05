# agent-tools

Pre-built Windows x64 agent tooling — a curated bundle of CLI agents, network utilities, SSH clients, and runtime helpers for the SuperAgent / neuralOS / CyberAgent ecosystem.

**Platform:** Windows x64 (10/11, Server 2019+)
**Install:** run `install-agent-tools.bat` as Administrator → copies all tools to `%ProgramFiles%\AgentTools` and adds it to system `PATH`.

## What's inside

A single drop-in folder of standalone `.exe` tools — no installers, no dependencies (one bundled `pcre2-8.dll` for ngrep). Categories:

- **Agent runtimes:** `opencode` (omitted — see below), `omp`, `kagent`, `multica`, `agentspan`, `stakpak`, `agent-browser`, `dev-browser`, `open-terminal`, `vshell`
- **Secrets:** `agentsecrets`, `scrt`
- **Database:** `dbcli`, `usql` (omitted — see below)
- **Network & packet diagnostics:** `netwatch`, `rustnet`, `ngrep`, `wtrace`, `probe`, `zero`
- **Messaging / RPC:** `nats`, `nats-server`, `websocat`, `websocketd`, `webhook`
- **SSH / remote exec:** `pssh`, `plink`, `pscp`, `psftp`, `pmux`, `psmux`, `sshpass`, `pywinrm`
- **Email:** `himalaya`
- **Runtimes / package managers:** `uv`, `uvw`, `uvx`
- **Utilities:** `jq`, `rg`, `oauth2l`, `task`

## Install

```bat
:: Run as Administrator
install-agent-tools.bat
```

The installer:
1. Creates `%ProgramFiles%\AgentTools`
2. Copies every `.exe` (+ `pcre2-8.dll`) into it
3. Appends the directory to the system `PATH`
4. Broadcasts the environment change (restart your terminal to pick it up)

Verify:
```bat
where netwatch
where multica
```

## Manual install

```bat
copy *.exe "%ProgramFiles%\AgentTools\"
:: then add %ProgramFiles%\AgentTools to PATH manually if needed
```

## Tools

| File | Tool | Size |
|---|---|---|
| `agent-browser.exe` | agent-browser | 11 MB |
| `agentsecrets.exe` | agentsecrets | 13 MB |
| `agentspan.exe` | agentspan | 14 MB |
| `dbcli.exe` | dbcli | 45 MB |
| `dev-browser.exe` | dev-browser | 2 MB |
| `himalaya.exe` | himalaya | 37 MB |
| `install-agent-tools.bat` | install-agent-tools | 4 KB |
| `jq.exe` | jq | 1002 KB |
| `kagent.exe` | kagent | 63 MB |
| `multica.exe` | multica | 14 MB |
| `nats-server.exe` | nats-server | 18 MB |
| `nats.exe` | nats | 25 MB |
| `netwatch.exe` | netwatch | 8 MB |
| `ngrep.exe` | ngrep | 36 KB |
| `oauth2l.exe` | oauth2l | 7 MB |
| `open-terminal.exe` | open-terminal | 16 MB |
| `opensre.exe` | opensre | 63 MB |
| `pcre2-8.dll` | pcre2-8 | 590 KB |
| `plink.exe` | plink | 1019 KB |
| `pmux.exe` | pmux | 2 MB |
| `probe.exe` | probe | 39 MB |
| `pscp.exe` | pscp | 1018 KB |
| `psftp.exe` | psftp | 1 MB |
| `psmux.exe` | psmux | 2 MB |
| `pssh.exe` | pssh | 18 MB |
| `pywinrm.exe` | pywinrm | 14 MB |
| `rg.exe` | rg | 4 MB |
| `rustnet.exe` | rustnet | 4 MB |
| `scrt.exe` | scrt | 17 MB |
| `sshpass.exe` | sshpass | 198 KB |
| `stakpak.exe` | stakpak | 69 MB |
| `task.exe` | task | 49 MB |
| `uv.exe` | uv | 59 MB |
| `uvw.exe` | uvw | 325 KB |
| `uvx.exe` | uvx | 325 KB |
| `vshell.exe` | vshell | 5 MB |
| `webhook.exe` | webhook | 12 MB |
| `websocat.exe` | websocat | 2 MB |
| `websocketd.exe` | websocketd | 7 MB |
| `wtrace.exe` | wtrace | 22 MB |
| `zero.exe` | zero | 1 MB |

## Omitted (exceed GitHub's 100 MB per-file limit)

Three tools exceed GitHub's hard per-file limit and are **not** in this repo. Fetch them separately from their upstream sources:

| Tool | Approx. size | Source |
|---|---|---|
| `opencode.exe` | ~158 MB | https://github.com/sst/opencode/releases |
| `omp.exe` | ~162 MB | https://github.com/earendil-works/pi (oh-my-pi) releases |
| `usql.exe` | ~155 MB | https://github.com/xo/usql/releases |

Drop the downloaded `.exe` into `%ProgramFiles%\AgentTools\` alongside the rest after running the installer.

## Automatic updates

A daily GitHub Actions workflow (`.github/workflows/update-tools.yml`, runs at 06:00 UTC, also runnable manually) keeps the **auto-updatable** binaries in sync with their upstream GitHub releases.

How it works:
1. Reads `tools-manifest.json` — a list of tools with their upstream repo, the release-asset glob to match, and (for zips) the glob to find the `.exe` inside.
2. For each tool, fetches `releases/latest`, matches the Windows x64 asset (preferring amd64/x64, avoiding arm/i386), and compares the tag to `.tool-versions.json`.
3. If newer: downloads, **unzips** if needed, **renames to the canonical tool name** (stripping version/platform hyphens — e.g. `ripgrep-15.1.0-x86_64-pc-windows-msvc.zip` → `rg.exe`, `agentspan_windows_amd64.exe` → `agentspan.exe`), writes it, records the new tag.
4. Commits any changes in a single `chore(tools): auto-update binaries (<date>)` commit. No empty commits when nothing changed.

The workflow authenticates to the GitHub API and pushes back with the built-in `GITHUB_TOKEN` — **no stored PAT required**.

### Auto-updated tools (23)

| Tool | Upstream repo | Asset |
|---|---|---|
| `jq.exe` | jqlang/jq | `jq-windows-amd64.exe` |
| `rg.exe` | BurntSushi/ripgrep | `ripgrep-*-x86_64-pc-windows-msvc.zip` |
| `nats.exe` | nats-io/natscli | `nats-*-windows-amd64.zip` |
| `nats-server.exe` | nats-io/nats-server | `nats-server-v*-windows-amd64.zip` |
| `himalaya.exe` | pimalaya/himalaya | `himalaya.x86_64-windows.zip` |
| `netwatch.exe` | matthart1983/netwatch | `netwatch-windows-x86_64.exe.zip` |
| `rustnet.exe` | domcyrus/rustnet | `rustnet-v*-x86_64-pc-windows-msvc.zip` |
| `websocat.exe` | vi/websocat | `websocat.x86_64-pc-windows-gnu.exe` |
| `websocketd.exe` | joewalnes/websocketd | `websocketd-*-windows_amd64.zip` |
| `task.exe` | go-task/task | `task_windows_amd64.zip` |
| `uv.exe` | astral-sh/uv | `uv-x86_64-pc-windows-msvc.zip` |
| `kagent.exe` | kagent-dev/kagent | `kagent-windows-amd64.exe` |
| `multica.exe` | multica-ai/multica | `multica-cli-*-windows-amd64.zip` |
| `opensre.exe` | Tracer-Cloud/opensre | `opensre_*_windows-x64.zip` |
| `stakpak.exe` | stakpak/agent | `stakpak-windows-x86_64.zip` |
| `agentsecrets.exe` | The-17/agentsecrets | `agentsecrets_*_windows_amd64.zip` |
| `scrt.exe` | loderunner/scrt | `scrt_*_windows_x86_64.zip` |
| `wtrace.exe` | lowleveldesign/wtrace | `wtrace.zip` |
| `psmux.exe` | psmux/psmux | `psmux-v*-windows-x64.zip` |
| `dev-browser.exe` | SawyerHood/dev-browser | `dev-browser-windows-x64.exe` |
| `sshpass.exe` | xhcoding/sshpass-win32 | `sshpass.exe` |
| `agentspan.exe` | agentspan-ai/agentspan | `agentspan_windows_amd64.exe` |
| `vshell.exe` | veithly/vibeshell | `vshell-*-windows-x64.exe` |

### Not auto-updatable (15 + 1 dll)

These binaries are **not** published as Windows release assets on GitHub — they are custom builds, website-distributed, or source-only — so they cannot be auto-fetched from a release. They are kept as-is (manual update only):

| Tool | Reason |
|---|---|
| `agent-browser.exe` | DrOlu/agent-browser ships via npm + build-from-source; no release binaries |
| `open-terminal.exe` | DrOlu/open-terminal ships via pip/Docker; no release binaries |
| `zero.exe` | DrOlu/zero ships via `zerolang.ai/install.sh`; no GitHub releases |
| `ngrep.exe` | jpr5/ngrep releases have no Windows asset |
| `pcre2-8.dll` | PCRE2 ships source only; the DLL is a custom build (ngrep dependency) |
| `plink.exe`, `pscp.exe`, `psftp.exe` | PuTTY distributes via its website, not GitHub releases |
| `pssh.exe` | no upstream repo publishes a Windows release binary |
| `pmux.exe` | ShiftInBits/pmux-agent has no Windows asset |
| `probe.exe` | no upstream repo publishes a Windows release binary |
| `dbcli.exe` | dbcli/* are Python packages; the standalone `.exe` is a custom build |
| `pywinrm.exe` | diyan/pywinrm is a Python library; the `.exe` is a custom PyInstaller build |
| `uvw.exe`, `uvx.exe` | tiny launcher stubs not shipped in astral-sh/uv releases (only `uv.exe` is) |
| `oauth2l.exe` | google/oauth2l publishes no release assets |
| `webhook.exe` | adnanh/webhook has no Windows asset |

## Notes

- All binaries are pre-built for **Windows x64**. For macOS/Linux, see the parallel `neuralOS-macOS-ARM64` and `neuralOS-Linux-x64` distributions.
- `pcre2-8.dll` is a runtime dependency for `ngrep.exe` — keep them together.
- This repo holds binaries directly (no LFS). Clone with `--depth 1` for speed: `git clone --depth 1 https://github.com/DrOlu/agent-tools.git`
