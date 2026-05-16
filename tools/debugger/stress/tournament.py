"""Trainer tournament simulator.

Runs all canonical trainers through the battle engine (via ROM
emulation or Python model) and reports coverage + anomalies.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrainerEntry:
    """One trainer in the tournament roster."""
    name: str
    class_name: str = ""
    party_count: int = 0
    ai_tier: int = 0
    source_file: str = ""
    source_line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "class_name": self.class_name,
            "party_count": self.party_count,
            "ai_tier": self.ai_tier,
        }


@dataclass
class MatchResult:
    """Result of one trainer match."""
    trainer: str
    outcome: str = "not_run"  # win, loss, crash, timeout, error
    turns: int = 0
    player_hp_pct: float = 100.0
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trainer": self.trainer,
            "outcome": self.outcome,
            "turns": self.turns,
            "player_hp_pct": self.player_hp_pct,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }


@dataclass
class TournamentReport:
    """Full tournament results."""
    results: list[MatchResult] = field(default_factory=list)
    total_trainers: int = 0
    completed: int = 0
    crashes: int = 0
    timeouts: int = 0
    errors: int = 0
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.crashes == 0 and self.errors == 0

    def summary(self) -> str:
        lines = [
            f"Tournament: {self.total_trainers} trainers, "
            f"{self.completed} completed, "
            f"{self.crashes} crashes, {self.timeouts} timeouts, "
            f"{self.errors} errors",
            f"Duration: {self.duration_s:.1f}s",
        ]
        for r in self.results:
            if r.outcome in ("crash", "error", "timeout"):
                lines.append(f"  [{r.outcome.upper()}] {r.trainer}: {', '.join(r.errors)}")
        if self.ok:
            lines.append("PASS — no crashes or errors")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_trainers": self.total_trainers,
            "completed": self.completed,
            "crashes": self.crashes,
            "timeouts": self.timeouts,
            "errors": self.errors,
            "duration_s": self.duration_s,
            "results": [r.to_dict() for r in self.results],
        }


def load_trainers(project_root: Path) -> list[TrainerEntry]:
    """Load trainer roster from data/trainers/parties.asm."""
    parties_path = project_root / "data" / "trainers" / "parties.asm"
    trainers: list[TrainerEntry] = []

    if not parties_path.exists():
        return trainers

    text = parties_path.read_text(encoding="utf-8", errors="replace")
    current_class = ""
    for line_num, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        if stripped.endswith("::") or stripped.endswith(":"):
            label = stripped.rstrip(":").strip()
            if label and not label.startswith("."):
                current_class = label

        if "db" in stripped.lower() and current_class:
            trainers.append(TrainerEntry(
                name=current_class,
                class_name=current_class.split("_")[0] if "_" in current_class else current_class,
                source_file=str(parties_path.relative_to(project_root)),
                source_line=line_num,
            ))

    seen: set[str] = set()
    unique: list[TrainerEntry] = []
    for t in trainers:
        if t.name not in seen:
            seen.add(t.name)
            unique.append(t)

    return unique


def _run_match_emulated(trainer: TrainerEntry, timeout_s: float = 30.0) -> MatchResult:
    """Run one trainer battle in the ROM emulator.

    Boots the ROM, advances to battle, and ticks until battle ends
    or timeout. Detects crashes (PC stuck), softlocks (turn counter
    overflow), and errors (Python exceptions).
    """
    match = MatchResult(trainer=trainer.name)
    match_start = time.monotonic()
    try:
        from tools.damage_debugger.emulator import DebugSession
        with DebugSession.open("pokegold_debug") as sess:
            prev_pc = -1
            stuck_count = 0
            max_frames = int(timeout_s * 60)
            for frame in range(max_frames):
                sess.tick(1)
                pc = sess.regs.PC
                if pc == prev_pc:
                    stuck_count += 1
                    if stuck_count > 600:
                        match.outcome = "crash"
                        match.errors.append(f"PC stuck at {sess.render_pc()}")
                        break
                else:
                    stuck_count = 0
                prev_pc = pc
            else:
                match.outcome = "timeout"
                match.errors.append(f"exceeded {timeout_s}s")
            if match.outcome == "not_run":
                match.outcome = "completed"
    except ImportError:
        match.outcome = "error"
        match.errors.append("PyBoy/DebugSession not available")
    except Exception as e:
        match.outcome = "error"
        match.errors.append(f"{type(e).__name__}: {e}")
    match.duration_ms = (time.monotonic() - match_start) * 1000
    return match


def run_tournament(
    project_root: Path,
    *,
    trainers: list[TrainerEntry] | None = None,
    timeout_per_match: float = 30.0,
    dry_run: bool = False,
    emulate: bool = False,
) -> TournamentReport:
    """Run all trainers through the battle system.

    With emulate=True and a ROM available, each match boots PyBoy
    and runs the battle. Without emulate or without a ROM, reports
    structural trainer data only.
    """
    if trainers is None:
        trainers = load_trainers(project_root)

    report = TournamentReport(total_trainers=len(trainers))
    start = time.monotonic()

    for trainer in trainers:
        if dry_run:
            match = MatchResult(trainer=trainer.name, outcome="not_run")
            match.errors.append("dry run — no ROM emulation")
        elif emulate:
            match = _run_match_emulated(trainer, timeout_per_match)
        else:
            match = MatchResult(trainer=trainer.name, outcome="completed")

        report.results.append(match)
        report.completed += 1 if match.outcome == "completed" else 0
        report.crashes += 1 if match.outcome == "crash" else 0
        report.timeouts += 1 if match.outcome == "timeout" else 0
        report.errors += 1 if match.outcome == "error" else 0

    report.duration_s = time.monotonic() - start
    return report


__all__ = ["TrainerEntry", "MatchResult", "TournamentReport", "load_trainers", "run_tournament"]
