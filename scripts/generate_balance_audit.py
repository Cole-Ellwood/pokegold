#!/usr/bin/env python3
"""Generate a source-derived Pokemon balance audit.

This audit is intentionally lightweight: it parses the assembly data directly
and highlights species that need human balance intent, especially standalone
Pokemon with low stats, removed evolutions, thin learnsets, or no reliable STAB.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import re
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_REF = "060d4accd7c0d01b1697ac97e7d7e2da72e3646b"

STAT_NAMES = ("HP", "Atk", "Def", "Spe", "SpA", "SpD")
LEGENDARIES = {
    "ARTICUNO",
    "ZAPDOS",
    "MOLTRES",
    "MEWTWO",
    "MEW",
    "RAIKOU",
    "ENTEI",
    "SUICUNE",
    "LUGIA",
    "HO_OH",
    "CELEBI",
}
FIXED_OR_UNRELIABLE_EFFECTS = {
    "EFFECT_COUNTER",
    "EFFECT_HIDDEN_POWER",
    "EFFECT_LEVEL_DAMAGE",
    "EFFECT_MIRROR_COAT",
    "EFFECT_OHKO",
    "EFFECT_PRESENT",
    "EFFECT_STATIC_DAMAGE",
    "EFFECT_SUPER_FANG",
}

@dataclass(frozen=True)
class BaseStats:
    stats: tuple[int, int, int, int, int, int]
    types: tuple[str, str]
    tms: tuple[str, ...]

    @property
    def bst(self) -> int:
        return sum(self.stats)


@dataclass(frozen=True)
class Move:
    power: int
    move_type: str
    accuracy: int
    pp: int
    effect: str

    @property
    def score(self) -> float:
        return self.power * self.accuracy / 100

    @property
    def reliable_damage(self) -> bool:
        return self.power > 1 and self.effect not in FIXED_OR_UNRELIABLE_EFFECTS


def repo_text(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def parse_documented_gimmicks(text: str) -> set[str]:
    gimmicks: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        species = cells[0].strip("`")
        intent_status = cells[1]
        power_tier = cells[2]
        if intent_status == "locked" and power_tier == "gimmick":
            gimmicks.add(species)
    return gimmicks


def git_text(ref: str, path: str | Path) -> str | None:
    posix = Path(path).as_posix()
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{posix}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_archive_texts(ref: str, tree_path: str | Path) -> dict[str, str]:
    posix = Path(tree_path).as_posix()
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", ref, posix],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return {}

    texts: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith(".asm"):
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            texts[member.name] = extracted.read().decode("utf-8")
    return texts


def parse_species_order(text: str) -> list[str]:
    species: list[str] = []
    for line in text.splitlines():
        if line.startswith("DEF NUM_POKEMON"):
            break
        match = re.match(r"\s*const\s+([A-Z0-9_]+)\b", line)
        if match:
            species.append(match.group(1))
    return species


def parse_evos_pointer_labels(text: str) -> list[str]:
    labels: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*dw\s+([A-Za-z0-9_]+)EvosAttacks\b", line)
        if match:
            labels.append(match.group(1))
    return labels


def parse_evos_attacks(
    text: str,
    label_to_species: dict[str, str],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[tuple[int, str], ...]]]:
    sections: dict[str, list[str]] = {}
    current_label: str | None = None
    for line in text.splitlines():
        label_match = re.match(r"^([A-Za-z0-9_]+)EvosAttacks:", line)
        if label_match:
            current_label = label_match.group(1)
            sections[current_label] = []
        elif current_label is not None:
            sections[current_label].append(line)

    evolutions: dict[str, tuple[str, ...]] = {}
    level_moves: dict[str, tuple[tuple[int, str], ...]] = {}
    for label, lines in sections.items():
        species = label_to_species.get(label)
        if species is None:
            continue
        phase = "evolutions"
        evos: list[str] = []
        moves: list[tuple[int, str]] = []
        for raw in lines:
            code = raw.split(";", 1)[0].strip()
            if not code:
                continue
            if code.startswith("db 0"):
                if phase == "evolutions":
                    phase = "moves"
                    continue
                break
            if not code.startswith("db "):
                continue
            values = [part.strip() for part in code[3:].split(",")]
            if phase == "evolutions":
                if values and values[0].startswith("EVOLVE"):
                    evos.append(values[-1])
            elif len(values) >= 2 and values[0].isdigit():
                moves.append((int(values[0]), values[1]))
        evolutions[species] = tuple(evos)
        level_moves[species] = tuple(moves)
    return evolutions, level_moves


def parse_base_stats_file(text: str) -> tuple[str, BaseStats] | None:
    species: str | None = None
    stats: tuple[int, int, int, int, int, int] | None = None
    types: tuple[str, str] | None = None
    tms: list[str] = []

    for raw in text.splitlines():
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        if species is None:
            match = re.match(r"db\s+([A-Z0-9_]+)\b", code)
            if match:
                species = match.group(1)
            continue
        if stats is None:
            match = re.match(
                r"db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                code,
            )
            if match:
                stats = tuple(int(value) for value in match.groups())  # type: ignore[assignment]
            continue
        if types is None:
            match = re.match(r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\b", code)
            if match and not match.group(1).isdigit():
                types = (match.group(1), match.group(2))
        if code.startswith("tmhm"):
            rest = code[4:].strip()
            if rest:
                tms.extend(part.strip() for part in rest.split(",") if part.strip())

    if species is None or stats is None or types is None:
        return None
    return species, BaseStats(stats=stats, types=types, tms=tuple(tms))


def parse_base_stats(ref: str | None = None) -> dict[str, BaseStats]:
    parsed: dict[str, BaseStats] = {}
    if ref:
        texts = git_archive_texts(ref, "data/pokemon/base_stats")
    else:
        texts = {
            path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "data/pokemon/base_stats").glob("*.asm"))
        }

    for _path, text in sorted(texts.items()):
        if text is None:
            continue
        entry = parse_base_stats_file(text)
        if entry is not None:
            species, stats = entry
            parsed[species] = stats
    return parsed


def parse_type_categories(text: str) -> tuple[set[str], set[str]]:
    physical: set[str] = set()
    special: set[str] = set()
    mode: str | None = None
    for line in text.splitlines():
        if "DEF PHYSICAL" in line:
            mode = "physical"
            continue
        if "DEF SPECIAL" in line:
            mode = "special"
            continue
        if "DEF UNUSED_TYPES" in line:
            mode = None
            continue
        match = re.match(r"\s*const\s+([A-Z0-9_]+)\b", line)
        if match and mode == "physical":
            physical.add(match.group(1))
        elif match and mode == "special":
            special.add(match.group(1))
    return physical, special


def parse_moves(text: str) -> dict[str, Move]:
    moves: dict[str, Move] = {}
    move_re = re.compile(
        r"\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        match = move_re.match(code)
        if not match:
            continue
        name, effect, power, move_type, accuracy, pp, _chance = match.groups()
        moves[name] = Move(
            power=int(power),
            move_type=move_type,
            accuracy=int(accuracy),
            pp=int(pp),
            effect=effect,
        )
    return moves


def best_standard_move(
    species: str,
    base_stats: dict[str, BaseStats],
    level_moves: dict[str, tuple[tuple[int, str], ...]],
    moves: dict[str, Move],
    *,
    stab_only: bool,
) -> tuple[str, Move] | None:
    stats = base_stats.get(species)
    if stats is None:
        return None
    learned = {move for _level, move in level_moves.get(species, ())}
    learned.update(stats.tms)
    candidates: list[tuple[str, Move]] = []
    for move_name in learned:
        move = moves.get(move_name)
        if move is None or not move.reliable_damage:
            continue
        if stab_only and move.move_type not in stats.types:
            continue
        candidates.append((move_name, move))
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            item[1].score,
            item[1].power,
            item[1].accuracy,
            item[0],
        ),
    )


def stat_delta(current: BaseStats, baseline: BaseStats | None) -> str:
    if baseline is None:
        return "n/a"
    deltas = [current.stats[i] - baseline.stats[i] for i in range(len(STAT_NAMES))]
    changed = [
        f"{name}{delta:+d}"
        for name, delta in zip(STAT_NAMES, deltas, strict=True)
        if delta != 0
    ]
    return ", ".join(changed) if changed else "+0"


def score_species(
    species: str,
    current: BaseStats,
    baseline: BaseStats | None,
    current_evos: tuple[str, ...],
    baseline_evos: tuple[str, ...],
    level_moves: tuple[tuple[int, str], ...],
    best_stab: tuple[str, Move] | None,
    documented_gimmicks: set[str],
) -> tuple[int, list[str]]:
    flags: list[str] = []
    score = 0
    current_final = not current_evos
    if current_final:
        flags.append("current-final")
    documented_gimmick = species in documented_gimmicks
    if documented_gimmick:
        flags.append("documented-gimmick")
    if baseline_evos and not current_evos:
        flags.append("removed-evolution")
        score += 5
    if species not in LEGENDARIES and current_final and not documented_gimmick:
        if current.bst < 400:
            flags.append("severe-low-bst-final")
            score += 4
        elif current.bst < 450:
            flags.append("low-bst-final")
            score += 3
        elif current.bst < 490:
            flags.append("watch-bst-final")
            score += 1
    if documented_gimmick:
        pass
    elif best_stab is None:
        flags.append("no-reliable-stab")
        score += 3
    elif best_stab[1].score < 70:
        flags.append("weak-reliable-stab")
        score += 1
    if not current.tms and not documented_gimmick:
        flags.append("no-tms")
        score += 2
    if len(level_moves) <= 4 and not documented_gimmick:
        flags.append("thin-levelset")
        score += 1
    if baseline is not None:
        bst_delta = current.bst - baseline.bst
        if (
            current_final
            and current.bst <= 490
            and bst_delta <= 0
            and not documented_gimmick
        ):
            flags.append("low-and-unbuffed-vs-baseline")
            score += 2
        if bst_delta <= -80 and not documented_gimmick:
            flags.append("large-bst-regression-vs-baseline")
            score += 2
    return score, flags


def markdown_move(entry: tuple[str, Move] | None) -> str:
    if entry is None:
        return "-"
    name, move = entry
    return f"{name} ({move.move_type} {move.power}bp {move.accuracy}%)"


def build_report(baseline_ref: str) -> str:
    species_order = parse_species_order(repo_text("constants/pokemon_constants.asm"))
    labels = parse_evos_pointer_labels(repo_text("data/pokemon/evos_attacks_pointers.asm"))
    label_to_species = {
        label: species
        for label, species in zip(labels, species_order, strict=False)
    }
    current_evos, current_level_moves = parse_evos_attacks(
        repo_text("data/pokemon/evos_attacks.asm"),
        label_to_species,
    )
    baseline_evos_text = git_text(baseline_ref, "data/pokemon/evos_attacks.asm")
    if baseline_evos_text is None:
        baseline_evos: dict[str, tuple[str, ...]] = {}
    else:
        baseline_evos, _baseline_moves = parse_evos_attacks(
            baseline_evos_text,
            label_to_species,
        )

    current_stats = parse_base_stats()
    baseline_stats = parse_base_stats(baseline_ref)
    moves = parse_moves(repo_text("data/moves/moves.asm"))
    documented_gimmicks = parse_documented_gimmicks(repo_text("docs/balance_intent.md"))

    rows: list[dict[str, object]] = []
    for species in species_order:
        current = current_stats.get(species)
        if current is None:
            continue
        evos = current_evos.get(species, ())
        baseline_ev = baseline_evos.get(species, ())
        level_moves = current_level_moves.get(species, ())
        best_stab = best_standard_move(
            species,
            current_stats,
            current_level_moves,
            moves,
            stab_only=True,
        )
        best_any = best_standard_move(
            species,
            current_stats,
            current_level_moves,
            moves,
            stab_only=False,
        )
        baseline = baseline_stats.get(species)
        score, flags = score_species(
            species,
            current,
            baseline,
            evos,
            baseline_ev,
            level_moves,
            best_stab,
            documented_gimmicks,
        )
        rows.append(
            {
                "species": species,
                "score": score,
                "flags": flags,
                "bst": current.bst,
                "baseline_bst": baseline.bst if baseline else "n/a",
                "bst_delta": current.bst - baseline.bst if baseline else "n/a",
                "stats": "/".join(str(value) for value in current.stats),
                "stat_delta": stat_delta(current, baseline),
                "types": "/".join(current.types),
                "current_evos": ", ".join(evos) if evos else "-",
                "baseline_evos": ", ".join(baseline_ev) if baseline_ev else "-",
                "level_moves": len(level_moves),
                "tms": len(current.tms),
                "best_stab": markdown_move(best_stab),
                "best_any": markdown_move(best_any),
            }
        )

    suspicious = [
        row
        for row in rows
        if (
            row["current_evos"] == "-"
            and int(row["score"]) >= 5
        )
        or "removed-evolution" in row["flags"]
    ]
    suspicious.sort(key=lambda row: (-int(row["score"]), int(row["bst"]), str(row["species"])))

    final_rows = [row for row in rows if row["current_evos"] == "-"]
    final_rows.sort(key=lambda row: (-int(row["score"]), int(row["bst"]), str(row["species"])))

    evolution_removed = [row for row in rows if "removed-evolution" in row["flags"]]
    evolution_removed.sort(key=lambda row: (int(row["bst"]), str(row["species"])))

    documented_gimmick_rows = [row for row in rows if "documented-gimmick" in row["flags"]]
    documented_gimmick_rows.sort(key=lambda row: str(row["species"]))

    lines: list[str] = []
    lines.append("# Generated Balance Audit")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Baseline ref: `{baseline_ref}`")
    lines.append("")
    lines.append("Do not hand-edit this file. Regenerate it with:")
    lines.append("")
    lines.append("```powershell")
    lines.append(
        f"python scripts\\generate_balance_audit.py --baseline-ref {baseline_ref}"
    )
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Parses current `data/pokemon/base_stats/`, `data/pokemon/evos_attacks.asm`, `data/moves/moves.asm`, and Pokemon constants.")
    lines.append("- Parses locked gimmick intent from `docs/balance_intent.md` for `documented-gimmick` demotion.")
    lines.append("- Compares stats/evolutions against the baseline ref when that ref is available.")
    lines.append("- Best move columns are power/accuracy heuristics only; they are not stat-weighted damage calculations.")
    lines.append("- Best move columns ignore fixed-damage, OHKO, Hidden Power, Present, Counter, and Mirror Coat style effects.")
    lines.append("- Scores are audit hints, not final balance judgments. Use `docs/balance_intent.md` and `docs/evolution_policy.md` for human intent.")
    lines.append("")
    lines.append("## Flag Legend")
    lines.append("")
    lines.append("- `removed-evolution`: baseline had an evolution rule and current source does not.")
    lines.append("- `severe-low-bst-final`: current standalone/final, non-legendary, BST below 400.")
    lines.append("- `low-bst-final`: current standalone/final, non-legendary, BST below 450.")
    lines.append("- `watch-bst-final`: current standalone/final, non-legendary, BST below 490.")
    lines.append("- `no-reliable-stab`: no standard damaging same-type move in direct level-up plus TM/HM learnset.")
    lines.append("- `weak-reliable-stab`: best standard damaging same-type move has effective power below 70.")
    lines.append("- `low-and-unbuffed-vs-baseline`: low current standalone/final and BST did not rise from baseline.")
    lines.append("- `large-bst-regression-vs-baseline`: current BST is at least 80 lower than baseline ref.")
    lines.append("- `documented-gimmick`: species has locked gimmick intent and is excluded from generic low-stat, TM, and STAB scoring.")
    lines.append("")
    lines.append("## High-Signal Review Queue")
    lines.append("")
    append_rows(lines, suspicious)
    lines.append("")
    lines.append("## Removed Evolutions")
    lines.append("")
    append_rows(lines, evolution_removed)
    lines.append("")
    lines.append("## Documented Gimmicks")
    lines.append("")
    append_rows(lines, documented_gimmick_rows)
    lines.append("")
    lines.append("## Current Standalone Or Final Species")
    lines.append("")
    append_rows(lines, final_rows)
    lines.append("")

    return "\n".join(lines)


def generate_report(baseline_ref: str, out_path: Path) -> None:
    report = build_report(baseline_ref)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")


def append_rows(lines: list[str], rows: list[dict[str, object]]) -> None:
    if not rows:
        lines.append("_No rows._")
        return
    headers = (
        "Score",
        "Pokemon",
        "Flags",
        "BST",
        "Base BST",
        "BST Delta",
        "Stats",
        "Stat Delta",
        "Types",
        "Current Evos",
        "Base Evos",
        "Lv",
        "TM",
        "Best STAB",
        "Best Move",
    )
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        values = (
            str(row["score"]),
            f"`{row['species']}`",
            ", ".join(f"`{flag}`" for flag in row["flags"]),
            str(row["bst"]),
            str(row["baseline_bst"]),
            str(row["bst_delta"]),
            str(row["stats"]),
            str(row["stat_delta"]),
            str(row["types"]),
            str(row["current_evos"]),
            str(row["baseline_evos"]),
            str(row["level_moves"]),
            str(row["tms"]),
            str(row["best_stab"]),
            str(row["best_any"]),
        )
        lines.append("| " + " | ".join(values) + " |")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-ref",
        default=DEFAULT_BASELINE_REF,
        help="git ref used for baseline stat/evolution comparison",
    )
    parser.add_argument(
        "--out",
        default="docs/generated/balance_audit.md",
        help="output markdown path",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="write generated Markdown to stdout instead of --out",
    )
    args = parser.parse_args(argv)
    if args.stdout:
        sys.stdout.write(build_report(args.baseline_ref))
    else:
        generate_report(args.baseline_ref, ROOT / args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
