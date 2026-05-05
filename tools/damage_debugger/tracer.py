"""Per-instruction tracer for any function in pokegold_debug.

Approach: walk the function statically, register a PyBoy hook at every
PC inside the body. Each hook callback snapshots register file + watch
list (HRAM math UNION + battle-state WRAM cells) and appends to an
in-memory trace list. PyBoy's hook system replaces the opcode byte with
$DB so the hook fires *before* the original instruction executes. We
also hook one PC past the end so we get a final post-state.

Output format: one JSON object per line (JSONL).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .disasm import Instruction, walk_function
from .emulator import DebugSession


# Default watch list: HRAM math UNION + key battle state cells. Resolved
# at trace start via the symbol table; misses are silently skipped so the
# tracer still works on a stripped sym build.
DEFAULT_WATCHES: tuple[tuple[str, int], ...] = (
    # HRAM math UNION (the divide/multiply scratch)
    ("hDividend", 4),       # also aliased as hQuotient
    ("hMultiplicand", 3),
    ("hMultiplier", 1),     # also aliased as hRemainder/hMathBuffer base
    ("hMathBuffer", 5),
    # Damage-state shadow
    ("wIsConfusionDamage", 1),
    ("wCriticalHit", 1),
    ("wEffectFailed", 1),
    ("wTypeMatchup", 1),
    ("wCurDamage", 2),
    # Stat-stage levels (sided)
    ("wPlayerAtkLevel", 5),  # Atk, Def, Spe, SpA, SpD
    ("wEnemyAtkLevel", 5),
    # Working stats arrays (5 stats × 2 bytes big-endian)
    ("wPlayerStats", 10),
    ("wEnemyStats", 10),
    # Active move struct
    ("wPlayerMoveStruct", 7),  # PP/anim/effect/power/type/acc/critrate
    # Per-side persistent battle struct slot of interest (computed Atk/Def/Spe)
    ("wEnemyMonAttack", 6),  # Atk, Def, Spe big-endian
    # Bank shadow
    ("hROMBank", 1),
)


@dataclass
class TraceFrame:
    seq: int
    bank: int
    pc: int
    pc_label: str
    mnemonic: str
    A: int
    F: int
    B: int
    C: int
    D: int
    E: int
    HL: int
    SP: int
    Z: int
    N: int
    H: int
    Cf: int
    cycles: int
    watches: dict[str, list[int]]


@dataclass
class Tracer:
    sess: DebugSession
    target: str
    instructions: list[Instruction] = field(default_factory=list)
    frames: list[TraceFrame] = field(default_factory=list)
    watch_list: list[tuple[str, int, int, int]] = field(default_factory=list)
    # name, bank, addr, size
    seq: int = 0
    max_frames: int = 50_000

    @classmethod
    def for_function(
        cls,
        sess: DebugSession,
        target: str,
        watches: tuple[tuple[str, int], ...] = DEFAULT_WATCHES,
    ) -> "Tracer":
        def read_byte(bank: int, addr: int) -> int:
            if addr < 0x4000:
                return int(sess.pyboy.memory[addr])
            return int(sess.pyboy.memory[bank, addr])

        instrs = walk_function(read_byte, sess.symbols, target)
        wl: list[tuple[str, int, int, int]] = []
        for name, size in watches:
            sym = sess.symbols.get(name)
            if sym is None:
                continue
            wl.append((name, sym.bank, sym.address, size))
        return cls(sess=sess, target=target, instructions=instrs, watch_list=wl)

    def _read_watch(self, bank: int, addr: int, size: int) -> list[int]:
        # HRAM and ROM0 ranges read directly; WRAMX (bank 1+) needs banked read.
        out: list[int] = []
        for i in range(size):
            a = addr + i
            if a >= 0xD000 and a <= 0xDFFF and bank:
                # WRAMX banked window
                old_svbk = int(self.sess.pyboy.memory[0xFF70])
                self.sess.pyboy.memory[0xFF70] = bank
                try:
                    out.append(int(self.sess.pyboy.memory[a]))
                finally:
                    self.sess.pyboy.memory[0xFF70] = old_svbk
            else:
                out.append(int(self.sess.pyboy.memory[a]))
        return out

    def _snapshot(self, bank: int, pc: int, mnemonic: str) -> TraceFrame:
        regs = self.sess.regs_snapshot()
        watches = {
            name: self._read_watch(b, a, size)
            for name, b, a, size in self.watch_list
        }
        cycles = 0
        try:
            cycles = int(self.sess.pyboy.cycle_count)
        except AttributeError:
            cycles = 0
        return TraceFrame(
            seq=self.seq,
            bank=bank,
            pc=pc,
            pc_label=self.sess.symbols.render(bank, pc),
            mnemonic=mnemonic,
            A=regs["A"], F=regs["F"],
            B=regs["B"], C=regs["C"],
            D=regs["D"], E=regs["E"],
            HL=regs["HL"], SP=regs["SP"],
            Z=regs["Z"], N=regs["N"], H=regs["H"], Cf=regs["Cf"],
            cycles=cycles,
            watches=watches,
        )

    def install(self) -> None:
        """Install hooks at every instruction PC in the function."""
        for instr in self.instructions:
            mnemonic = instr.mnemonic
            bank = instr.bank
            pc = instr.pc

            def make_cb(b: int, p: int, m: str):
                def cb(ctx):
                    if self.seq >= self.max_frames:
                        return
                    self.frames.append(self._snapshot(b, p, m))
                    self.seq += 1
                return cb

            self.sess.hook_register(bank, pc, make_cb(bank, pc, mnemonic), None)

    def uninstall(self) -> None:
        for instr in self.instructions:
            try:
                self.sess.hook_deregister(instr.bank, instr.pc)
            except Exception:
                pass

    def write_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for f in self.frames:
                fh.write(json.dumps({
                    "seq": f.seq,
                    "bank": f.bank,
                    "pc": f.pc,
                    "pc_label": f.pc_label,
                    "mnemonic": f.mnemonic,
                    "regs": {
                        "A": f.A, "F": f.F, "B": f.B, "C": f.C,
                        "D": f.D, "E": f.E, "HL": f.HL, "SP": f.SP,
                        "Z": f.Z, "N": f.N, "H": f.H, "Cf": f.Cf,
                    },
                    "cycles": f.cycles,
                    "watches": f.watches,
                }, separators=(",", ":")))
                fh.write("\n")


def trace_smoke() -> int:
    """M4 acceptance: hook every PC in VBlank and verify it fires during boot."""
    out_path = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "vblank_smoke.jsonl"
    with DebugSession.open("pokegold_debug") as sess:
        tr = Tracer.for_function(sess, "VBlank")
        if not tr.instructions:
            print("FAIL: walker returned 0 instructions for VBlank")
            return 1
        print(f"VBlank: {len(tr.instructions)} instructions; "
              f"installed {len(tr.watch_list)} watches")
        tr.install()
        try:
            sess.tick(120)  # enough frames to trigger several VBlanks
        finally:
            tr.uninstall()
        if not tr.frames:
            print("FAIL: 0 trace frames captured (hooks never fired)")
            return 1
        tr.write_jsonl(out_path)
        first = tr.frames[0]
        last = tr.frames[-1]
        print(f"Captured {len(tr.frames)} frames; "
              f"first PC ${first.bank:02x}:{first.pc:04x}, "
              f"last PC ${last.bank:02x}:{last.pc:04x}")
        print(f"JSONL: {out_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(trace_smoke())
