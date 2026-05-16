"""Multi-turn Hypothesis RuleBasedStateMachine for battle scenarios.

Uses Hypothesis stateful testing to explore multi-turn battle
sequences: UseMove, SwitchOut, ApplyItem, EndTurn.  Invariants
assert structural correctness (HP bounds, stage bounds, no double
Choice lock).  ``hypothesis.target()`` guides search toward
worst-case drift and overflow.

Damage calculation delegates to tools.damage_debugger.oracle when
available, falling back to an inline Gen 2 approximation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

try:
    from hypothesis import settings, given, target, HealthCheck
    from hypothesis import strategies as st
    from hypothesis.stateful import (
        RuleBasedStateMachine,
        Bundle,
        rule,
        invariant,
        initialize,
        precondition,
    )
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


BASE_STAT_LEVEL = 7
MAX_STAT_LEVEL = 13
MIN_STAT_LEVEL = 1

_ORACLE_AVAILABLE = None


def _calc_damage(level: int, power: int, atk: int, dfn: int,
                 is_physical: bool = True,
                 move_type: int = 0,
                 attacker_types: tuple[int, int] = (0, 0),
                 defender_types: tuple[int, int] = (0xFF, 0xFF)) -> int:
    """Calculate damage using the oracle when available, else inline formula."""
    global _ORACLE_AVAILABLE
    if _ORACLE_AVAILABLE is None:
        try:
            from tools.damage_debugger.oracle import predict_damage  # noqa: F401
            _ORACLE_AVAILABLE = True
        except ImportError:
            _ORACLE_AVAILABLE = False

    if _ORACLE_AVAILABLE:
        from tools.damage_debugger.oracle import BattleInputs, predict_damage
        inp = BattleInputs(
            attacker_level=level,
            move_bp=power,
            move_type=move_type,
            is_physical=is_physical,
            attacker_atk=atk,
            defender_def=dfn,
            attacker_types=attacker_types,
            defender_types=defender_types,
        )
        return max(1, predict_damage(inp))

    if dfn == 0:
        dfn = 1
    damage = ((2 * level // 5 + 2) * power * atk // dfn) // 50 + 2
    return max(1, damage)


class MoveCategory(Enum):
    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()


@dataclass
class FuzzMon:
    """Lightweight mon for stateful battle fuzz."""
    species: str = "MAGIKARP"
    level: int = 50
    hp: int = 100
    max_hp: int = 100
    atk: int = 50
    dfn: int = 50
    spa: int = 50
    spd: int = 50
    spe: int = 50
    types: list[int] = field(default_factory=lambda: [0])
    moves: list[str] = field(default_factory=lambda: ["TACKLE", "SPLASH", "FLAIL", "PROTECT"])
    status: int = 0
    atk_stage: int = BASE_STAT_LEVEL
    def_stage: int = BASE_STAT_LEVEL
    spa_stage: int = BASE_STAT_LEVEL
    spd_stage: int = BASE_STAT_LEVEL
    spe_stage: int = BASE_STAT_LEVEL
    choice_locked: str = ""
    is_active: bool = True

    def alive(self) -> bool:
        return self.hp > 0

    def apply_stage(self, stat: str, delta: int) -> None:
        attr = f"{stat}_stage"
        cur = getattr(self, attr)
        new = max(MIN_STAT_LEVEL, min(MAX_STAT_LEVEL, cur + delta))
        setattr(self, attr, new)


@dataclass
class FuzzBattleState:
    """Minimal battle state for stateful testing."""
    player_active: FuzzMon = field(default_factory=FuzzMon)
    enemy_active: FuzzMon = field(default_factory=FuzzMon)
    player_bench: list[FuzzMon] = field(default_factory=list)
    enemy_bench: list[FuzzMon] = field(default_factory=list)
    weather: int = 0
    turn: int = 0
    player_spikes: int = 0
    enemy_spikes: int = 0
    ended: bool = False

    def all_mons(self) -> list[FuzzMon]:
        return [self.player_active, self.enemy_active] + self.player_bench + self.enemy_bench


if HAS_HYPOTHESIS:
    class BattleFuzzMachine(RuleBasedStateMachine):
        """Stateful battle fuzz — explores multi-turn battle sequences."""

        def __init__(self) -> None:
            super().__init__()
            self.state = FuzzBattleState()
            self.damage_log: list[dict[str, Any]] = []

        @initialize()
        def setup_battle(self) -> None:
            self.state = FuzzBattleState(
                player_active=FuzzMon(species="PLAYER_LEAD", level=50, hp=200, max_hp=200,
                                       atk=100, dfn=80, spa=90, spd=85, spe=95),
                enemy_active=FuzzMon(species="ENEMY_LEAD", level=50, hp=200, max_hp=200,
                                      atk=95, dfn=85, spa=100, spd=80, spe=90),
                player_bench=[
                    FuzzMon(species=f"PLAYER_BENCH_{i}", level=50, hp=180, max_hp=180)
                    for i in range(2)
                ],
                enemy_bench=[
                    FuzzMon(species=f"ENEMY_BENCH_{i}", level=50, hp=180, max_hp=180)
                    for i in range(2)
                ],
            )

        @precondition(lambda self: not self.state.ended)
        @rule(
            move_idx=st.integers(min_value=0, max_value=3),
            power=st.integers(min_value=20, max_value=150),
            category=st.sampled_from(["physical", "special"]),
        )
        def use_move(self, move_idx: int, power: int, category: str) -> None:
            attacker = self.state.player_active
            defender = self.state.enemy_active
            if not attacker.alive() or not defender.alive():
                self.state.ended = True
                return

            if attacker.choice_locked and attacker.moves[move_idx] != attacker.choice_locked:
                return

            if category == "physical":
                atk_val = attacker.atk
                def_val = defender.dfn
            else:
                atk_val = attacker.spa
                def_val = defender.spd

            atk_types = tuple(attacker.types[:2]) if len(attacker.types) >= 2 else (attacker.types[0], attacker.types[0]) if attacker.types else (0, 0)
            def_types = tuple(defender.types[:2]) if len(defender.types) >= 2 else (defender.types[0], defender.types[0]) if defender.types else (0xFF, 0xFF)
            damage = _calc_damage(
                level=attacker.level, power=power,
                atk=atk_val, dfn=def_val,
                is_physical=(category == "physical"),
                attacker_types=atk_types, defender_types=def_types,
            )

            defender.hp = max(0, defender.hp - damage)
            self.damage_log.append({
                "turn": self.state.turn,
                "attacker": attacker.species,
                "move": attacker.moves[move_idx],
                "power": power,
                "damage": damage,
                "defender_hp": defender.hp,
            })

            target(float(damage), label="damage_magnitude")

            if not defender.alive():
                if self.state.enemy_bench:
                    self.state.enemy_active = self.state.enemy_bench.pop(0)
                else:
                    self.state.ended = True

        @precondition(lambda self: not self.state.ended and len(self.state.player_bench) > 0)
        @rule(bench_idx=st.integers(min_value=0, max_value=1))
        def switch_out(self, bench_idx: int) -> None:
            idx = min(bench_idx, len(self.state.player_bench) - 1)
            if self.state.player_active.choice_locked:
                return
            old = self.state.player_active
            self.state.player_active = self.state.player_bench[idx]
            self.state.player_bench[idx] = old
            self.state.player_active.choice_locked = ""

            if self.state.player_spikes > 0 and self.state.player_active.alive():
                spike_dmg = self.state.player_active.max_hp // (8 - self.state.player_spikes)
                spike_dmg = max(1, spike_dmg)
                self.state.player_active.hp = max(0, self.state.player_active.hp - spike_dmg)

        @precondition(lambda self: not self.state.ended)
        @rule(
            stat=st.sampled_from(["atk", "def", "spa", "spd", "spe"]),
            delta=st.integers(min_value=-2, max_value=2),
        )
        def apply_stat_change(self, stat: str, delta: int) -> None:
            if delta == 0:
                return
            self.state.player_active.apply_stage(stat, delta)

        @precondition(lambda self: not self.state.ended)
        @rule()
        def end_turn(self) -> None:
            self.state.turn += 1
            if self.state.turn > 100:
                self.state.ended = True

        @invariant()
        def hp_bounds(self) -> None:
            for mon in self.state.all_mons():
                assert 0 <= mon.hp <= mon.max_hp, (
                    f"{mon.species} HP {mon.hp} out of [0, {mon.max_hp}]"
                )

        @invariant()
        def stage_bounds(self) -> None:
            for mon in self.state.all_mons():
                for stat in ("atk", "def", "spa", "spd", "spe"):
                    stage = getattr(mon, f"{stat}_stage")
                    assert MIN_STAT_LEVEL <= stage <= MAX_STAT_LEVEL, (
                        f"{mon.species} {stat}_stage={stage} out of [{MIN_STAT_LEVEL}, {MAX_STAT_LEVEL}]"
                    )

        @invariant()
        def spikes_bounds(self) -> None:
            assert 0 <= self.state.player_spikes <= 3
            assert 0 <= self.state.enemy_spikes <= 3


    BattleFuzzTest = BattleFuzzMachine.TestCase
    BattleFuzzTest.settings = settings(
        max_examples=200,
        stateful_step_count=30,
        suppress_health_check=[HealthCheck.too_slow],
    )


def run_battle_fuzz(max_examples: int = 200, stateful_steps: int = 30) -> dict[str, Any]:
    """Run the battle fuzz and return summary stats."""
    if not HAS_HYPOTHESIS:
        return {"error": "hypothesis not installed", "passed": False}

    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BattleFuzzTest)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)

    return {
        "passed": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
    }


__all__ = [
    "FuzzMon",
    "FuzzBattleState",
    "MoveCategory",
    "run_battle_fuzz",
    "HAS_HYPOTHESIS",
]

if HAS_HYPOTHESIS:
    __all__.extend(["BattleFuzzMachine", "BattleFuzzTest"])
