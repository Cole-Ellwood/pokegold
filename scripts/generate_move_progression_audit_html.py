#!/usr/bin/env python3
"""Generate an HTML audit for later weaker same-type level-up moves."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "audit" / "move_progression" / "move_progression_audit.html"

MOVE_RE = re.compile(
    r"^\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([0-9]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([0-9]+)"
)
POKEMON_CONST_RE = re.compile(r"\s*const\s+([A-Z0-9_]+)\b")
POINTER_RE = re.compile(r"\s*dw\s+([A-Za-z0-9_]+)EvosAttacks\b")
LABEL_RE = re.compile(r"^([A-Za-z0-9_]+)EvosAttacks:$")
LEARNSET_RE = re.compile(r"^(\d+)\s*,\s*([A-Z0-9_]+)$")

NON_COMPARABLE_EFFECTS = {
    "EFFECT_OHKO",
    "EFFECT_STATIC_DAMAGE",
    "EFFECT_LEVEL_DAMAGE",
    "EFFECT_COUNTER",
    "EFFECT_PSYWAVE",
    "EFFECT_SUPER_FANG",
    "EFFECT_REVERSAL",
    "EFFECT_RETURN",
    "EFFECT_FRUSTRATION",
    "EFFECT_PRESENT",
    "EFFECT_MAGNITUDE",
    "EFFECT_HIDDEN_POWER",
    "EFFECT_MIRROR_COAT",
    "EFFECT_BEAT_UP",
}

NOISE_EFFECT_REASONS = {
    "EFFECT_TRAP_TARGET": "trapping move",
    "EFFECT_MULTI_HIT": "multi-hit move",
    "EFFECT_DOUBLE_HIT": "multi-hit move",
    "EFFECT_TRIPLE_KICK": "multi-hit move",
    "EFFECT_POISON_MULTI_HIT": "multi-hit move",
    "EFFECT_PRIORITY_HIT": "priority move",
    "EFFECT_ROLLOUT": "scaling move",
    "EFFECT_LEECH_HIT": "drain/recovery move",
    "EFFECT_FLINCH_HIT": "secondary-effect utility",
    "EFFECT_ALWAYS_HIT": "accuracy utility",
}

EARLIER_CONTEXT_REASONS = {
    "EFFECT_DREAM_EATER": "conditional earlier move",
    "EFFECT_THUNDER": "accuracy/weather tradeoff",
    "EFFECT_SOLARBEAM": "charge/weather tradeoff",
    "EFFECT_HYPER_BEAM": "recharge tradeoff",
    "EFFECT_SKY_ATTACK": "charge tradeoff",
    "EFFECT_RECOIL_HIT": "recoil tradeoff",
    "EFFECT_SELFDESTRUCT": "self-KO move",
}

LATER_CONTEXT_REASONS = {
    "EFFECT_RAMPAGE": "lock-in move",
    "EFFECT_FUTURE_SIGHT": "delayed-damage move",
    "EFFECT_CONFUSE_HIT": "secondary-effect utility",
    "EFFECT_ACCURACY_DOWN_HIT": "secondary-effect utility",
    "EFFECT_SPEED_DOWN_HIT": "secondary-effect utility",
}

TYPE_COLORS = {
    "BUG": "#6b8f2a",
    "DARK": "#4b5563",
    "DRAGON": "#5866c9",
    "ELECTRIC": "#b98200",
    "FIGHTING": "#b45309",
    "FIRE": "#d9480f",
    "FLYING": "#4f74c8",
    "GHOST": "#6d5ca8",
    "GRASS": "#2f8f5b",
    "GROUND": "#956332",
    "ICE": "#0e7490",
    "NORMAL": "#6b7280",
    "POISON": "#8b5fbf",
    "PSYCHIC_TYPE": "#c0265a",
    "ROCK": "#806d30",
    "STEEL": "#52616b",
    "WATER": "#2878c7",
}


@dataclass(frozen=True)
class Move:
    name: str
    effect: str
    power: int
    move_type: str
    accuracy: int
    line: int


@dataclass(frozen=True)
class LearnMove:
    species: str
    level: int
    move: str
    line: int


@dataclass(frozen=True)
class Finding:
    family: tuple[str, ...]
    later: LearnMove
    earlier: LearnMove
    classification: str
    severity: str
    reason: str
    suggestion: str


def read_repo(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def pretty_species(name: str) -> str:
    return (
        name.replace("MR__MIME", "MR. MIME")
        .replace("FARFETCH_D", "FARFETCH'D")
        .replace("HO_OH", "HO-OH")
        .replace("_", " ")
    )


def pretty_move(name: str) -> str:
    return name.replace("PSYCHIC_M", "PSYCHIC").replace("_", " ")


def type_name(name: str) -> str:
    return "PSYCHIC" if name == "PSYCHIC_TYPE" else name


def parse_moves() -> dict[str, Move]:
    moves: dict[str, Move] = {}
    for line_number, line in enumerate(read_repo("data/moves/moves.asm").splitlines(), 1):
        match = MOVE_RE.match(line)
        if not match:
            continue
        name, effect, power, move_type, accuracy = match.groups()
        moves[name] = Move(
            name=name,
            effect=effect,
            power=int(power),
            move_type=move_type,
            accuracy=int(accuracy),
            line=line_number,
        )
    return moves


def parse_pokemon_order() -> list[str]:
    species: list[str] = []
    for line in read_repo("constants/pokemon_constants.asm").splitlines():
        match = POKEMON_CONST_RE.match(line)
        if not match:
            continue
        name = match.group(1)
        if name == "EGG":
            break
        species.append(name)
    return species


def parse_label_species_map(species_order: list[str]) -> dict[str, str]:
    labels: list[str] = []
    for line in read_repo("data/pokemon/evos_attacks_pointers.asm").splitlines():
        match = POINTER_RE.match(line)
        if match:
            labels.append(match.group(1))
    return dict(zip(labels, species_order))


def parse_evos_and_learnsets(
    label_to_species: dict[str, str],
) -> tuple[dict[str, list[tuple[str, int | None, str]]], dict[str, list[LearnMove]]]:
    evolutions: dict[str, list[tuple[str, int | None, str]]] = defaultdict(list)
    learnsets: dict[str, list[LearnMove]] = defaultdict(list)

    current_label: str | None = None
    in_attacks = False
    for line_number, raw_line in enumerate(read_repo("data/pokemon/evos_attacks.asm").splitlines(), 1):
        line = raw_line.split(";", 1)[0].strip()
        label_match = LABEL_RE.match(line)
        if label_match:
            current_label = label_match.group(1)
            in_attacks = False
            continue
        if current_label is None or not line.startswith("db"):
            continue

        payload = line[2:].strip()
        if payload.startswith("0"):
            if not in_attacks:
                in_attacks = True
            else:
                current_label = None
            continue

        species = label_to_species[current_label]
        if not in_attacks:
            parts = [part.strip() for part in payload.split(",")]
            if parts and parts[0].startswith("EVOLVE_"):
                target = parts[-1]
                try:
                    level = int(parts[1])
                except ValueError:
                    level = None
                evolutions[species].append((target, level, parts[0]))
            continue

        move_match = LEARNSET_RE.match(payload)
        if move_match:
            learnsets[species].append(
                LearnMove(
                    species=species,
                    level=int(move_match.group(1)),
                    move=move_match.group(2),
                    line=line_number,
                )
            )

    return evolutions, learnsets


def is_comparable(move_name: str, moves: dict[str, Move]) -> bool:
    move = moves.get(move_name)
    return bool(move and move.power > 0 and move.effect not in NON_COMPARABLE_EFFECTS)


def build_families(
    species_order: list[str],
    evolutions: dict[str, list[tuple[str, int | None, str]]],
) -> list[tuple[str, ...]]:
    adjacent: dict[str, set[str]] = defaultdict(set)
    for species, targets in evolutions.items():
        for target, _, _ in targets:
            adjacent[species].add(target)
            adjacent[target].add(species)

    families: list[tuple[str, ...]] = []
    seen: set[str] = set()
    for species in species_order:
        if species in seen:
            continue
        queue: deque[str] = deque([species])
        seen.add(species)
        family: list[str] = []
        while queue:
            current = queue.popleft()
            family.append(current)
            for neighbor in adjacent[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        families.append(tuple(sorted(family, key=species_order.index)))
    return families


def min_species_levels(
    species_order: list[str],
    evolutions: dict[str, list[tuple[str, int | None, str]]],
) -> dict[str, int]:
    parents: dict[str, list[tuple[str, int | None, str]]] = defaultdict(list)
    for species, targets in evolutions.items():
        for target, level, method in targets:
            parents[target].append((species, level, method))

    min_level = {species: 1 for species in species_order}
    changed = True
    while changed:
        changed = False
        for species, species_parents in parents.items():
            levels = [
                max(min_level.get(parent, 1), level or 1)
                for parent, level, _ in species_parents
            ]
            if not levels:
                continue
            new_level = min(levels)
            if min_level.get(species, 1) != new_level:
                min_level[species] = new_level
                changed = True
    return min_level


def best_earlier(
    items: list[LearnMove],
    later: LearnMove,
    moves: dict[str, Move],
    species_order: list[str],
) -> LearnMove | None:
    later_move = moves[later.move]
    candidates = []
    for earlier in items:
        if earlier.level >= later.level or not is_comparable(earlier.move, moves):
            continue
        earlier_move = moves[earlier.move]
        if (
            earlier_move.move_type == later_move.move_type
            and earlier_move.power > later_move.power
        ):
            candidates.append(earlier)

    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda earlier: (
            -moves[earlier.move].power,
            earlier.level,
            species_order.index(earlier.species),
            earlier.line,
        ),
    )[0]


def family_scope(later: LearnMove, earlier: LearnMove, min_levels: dict[str, int]) -> str:
    if later.species == earlier.species:
        return "same species"
    if min_levels[earlier.species] > min_levels[later.species]:
        return "lower-stage delay"
    if min_levels[later.species] > min_levels[earlier.species]:
        return "evolved-stage echo"
    return "family branch"


def classify_finding(
    family: tuple[str, ...],
    later: LearnMove,
    earlier: LearnMove,
    moves: dict[str, Move],
    min_levels: dict[str, int],
) -> tuple[str, str, str, str]:
    later_move = moves[later.move]
    earlier_move = moves[earlier.move]
    gap = earlier_move.power - later_move.power
    scope = family_scope(later, earlier, min_levels)

    if later_move.move_type == "NORMAL":
        return (
            "filtered",
            "noise",
            "Normal-type utility/progression move",
            "Ignored in the main view.",
        )

    if later_move.effect in NOISE_EFFECT_REASONS:
        reason = NOISE_EFFECT_REASONS[later_move.effect]
        return ("filtered", "noise", reason, "Ignored because its utility can justify lower BP.")

    if earlier_move.effect in EARLIER_CONTEXT_REASONS:
        reason = EARLIER_CONTEXT_REASONS[earlier_move.effect]
        return (
            "review",
            "low",
            reason,
            "Keep visible as context, but do not treat as a clear mistake.",
        )

    if earlier_move.accuracy < later_move.accuracy:
        return (
            "review",
            "low",
            "power/accuracy tradeoff",
            "Lower BP may be intentional because the later move is more accurate.",
        )

    if later_move.effect in LATER_CONTEXT_REASONS:
        reason = LATER_CONTEXT_REASONS[later_move.effect]
        return (
            "issue",
            "medium" if gap < 30 else "high",
            reason,
            "Review the level order; the later move adds context but is still lower BP.",
        )

    if len(family) == 1 and earlier.level == 1 and earlier_move.power >= 100:
        return (
            "review",
            "low",
            "signature or special L1 move",
            "Likely intentional, but visible because it is a clean power downgrade.",
        )

    severity = "high" if gap >= 30 else "medium" if gap >= 15 else "low"
    if scope == "lower-stage delay":
        suggestion = "Move the weaker lower-stage move earlier, replace it, or move the stronger evolved-stage move later."
    elif scope == "same species":
        suggestion = "Replace the later move or confirm its role in this species' progression."
    elif scope == "evolved-stage echo":
        suggestion = "Check whether the evolved form should keep this later lower-BP echo."
    else:
        suggestion = "Check whether this branch should diverge or share the stronger move timing."
    return ("issue", severity, f"{scope}; {gap} BP lower", suggestion)


def find_issues(
    species_order: list[str],
    moves: dict[str, Move],
    evolutions: dict[str, list[tuple[str, int | None, str]]],
    learnsets: dict[str, list[LearnMove]],
) -> tuple[list[Finding], list[tuple[str, LearnMove, LearnMove]]]:
    families = build_families(species_order, evolutions)
    min_levels = min_species_levels(species_order, evolutions)
    findings: list[Finding] = []
    raw_species_hits: list[tuple[str, LearnMove, LearnMove]] = []

    for species, items in learnsets.items():
        for later in items:
            if not is_comparable(later.move, moves):
                continue
            earlier = best_earlier(items, later, moves, species_order)
            if earlier:
                raw_species_hits.append((species, later, earlier))

    seen_family_hits: set[tuple[tuple[str, ...], str, int, str]] = set()
    for family in families:
        family_items = [
            item
            for species in family
            for item in learnsets.get(species, [])
            if item.level >= min_levels[species]
        ]
        for later in family_items:
            if not is_comparable(later.move, moves):
                continue
            earlier = best_earlier(family_items, later, moves, species_order)
            if not earlier:
                continue
            key = (family, later.species, later.level, later.move)
            if key in seen_family_hits:
                continue
            seen_family_hits.add(key)
            classification, severity, reason, suggestion = classify_finding(
                family, later, earlier, moves, min_levels
            )
            findings.append(
                Finding(
                    family=family,
                    later=later,
                    earlier=earlier,
                    classification=classification,
                    severity=severity,
                    reason=reason,
                    suggestion=suggestion,
                )
            )

    return findings, raw_species_hits


def move_payload(move_name: str, moves: dict[str, Move]) -> dict[str, object]:
    move = moves[move_name]
    return {
        "name": pretty_move(move.name),
        "type": type_name(move.move_type),
        "rawType": move.move_type,
        "power": move.power,
        "accuracy": move.accuracy,
        "effect": move.effect.replace("EFFECT_", "").replace("_", " ").title(),
        "line": move.line,
    }


def finding_payload(finding: Finding, moves: dict[str, Move]) -> dict[str, object]:
    earlier_move = moves[finding.earlier.move]
    later_move = moves[finding.later.move]
    max_level = max(finding.later.level, finding.earlier.level, 60)
    return {
        "family": " / ".join(pretty_species(species) for species in finding.family),
        "laterSpecies": pretty_species(finding.later.species),
        "earlierSpecies": pretty_species(finding.earlier.species),
        "laterLevel": finding.later.level,
        "earlierLevel": finding.earlier.level,
        "later": move_payload(finding.later.move, moves),
        "earlier": move_payload(finding.earlier.move, moves),
        "gap": earlier_move.power - later_move.power,
        "classification": finding.classification,
        "severity": finding.severity,
        "reason": finding.reason,
        "suggestion": finding.suggestion,
        "laterSource": f"data/pokemon/evos_attacks.asm:{finding.later.line}",
        "earlierSource": f"data/pokemon/evos_attacks.asm:{finding.earlier.line}",
        "laterMoveSource": f"data/moves/moves.asm:{later_move.line}",
        "earlierMoveSource": f"data/moves/moves.asm:{earlier_move.line}",
        "laterPosition": round(finding.later.level / max_level * 100, 2),
        "earlierPosition": round(finding.earlier.level / max_level * 100, 2),
    }


def css() -> str:
    return r"""
    :root {
      color-scheme: light;
      --bg: #f6f3ec;
      --ink: #202124;
      --muted: #667085;
      --panel: #fffaf1;
      --panel-2: #ffffff;
      --line: #ddd5c5;
      --red: #c2410c;
      --amber: #a16207;
      --green: #1f7a5c;
      --blue: #2458a6;
      --shadow: 0 14px 38px rgba(72, 52, 26, 0.14);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 12% 8%, rgba(210, 69, 22, 0.12), transparent 24rem),
        radial-gradient(circle at 88% 0%, rgba(36, 88, 166, 0.10), transparent 26rem),
        linear-gradient(180deg, #fbf7ee 0%, var(--bg) 42%, #f0ebdf 100%);
      color: var(--ink);
      line-height: 1.45;
    }

    .shell {
      width: min(1220px, calc(100vw - 36px));
      margin: 0 auto;
      padding: 34px 0 56px;
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
      gap: 26px;
      align-items: stretch;
      margin-bottom: 22px;
    }

    .hero-copy {
      min-height: 310px;
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 250, 241, 0.78);
      box-shadow: var(--shadow);
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 18px;
      color: var(--blue);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .pokeball {
      width: 18px;
      height: 18px;
      border: 2px solid currentColor;
      border-radius: 50%;
      position: relative;
      display: inline-block;
      background: linear-gradient(180deg, currentColor 0 47%, transparent 47% 53%, #fff 53% 100%);
    }

    .pokeball::after {
      content: "";
      position: absolute;
      width: 6px;
      height: 6px;
      left: 4px;
      top: 4px;
      border: 2px solid currentColor;
      border-radius: 50%;
      background: #fffaf1;
    }

    h1 {
      margin: 0;
      max-width: 820px;
      font-size: clamp(38px, 6vw, 78px);
      line-height: 0.96;
      letter-spacing: 0;
    }

    .subtitle {
      max-width: 760px;
      margin: 20px 0 0;
      color: #4b5563;
      font-size: 18px;
    }

    .hero-graphic {
      min-height: 310px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fffdf8;
      box-shadow: var(--shadow);
      overflow: hidden;
      position: relative;
    }

    .hero-graphic svg {
      width: 100%;
      height: 100%;
      display: block;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 0 0 24px;
    }

    .stat {
      padding: 18px 18px 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
      box-shadow: 0 8px 22px rgba(72, 52, 26, 0.08);
    }

    .stat .value {
      display: block;
      font-size: 34px;
      line-height: 1;
      font-weight: 850;
    }

    .stat .label {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 750;
      text-transform: uppercase;
    }

    .toolbar {
      position: sticky;
      top: 0;
      z-index: 20;
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto auto;
      gap: 12px;
      align-items: center;
      margin: 22px 0;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 250, 241, 0.94);
      backdrop-filter: blur(14px);
      box-shadow: 0 12px 30px rgba(72, 52, 26, 0.12);
    }

    .search {
      width: 100%;
      min-height: 42px;
      border: 1px solid #c9bea9;
      border-radius: 6px;
      padding: 0 14px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }

    .segmented {
      display: inline-grid;
      grid-auto-flow: column;
      gap: 4px;
      padding: 4px;
      border: 1px solid #c9bea9;
      border-radius: 8px;
      background: #f3ebdd;
    }

    .segmented button {
      min-width: 82px;
      min-height: 34px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: #4b5563;
      font: inherit;
      font-weight: 780;
      cursor: pointer;
    }

    .segmented button.active {
      background: #202124;
      color: #fffaf1;
    }

    .select {
      min-height: 42px;
      border: 1px solid #c9bea9;
      border-radius: 6px;
      padding: 0 12px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-weight: 700;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
      gap: 20px;
      align-items: start;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.76);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      padding: 22px 22px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 250, 241, 0.76);
    }

    .panel h2 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }

    .panel-note {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }

    .cards {
      display: grid;
      gap: 14px;
      padding: 18px;
    }

    .issue-card {
      border: 1px solid #ded3c0;
      border-radius: 8px;
      background: #fffdf8;
      overflow: hidden;
    }

    .issue-card.hidden { display: none; }

    .issue-top {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 16px 10px;
    }

    .issue-title {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
    }

    .issue-family {
      margin-top: 5px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }

    .badge, .type-pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 0 10px;
      color: #fff;
      font-size: 12px;
      font-weight: 850;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .badge.high { background: var(--red); }
    .badge.medium { background: var(--amber); }
    .badge.low { background: var(--blue); }
    .badge.review { background: #596273; }

    .comparison {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 12px;
      padding: 0 16px 14px;
    }

    .move-box {
      border: 1px solid #e5dccb;
      border-radius: 8px;
      padding: 12px;
      background: #fff8ea;
    }

    .move-label {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 850;
      text-transform: uppercase;
    }

    .move-name {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 850;
    }

    .bar {
      position: relative;
      height: 10px;
      border-radius: 999px;
      background: #eee3d2;
      overflow: hidden;
    }

    .bar span {
      position: absolute;
      inset: 0 auto 0 0;
      width: var(--w);
      border-radius: inherit;
      background: var(--c);
    }

    .move-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
      color: #4b5563;
      font-size: 12px;
      font-weight: 760;
    }

    .timeline {
      position: relative;
      height: 44px;
      margin: 0 16px 12px;
      border-radius: 8px;
      background:
        linear-gradient(90deg, rgba(32, 33, 36, 0.08) 0 1px, transparent 1px) 0 0 / 10% 100%,
        #f6efe2;
      border: 1px solid #e0d4bf;
    }

    .timeline::before {
      content: "";
      position: absolute;
      left: 12px;
      right: 12px;
      top: 21px;
      height: 2px;
      background: #b9aa91;
    }

    .dot {
      position: absolute;
      top: 12px;
      width: 20px;
      height: 20px;
      margin-left: -10px;
      border: 3px solid #fffdf8;
      border-radius: 50%;
      background: var(--dot);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22);
    }

    .dot::after {
      content: attr(data-level);
      position: absolute;
      top: 22px;
      left: 50%;
      transform: translateX(-50%);
      color: #4b5563;
      font-size: 11px;
      font-weight: 850;
      white-space: nowrap;
    }

    .issue-footer {
      display: grid;
      gap: 8px;
      padding: 12px 16px 16px;
      border-top: 1px solid #eadfcb;
      color: #394150;
      font-size: 14px;
    }

    .source {
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
    }

    .chart-stack {
      display: grid;
      gap: 16px;
      padding: 18px;
    }

    .chart-row {
      display: grid;
      grid-template-columns: 108px minmax(0, 1fr) 42px;
      gap: 10px;
      align-items: center;
      font-size: 13px;
      font-weight: 800;
    }

    .chart-track {
      height: 16px;
      border-radius: 999px;
      background: #eee3d2;
      overflow: hidden;
    }

    .chart-fill {
      height: 100%;
      width: var(--w);
      border-radius: inherit;
      background: var(--c);
    }

    .table-wrap {
      overflow-x: auto;
      padding: 0 18px 18px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    th, td {
      padding: 11px 10px;
      border-bottom: 1px solid #eadfcb;
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }

    th {
      color: #475467;
      font-size: 12px;
      text-transform: uppercase;
      background: #fff8ea;
    }

    td.wrap { white-space: normal; min-width: 260px; }

    .empty {
      display: none;
      padding: 32px;
      color: var(--muted);
      text-align: center;
      font-weight: 750;
    }

    .footnote {
      margin-top: 18px;
      color: var(--muted);
      font-size: 13px;
    }

    @media (max-width: 980px) {
      .hero, .grid { grid-template-columns: 1fr; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .toolbar { grid-template-columns: 1fr; }
      .segmented { grid-auto-flow: row; grid-template-columns: repeat(3, 1fr); }
    }

    @media (max-width: 620px) {
      .shell { width: min(100vw - 22px, 1220px); padding-top: 18px; }
      .hero-copy { padding: 22px; }
      h1 { font-size: 38px; }
      .stats, .comparison { grid-template-columns: 1fr; }
      .issue-top { display: block; }
      .badge-row { justify-content: flex-start; margin-top: 12px; }
      .chart-row { grid-template-columns: 82px minmax(0, 1fr) 32px; }
    }
    """


def js() -> str:
    return r"""
    const DATA = window.REPORT_DATA;
    const cards = Array.from(document.querySelectorAll("[data-card]"));
    const rows = Array.from(document.querySelectorAll("[data-row]"));
    const search = document.querySelector("#search");
    const typeFilter = document.querySelector("#typeFilter");
    const buttons = Array.from(document.querySelectorAll("[data-filter]"));
    const visibleCount = document.querySelector("#visibleCount");
    const empty = document.querySelector("#empty");
    let activeFilter = "issue";

    function matches(item, query, type, mode) {
      const haystack = [
        item.family,
        item.laterSpecies,
        item.earlierSpecies,
        item.later.name,
        item.earlier.name,
        item.reason,
        item.suggestion,
        item.severity,
      ].join(" ").toLowerCase();
      const classOk = mode === "all" || item.classification === mode;
      const typeOk = type === "all" || item.later.rawType === type;
      const queryOk = !query || haystack.includes(query);
      return classOk && typeOk && queryOk;
    }

    function applyFilters() {
      const query = search.value.trim().toLowerCase();
      const type = typeFilter.value;
      let count = 0;
      cards.forEach((card) => {
        const item = DATA.findings[Number(card.dataset.card)];
        const show = matches(item, query, type, activeFilter);
        card.classList.toggle("hidden", !show);
        if (show) count += 1;
      });
      rows.forEach((row) => {
        const item = DATA.findings[Number(row.dataset.row)];
        row.hidden = !matches(item, query, type, activeFilter);
      });
      visibleCount.textContent = count;
      empty.style.display = count === 0 ? "block" : "none";
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        buttons.forEach((other) => other.classList.remove("active"));
        button.classList.add("active");
        activeFilter = button.dataset.filter;
        applyFilters();
      });
    });
    search.addEventListener("input", applyFilters);
    typeFilter.addEventListener("change", applyFilters);
    applyFilters();
    """


def hero_svg(issue_count: int, filtered_count: int, review_count: int) -> str:
    return f"""
      <svg viewBox="0 0 620 360" role="img" aria-label="Move power timeline graphic">
        <defs>
          <linearGradient id="fireGrad" x1="0" x2="1">
            <stop offset="0" stop-color="#f97316"/>
            <stop offset="1" stop-color="#dc2626"/>
          </linearGradient>
          <linearGradient id="waterGrad" x1="0" x2="1">
            <stop offset="0" stop-color="#38bdf8"/>
            <stop offset="1" stop-color="#1d4ed8"/>
          </linearGradient>
          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="9" flood-color="#4b3415" flood-opacity=".22"/>
          </filter>
        </defs>
        <rect width="620" height="360" fill="#fffdf8"/>
        <path d="M0 266 C88 224 152 286 236 244 C321 201 382 123 462 151 C523 173 561 226 620 194 L620 360 L0 360 Z" fill="#efe4cf"/>
        <path d="M0 289 C98 248 167 309 255 267 C345 224 399 154 477 181 C537 202 565 254 620 223" fill="none" stroke="#d6c5a7" stroke-width="3"/>
        <g filter="url(#softShadow)">
          <rect x="72" y="64" width="476" height="148" rx="8" fill="#ffffff" stroke="#decfb9"/>
          <line x1="118" y1="158" x2="500" y2="158" stroke="#b8a68a" stroke-width="4" stroke-linecap="round"/>
          <circle cx="188" cy="158" r="19" fill="url(#fireGrad)" stroke="#fff" stroke-width="6"/>
          <circle cx="337" cy="158" r="19" fill="url(#waterGrad)" stroke="#fff" stroke-width="6"/>
          <circle cx="451" cy="158" r="19" fill="#2f8f5b" stroke="#fff" stroke-width="6"/>
          <text x="188" y="117" text-anchor="middle" font-size="24" font-weight="800" fill="#202124">95</text>
          <text x="337" y="117" text-anchor="middle" font-size="24" font-weight="800" fill="#202124">60</text>
          <text x="451" y="117" text-anchor="middle" font-size="24" font-weight="800" fill="#202124">50</text>
          <text x="188" y="201" text-anchor="middle" font-size="12" font-weight="800" fill="#667085">Earlier</text>
          <text x="337" y="201" text-anchor="middle" font-size="12" font-weight="800" fill="#667085">Later</text>
          <text x="451" y="201" text-anchor="middle" font-size="12" font-weight="800" fill="#667085">Noise</text>
        </g>
        <g font-family="system-ui, sans-serif" font-weight="850">
          <text x="76" y="276" font-size="40" fill="#202124">{issue_count}</text>
          <text x="76" y="299" font-size="13" fill="#667085">primary issues</text>
          <text x="250" y="276" font-size="40" fill="#202124">{review_count}</text>
          <text x="250" y="299" font-size="13" fill="#667085">review notes</text>
          <text x="430" y="276" font-size="40" fill="#202124">{filtered_count}</text>
          <text x="430" y="299" font-size="13" fill="#667085">filtered hits</text>
        </g>
      </svg>
    """


def render_report(findings: list[Finding], raw_species_hits: list[tuple[str, LearnMove, LearnMove]], moves: dict[str, Move]) -> str:
    payload = [finding_payload(finding, moves) for finding in findings]
    visible_payload = [item for item in payload if item["classification"] != "filtered"]
    issue_payload = [item for item in payload if item["classification"] == "issue"]
    review_payload = [item for item in payload if item["classification"] == "review"]
    filtered_payload = [item for item in payload if item["classification"] == "filtered"]

    max_gap = max([int(item["gap"]) for item in visible_payload] or [1])
    type_counts = Counter(str(item["later"]["rawType"]) for item in visible_payload)
    noise_counts = Counter(str(item["reason"]) for item in filtered_payload)
    type_options = "\n".join(
        f'<option value="{escape(move_type)}">{escape(type_name(move_type))}</option>'
        for move_type in sorted(type_counts)
    )

    card_html = []
    row_html = []
    for index, item in enumerate(payload):
        later = item["later"]
        earlier = item["earlier"]
        type_color = TYPE_COLORS.get(str(later["rawType"]), "#6b7280")
        earlier_width = min(100, int(earlier["power"]) / 180 * 100)
        later_width = min(100, int(later["power"]) / 180 * 100)
        severity_class = "review" if item["classification"] == "review" else item["severity"]
        default_hidden_class = "" if item["classification"] == "issue" else " hidden"
        default_hidden_attr = "" if item["classification"] == "issue" else " hidden"
        card_html.append(
            f"""
            <article class="issue-card{default_hidden_class}" data-card="{index}">
              <div class="issue-top">
                <div>
                  <h3 class="issue-title">{escape(str(item["laterSpecies"]))} L{item["laterLevel"]} {escape(str(later["name"]))}</h3>
                  <div class="issue-family">{escape(str(item["family"]))}</div>
                </div>
                <div class="badge-row">
                  <span class="type-pill" style="background:{type_color}">{escape(str(later["type"]))}</span>
                  <span class="badge {escape(str(severity_class))}">{escape(str(item["severity"]))}</span>
                </div>
              </div>
              <div class="comparison">
                <div class="move-box">
                  <p class="move-label">Earlier stronger</p>
                  <p class="move-name">{escape(str(item["earlierSpecies"]))} L{item["earlierLevel"]} {escape(str(earlier["name"]))}</p>
                  <div class="bar" style="--c:{type_color};--w:{earlier_width:.1f}%"><span></span></div>
                  <div class="move-meta">
                    <span>{earlier["power"]} BP</span>
                    <span>{earlier["accuracy"]}% acc</span>
                    <span>{escape(str(earlier["effect"]))}</span>
                  </div>
                </div>
                <div class="move-box">
                  <p class="move-label">Later weaker</p>
                  <p class="move-name">{escape(str(item["laterSpecies"]))} L{item["laterLevel"]} {escape(str(later["name"]))}</p>
                  <div class="bar" style="--c:{type_color};--w:{later_width:.1f}%"><span></span></div>
                  <div class="move-meta">
                    <span>{later["power"]} BP</span>
                    <span>{later["accuracy"]}% acc</span>
                    <span>{escape(str(later["effect"]))}</span>
                  </div>
                </div>
              </div>
              <div class="timeline">
                <span class="dot" data-level="L{item["earlierLevel"]}" style="left:{item["earlierPosition"]}%;--dot:{type_color}"></span>
                <span class="dot" data-level="L{item["laterLevel"]}" style="left:{item["laterPosition"]}%;--dot:#202124"></span>
              </div>
              <div class="issue-footer">
                <div><strong>Why it is visible:</strong> {escape(str(item["reason"]))}</div>
                <div><strong>Review:</strong> {escape(str(item["suggestion"]))}</div>
                <div class="source">{escape(str(item["earlierSource"]))} -> {escape(str(item["laterSource"]))}</div>
              </div>
            </article>
            """
        )
        row_html.append(
            f"""
            <tr data-row="{index}"{default_hidden_attr}>
              <td>{escape(str(item["classification"]))}</td>
              <td>{escape(str(item["severity"]))}</td>
              <td class="wrap">{escape(str(item["family"]))}</td>
              <td>{escape(str(item["earlierSpecies"]))} L{item["earlierLevel"]} {escape(str(earlier["name"]))}</td>
              <td>{earlier["power"]}</td>
              <td>{escape(str(item["laterSpecies"]))} L{item["laterLevel"]} {escape(str(later["name"]))}</td>
              <td>{later["power"]}</td>
              <td>{item["gap"]}</td>
              <td class="wrap">{escape(str(item["reason"]))}</td>
            </tr>
            """
        )

    type_chart = []
    max_type_count = max(type_counts.values() or [1])
    for move_type, count in type_counts.most_common():
        color = TYPE_COLORS.get(move_type, "#6b7280")
        width = count / max_type_count * 100
        type_chart.append(
            f"""
            <div class="chart-row">
              <span>{escape(type_name(move_type))}</span>
              <div class="chart-track"><div class="chart-fill" style="--w:{width:.1f}%;--c:{color}"></div></div>
              <span>{count}</span>
            </div>
            """
        )

    noise_chart = []
    max_noise_count = max(noise_counts.values() or [1])
    for reason, count in noise_counts.most_common():
        width = count / max_noise_count * 100
        noise_chart.append(
            f"""
            <div class="chart-row">
              <span>{escape(reason[:22])}</span>
              <div class="chart-track"><div class="chart-fill" style="--w:{width:.1f}%;--c:#596273"></div></div>
              <span>{count}</span>
            </div>
            """
        )

    data = {
        "findings": payload,
        "generated": date.today().isoformat(),
    }
    data_json = json.dumps(data, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Move Progression Audit - pokemon gold hack</title>
<style>
{css()}
</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow"><span class="pokeball"></span> Source-derived learnset audit</p>
        <h1>Move Progression Audit</h1>
        <p class="subtitle">
          Later same-type level-up moves that are weaker than an earlier move in the same evolution family.
          Utility noise is filtered out so the remaining rows are the ones worth reviewing.
        </p>
      </div>
      <div class="hero-graphic">
        {hero_svg(len(issue_payload), len(filtered_payload), len(review_payload))}
      </div>
    </section>

    <section class="stats" aria-label="Audit summary">
      <div class="stat"><span class="value">{len(issue_payload)}</span><span class="label">Primary issues</span></div>
      <div class="stat"><span class="value">{len(review_payload)}</span><span class="label">Review notes</span></div>
      <div class="stat"><span class="value">{len(filtered_payload)}</span><span class="label">Noise filtered</span></div>
      <div class="stat"><span class="value">{len(raw_species_hits)}</span><span class="label">Species raw hits</span></div>
    </section>

    <section class="toolbar" aria-label="Report filters">
      <input id="search" class="search" type="search" placeholder="Search family, species, move, reason">
      <div class="segmented" aria-label="Finding type">
        <button class="active" type="button" data-filter="issue">Issues</button>
        <button type="button" data-filter="review">Review</button>
        <button type="button" data-filter="all">All</button>
      </div>
      <select id="typeFilter" class="select" aria-label="Type filter">
        <option value="all">All types</option>
        {type_options}
      </select>
    </section>

    <section class="grid">
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2>Visible Findings</h2>
            <p class="panel-note"><span id="visibleCount">0</span> rows match the current filters.</p>
          </div>
        </div>
        <div class="cards">
          {"".join(card_html)}
          <div id="empty" class="empty">No findings match the current filters.</div>
        </div>
      </div>

      <aside class="panel">
        <div class="panel-head">
          <div>
            <h2>Signal Shape</h2>
            <p class="panel-note">Filtered view by later move type and ignored-noise reason.</p>
          </div>
        </div>
        <div class="chart-stack">
          <h3 class="move-label">Visible types</h3>
          {"".join(type_chart)}
          <h3 class="move-label">Ignored noise</h3>
          {"".join(noise_chart)}
        </div>
      </aside>
    </section>

    <section class="panel" style="margin-top:20px">
      <div class="panel-head">
        <div>
          <h2>Issue Table</h2>
          <p class="panel-note">Same data as the cards, kept compact for scanning.</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Class</th>
              <th>Severity</th>
              <th>Family</th>
              <th>Earlier stronger</th>
              <th>BP</th>
              <th>Later weaker</th>
              <th>BP</th>
              <th>Gap</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {"".join(row_html)}
          </tbody>
        </table>
      </div>
    </section>

    <p class="footnote">
      Generated {date.today().isoformat()} from <code>data/pokemon/evos_attacks.asm</code> and
      <code>data/moves/moves.asm</code>. Fixed/variable-power, status, OHKO, and other non-comparable
      effects are excluded before classification. The default view hides filtered noise; use "All" to inspect it.
    </p>
  </main>
  <script>
    window.REPORT_DATA = {data_json};
{js()}
  </script>
</body>
</html>
"""


def main() -> int:
    moves = parse_moves()
    species_order = parse_pokemon_order()
    label_to_species = parse_label_species_map(species_order)
    evolutions, learnsets = parse_evos_and_learnsets(label_to_species)
    findings, raw_species_hits = find_issues(species_order, moves, evolutions, learnsets)
    html = render_report(findings, raw_species_hits, moves)
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
