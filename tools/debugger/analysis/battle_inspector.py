"""Live battle state inspector — one-page summary a non-coder can read.

Renders mons + stages + status + weather + damage context from a
WorldState or raw WRAM snapshot. This is the P5 "one-page summary"
deliverable.

Usage:
    from tools.debugger.analysis.battle_inspector import BattleInspector
    inspector = BattleInspector(svc)
    print(inspector.render_text(wram_bytes))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..kernel.symbol_service import SymbolService


BASE_STAT_LEVEL = 7
MAX_STAT_LEVEL = 13

STAGE_LABELS = {
    1: "-6", 2: "-5", 3: "-4", 4: "-3", 5: "-2", 6: "-1",
    7: "+0", 8: "+1", 9: "+2", 10: "+3", 11: "+4", 12: "+5", 13: "+6",
}

STATUS_BITS = {
    0: "SLP", 1: "SLP", 2: "SLP",
    3: "PSN",
    4: "BRN",
    5: "FRZ",
    6: "PAR",
}

WEATHER_NAMES = {0: "None", 1: "Rain", 2: "Sun", 3: "Sandstorm"}

TYPE_NAMES = {
    0x00: "Normal", 0x01: "Fighting", 0x02: "Flying", 0x03: "Poison",
    0x04: "Ground", 0x05: "Rock", 0x07: "Bug", 0x08: "Ghost",
    0x09: "Steel", 0x14: "Fire", 0x15: "Water", 0x16: "Grass",
    0x17: "Electric", 0x18: "Psychic", 0x19: "Ice", 0x1A: "Dragon",
    0x1B: "Dark",
}


def _read_byte(wram: bytes, addr: int, wram_base: int = 0xC000) -> int:
    offset = addr - wram_base
    if 0 <= offset < len(wram):
        return wram[offset]
    return 0


def _read_word_be(wram: bytes, addr: int, wram_base: int = 0xC000) -> int:
    """Big-endian word read (battle-engine stat fields are runtime BE)."""
    hi = _read_byte(wram, addr, wram_base)
    lo = _read_byte(wram, addr + 1, wram_base)
    return (hi << 8) | lo


def _read_word_le(wram: bytes, addr: int, wram_base: int = 0xC000) -> int:
    lo = _read_byte(wram, addr, wram_base)
    hi = _read_byte(wram, addr + 1, wram_base)
    return (hi << 8) | lo


def _decode_status(byte: int) -> str:
    if byte == 0:
        return "OK"
    slp = byte & 0x07
    if slp > 0:
        return f"SLP({slp})"
    parts = []
    for bit, name in STATUS_BITS.items():
        if bit >= 3 and (byte & (1 << bit)):
            parts.append(name)
    return "/".join(parts) if parts else f"???({byte:02x})"


def _decode_stage(byte: int) -> str:
    if byte < 1 or byte > MAX_STAT_LEVEL:
        return f"?({byte})"
    return STAGE_LABELS.get(byte, f"?({byte})")


@dataclass
class MonSnapshot:
    """One battler's visible state."""
    side: str
    species_id: int = 0
    level: int = 0
    hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0
    sp_attack: int = 0
    sp_defense: int = 0
    type1: int = 0
    type2: int = 0
    status: int = 0
    atk_stage: int = 7
    def_stage: int = 7
    spd_stage: int = 7
    spa_stage: int = 7
    spd_stage_def: int = 7
    accuracy_stage: int = 7
    evasion_stage: int = 7

    @property
    def hp_pct(self) -> int:
        if self.max_hp <= 0:
            return 0
        return self.hp * 100 // self.max_hp

    @property
    def type_str(self) -> str:
        t1 = TYPE_NAMES.get(self.type1, f"?{self.type1:02x}")
        t2 = TYPE_NAMES.get(self.type2, f"?{self.type2:02x}")
        if self.type1 == self.type2:
            return t1
        return f"{t1}/{t2}"

    @property
    def status_str(self) -> str:
        return _decode_status(self.status)


@dataclass
class BattleSnapshot:
    """Full battle state at one moment."""
    player: MonSnapshot = field(default_factory=lambda: MonSnapshot("Player"))
    enemy: MonSnapshot = field(default_factory=lambda: MonSnapshot("Enemy"))
    weather: int = 0
    weather_count: int = 0
    turn: int = 0
    cur_damage: int = 0
    type_modifier: int = 0

    @property
    def weather_str(self) -> str:
        return WEATHER_NAMES.get(self.weather, f"?({self.weather})")


class BattleInspector:
    """Builds a BattleSnapshot from WRAM bytes using the symbol service."""

    _PLAYER_SYMBOLS = {
        "hp": "wBattleMonHP",
        "max_hp": "wBattleMonMaxHP",
        "attack": "wBattleMonAttack",
        "defense": "wBattleMonDefense",
        "speed": "wBattleMonSpeed",
        "sp_attack": "wBattleMonSpclAtk",
        "sp_defense": "wBattleMonSpclDef",
        "type1": "wBattleMonType1",
        "type2": "wBattleMonType2",
        "level": "wBattleMonLevel",
        "status": "wBattleMonStatus",
        "species": "wBattleMonSpecies",
    }

    _ENEMY_SYMBOLS = {
        "hp": "wEnemyMonHP",
        "max_hp": "wEnemyMonMaxHP",
        "attack": "wEnemyMonAttack",
        "defense": "wEnemyMonDefense",
        "speed": "wEnemyMonSpeed",
        "sp_attack": "wEnemyMonSpclAtk",
        "sp_defense": "wEnemyMonSpclDef",
        "type1": "wEnemyMonType1",
        "type2": "wEnemyMonType2",
        "level": "wEnemyMonLevel",
        "status": "wEnemyMonStatus",
        "species": "wEnemyMonSpecies",
    }

    _PLAYER_STAGES = {
        "atk": "wPlayerAtkLevel",
        "def": "wPlayerDefLevel",
        "spd": "wPlayerSpdLevel",
        "spa": "wPlayerSAtkLevel",
        "spd_def": "wPlayerSDefLevel",
        "acc": "wPlayerAccLevel",
        "eva": "wPlayerEvaLevel",
    }

    _ENEMY_STAGES = {
        "atk": "wEnemyAtkLevel",
        "def": "wEnemyDefLevel",
        "spd": "wEnemySpdLevel",
        "spa": "wEnemySAtkLevel",
        "spd_def": "wEnemySDefLevel",
        "acc": "wEnemyAccLevel",
        "eva": "wEnemyEvaLevel",
    }

    def __init__(self, svc: SymbolService) -> None:
        self._svc = svc
        self._addr_cache: dict[str, int | None] = {}

    def _addr(self, name: str) -> int | None:
        if name not in self._addr_cache:
            sym = self._svc.resolve(name)
            self._addr_cache[name] = sym.address if sym else None
        return self._addr_cache[name]

    def _read_stat(self, wram: bytes, sym_name: str) -> int:
        addr = self._addr(sym_name)
        if addr is None:
            return 0
        return _read_word_be(wram, addr)

    def _read_b(self, wram: bytes, sym_name: str) -> int:
        addr = self._addr(sym_name)
        if addr is None:
            return 0
        return _read_byte(wram, addr)

    def _build_mon(
        self, wram: bytes, side: str,
        sym_map: dict[str, str],
        stage_map: dict[str, str],
    ) -> MonSnapshot:
        mon = MonSnapshot(side=side)
        mon.species_id = self._read_b(wram, sym_map["species"])
        mon.level = self._read_b(wram, sym_map["level"])
        mon.hp = self._read_stat(wram, sym_map["hp"])
        mon.max_hp = self._read_stat(wram, sym_map["max_hp"])
        mon.attack = self._read_stat(wram, sym_map["attack"])
        mon.defense = self._read_stat(wram, sym_map["defense"])
        mon.speed = self._read_stat(wram, sym_map["speed"])
        mon.sp_attack = self._read_stat(wram, sym_map["sp_attack"])
        mon.sp_defense = self._read_stat(wram, sym_map["sp_defense"])
        mon.type1 = self._read_b(wram, sym_map["type1"])
        mon.type2 = self._read_b(wram, sym_map["type2"])
        mon.status = self._read_b(wram, sym_map["status"])
        mon.atk_stage = self._read_b(wram, stage_map["atk"])
        mon.def_stage = self._read_b(wram, stage_map["def"])
        mon.spd_stage = self._read_b(wram, stage_map["spd"])
        mon.spa_stage = self._read_b(wram, stage_map["spa"])
        mon.spd_stage_def = self._read_b(wram, stage_map["spd_def"])
        mon.accuracy_stage = self._read_b(wram, stage_map["acc"])
        mon.evasion_stage = self._read_b(wram, stage_map["eva"])
        return mon

    def inspect(self, wram: bytes) -> BattleSnapshot:
        snap = BattleSnapshot()
        snap.player = self._build_mon(
            wram, "Player", self._PLAYER_SYMBOLS, self._PLAYER_STAGES,
        )
        snap.enemy = self._build_mon(
            wram, "Enemy", self._ENEMY_SYMBOLS, self._ENEMY_STAGES,
        )
        snap.weather = self._read_b(wram, "wBattleWeather")
        snap.weather_count = self._read_b(wram, "wWeatherCount")
        snap.cur_damage = self._read_stat(wram, "wCurDamage")

        type_mod_addr = self._addr("wTypeModifier")
        if type_mod_addr is not None:
            snap.type_modifier = _read_byte(wram, type_mod_addr)

        return snap

    def render_text(self, wram: bytes) -> str:
        snap = self.inspect(wram)
        return format_battle_snapshot(snap)


def _format_mon_block(mon: MonSnapshot) -> list[str]:
    lines = [
        f"  Species: #{mon.species_id}  Lv{mon.level}  [{mon.type_str}]",
        f"  HP: {mon.hp}/{mon.max_hp} ({mon.hp_pct}%)  Status: {mon.status_str}",
        f"  Atk:{mon.attack:>4}  Def:{mon.defense:>4}  Spd:{mon.speed:>4}",
        f"  SpA:{mon.sp_attack:>4}  SpD:{mon.sp_defense:>4}",
    ]
    stages = []
    for label, val in [
        ("Atk", mon.atk_stage), ("Def", mon.def_stage),
        ("Spd", mon.spd_stage), ("SpA", mon.spa_stage),
        ("SpD", mon.spd_stage_def),
        ("Acc", mon.accuracy_stage), ("Eva", mon.evasion_stage),
    ]:
        decoded = _decode_stage(val)
        if decoded != "+0":
            stages.append(f"{label}{decoded}")
    if stages:
        lines.append(f"  Stages: {', '.join(stages)}")
    else:
        lines.append("  Stages: all neutral")
    return lines


def format_battle_snapshot(snap: BattleSnapshot) -> str:
    lines = ["=== Battle State ===", ""]

    lines.append(f"--- {snap.player.side} ---")
    lines.extend(_format_mon_block(snap.player))
    lines.append("")

    lines.append(f"--- {snap.enemy.side} ---")
    lines.extend(_format_mon_block(snap.enemy))
    lines.append("")

    lines.append("--- Field ---")
    weather_str = snap.weather_str
    if snap.weather_count > 0:
        weather_str += f" ({snap.weather_count} turns)"
    lines.append(f"  Weather: {weather_str}")
    if snap.cur_damage > 0:
        lines.append(f"  Last damage: {snap.cur_damage}")
    if snap.type_modifier != 0:
        lines.append(f"  Type modifier: ${snap.type_modifier:02x}")

    return "\n".join(lines)


def format_battle_markdown(snap: BattleSnapshot) -> str:
    lines = ["### Battle State", ""]

    lines.append("| | Player | Enemy |")
    lines.append("|---|---|---|")
    p, e = snap.player, snap.enemy
    lines.append(f"| Species | #{p.species_id} Lv{p.level} | #{e.species_id} Lv{e.level} |")
    lines.append(f"| Type | {p.type_str} | {e.type_str} |")
    lines.append(f"| HP | {p.hp}/{p.max_hp} ({p.hp_pct}%) | {e.hp}/{e.max_hp} ({e.hp_pct}%) |")
    lines.append(f"| Status | {p.status_str} | {e.status_str} |")
    lines.append(f"| Atk | {p.attack} | {e.attack} |")
    lines.append(f"| Def | {p.defense} | {e.defense} |")
    lines.append(f"| Spd | {p.speed} | {e.speed} |")
    lines.append(f"| SpA | {p.sp_attack} | {e.sp_attack} |")
    lines.append(f"| SpD | {p.sp_defense} | {e.sp_defense} |")

    lines.append("")
    lines.append(f"**Weather:** {snap.weather_str}")
    if snap.cur_damage > 0:
        lines.append(f"**Last damage:** {snap.cur_damage}")

    return "\n".join(lines)
