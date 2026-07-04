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

## Notes

- All binaries are pre-built for **Windows x64**. For macOS/Linux, see the parallel `neuralOS-macOS-ARM64` and `neuralOS-Linux-x64` distributions.
- `pcre2-8.dll` is a runtime dependency for `ngrep.exe` — keep them together.
- This repo holds binaries directly (no LFS). Clone with `--depth 1` for speed: `git clone --depth 1 https://github.com/DrOlu/agent-tools.git`
