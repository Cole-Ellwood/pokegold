"""Scenario loader + runner.

A scenario file is YAML::

    name: falkner_first_damage
    rom: pokegold_trace        # ROM variant (pokegold_debug or pokegold_trace)
    state: .local/tmp/boss_state_factory/falkner_chosen_frame_4655.state
    target: BattleCommand_DamageCalc
    max_frames: 600
    setup_buttons: ['a', 'a', 'a']   # optional advance through menus
    pokes: {}                         # optional WRAM/register pokes after load

Running a scenario loads the ROM, loads the save state, optionally
applies button presses or memory pokes, installs the Tracer on the
target function, ticks max_frames, and writes the JSONL trace.

The interesting moment is when the target function fires for the first
time during the run — that gives us inputs (registers + WRAM) at the
exact entry point we care about.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .emulator import DebugSession
from .paths import find_rom, find_sym
from .tracer import Tracer

# PyBoy button names: 'a','b','start','select','up','down','left','right'
BUTTONS = ('a', 'b', 'start', 'select', 'up', 'down', 'left', 'right')


@dataclass
class Scenario:
    name: str
    rom: str = "pokegold_trace"
    state: str | None = None
    target: str = "BattleCommand_DamageCalc"
    max_frames: int = 600
    setup_buttons: list[str] = field(default_factory=list)
    pokes: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    @classmethod
    def load(cls, path: Path) -> "Scenario":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if "name" not in data:
            data["name"] = path.stem
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ScenarioResult:
    scenario: Scenario
    frames: int
    target_hit_count: int
    first_entry_seq: int | None
    last_exit_seq: int | None
    jsonl_path: Path


def _press_button(sess: DebugSession, name: str) -> None:
    name = name.lower()
    if name not in BUTTONS:
        raise ValueError(f"unknown button {name!r}; valid: {BUTTONS}")
    pyboy = sess.pyboy
    btn = getattr(pyboy, "button", None)
    if btn is not None:
        btn(name, 1)
        sess.tick(2)
    else:
        # Fallback to send_input style if button() isn't present.
        for delay in (3, 3, 3):
            try:
                pyboy.send_input(getattr(pyboy, name.upper()))
                sess.tick(delay)
            except AttributeError:
                pass


def _apply_pokes(sess: DebugSession, pokes: dict[str, Any]) -> None:
    """Apply named pokes; supports symbol or hex addresses, scalar or list."""
    for key, value in pokes.items():
        # Resolve key
        if isinstance(key, str) and key.startswith("0x"):
            bank, addr = None, int(key, 16)
        elif isinstance(key, str) and key in sess.symbols:
            sym = sess.symbols[key]
            bank, addr = sym.bank, sym.address
        else:
            raise ValueError(f"unknown poke target {key!r}")
        # Coerce value
        if isinstance(value, int):
            data = [value & 0xFF]
        elif isinstance(value, list):
            data = [int(v) & 0xFF for v in value]
        elif isinstance(value, str):
            if value.startswith("0x"):
                data = [int(value, 16) & 0xFF]
            else:
                raise ValueError(f"unknown poke value {value!r} for {key!r}")
        else:
            raise ValueError(f"unknown poke value type {type(value)} for {key!r}")
        for i, b in enumerate(data):
            if bank is None or addr + i < 0x4000:
                sess.pyboy.memory[addr + i] = b
            else:
                # WRAMX: switch SVBK
                if 0xD000 <= addr + i <= 0xDFFF and bank:
                    old = int(sess.pyboy.memory[0xFF70])
                    sess.pyboy.memory[0xFF70] = bank
                    try:
                        sess.pyboy.memory[addr + i] = b
                    finally:
                        sess.pyboy.memory[0xFF70] = old
                else:
                    sess.pyboy.memory[bank, addr + i] = b


def run_scenario(scn: Scenario, *, project_root: Path | None = None) -> ScenarioResult:
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]

    out_dir = project_root / "audit" / "damage_debugger"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"{scn.name}.jsonl"

    with DebugSession.open(scn.rom) as sess:
        # Load state
        if scn.state:
            state_path = Path(scn.state)
            if not state_path.is_absolute():
                # Try project root then worktree root.
                for base in (project_root, project_root.parent.parent.parent):
                    candidate = base / scn.state
                    if candidate.exists():
                        state_path = candidate
                        break
            if not state_path.exists():
                raise FileNotFoundError(f"state not found: {scn.state}")
            sess.load_state(state_path)
        # Pokes
        if scn.pokes:
            _apply_pokes(sess, scn.pokes)
        # Set up tracer
        if scn.target not in sess.symbols:
            raise KeyError(f"target symbol {scn.target!r} not in sym table for {scn.rom}")
        tr = Tracer.for_function(sess, scn.target)
        tr.install()
        try:
            # Optional button presses then run
            for b in scn.setup_buttons:
                _press_button(sess, b)
            # Tick in batches so we don't lose responsiveness
            BATCH = 30
            ticked = 0
            while ticked < scn.max_frames:
                sess.tick(BATCH, False)
                ticked += BATCH
        finally:
            tr.uninstall()
        tr.write_jsonl(jsonl_path)

        # Find first entry hit (PC == target's start addr)
        target_sym = sess.symbols[scn.target]
        first_entry = None
        last_exit = None
        hit_count = 0
        for f in tr.frames:
            if f.pc == target_sym.address:
                if first_entry is None:
                    first_entry = f.seq
                hit_count += 1
        last_exit = tr.frames[-1].seq if tr.frames else None
        return ScenarioResult(
            scenario=scn,
            frames=len(tr.frames),
            target_hit_count=hit_count,
            first_entry_seq=first_entry,
            last_exit_seq=last_exit,
            jsonl_path=jsonl_path,
        )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", type=Path, help="YAML scenario file")
    args = p.parse_args()
    scn = Scenario.load(args.scenario)
    res = run_scenario(scn)
    print(f"scenario     : {res.scenario.name}")
    print(f"rom          : {res.scenario.rom}")
    print(f"target       : {res.scenario.target}")
    print(f"frames       : {res.frames}")
    print(f"target hits  : {res.target_hit_count}")
    print(f"first entry  : seq {res.first_entry_seq}")
    print(f"jsonl        : {res.jsonl_path}")
    return 0 if res.target_hit_count > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
