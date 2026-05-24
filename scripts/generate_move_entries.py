#!/usr/bin/env python3
"""Generate concise Bulbapedia-style move entries from source data."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "generated" / "move_entries.md"
MOVE_CONSTANTS = ROOT / "constants" / "move_constants.asm"
TYPE_CONSTANTS = ROOT / "constants" / "type_constants.asm"
MOVE_NAMES = ROOT / "data" / "moves" / "names.asm"
MOVE_DATA = ROOT / "data" / "moves" / "moves.asm"
MOVE_CRITICAL = ROOT / "data" / "moves" / "critical_hit_moves.asm"
MOVE_PRIORITIES = ROOT / "data" / "moves" / "effects_priorities.asm"


@dataclass(frozen=True)
class Move:
    index: int
    constant: str
    display_name: str
    effect: str
    power: int
    type_name: str
    accuracy: int
    pp: int
    effect_chance: int


TYPE_DISPLAY = {
    "NORMAL": "Normal",
    "FIGHTING": "Fighting",
    "FLYING": "Flying",
    "POISON": "Poison",
    "GROUND": "Ground",
    "ROCK": "Rock",
    "BUG": "Bug",
    "GHOST": "Ghost",
    "STEEL": "Steel",
    "FIRE": "Fire",
    "WATER": "Water",
    "GRASS": "Grass",
    "ELECTRIC": "Electric",
    "PSYCHIC_TYPE": "Psychic",
    "ICE": "Ice",
    "DRAGON": "Dragon",
    "DARK": "Dark",
}

NAME_OVERRIDES = {
    "ANCIENTPOWER": "Ancient Power",
    "BUBBLEBEAM": "Bubble Beam",
    "CONVERSION2": "Conversion 2",
    "DOUBLE_EDGE": "Double-Edge",
    "DOUBLESLAP": "Double Slap",
    "DRAGONBREATH": "Dragon Breath",
    "DYNAMICPUNCH": "Dynamic Punch",
    "EXTREMESPEED": "Extreme Speed",
    "HI_JUMP_KICK": "High Jump Kick",
    "LOCK_ON": "Lock-On",
    "MUD_SLAP": "Mud-Slap",
    "POISONPOWDER": "Poison Powder",
    "PSYCHIC_M": "Psychic",
    "SELFDESTRUCT": "Self-Destruct",
    "SOFTBOILED": "Soft-Boiled",
    "SOLARBEAM": "Solar Beam",
    "SONICBOOM": "Sonic Boom",
    "THUNDERPUNCH": "Thunder Punch",
    "THUNDERSHOCK": "Thunder Shock",
    "VICEGRIP": "Vise Grip",
}

STATUS_SUMMARIES = {
    "EFFECT_SLEEP": "It puts the target to sleep.",
    "EFFECT_POISON": "It poisons the target.",
    "EFFECT_TOXIC": "It badly poisons the target.",
    "EFFECT_PARALYZE": "It paralyzes the target.",
}

HIT_STATUS_EFFECTS = {
    "EFFECT_POISON_HIT": "poison",
    "EFFECT_BURN_HIT": "burn",
    "EFFECT_FREEZE_HIT": "freeze",
    "EFFECT_PARALYZE_HIT": "paralysis",
    "EFFECT_CONFUSE_HIT": "confusion",
    "EFFECT_FLINCH_HIT": "flinching",
}

STAT_NAMES = {
    "ATTACK": "Attack",
    "DEFENSE": "Defense",
    "SPEED": "Speed",
    "SP_ATK": "Sp. Atk",
    "SP_DEF": "Sp. Def",
    "ACCURACY": "accuracy",
    "EVASION": "evasion",
}

FIXED_OR_VARIABLE_DAMAGE = {
    "EFFECT_BIDE",
    "EFFECT_COUNTER",
    "EFFECT_LEVEL_DAMAGE",
    "EFFECT_MAGNITUDE",
    "EFFECT_MIRROR_COAT",
    "EFFECT_OHKO",
    "EFFECT_PRESENT",
    "EFFECT_PSYWAVE",
    "EFFECT_RETURN",
    "EFFECT_REVERSAL",
    "EFFECT_STATIC_DAMAGE",
    "EFFECT_SUPER_FANG",
    "EFFECT_FRUSTRATION",
}

DAMAGING_ZERO_POWER_EFFECTS = {"EFFECT_BIDE", "EFFECT_OHKO"}
FIXED_OR_VARIABLE_POWER_EFFECTS = FIXED_OR_VARIABLE_DAMAGE | {"EFFECT_HIDDEN_POWER"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def parse_move_constants() -> list[str]:
    constants: list[str] = []
    in_constants = False
    for raw in read(MOVE_CONSTANTS).splitlines():
        code = strip_comment(raw)
        if code == "const_def":
            in_constants = True
            continue
        if not in_constants:
            continue
        if code.startswith("DEF NUM_ATTACKS"):
            break
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match and match.group(1) != "NO_MOVE":
            constants.append(match.group(1))
    return constants


def parse_type_values() -> tuple[dict[str, int], int]:
    values: dict[str, int] = {}
    current = 0
    special_threshold: int | None = None
    for raw in read(TYPE_CONSTANTS).splitlines():
        code = strip_comment(raw)
        if not code:
            continue
        match = re.match(r"const_def(?:\s+(\d+))?$", code)
        if match:
            current = int(match.group(1) or 0)
            continue
        match = re.match(r"const_next\s+(\d+)$", code)
        if match:
            current = int(match.group(1))
            continue
        if code == "DEF SPECIAL EQU const_value":
            special_threshold = current
            continue
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match:
            values[match.group(1)] = current
            current += 1
    if special_threshold is None:
        raise ValueError(f"{TYPE_CONSTANTS}: missing SPECIAL threshold")
    return values, special_threshold


def title_move_constant(constant: str) -> str:
    if constant in NAME_OVERRIDES:
        return NAME_OVERRIDES[constant]
    return constant.replace("_", " ").title()


def parse_names(constants: list[str]) -> dict[str, str]:
    names: list[str] = []
    for raw in read(MOVE_NAMES).splitlines():
        match = re.search(r'li\s+"([^"]+)"', raw)
        if match:
            names.append(match.group(1))
    if len(names) != len(constants):
        raise ValueError(f"move name count mismatch: {len(names)} names for {len(constants)} constants")
    return {
        constant: NAME_OVERRIDES.get(constant, title_move_constant(raw_name.replace("-", "_")))
        for constant, raw_name in zip(constants, names)
    }


def parse_moves(constants: list[str], names: dict[str, str]) -> list[Move]:
    rows: list[Move] = []
    move_pat = re.compile(
        r"^\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*"
        r"([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    for raw in read(MOVE_DATA).splitlines():
        match = move_pat.match(raw)
        if not match:
            continue
        constant, effect, power, type_name, accuracy, pp, effect_chance = match.groups()
        rows.append(
            Move(
                index=len(rows) + 1,
                constant=constant,
                display_name=names[constant],
                effect=effect,
                power=int(power),
                type_name=type_name,
                accuracy=int(accuracy),
                pp=int(pp),
                effect_chance=int(effect_chance),
            )
        )
    if [move.constant for move in rows] != constants:
        raise ValueError("move data order does not match constants/move_constants.asm")
    return rows


def parse_critical_moves() -> set[str]:
    critical: set[str] = set()
    for raw in read(MOVE_CRITICAL).splitlines():
        code = strip_comment(raw)
        match = re.match(r"db\s+([A-Z0-9_]+)$", code)
        if match and match.group(1) != "-1":
            critical.add(match.group(1))
    return critical


def parse_priorities() -> dict[str, int]:
    priorities: dict[str, int] = {}
    for raw in read(MOVE_PRIORITIES).splitlines():
        code = strip_comment(raw)
        match = re.match(r"db\s+([A-Z0-9_]+)\s*,\s*(-?\d+)$", code)
        if match:
            priorities[match.group(1)] = int(match.group(2))
    return priorities


def article(word: str) -> str:
    return "an" if word[0].lower() in {"a", "e", "i", "o", "u"} else "a"


def type_display(type_name: str) -> str:
    return TYPE_DISPLAY.get(type_name, type_name.replace("_", " ").title())


def category(type_name: str, type_values: dict[str, int], special_threshold: int) -> str:
    return "special" if type_values[type_name] >= special_threshold else "physical"


def is_damaging(move: Move) -> bool:
    return move.power > 0 or move.effect in DAMAGING_ZERO_POWER_EFFECTS


def has_listed_base_power(move: Move) -> bool:
    return move.power > 1 and move.effect not in FIXED_OR_VARIABLE_POWER_EFFECTS


def chance_text(move: Move) -> str:
    return f"{move.effect_chance}%"


def chance_prefix(move: Move) -> str:
    return "" if move.effect_chance >= 100 else f"It has a {chance_text(move)} chance to "


def sentence_start(text: str) -> str:
    return text[0].upper() + text[1:]


def stage_text(stages: int) -> str:
    return "one stage" if stages == 1 else "two stages"


def stat_change_summary(effect: str, move: Move) -> str | None:
    hit_match = re.match(r"EFFECT_(ATTACK|DEFENSE|SPEED|SP_ATK|SP_DEF|ACCURACY|EVASION)_DOWN_HIT$", effect)
    if hit_match:
        stat = STAT_NAMES[hit_match.group(1)]
        return sentence_start(chance_prefix(move) + f"lower the target's {stat} by one stage.")
    hit_match = re.match(r"EFFECT_(ATTACK|DEFENSE|SPEED|SP_ATK|SP_DEF|ACCURACY|EVASION)_UP_HIT$", effect)
    if hit_match:
        stat = STAT_NAMES[hit_match.group(1)]
        return sentence_start(chance_prefix(move) + f"raise the user's {stat} by one stage.")
    match = re.match(r"EFFECT_(ATTACK|DEFENSE|SPEED|SP_ATK|SP_DEF|ACCURACY|EVASION)_UP(_2)?$", effect)
    if match:
        stat = STAT_NAMES[match.group(1)]
        stages = 2 if match.group(2) else 1
        return f"It raises the user's {stat} by {stage_text(stages)}."
    match = re.match(r"EFFECT_(ATTACK|DEFENSE|SPEED|SP_ATK|SP_DEF|ACCURACY|EVASION)_DOWN(_2)?$", effect)
    if match:
        stat = STAT_NAMES[match.group(1)]
        stages = 2 if match.group(2) else 1
        return f"It lowers the target's {stat} by {stage_text(stages)}."
    return None


def effect_summary(move: Move) -> list[str]:
    effect = move.effect
    if move.constant == "HIDDEN_POWER":
        return [
            "Its type can be any type except Normal, based on the user's Attack and Defense DVs.",
            "The chosen type is used for type effectiveness, STAB, and the Gen II physical/special split.",
            "If the user is Unown, Hidden Power has 100 base power and becomes a type that is super effective against the target, defaulting to Psychic if none is available.",
        ]
    stat_summary = stat_change_summary(effect, move)
    if stat_summary:
        return [stat_summary]
    if effect in HIT_STATUS_EFFECTS:
        status = HIT_STATUS_EFFECTS[effect]
        verb = "make the target flinch" if effect == "EFFECT_FLINCH_HIT" else f"inflict {status}"
        return [sentence_start(chance_prefix(move) + f"{verb}.")]
    if effect in STATUS_SUMMARIES:
        return [STATUS_SUMMARIES[effect]]

    exact = {
        "EFFECT_ACCURACY_DOWN": "It lowers the target's accuracy by one stage.",
        "EFFECT_ALL_UP_HIT": f"It has a {chance_text(move)} chance to raise all of the user's stats by one stage.",
        "EFFECT_ALWAYS_HIT": "It bypasses accuracy checks.",
        "EFFECT_ATTRACT": "It infatuates an opposite-gender target.",
        "EFFECT_BATON_PASS": "It switches the user out while passing stat changes and other passable effects to the replacement.",
        "EFFECT_BEAT_UP": "It attacks once for each conscious non-statused Pokemon in the user's party.",
        "EFFECT_BELLY_DRUM": "It maximizes the user's Attack by cutting the user's HP if enough HP is available.",
        "EFFECT_BIDE": "The user stores damage for two turns, then returns double the damage taken.",
        "EFFECT_CALM_MIND": "It raises the user's Sp. Atk and Sp. Def by one stage each.",
        "EFFECT_CONFUSE": "It confuses the target.",
        "EFFECT_CONVERSION": "It changes the user's type based on one of the user's moves.",
        "EFFECT_CONVERSION2": "It changes the user's type in response to the target's last move.",
        "EFFECT_COUNTER": "It deals double the damage taken from the last physical attack.",
        "EFFECT_CURSE": "If used by a Ghost-type Pokemon, it cuts the user's HP and curses the target; otherwise, it raises the user's Attack and Defense and lowers its Speed.",
        "EFFECT_DEFENSE_CURL": "It raises the user's Defense by one stage and powers up later Rollout damage.",
        "EFFECT_DESTINY_BOND": "If the user faints from the target's attack before the user's next move, the target faints too.",
        "EFFECT_DISABLE": "It disables one of the target's moves.",
        "EFFECT_DOUBLE_HIT": "It hits twice.",
        "EFFECT_DRAGON_DANCE": "It raises the user's Attack and Speed by one stage each.",
        "EFFECT_DREAM_EATER": "It only works on a sleeping target and restores the user's HP by half the damage dealt.",
        "EFFECT_EARTHQUAKE": "It deals double damage to a target using Dig.",
        "EFFECT_ENCORE": "It forces the target to repeat its last move for several turns.",
        "EFFECT_ENDURE": "It lets the user survive an otherwise-fainting hit with 1 HP that turn.",
        "EFFECT_FALSE_SWIPE": "It leaves the target with at least 1 HP.",
        "EFFECT_FLAME_WHEEL": f"It thaws the user if frozen and has a {chance_text(move)} chance to burn the target.",
        "EFFECT_FLY": "On the first turn, the user becomes semi-invulnerable; on the second turn, it attacks.",
        "EFFECT_FOCUS_ENERGY": "It raises the user's critical-hit ratio.",
        "EFFECT_FOCUS_PUNCH": "It fails if the user is hit before executing the move.",
        "EFFECT_FORCE_SWITCH": "It forces the target out in trainer battles and ends wild battles.",
        "EFFECT_FORESIGHT": "It identifies the target, making Normal- and Fighting-type moves affect Ghost-type targets and ignoring evasion boosts.",
        "EFFECT_FRUSTRATION": "Its base power increases as the user's happiness decreases.",
        "EFFECT_FURY_CUTTER": "Its damage doubles after each consecutive hit, up to five successful uses.",
        "EFFECT_FUTURE_SIGHT": "It deals delayed damage two turns after use.",
        "EFFECT_GUST": "It deals double damage to a target using Fly.",
        "EFFECT_HEAL": "It restores the user's HP by half of its maximum HP.",
        "EFFECT_HEAL_BELL": "It cures status conditions from the user's party.",
        "EFFECT_HYPER_BEAM": "The user must recharge on the next turn.",
        "EFFECT_JUMP_KICK": "If it misses, the user takes crash damage.",
        "EFFECT_LEECH_HIT": "It restores the user's HP by half the damage dealt.",
        "EFFECT_LEECH_SEED": "It plants a seed that drains the target's HP each turn and heals the user's side.",
        "EFFECT_LEVEL_DAMAGE": "It deals damage equal to the user's level.",
        "EFFECT_LIGHT_SCREEN": "It halves special damage against the user's side for several turns.",
        "EFFECT_LOCK_ON": "It makes the user's next move against the target ignore accuracy checks.",
        "EFFECT_MAGNITUDE": "Its base power is randomly chosen from Magnitude 4 through Magnitude 10.",
        "EFFECT_MEAN_LOOK": "It prevents the target from fleeing or switching.",
        "EFFECT_METRONOME": "It randomly calls another move.",
        "EFFECT_MIMIC": "It copies one of the target's moves for the rest of the battle.",
        "EFFECT_MIRROR_COAT": "It deals double the damage taken from the last special attack.",
        "EFFECT_MIRROR_MOVE": "It uses the last move used by the target.",
        "EFFECT_MIST": "It protects the user's side from stat reductions.",
        "EFFECT_MOONLIGHT": "It restores the user's HP, with the amount varying by battle conditions.",
        "EFFECT_MORNING_SUN": "It restores the user's HP, with the amount varying by battle conditions.",
        "EFFECT_MULTI_HIT": "It hits two to five times.",
        "EFFECT_NIGHTMARE": "It afflicts a sleeping target with Nightmare, causing HP loss each turn.",
        "EFFECT_NORMAL_HIT": "It has no additional effect.",
        "EFFECT_OHKO": "It causes the target to faint in one hit if it succeeds.",
        "EFFECT_PAIN_SPLIT": "It averages the user's and target's current HP, then gives both that amount.",
        "EFFECT_PAY_DAY": "It scatters coins that are picked up after battle.",
        "EFFECT_PERISH_SONG": "All active Pokemon receive a perish count and faint when it reaches zero unless they switch out.",
        "EFFECT_POISON_MULTI_HIT": f"It hits twice and has a {chance_text(move)} chance to poison the target.",
        "EFFECT_PRESENT": "It randomly deals 40, 80, or 120 base power damage, or heals the target by one quarter of its maximum HP.",
        "EFFECT_PRIORITY_HIT": "It has increased priority.",
        "EFFECT_PROTECT": "It protects the user from most moves for the turn.",
        "EFFECT_PSYCH_UP": "It copies the target's stat changes.",
        "EFFECT_PSYWAVE": "It deals random fixed damage based on the user's level.",
        "EFFECT_PURSUIT": "It doubles in power against a target that is switching out.",
        "EFFECT_QUIVER_DANCE": "It raises the user's Sp. Atk, Sp. Def, and Speed by one stage each.",
        "EFFECT_RAGE": "While Rage is active, the user's Attack rises when it is hit.",
        "EFFECT_RAIN_DANCE": "It starts rain for five turns.",
        "EFFECT_RAMPAGE": "It attacks for two to three turns, then confuses the user.",
        "EFFECT_RAPID_SPIN": "It removes Leech Seed, binding effects, and Spikes from the user's side.",
        "EFFECT_RAZOR_WIND": "It charges on the first turn and attacks on the second turn.",
        "EFFECT_RECOIL_HIT": "The user takes recoil damage after it hits.",
        "EFFECT_REFLECT": "It halves physical damage against the user's side for several turns.",
        "EFFECT_RESET_STATS": "It resets stat changes for both active Pokemon.",
        "EFFECT_RETURN": "Its base power increases as the user's happiness increases.",
        "EFFECT_REVERSAL": "Its base power increases as the user's HP gets lower.",
        "EFFECT_ROLLOUT": "It attacks for up to five turns, doubling in power each time and gaining extra power after Defense Curl.",
        "EFFECT_SACRED_FIRE": f"It thaws the user if frozen and has a {chance_text(move)} chance to burn the target.",
        "EFFECT_SAFEGUARD": "It protects the user's side from major status conditions for several turns.",
        "EFFECT_SANDSTORM": "It starts a sandstorm for five turns.",
        "EFFECT_SELFDESTRUCT": "The user faints after using it.",
        "EFFECT_SKETCH": "It permanently copies the target's last move.",
        "EFFECT_SKULL_BASH": "It raises the user's Defense on the first turn and attacks on the second turn.",
        "EFFECT_SKY_ATTACK": f"It charges on the first turn and attacks on the second turn, with a {chance_text(move)} chance to make the target flinch.",
        "EFFECT_SLEEP_TALK": "It can be used while asleep and randomly calls one of the user's other moves.",
        "EFFECT_SNORE": f"It can only be used while asleep and has a {chance_text(move)} chance to make the target flinch.",
        "EFFECT_SOLARBEAM": "It normally charges on the first turn and attacks on the second turn, but skips charging in sun.",
        "EFFECT_SPIKES": "It lays Spikes on the target's side of the field.",
        "EFFECT_SPITE": "It reduces PP from the target's last move.",
        "EFFECT_SPLASH": "It has no effect.",
        "EFFECT_STATIC_DAMAGE": f"It deals {move.power} HP of fixed damage.",
        "EFFECT_STOMP": f"It has a {chance_text(move)} chance to make the target flinch and deals double damage to a minimized target.",
        "EFFECT_SUBSTITUTE": "It creates a substitute by using one quarter of the user's maximum HP.",
        "EFFECT_SUNNY_DAY": "It starts harsh sunlight for five turns.",
        "EFFECT_SUPER_FANG": "It cuts the target's current HP in half.",
        "EFFECT_SWAGGER": "It confuses the target and raises the target's Attack by two stages.",
        "EFFECT_SYNTHESIS": "It restores the user's HP, with the amount varying by battle conditions.",
        "EFFECT_TELEPORT": "It ends wild battles.",
        "EFFECT_THIEF": "It steals the target's held item if the user is not holding one.",
        "EFFECT_THUNDER": f"It has a {chance_text(move)} chance to paralyze the target, always hits in rain, and has reduced accuracy in sun.",
        "EFFECT_TRANSFORM": "It transforms the user into the target.",
        "EFFECT_TRAP_TARGET": "It traps and damages the target for multiple turns.",
        "EFFECT_TRIPLE_KICK": "It hits up to three times, increasing in power with each hit.",
        "EFFECT_TRI_ATTACK": f"It has a {chance_text(move)} chance to inflict burn, freeze, or paralysis.",
        "EFFECT_TWISTER": f"It has a {chance_text(move)} chance to make the target flinch and deals double damage to a target using Fly.",
    }
    if effect not in exact:
        raise KeyError(f"missing prose for {effect}")
    return [exact[effect]]


def first_sentence(move: Move, type_values: dict[str, int], special_threshold: int) -> str:
    type_name = type_display(move.type_name)
    kind = "damage-dealing" if is_damaging(move) else "non-damaging"
    if move.constant == "HIDDEN_POWER":
        return (
            "Hidden Power is a damage-dealing move whose type is determined by the user's DVs. "
            "It has 60 base power, 100% accuracy, and 15 PP."
        )
    if has_listed_base_power(move):
        cat = category(move.type_name, type_values, special_threshold)
        return (
            f"{move.display_name} is {article(kind)} {kind} {type_name}-type move. "
            f"It has {move.power} base power, {move.accuracy}% accuracy, {move.pp} PP, and is {cat}."
        )
    return (
        f"{move.display_name} is {article(kind)} {kind} {type_name}-type move. "
        f"It has {move.accuracy}% accuracy and {move.pp} PP."
    )


def render_entry(move: Move, *, type_values: dict[str, int], special_threshold: int, critical_moves: set[str], priorities: dict[str, int]) -> list[str]:
    lines = [f"## {move.display_name}", ""]
    summary_sentences = effect_summary(move)
    extra_sentences: list[str] = []
    if move.constant in critical_moves:
        extra_sentences.append("It has an increased critical-hit ratio.")
    priority = priorities.get(move.effect)
    if priority and priority > 0 and move.effect not in {"EFFECT_PRIORITY_HIT", "EFFECT_PROTECT", "EFFECT_ENDURE"}:
        extra_sentences.append("It has increased priority.")
    if summary_sentences == ["It has no additional effect."] and extra_sentences:
        summary_sentences = []
    lines.append(first_sentence(move, type_values, special_threshold))
    lines.append(" ".join(summary_sentences + extra_sentences))
    lines.append("")
    return lines


def render_document(moves: list[Move]) -> str:
    type_values, special_threshold = parse_type_values()
    critical_moves = parse_critical_moves()
    priorities = parse_priorities()
    lines = [
        "# Move Entries",
        "",
        "<!-- Generated by scripts/generate_move_entries.py. Do not edit by hand. -->",
        "",
        "Concise source-derived entries for every move in this hack. Move order, type, base power, accuracy, PP, effect, priority, and high-critical-hit data are generated from the current assembly source.",
        "",
    ]
    for move in moves:
        lines.extend(
            render_entry(
                move,
                type_values=type_values,
                special_threshold=special_threshold,
                critical_moves=critical_moves,
                priorities=priorities,
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def build_document() -> str:
    constants = parse_move_constants()
    names = parse_names(constants)
    moves = parse_moves(constants, names)
    return render_document(moves)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    output = args.output if args.output.is_absolute() else ROOT / args.output
    document = build_document()
    if args.check:
        if not output.exists():
            print(f"missing generated file: {output.relative_to(ROOT)}", file=sys.stderr)
            return 1
        current = read(output)
        if current != document:
            diff = difflib.unified_diff(
                current.splitlines(),
                document.splitlines(),
                fromfile=str(output.relative_to(ROOT)),
                tofile="generated",
                lineterm="",
            )
            print("\n".join(diff), file=sys.stderr)
            return 1
        print(f"PASS: {output.relative_to(ROOT)} is up to date")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
