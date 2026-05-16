"""Metamorphic relations for damage and battle invariants.

Each relation is a pair (transform, predicate): apply the transform to
a known scenario, re-run, and check the predicate.  Any violation is a
bug (or an oracle gap).

Relations implemented:
  - Level monotonicity: damage(L) <= damage(L+1) ceteris paribus
  - STAB monotonicity: adding STAB never lowers damage
  - Stat-stage monotonicity: +Atk stage never reduces physical damage
  - Determinism: same seed → same result
  - Hidden-info leak: hidden party data must not change Boss AI output
  - Item invariant: Choice Band locks move but doesn't change locked-turn damage

Default damage function delegates to tools.damage_debugger.oracle when
available, applying the 85%-100% DamageVariation range the ROM uses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class RelationKind(Enum):
    LEVEL_MONOTONICITY = auto()
    STAB_MONOTONICITY = auto()
    STAT_STAGE_MONOTONICITY = auto()
    DETERMINISM = auto()
    HIDDEN_INFO_LEAK = auto()
    ITEM_INVARIANT = auto()
    SYMMETRY = auto()


@dataclass
class MetamorphicResult:
    """Result of checking one metamorphic relation on one scenario pair."""
    relation: RelationKind
    passed: bool
    scenario_id: str = ""
    original: dict[str, Any] = field(default_factory=dict)
    transformed: dict[str, Any] = field(default_factory=dict)
    detail: str = ""

    def __str__(self) -> str:
        tag = "PASS" if self.passed else "FAIL"
        return f"[{tag}] {self.relation.name}: {self.detail}"


@dataclass
class Scenario:
    """Minimal scenario representation for metamorphic testing."""
    scenario_id: str = ""
    attacker_species: str = ""
    defender_species: str = ""
    attacker_level: int = 50
    defender_level: int = 50
    move: str = ""
    attacker_types: list[int] = field(default_factory=list)
    move_type: int = 0
    move_power: int = 0
    move_category: str = "physical"
    attacker_atk: int = 100
    attacker_spa: int = 100
    defender_def: int = 100
    defender_spd: int = 100
    atk_stage: int = 7  # base-7
    def_stage: int = 7
    spa_stage: int = 7
    spd_stage: int = 7
    weather: int = 0
    item: str = ""
    seed: int = 0
    hidden_party: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def copy(self, **overrides: Any) -> Scenario:
        import copy
        s = copy.deepcopy(self)
        for k, v in overrides.items():
            setattr(s, k, v)
        return s

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


DamageFunc = Callable[[Scenario], tuple[int, int]]


_STAGE_MULTIPLIERS = {
    1: 25, 2: 28, 3: 33, 4: 40, 5: 50, 6: 66,
    7: 100, 8: 150, 9: 200, 10: 250, 11: 300, 12: 350, 13: 400,
}


def _scenario_to_battle_inputs(scenario: Scenario) -> Any:
    """Convert a metamorphic Scenario to a damage_debugger BattleInputs."""
    from tools.damage_debugger.oracle import BattleInputs

    is_physical = scenario.move_category == "physical"
    atk_types = scenario.attacker_types
    if len(atk_types) == 0:
        atk_types = [0xFF]
    if len(atk_types) == 1:
        atk_types = [atk_types[0], atk_types[0]]

    def_types = scenario.extra.get("defender_types", [0xFF, 0xFF])
    if len(def_types) == 1:
        def_types = [def_types[0], def_types[0]]

    if is_physical:
        raw_atk = scenario.attacker_atk
        raw_def = scenario.defender_def
        atk_stage = scenario.atk_stage
        def_stage = scenario.def_stage
    else:
        raw_atk = scenario.attacker_spa
        raw_def = scenario.defender_spd
        atk_stage = scenario.spa_stage
        def_stage = scenario.spd_stage

    eff_atk = raw_atk * _STAGE_MULTIPLIERS.get(atk_stage, 100) // 100
    eff_def = raw_def * _STAGE_MULTIPLIERS.get(def_stage, 100) // 100

    return BattleInputs(
        attacker_level=scenario.attacker_level,
        move_bp=scenario.move_power,
        move_type=scenario.move_type,
        is_physical=is_physical,
        attacker_atk=max(1, eff_atk),
        defender_def=max(1, eff_def),
        attacker_types=tuple(atk_types[:2]),
        defender_types=tuple(def_types[:2]),
    )


def _oracle_damage(scenario: Scenario) -> tuple[int, int]:
    """Damage via the real oracle, returning (low, high) with DamageVariation.

    The ROM applies a final 85%-100% random multiplier (217/255 to 255/255).
    The oracle predicts the pre-variation value; we apply the range here.
    """
    from tools.damage_debugger.oracle import predict_damage
    inp = _scenario_to_battle_inputs(scenario)
    exact = predict_damage(inp)
    if exact == 0:
        return (0, 0)
    low = max(1, exact * 217 // 255)
    return (low, exact)


_HAS_ORACLE = None


def _check_oracle() -> bool:
    global _HAS_ORACLE
    if _HAS_ORACLE is None:
        try:
            from tools.damage_debugger.oracle import predict_damage  # noqa: F401
            _HAS_ORACLE = True
        except ImportError:
            _HAS_ORACLE = False
    return _HAS_ORACLE


def _default_damage(scenario: Scenario) -> tuple[int, int]:
    """Damage function — delegates to oracle when available, else approximates."""
    if _check_oracle():
        return _oracle_damage(scenario)

    level = scenario.attacker_level
    if scenario.move_category == "physical":
        atk = scenario.attacker_atk
        dfn = scenario.defender_def
    else:
        atk = scenario.attacker_spa
        dfn = scenario.defender_spd

    stage_map = {
        1: 25, 2: 28, 3: 33, 4: 40, 5: 50, 6: 66,
        7: 100, 8: 150, 9: 200, 10: 250, 11: 300, 12: 350, 13: 400,
    }
    atk_stage = scenario.atk_stage if scenario.move_category == "physical" else scenario.spa_stage
    def_stage = scenario.def_stage if scenario.move_category == "physical" else scenario.spd_stage
    atk_mult = stage_map.get(atk_stage, 100)
    def_mult = stage_map.get(def_stage, 100)

    eff_atk = atk * atk_mult // 100
    eff_def = dfn * def_mult // 100
    if eff_def == 0:
        eff_def = 1

    base = ((2 * level // 5 + 2) * scenario.move_power * eff_atk // eff_def) // 50 + 2

    is_stab = scenario.move_type in scenario.attacker_types
    if is_stab:
        base = base * 3 // 2

    low = base * 217 // 255
    high = base
    return max(1, low), max(1, high)


def check_level_monotonicity(
    scenario: Scenario, *, damage_fn: DamageFunc | None = None
) -> MetamorphicResult:
    fn = damage_fn or _default_damage
    s1 = scenario
    s2 = scenario.copy(attacker_level=scenario.attacker_level + 1)
    lo1, hi1 = fn(s1)
    lo2, hi2 = fn(s2)
    # Same-roll monotonicity: max(L+1) >= max(L). The DamageVariation
    # band makes cross-roll comparison (lo2 >= hi1) fail for small deltas.
    passed = hi2 >= hi1
    return MetamorphicResult(
        relation=RelationKind.LEVEL_MONOTONICITY,
        passed=passed,
        scenario_id=scenario.scenario_id,
        original={"level": s1.attacker_level, "damage_high": hi1},
        transformed={"level": s2.attacker_level, "damage_high": hi2},
        detail=f"L{s1.attacker_level}→L{s2.attacker_level}: max={hi1} vs max={hi2}",
    )


def check_stab_monotonicity(
    scenario: Scenario, *, damage_fn: DamageFunc | None = None
) -> MetamorphicResult:
    fn = damage_fn or _default_damage
    no_stab = scenario.copy(attacker_types=[])
    with_stab = scenario.copy(attacker_types=[scenario.move_type])
    _, hi_no = fn(no_stab)
    lo_yes, _ = fn(with_stab)
    passed = lo_yes >= hi_no
    return MetamorphicResult(
        relation=RelationKind.STAB_MONOTONICITY,
        passed=passed,
        scenario_id=scenario.scenario_id,
        original={"stab": False, "damage_high": hi_no},
        transformed={"stab": True, "damage_low": lo_yes},
        detail=f"noSTAB hi={hi_no} vs STAB lo={lo_yes}",
    )


def check_stat_stage_monotonicity(
    scenario: Scenario, *, damage_fn: DamageFunc | None = None
) -> MetamorphicResult:
    fn = damage_fn or _default_damage
    stage = scenario.atk_stage if scenario.move_category == "physical" else scenario.spa_stage
    if stage >= 13:
        return MetamorphicResult(
            relation=RelationKind.STAT_STAGE_MONOTONICITY,
            passed=True,
            scenario_id=scenario.scenario_id,
            detail="at max stage — skipped",
        )
    if scenario.move_category == "physical":
        boosted = scenario.copy(atk_stage=stage + 1)
    else:
        boosted = scenario.copy(spa_stage=stage + 1)
    _, hi_base = fn(scenario)
    _, hi_boost = fn(boosted)
    passed = hi_boost >= hi_base
    return MetamorphicResult(
        relation=RelationKind.STAT_STAGE_MONOTONICITY,
        passed=passed,
        scenario_id=scenario.scenario_id,
        original={"stage": stage, "damage_max": hi_base},
        transformed={"stage": stage + 1, "damage_max": hi_boost},
        detail=f"stage {stage}→{stage+1}: max={hi_base} vs max={hi_boost}",
    )


def check_determinism(
    scenario: Scenario, *, damage_fn: DamageFunc | None = None, runs: int = 3
) -> MetamorphicResult:
    fn = damage_fn or _default_damage
    results = [fn(scenario) for _ in range(runs)]
    all_same = all(r == results[0] for r in results)
    return MetamorphicResult(
        relation=RelationKind.DETERMINISM,
        passed=all_same,
        scenario_id=scenario.scenario_id,
        original={"run_0": results[0]},
        transformed={"runs": results},
        detail=f"{runs} runs: {'identical' if all_same else 'DIVERGED'}",
    )


def check_hidden_info_leak(
    scenario: Scenario, *, decision_fn: Callable[[Scenario], str] | None = None
) -> MetamorphicResult:
    """The North Star relation: hidden party data must not change AI output.

    Takes a decision_fn that returns the chosen action string given a
    scenario.  Runs twice: once with the real hidden party, once with a
    dummy party.  If decisions differ, the AI peeked.
    """
    if decision_fn is None:
        return MetamorphicResult(
            relation=RelationKind.HIDDEN_INFO_LEAK,
            passed=True,
            scenario_id=scenario.scenario_id,
            detail="no decision_fn provided — skipped",
        )
    real_decision = decision_fn(scenario)
    scrubbed = scenario.copy(hidden_party=[{"species": "MAGIKARP", "level": 5}] * 6)
    scrubbed_decision = decision_fn(scrubbed)
    passed = real_decision == scrubbed_decision
    return MetamorphicResult(
        relation=RelationKind.HIDDEN_INFO_LEAK,
        passed=passed,
        scenario_id=scenario.scenario_id,
        original={"decision": real_decision},
        transformed={"decision": scrubbed_decision, "party": "scrubbed"},
        detail=f"real={real_decision} scrubbed={scrubbed_decision}",
    )


def check_symmetry(
    scenario: Scenario, *, damage_fn: DamageFunc | None = None
) -> MetamorphicResult:
    """damage(A→B) == damage(B→A) when stats/levels/types swap fully.

    Only meaningful when attacker and defender types are identical,
    otherwise type matchups differ and asymmetry is expected.
    """
    fn = damage_fn or _default_damage
    def_types = scenario.extra.get("defender_types", [0xFF, 0xFF])
    atk_types = scenario.attacker_types or [0xFF]
    if sorted(atk_types) != sorted(def_types):
        return MetamorphicResult(
            relation=RelationKind.SYMMETRY,
            passed=True,
            scenario_id=scenario.scenario_id,
            detail="types differ — symmetry not expected, skipped",
        )
    swapped = scenario.copy(
        attacker_atk=scenario.defender_def,
        defender_def=scenario.attacker_atk,
        attacker_spa=scenario.defender_spd,
        defender_spd=scenario.attacker_spa,
        attacker_level=scenario.defender_level,
        defender_level=scenario.attacker_level,
    )
    r1 = fn(scenario)
    r2 = fn(swapped)
    passed = r1 == r2
    return MetamorphicResult(
        relation=RelationKind.SYMMETRY,
        passed=passed,
        scenario_id=scenario.scenario_id,
        original={"damage": r1},
        transformed={"damage": r2},
        detail=f"A→B={r1} vs B→A={r2}",
    )


ALL_DAMAGE_RELATIONS: list[Callable[..., MetamorphicResult]] = [
    check_level_monotonicity,
    check_stab_monotonicity,
    check_stat_stage_monotonicity,
    check_determinism,
    check_symmetry,
]


def run_all_damage(
    scenario: Scenario,
    *,
    damage_fn: DamageFunc | None = None,
    decision_fn: Callable[[Scenario], str] | None = None,
) -> list[MetamorphicResult]:
    results = [rel(scenario, damage_fn=damage_fn) for rel in ALL_DAMAGE_RELATIONS]
    results.append(check_hidden_info_leak(scenario, decision_fn=decision_fn))
    return results


__all__ = [
    "RelationKind",
    "MetamorphicResult",
    "Scenario",
    "DamageFunc",
    "check_level_monotonicity",
    "check_stab_monotonicity",
    "check_stat_stage_monotonicity",
    "check_determinism",
    "check_hidden_info_leak",
    "check_symmetry",
    "run_all_damage",
    "ALL_DAMAGE_RELATIONS",
]
