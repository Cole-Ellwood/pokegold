"""Reusable ROM-driving harness for boss-AI decision-path fixtures.

Why this exists
---------------
Three real bugs shipped in one week, and every one of them lived in a branch that
nothing exercised:

  * Grass regrowth healed every mon at the dual rate -- the mono branch was
    unreachable because a register carrying the type contribution was clobbered.
  * Paralysed Electric mons skipped the Fighting Speed check -- the types
    pointer was overwritten by a denominator before the second read.
  * A Haki'd boss picked a move the defender was immune to -- the boss-first
    entry point never ran the scoring model, so "best move" decayed to slot 1.

None were visible to a Python reimplementation of the intended logic. All three
were obvious the moment the real routine was driven on the real ROM with the
branch conditions actually set. That is what this module makes cheap: describe a
decision path and its expected outcome as data, and the runner drives it.

Design rules learned the hard way
---------------------------------
1. Never use $0008 as a call sentinel. It is the FarCall RST vector that the
   battle engine hits constantly, so a hook there fires mid-routine. Push a
   `jr -2` trap in HRAM instead (see tools/damage_debugger/safe_call.py).
2. Mask interrupts before jumping. We hijack PC/SP, so a VBlank hands control to
   the real game loop and never comes back.
3. Read outputs only after the routine parks in the trap. `tick()` cannot stop
   mid-frame, so anything read while the ROM is still running is post-return
   garbage.
4. Pin every branch with BOTH polarities. A collapsed branch still passes a
   one-sided test -- that is precisely how the mono/dual bugs survived.
5. Derive stats and types from the real data files, never hardcode them. This
   hack re-types and rebalances species (Gengar is GHOST/PSYCHIC here, not
   vanilla Ghost/Poison), so a fixture with baked-in numbers silently drifts
   away from the game it is supposed to be guarding.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SENTINEL_ADDR = 0xFFFD
BOOT_FRAMES = 600
RUN_BUDGET = 3000

# Haki bit positions in wBossAIRevealedMovesBitmapSpare + 1
HAKI_SPENT_F, HAKI_ACE_SEEN_F, HAKI_ELIGIBLE_F, HAKI_TRACE_F = 0, 1, 2, 3

AI_TIER_BASELINE, AI_TIER_EARLY, AI_TIER_MID, AI_TIER_LATE = 0, 1, 2, 3

# constants/battle_constants.asm: USEMOVE, USEITEM, SWITCH -- SWITCH is 2, not 1.
BATTLEPLAYERACTION_USEMOVE = 0
BATTLEPLAYERACTION_USEITEM = 1
BATTLEPLAYERACTION_SWITCH = 2

# status bit flags (constants/battle_constants.asm const_def 3)
PSN, BRN, FRZ, PAR = 1 << 3, 1 << 4, 1 << 5, 1 << 6

# wPlayerSubStatus5 / wEnemySubStatus5 bit positions. Defined here rather than
# parsed: battle_constants.asm holds dozens of independent const_def blocks, so
# whole-file parsing is fragile. Source block is
#   TOXIC=0, skip, skip, TRANSFORMED=3, ENCORED=4, LOCK_ON=5,
#   DESTINY_BOND=6, CANT_RUN=7
SUBSTATUS_ENCORED = 4
SUBSTATUS_DESTINY_BOND = 6


# ---------------------------------------------------------------- constants ---

def _parse_const_file(path: Path) -> dict[str, int]:
    """Parse a `const_def` / `const NAME` constants file into {name: value}."""
    out: dict[str, int] = {}
    value = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        m = re.match(r"const_def\s+(\d+)", s)
        if m:
            value = int(m.group(1))
            continue
        if s.startswith("const_def"):
            value = 0
            continue
        m = re.match(r"const_next\s+(\d+)", s)
        if m:
            value = int(m.group(1))
            continue
        if s.startswith("const_skip"):
            m = re.match(r"const_skip\s+(\d+)", s)
            value += int(m.group(1)) if m else 1
            continue
        m = re.match(r"const\s+([A-Z0-9_]+)", s)
        if m:
            out[m.group(1)] = value
            value += 1
    return out


def _parse_trainer_classes(path: Path) -> dict[str, int]:
    """Trainer classes use a `trainerclass NAME` macro, not `const`.

    Values come from ordinal position, matching the macro
    (`DEF \\1 EQU __trainer_class__` then `+= 1`, starting at 0). Deliberately
    ignores the trailing `; NN` comments: those are HEX, so reading them as
    decimal silently mis-values every class above 9 -- BROCK's `; 11` is 17, and
    MORTY's `; 4` happens to agree only because 0x04 == 4. That cost a debug
    cycle here; the ordinal is the authoritative source.
    """
    out: dict[str, int] = {}
    value = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"\s*MACRO\s+trainerclass", line):
            continue
        m = re.match(r"\s*trainerclass\s+([A-Z0-9_]+)", line)
        if m:
            out[m.group(1)] = value
            value += 1
    return out


MOVES = _parse_const_file(ROOT / "constants" / "move_constants.asm")
SPECIES = _parse_const_file(ROOT / "constants" / "pokemon_constants.asm")
TYPES = _parse_const_file(ROOT / "constants" / "type_constants.asm")
TRAINER_CLASSES = _parse_trainer_classes(
    ROOT / "constants" / "trainer_constants.asm")

MOVE_NAME = {v: k for k, v in MOVES.items()}
SPECIES_NAME = {v: k for k, v in SPECIES.items()}
TYPE_NAME = {v: k for k, v in TYPES.items()}


def move_name(mid: int) -> str:
    return MOVE_NAME.get(mid, f"move#{mid}") if mid else "(none)"


# --------------------------------------------------------------- base stats ---

@dataclass(frozen=True)
class BaseStats:
    species: int
    hp: int
    atk: int
    deff: int
    spe: int
    spa: int
    spd: int
    type1: int
    type2: int


def load_base_stats(name: str) -> BaseStats:
    """Read a species' real base stats and typing out of data/pokemon/base_stats.

    Deliberately sourced from the data files rather than hardcoded: this hack
    re-types and rebalances species, and a fixture that bakes in numbers stops
    describing the game the moment those change.
    """
    path = ROOT / "data" / "pokemon" / "base_stats" / f"{name.lower()}.asm"
    if not path.exists():
        raise FileNotFoundError(f"no base stats file for {name}: {path}")
    text = path.read_text(encoding="utf-8")

    m = re.search(r"^\s*db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
                  r"\s*(\d+)\s*,\s*(\d+)\s*$", text, re.M)
    if not m:
        raise ValueError(f"could not parse base stat line for {name}")
    hp, atk, deff, spe, spa, spd = (int(g) for g in m.groups())

    m = re.search(r"^\s*db\s+([A-Z_0-9]+)\s*,\s*([A-Z_0-9]+)\s*;\s*type", text, re.M)
    if not m:
        raise ValueError(f"could not parse type line for {name}")
    t1, t2 = TYPES[m.group(1)], TYPES[m.group(2)]

    return BaseStats(SPECIES[name.upper()], hp, atk, deff, spe, spa, spd, t1, t2)


def computed(base: int, level: int, iv: int = 8, is_hp: bool = False) -> int:
    """Gen 2 computed stat. Stat exp removed in this hack, so EV term is 0."""
    core = (2 * base + iv) * level // 100
    return core + level + 10 if is_hp else core + 5


# ---------------------------------------------------------------------- mon ---

@dataclass
class Mon:
    """A battle-ready mon, resolved from real base stats unless overridden."""
    species: int
    type1: int
    type2: int
    level: int
    max_hp: int
    hp: int
    atk: int
    deff: int
    spe: int
    spa: int
    spd: int
    moves: list[int] = field(default_factory=list)
    status: int = 0
    pp: int = 30

    @classmethod
    def of(cls, name: str, level: int, moves: list[str] | None = None, *,
           hp_pct: int = 100, status: int = 0,
           types: tuple[str, str] | None = None) -> "Mon":
        b = load_base_stats(name)
        max_hp = computed(b.hp, level, is_hp=True)
        t1, t2 = (b.type1, b.type2)
        if types is not None:
            t1, t2 = TYPES[types[0]], TYPES[types[1]]
        return cls(
            species=b.species, type1=t1, type2=t2, level=level,
            max_hp=max_hp, hp=max(1, max_hp * hp_pct // 100),
            atk=computed(b.atk, level), deff=computed(b.deff, level),
            spe=computed(b.spe, level), spa=computed(b.spa, level),
            spd=computed(b.spd, level),
            moves=[MOVES[m] for m in (moves or [])], status=status,
        )

    def describe(self) -> str:
        t = TYPE_NAME.get(self.type1, "?")
        if self.type2 != self.type1:
            t += "/" + TYPE_NAME.get(self.type2, "?")
        return (f"{SPECIES_NAME.get(self.species, self.species)} L{self.level} "
                f"{t} {self.hp}/{self.max_hp}")


# ------------------------------------------------------------------ harness ---

class BossAIHarness:
    """Drives boss-AI routines on the real ROM against a seeded battle state."""

    def __init__(self, sess):
        self.sess = sess
        self.pb = sess.pyboy
        self.syms = sess.symbols
        from tools.damage_debugger.safe_call import write_byte_banked
        self._wb = write_byte_banked

    # --- memory ---
    def has(self, name: str) -> bool:
        return self.syms.get(name) is not None

    def wr(self, name: str, value: int, off: int = 0) -> None:
        s = self.syms.get(name)
        if s is None:
            raise KeyError(f"{name} not in symbol table")
        self._wb(self.pb, s.address + off, value & 0xFF, s.bank)

    def wr_be16(self, name: str, value: int) -> None:
        self.wr(name, (value >> 8) & 0xFF, 0)
        self.wr(name, value & 0xFF, 1)

    def rd(self, name: str, off: int = 0) -> int:
        s = self.syms[name]
        old = int(self.pb.memory[0xFF70])
        if 0xD000 <= s.address <= 0xDFFF and s.bank:
            self.pb.memory[0xFF70] = s.bank
        try:
            return int(self.pb.memory[s.address + off])
        finally:
            self.pb.memory[0xFF70] = old

    def rd_be16(self, name: str) -> int:
        return (self.rd(name, 0) << 8) | self.rd(name, 1)

    def set_bit(self, name: str, bit: int, on: bool = True, off: int = 0) -> None:
        cur = self.rd(name, off)
        self.wr(name, (cur | (1 << bit)) if on else (cur & ~(1 << bit)), off)

    # --- state seeding ---
    def seed_mon(self, prefix: str, mon: Mon) -> None:
        """prefix is 'wBattleMon' (player) or 'wEnemyMon' (boss)."""
        self.wr(f"{prefix}Species", mon.species)
        self.wr(f"{prefix}Type1", mon.type1)
        self.wr(f"{prefix}Type1", mon.type2, 1)   # Type2 is Type1 + 1
        self.wr(f"{prefix}Level", mon.level)
        self.wr_be16(f"{prefix}MaxHP", mon.max_hp)
        self.wr_be16(f"{prefix}HP", mon.hp)
        self.wr_be16(f"{prefix}Attack", mon.atk)
        self.wr_be16(f"{prefix}Defense", mon.deff)
        self.wr_be16(f"{prefix}Speed", mon.spe)
        self.wr_be16(f"{prefix}SpclAtk", mon.spa)
        self.wr_be16(f"{prefix}SpclDef", mon.spd)
        self.wr(f"{prefix}Status", mon.status)
        for i in range(4):
            mv = mon.moves[i] if i < len(mon.moves) else 0
            self.wr(f"{prefix}Moves", mv, i)
            self.wr(f"{prefix}PP", mon.pp if mv else 0, i)

    def seed_battle(self, boss: Mon, player: Mon, *, tier: int = AI_TIER_MID,
                    scores: list[int] | None = None,
                    battle_turn: int = 1, extra: dict | None = None) -> None:
        self.wr("wBossAITier", tier)
        self.seed_mon("wEnemyMon", boss)
        self.seed_mon("wBattleMon", player)
        self.wr("wEnemyDisabledMove", 0)
        self.wr("hBattleTurn", battle_turn)
        for i in range(4):
            self.wr("wEnemyAIMoveScores", 20 if scores is None else scores[i], i)
        for key, val in (extra or {}).items():
            if isinstance(key, tuple):
                self.wr(key[0], val, key[1])
            else:
                self.wr(key, val)

    # --- invocation ---
    def invoke(self, func: str, regs: dict | None = None) -> bool:
        """Run `func` until it returns into the HRAM trap. False on no-return."""
        s = self.syms.get(func)
        if s is None:
            raise KeyError(f"{func} not in symbol table")
        pb, rf = self.pb, self.pb.register_file
        pb.memory[0xFFFF] = 0          # mask all interrupts
        pb.memory[0xFF0F] = 0          # clear pending
        pb.memory[SENTINEL_ADDR] = 0x18       # jr
        pb.memory[SENTINEL_ADDR + 1] = 0xFE   # -2
        nsp = (int(rf.SP) - 2) & 0xFFFF
        pb.memory[nsp] = SENTINEL_ADDR & 0xFF
        pb.memory[nsp + 1] = SENTINEL_ADDR >> 8
        rf.SP = nsp
        for k, v in (regs or {}).items():
            setattr(rf, k, v)
        self.wr("hROMBank", s.bank)
        pb.memory[0x2000] = s.bank
        rf.PC = s.address
        ticked = 0
        while ticked < RUN_BUDGET:
            pb.tick(2, False, False)
            ticked += 2
            if int(rf.PC) in (SENTINEL_ADDR, SENTINEL_ADDR + 2):
                return True
        return False

    # --- observation ---
    def scores(self) -> list[int]:
        return [self.rd("wEnemyAIMoveScores", i) for i in range(4)]

    def outcome(self) -> dict:
        rf = self.pb.register_file
        out = {
            "scores": self.scores(),
            "chosen_move": self.rd("wCurEnemyMove"),
            "choice_ready": self.rd("wBossAIMoveChoiceReady"),
            # Many boss-AI predicates answer in the carry flag rather than in
            # memory, so fixtures that pin a gate need to read it. Safe to read
            # after the run: the CPU is parked in the HRAM trap, and `jr -2`
            # does not touch flags.
            "carry": bool((int(rf.F) >> 4) & 1),
            "a": int(rf.A),
        }
        if self.has("wCurEnemyMoveNum"):
            out["chosen_slot"] = self.rd("wCurEnemyMoveNum")
        if self.has("wEnemySwitchMonIndex"):
            out["switch_index"] = self.rd("wEnemySwitchMonIndex")
        if self.has("wEnemySwitchMonParam"):
            out["switch_param"] = self.rd("wEnemySwitchMonParam")
        return out


def open_harness(rom: str = "pokegold"):
    """Context-manage a booted harness. Raises if PyBoy/ROM unavailable."""
    from tools.damage_debugger.emulator import DebugSession

    class _Ctx:
        def __enter__(self):
            self._sess = DebugSession.open(rom)
            self._sess.__enter__()
            self._sess.tick(BOOT_FRAMES)
            return BossAIHarness(self._sess)

        def __exit__(self, *exc):
            return self._sess.__exit__(*exc)

    return _Ctx()
