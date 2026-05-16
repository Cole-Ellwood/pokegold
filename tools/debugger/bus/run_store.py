"""Run metadata + artifact store.

Generalizes the boss_ai_debugger run_store pattern for project-wide
debugger runs. Each run gets a timestamped directory with metadata,
events, and artifacts.

Layout:
    audit/debugger/runs/
      YYYY-MM-DD_HHMM_<slug>/
        meta.json       # commit, ROM hash, symbol hash, seed, command
        events.jsonl    # streaming events
        summary.md      # human-readable report
        artifacts/      # decision waterfalls, diagrams, etc
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RunMeta:
    """Metadata for a single debugger run."""
    run_id: str
    timestamp: str
    command: str
    rom_hash: str = ""
    sym_hash: str = ""
    commit: str = ""
    seed: int | str = ""
    variant: str = "pokegold"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunMeta:
        extra = d.pop("extra", {})
        return cls(**d, extra=extra)


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


class RunStore:
    """Manages debugger run directories."""

    def __init__(self, base: Path | None = None) -> None:
        if base is None:
            base = Path(__file__).resolve().parents[3] / "audit" / "debugger" / "runs"
        self._base = base

    @property
    def base(self) -> Path:
        return self._base

    def create_run(
        self,
        slug: str,
        command: str,
        variant: str = "pokegold",
        seed: int | str = "",
        extra: dict[str, Any] | None = None,
    ) -> tuple[Path, RunMeta]:
        ts = time.strftime("%Y-%m-%d_%H%M")
        run_id = f"{ts}_{slug}"
        run_dir = self._base / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)

        project_root = Path(__file__).resolve().parents[3]
        rom_path = project_root / f"{variant}.gbc"
        sym_path = project_root / f"{variant}.sym"

        meta = RunMeta(
            run_id=run_id,
            timestamp=ts,
            command=command,
            rom_hash=_file_sha256(rom_path),
            sym_hash=_file_sha256(sym_path),
            commit=_git_commit(),
            seed=seed,
            variant=variant,
            extra=extra or {},
        )

        (run_dir / "meta.json").write_text(
            json.dumps(meta.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        return run_dir, meta

    def list_runs(self) -> list[Path]:
        if not self._base.exists():
            return []
        return sorted(
            (d for d in self._base.iterdir() if d.is_dir() and (d / "meta.json").exists()),
            reverse=True,
        )

    def load_meta(self, run_dir: Path) -> RunMeta:
        data = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        return RunMeta.from_dict(data)

    def latest_run(self) -> Path | None:
        runs = self.list_runs()
        return runs[0] if runs else None
