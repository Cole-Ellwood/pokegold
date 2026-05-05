"""Bug-hunt sweeper: vary one input at a time, compare live to oracle.

The Gen 2 damage formula:

    D = (((2*L/5 + 2) * A * P / Def) / 50 + 2)
    D *= STAB              # 1.5x normally, 1.6x or 1.55x for type-passive (this hack)
    D *= Type              # 1.0/2.0/4.0/0.5/0.25/0.0
    D *= Crit              # 1.0 or 2.0
    D *= ItemMod           # 1.1 for type-boosting items in vanilla Gen 2;
                           # this hack adds Choice/Assault Vest etc.
    D *= Random / 255      # 0.85..1.0 (we set this to 255 for max determinism)

Stat-stage modifiers apply to A (attacker's effective Atk) and Def
(defender's effective Def) BEFORE the formula runs. Multipliers per stage:
    +1 = 1.5, +2 = 2.0, +3 = 2.5, +4 = 3.0, +5 = 3.5, +6 = 4.0
    -1 = 0.66 (=2/3), -2 = 0.5, -3 = 0.4, -4 = 0.33, -5 = 0.28 (=2/7), -6 = 0.25

CLAUDE.md confirms these multipliers and notes wEnemySpdLevel etc. uses
base-7 encoding (BASE_STAT_LEVEL=7=+0).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable

from .synth import SynthBattle, SynthMon, SynthMove, run_synth


# Type IDs in Gen 2 (verify against constants/type_constants.asm)
TYPE_NORMAL = 0x00
TYPE_FIGHTING = 0x01
TYPE_FLYING = 0x02
TYPE_POISON = 0x03
TYPE_GROUND = 0x04
TYPE_ROCK = 0x05
TYPE_BUG = 0x07
TYPE_GHOST = 0x08
TYPE_STEEL = 0x09
TYPE_FIRE = 0x14
TYPE_WATER = 0x15
TYPE_GRASS = 0x16
TYPE_ELECTRIC = 0x17
TYPE_PSYCHIC = 0x18
TYPE_ICE = 0x19
TYPE_DRAGON = 0x1A
TYPE_DARK = 0x1B


# Stat-stage multiplier (numerator/denominator pairs) — base-7 encoded
# input. Output: (num, den) so we get exact integer ops.
_STAGE_MULTIPLIERS = {
    13: (4, 1),  # +6
    12: (7, 2),  # +5: 3.5
    11: (3, 1),  # +4: 3.0
    10: (5, 2),  # +3: 2.5
    9: (2, 1),   # +2: 2.0
    8: (3, 2),   # +1: 1.5
    7: (1, 1),   # +0
    6: (2, 3),   # -1: 0.66
    5: (1, 2),   # -2: 0.5
    4: (2, 5),   # -3: 0.4
    3: (1, 3),   # -4: 0.33
    2: (2, 7),   # -5: 0.28
    1: (1, 4),   # -6: 0.25
}


@dataclass
class OracleResult:
    base_damage: int
    after_stab: int
    after_type: int
    after_crit: int
    after_item: int
    final: int
    notes: list[str] = field(default_factory=list)


def apply_stage(value: int, stage: int) -> int:
    num, den = _STAGE_MULTIPLIERS[stage]
    return (value * num) // den


def has_stab(attacker_t1: int, attacker_t2: int, move_type: int) -> bool:
    return move_type == attacker_t1 or move_type == attacker_t2


def python_oracle(battle: SynthBattle, *, stab_mult: tuple[int, int] = (3, 2),
                  type_passive_active: bool = False) -> OracleResult:
    """Compute expected damage from the input. Pure Python; no emulator."""
    notes: list[str] = []
    is_p = battle.is_player_turn
    attacker = battle.player if is_p else battle.enemy
    defender = battle.enemy if is_p else battle.player

    # Effective attack (apply stat stage)
    eff_atk = apply_stage(attacker.attack, attacker.atk_stage)
    eff_def = apply_stage(defender.defense, defender.def_stage)
    if eff_def == 0:
        eff_def = 1

    L = attacker.level
    P = battle.move.power
    inner = (2 * L) // 5 + 2
    base = ((inner * eff_atk * P) // eff_def) // 50 + 2
    notes.append(f"L={L} P={P} eff_atk={eff_atk} eff_def={eff_def} inner={inner} base={base}")

    after_stab = base
    if has_stab(attacker.type1, attacker.type2, battle.move.type):
        # Vanilla 1.5x = 3/2; type-passive variants in this hack: 1.6x=8/5 or 1.55x=31/20
        if type_passive_active:
            # We don't know which without reading the source — start with 1.5 then sweep
            after_stab = (base * 8) // 5
            notes.append("STAB×1.6 (type-passive variant)")
        else:
            after_stab = (base * stab_mult[0]) // stab_mult[1]
            notes.append(f"STAB×{stab_mult[0]}/{stab_mult[1]}")
    else:
        notes.append("no STAB")

    # Type effectiveness (caller supplies; 0x10 = 1.0, 0x20 = 2.0, 0x08 = 0.5, etc.)
    te = battle.type_effectiveness
    after_type = (after_stab * te) // 0x10
    notes.append(f"type_eff×{te:#04x}/0x10")

    # Critical hit
    after_crit = after_type * (2 if battle.is_critical else 1)
    if battle.is_critical:
        notes.append("crit×2")

    # Item modifier — start with no item (1.0) since we'd need item data
    after_item = after_crit
    if attacker.item:
        notes.append(f"item={attacker.item:#04x} (oracle assumes 1.0×)")

    # Damage clamp at 1 if positive base; the asm has special-case for 0 power.
    final = after_item
    if final < 1 and base > 0:
        final = 1

    return OracleResult(
        base_damage=base,
        after_stab=after_stab,
        after_type=after_type,
        after_crit=after_crit,
        after_item=after_item,
        final=final,
        notes=notes,
    )


@dataclass
class SweepRow:
    name: str
    live: int | None
    oracle: int
    delta: int
    ratio: float
    notes: str
    boot_frames: int = 240


def make_baseline() -> SynthBattle:
    """Lvl-50 vs lvl-50, base 100 stats, 50-power Rock move, no STAB, neutral type."""
    return SynthBattle(
        name="baseline",
        player=SynthMon(level=50, attack=100, defense=100, type1=TYPE_FIRE, type2=TYPE_FIRE),
        enemy=SynthMon(level=50, attack=100, defense=100, type1=TYPE_NORMAL, type2=TYPE_NORMAL),
        move=SynthMove(power=50, type=TYPE_ROCK, effect=0),
        type_effectiveness=0x10,
    )


def variants() -> Iterable[SynthBattle]:
    """All single-variable variations from baseline."""
    yield make_baseline()

    # STAB: ROCK move with ROCK attacker
    b = make_baseline(); b.name = "stab_only"
    b.player.type1 = TYPE_ROCK; b.player.type2 = TYPE_ROCK
    yield b

    # Type effectiveness 2.0x
    b = make_baseline(); b.name = "super_effective_2x"
    b.type_effectiveness = 0x20
    yield b

    # Type effectiveness 4.0x (double weakness)
    b = make_baseline(); b.name = "super_effective_4x"
    b.type_effectiveness = 0x40
    yield b

    # Type effectiveness 0.5x
    b = make_baseline(); b.name = "not_very_effective"
    b.type_effectiveness = 0x08
    yield b

    # Critical hit
    b = make_baseline(); b.name = "critical_hit"
    b.is_critical = True
    yield b

    # Stat stage +1 attack
    b = make_baseline(); b.name = "atk_plus_1"
    b.player.atk_stage = 8
    yield b

    # Stat stage +2 attack
    b = make_baseline(); b.name = "atk_plus_2"
    b.player.atk_stage = 9
    yield b

    # Stat stage -1 defender def
    b = make_baseline(); b.name = "enemy_def_minus_1"
    b.enemy.def_stage = 6
    yield b

    # FIRE STAB (the type-passive STAB this hack changes)
    b = make_baseline(); b.name = "stab_fire_normal_attacker"
    # Player is FIRE/FIRE, give them a FIRE move
    b.move.type = TYPE_FIRE
    yield b

    # FIRE attacker dual-type FIRE/FLYING (per type_passives_smoketests.md doc:
    # "Dual-type user including Normal with a Normal damaging move: 1.55x")
    b = make_baseline(); b.name = "stab_fire_dual_flying"
    b.player.type1 = TYPE_FIRE; b.player.type2 = TYPE_FLYING
    b.move.type = TYPE_FIRE
    yield b

    # Late-gen item variants — these probe the new-mechanic surface that
    # ApplyLateGenDamageMultipliers_Far handles (called from inside DamageCalc
    # at effect_commands.asm:2924).
    ITEM_LIFE_ORB = 0x46
    ITEM_CHOICE_BAND = 0x74
    ITEM_CHOICE_SPECS = 0x81
    ITEM_ASSAULT_VEST = 0x89
    ITEM_EXPERT_BELT = 0x8D
    ITEM_MUSCLE_BAND = 0x8E
    ITEM_WISE_GLASSES = 0x91
    ITEM_METRONOME = 0x9A

    b = make_baseline(); b.name = "item_muscle_band"
    b.player.item = ITEM_MUSCLE_BAND
    yield b

    b = make_baseline(); b.name = "item_life_orb"
    b.player.item = ITEM_LIFE_ORB
    yield b

    b = make_baseline(); b.name = "item_wise_glasses_phys"
    b.player.item = ITEM_WISE_GLASSES  # WG only fires on special; expect 1.0×
    yield b

    b = make_baseline(); b.name = "item_choice_band_via_damagecalc_only"
    b.player.item = ITEM_CHOICE_BAND  # CB applies in DamageStats, not DamageCalc;
                                       # synth that only calls DamageCalc => 1.0×
    yield b

    b = make_baseline(); b.name = "item_metronome"
    b.player.item = ITEM_METRONOME
    yield b

    b = make_baseline(); b.name = "item_expert_belt_neutral"
    b.player.item = ITEM_EXPERT_BELT
    b.type_effectiveness = 0x10  # neutral, EB shouldn't fire
    yield b

    b = make_baseline(); b.name = "item_expert_belt_super_eff"
    b.player.item = ITEM_EXPERT_BELT
    b.type_effectiveness = 0x20  # 2× super effective, EB should fire
    yield b


FULL_CHAIN = (
    "BattleCommand_Critical",
    "BattleCommand_DamageStats",
    "BattleCommand_DamageCalc",
    "BattleCommand_Stab",
    # damagevariation skipped for determinism
)

# DamageCalc-only chain probes the inner formula AND
# ApplyLateGenDamageMultipliers_Far (called from inside it at line 2924).
DAMAGECALC_ONLY = ("BattleCommand_DamageCalc",)


def run_sweep(*, chain: tuple[str, ...] = DAMAGECALC_ONLY) -> list[SweepRow]:
    rows: list[SweepRow] = []
    for battle in variants():
        oracle = python_oracle(battle)
        try:
            res = run_synth(battle, chain=chain)
            live = res["cur_damage"]
            per_step = res.get("per_step", [])
            step_str = " ".join(f"{s['fn'].replace('BattleCommand_','')}={s['wCurDamage']}" for s in per_step)
        except Exception as exc:
            rows.append(SweepRow(
                name=battle.name, live=None, oracle=oracle.final,
                delta=0, ratio=0.0,
                notes=f"ERROR: {exc}",
            ))
            continue
        delta = (live - oracle.final) if live is not None else 0
        ratio = (live / oracle.final) if (live and oracle.final) else 0.0
        rows.append(SweepRow(
            name=battle.name,
            live=live,
            oracle=oracle.final,
            delta=delta,
            ratio=ratio,
            notes=step_str + " | " + " / ".join(oracle.notes),
        ))
    return rows


def main() -> int:
    rows = run_sweep()
    out_dir = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sweep.md"

    lines = ["# Damage debugger sweep", "",
             "| scenario | live | oracle | delta | ratio | notes |",
             "|----------|-----:|-------:|------:|------:|-------|"]
    print(f"{'scenario':30s} {'live':>6s} {'oracle':>6s} {'delta':>6s} {'ratio':>6s}  notes")
    print("-" * 100)
    for r in rows:
        live = "ERR" if r.live is None else str(r.live)
        ratio = f"{r.ratio:.2f}" if r.ratio else "-"
        print(f"{r.name:30s} {live:>6s} {r.oracle:>6d} {r.delta:>+6d} {ratio:>6s}  {r.notes}")
        lines.append(f"| `{r.name}` | {live} | {r.oracle} | {r.delta:+d} | {ratio} | {r.notes} |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport: {out_path}")

    diverged = [r for r in rows if r.live is not None and r.live != r.oracle]
    if diverged:
        print(f"\n*** {len(diverged)} divergent scenario(s) — likely bug surface:")
        for r in diverged:
            print(f"  - {r.name}: live={r.live} oracle={r.oracle} ratio={r.ratio:.2f}")
        return 1
    print("\nAll scenarios match oracle.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
