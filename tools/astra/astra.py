#!/usr/bin/env python3
"""Run and watch Codex (GPT-6 Astra) worker jobs, one git worktree each.

Codex cannot message the lead back, so each job is a worktree plus a brief
file plus three channel files it writes (`.local/<job>-status.md`,
`.local/<job>-blocked.md`, `.local/<job>-report.md`; see AGENTS.md). This
tool starts the detached process, records a manifest, and shows state.

  python tools/astra/astra.py start <job> --brief <file> [--base <commit>] [--effort medium]
  python tools/astra/astra.py status [<job>]
  python tools/astra/astra.py collect <job>
  python tools/astra/astra.py resume <job> "<answer or new instruction>"
  python tools/astra/astra.py stop <job>
  python tools/astra/astra.py ask "<question>" [--job <job>] [--cwd <dir>]   (synchronous, reply printed)
  python tools/astra/astra.py sweep <brief1.md> <brief2.md> ...              (one job per brief)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\Users\lolno\Downloads\pokemon gold hack")
JOBS = MAIN / ".local" / "astra-jobs"
CODEX = shutil.which("codex.exe") or shutil.which("codex") or "codex"
MODEL = "gpt-6-astra"
COPY_IN = ["rgbds-1.0.1", ".local/ai-two-second"]


def sh(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()


def manifest_path(job: str) -> Path:
    return JOBS / f"{job}.json"


def load(job: str) -> dict:
    p = manifest_path(job)
    if not p.exists():
        sys.exit(f"no such job {job!r}; see {JOBS}")
    return json.loads(p.read_text(encoding="utf-8"))


def alive(pid: int) -> bool:
    out = sh(["tasklist", "/FI", f"PID eq {pid}", "/NH"])
    return str(pid) in out


def start(job: str, brief: Path, base: str, effort: str, sandbox: str) -> None:
    wt = MAIN / ".claude" / "worktrees" / f"astra-{job}"
    branch = f"astra/{job}"
    if wt.exists():
        sys.exit(f"{wt} exists; pick another job name or stop/collect the old one")
    JOBS.mkdir(parents=True, exist_ok=True)
    print(sh(["git", "worktree", "add", "-b", branch, str(wt), base], cwd=MAIN))
    for rel in COPY_IN:
        src, dst = MAIN / rel, wt / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
    local = wt / ".local"
    shutil.copy(brief, local / f"{job}-brief.md")
    for ext in ("gbc", "sym"):
        src = MAIN / f"pokegold.{ext}"
        if src.exists():
            shutil.copy(src, local / f"old_pokegold.{ext}")
    prompt = (f"Read AGENTS.md, then .local/{job}-brief.md in full, and carry the brief "
              f"out completely: every task, every gate, the status file as you go, and "
              f"the final report at .local/{job}-report.md.")
    log = local / f"{job}.log"
    err = local / f"{job}.err"
    args = [CODEX, "exec", "-s", sandbox, "-c", "approval_policy=never",
            "-m", MODEL, "-c", f"model_reasoning_effort={effort}",
            "-o", str(local / f"{job}-last.md"), prompt]
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0)
    with open(log, "w", encoding="utf-8") as lf, open(err, "w", encoding="utf-8") as ef:
        p = subprocess.Popen(args, cwd=wt, stdout=lf, stderr=ef, creationflags=flags)
    manifest_path(job).write_text(json.dumps({
        "job": job, "worktree": str(wt), "branch": branch, "base": base, "pid": p.pid,
        "model": MODEL, "effort": effort, "sandbox": sandbox, "started": time.strftime("%Y-%m-%d %H:%M"),
        "brief": str(local / f"{job}-brief.md"), "log": str(log),
    }, indent=2), encoding="utf-8")
    print(f"started {job}: pid {p.pid}, worktree {wt}, branch {branch}")


def status(job: str | None) -> None:
    jobs = [job] if job else sorted(p.stem for p in JOBS.glob("*.json"))
    for name in jobs:
        m = load(name)
        wt = Path(m["worktree"])
        running = alive(m["pid"])
        head = sh(["git", "log", "--oneline", "-1"], cwd=wt) if wt.exists() else "(worktree gone)"
        print(f"== {name}: {'RUNNING' if running else 'EXITED'} pid {m['pid']} since {m['started']}")
        print(f"   {wt}\n   HEAD {head}")
        for chan in ("status", "blocked", "report"):
            f = wt / ".local" / f"{name}-{chan}.md"
            if f.exists():
                lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
                print(f"   {chan}: {len(lines)} line(s); last: {lines[-1] if lines else ''}")
        log = Path(m["log"])
        if log.exists():
            tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-3:]
            for line in tail:
                print(f"   log> {line[:160]}")


def collect(job: str) -> None:
    m = load(job)
    wt = Path(m["worktree"])
    print(sh(["git", "log", "--oneline", f"{m['base']}..HEAD"], cwd=wt) or "(no commits)")
    print(sh(["git", "diff", "--stat", f"{m['base']}..HEAD"], cwd=wt))
    dirty = sh(["git", "status", "--short"], cwd=wt)
    if dirty:
        print("UNCOMMITTED:\n" + dirty)
    for chan in ("blocked", "report"):
        f = wt / ".local" / f"{job}-{chan}.md"
        if f.exists():
            print(f"\n----- {chan} -----\n" + f.read_text(encoding="utf-8", errors="replace"))


def resume(job: str, message: str) -> None:
    m = load(job)
    wt = Path(m["worktree"])
    if alive(m["pid"]):
        sys.exit("still running; stop it first or wait")
    blocked = wt / ".local" / f"{job}-blocked.md"
    if blocked.exists():
        blocked.rename(wt / ".local" / f"{job}-blocked-{time.strftime('%H%M')}.md")
    log = Path(m["log"])
    # options belong before `resume`: `codex exec [OPTIONS] resume --last [PROMPT]`
    args = [CODEX, "exec", "-s", m["sandbox"], "-c", "approval_policy=never",
            "-m", m["model"], "-c", f"model_reasoning_effort={m['effort']}",
            "-o", str(wt / ".local" / f"{job}-last.md"), "resume", "--last", message]
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0)
    with open(log, "a", encoding="utf-8") as lf, open(str(log)[:-4] + ".err", "a", encoding="utf-8") as ef:
        p = subprocess.Popen(args, cwd=wt, stdout=lf, stderr=ef, creationflags=flags)
    m["pid"] = p.pid
    manifest_path(job).write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"resumed {job}: pid {p.pid}")


def ask(job: str | None, message: str, cwd: Path | None, effort: str, sandbox: str) -> str:
    """Synchronous turn: run Codex, wait, return its final message (keeps the
    session so a later `ask` with the same job continues the conversation).
    Turns must finish inside the caller's timeout; long builds use `start`."""
    args = [CODEX, "exec", "-s", sandbox, "-c", "approval_policy=never", "-m", MODEL,
            "-c", f"model_reasoning_effort={effort}", "--json"]
    if job:
        m = load(job)
        wt = Path(m["worktree"])
        args += ["resume", "--last", message]
    else:
        wt = cwd or ROOT
        args += [message]
    out = subprocess.run(args, cwd=wt, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    last = ""
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") == "item.completed" and item.get("type") == "agent_message":
            last = item.get("text", last)
    return last or out[-2000:]


def sweep(briefs: list[Path], base: str, effort: str, sandbox: str) -> None:
    for brief in briefs:
        start(brief.stem.replace("-brief", ""), brief, base, effort, sandbox)


def stop(job: str) -> None:
    m = load(job)
    if alive(m["pid"]):
        subprocess.run(["taskkill", "/PID", str(m["pid"]), "/T", "/F"], capture_output=True)
        print(f"killed {m['pid']}")
    else:
        print("not running")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("job"); s.add_argument("--brief", required=True, type=Path)
    s.add_argument("--base", default="master"); s.add_argument("--effort", default="medium")
    # Build jobs need WSL (the sandbox refuses to start it) and the worktree's
    # git metadata lives in the main repo's .git, so worktree jobs run unsandboxed;
    # the worktree, AGENTS.md and the lead's review are the containment.
    s.add_argument("--sandbox", default="danger-full-access", choices=["read-only", "workspace-write", "danger-full-access"])
    t = sub.add_parser("status"); t.add_argument("job", nargs="?")
    c = sub.add_parser("collect"); c.add_argument("job")
    r = sub.add_parser("resume"); r.add_argument("job"); r.add_argument("message")
    k = sub.add_parser("stop"); k.add_argument("job")
    q = sub.add_parser("ask"); q.add_argument("message"); q.add_argument("--job")
    q.add_argument("--cwd", type=Path); q.add_argument("--effort", default="medium")
    q.add_argument("--sandbox", default="read-only", choices=["read-only", "workspace-write", "danger-full-access"])
    w = sub.add_parser("sweep"); w.add_argument("briefs", nargs="+", type=Path)
    w.add_argument("--base", default="master"); w.add_argument("--effort", default="medium")
    w.add_argument("--sandbox", default="danger-full-access")
    a = ap.parse_args()
    if a.cmd == "ask":
        print(ask(a.job, a.message, a.cwd, a.effort, a.sandbox)); return
    if a.cmd == "sweep":
        sweep(a.briefs, a.base, a.effort, a.sandbox); return
    if a.cmd == "start":
        start(a.job, a.brief, a.base, a.effort, a.sandbox)
    elif a.cmd == "status":
        status(a.job)
    elif a.cmd == "collect":
        collect(a.job)
    elif a.cmd == "resume":
        resume(a.job, a.message)
    elif a.cmd == "stop":
        stop(a.job)


if __name__ == "__main__":
    main()
