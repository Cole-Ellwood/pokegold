#!/usr/bin/env python3
"""Forward consequence / impact oracle: "what could change if I edit X?"

This is the forward-direction companion to `when-wrote` / `reverse-query`
(which answer "what produced this value?"). Given a symbol, function, or
changed file, it reports the consequences an edit there can have AND names
the known-failure-class audit gates that must run as proof.

It is deliberately NOT omniscient, and says so in every report. Hand-written
SM83 has indirect jumps (`jp hl`, jump tables), computed WRAM addresses,
UNION aliasing tied to the save format, data interpreted as code, and
runtime bank state. No sound static pass enumerates *every* dynamic
consequence (the masterpiece roadmap scoped whole-ROM symbolic execution
out for exactly this reason). So this command is exhaustive over the
*known* failure classes plus the static reference closure, and prints an
explicit blind-spot list with the dynamic commands that close it.

Composes existing analyzers rather than re-deriving:
  - register_flow.analyze_function        -> forward register ABI / clobber set
  - clobber_chain.build_clobber_chain_report -> transitive callee clobber
  - slicing.build_slice_report            -> static readers / writers / callers
  - provenance.build_provenance_report    -> source references
  - HAZARD_RULES (this module)            -> which audit gates apply to the edit

CLI:
  python -m tools.debugger consequence --symbol GetUserItem
  python -m tools.debugger consequence --file engine/battle/late_gen_held_items.asm
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT
from . import register_flow, clobber_chain, slicing, provenance


SCHEMA_VERSION = 1
KIND = "unified_debugger_consequence"


@dataclass(frozen=True)
class HazardRule:
    """A known failure class: when an edit touches `path_contains`/`code_contains`,
    these `commands` are the consequence detectors that must run as proof."""

    id: str
    title: str
    why: str
    path_contains: tuple[str, ...]
    code_contains: tuple[str, ...]
    commands: tuple[str, ...]


# Declarative table of this repo's recurring failure classes, sourced from
# CLAUDE.md + docs/asm_authoring_guide.md §6. A rule with empty triggers
# always fires (the release floor). Keep this table-shaped and local.
HAZARD_RULES: tuple[HazardRule, ...] = (
    HazardRule(
        id="release_smoke",
        title="Broad release sanity",
        why="Every tooling-visible edit gets the release floor.",
        path_contains=(),
        code_contains=(),
        commands=("python tools/audit/check_release_smoke.py",),
    ),
    HazardRule(
        id="damage_chain_abi",
        title="Battle damage-chain register ABI (5x-damage clobber class)",
        why=(
            "Edits to the damage chain have twice shipped as 5x physical damage "
            "via a register clobber that broke same-bank callers "
            "(asm_authoring_guide §3.13/§3.14)."
        ),
        path_contains=(
            "engine/battle/effect_commands.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "home/farcall.asm",
        ),
        code_contains=(),
        commands=(
            "python -m tools.damage_debugger.clobber_smoke",
            "python tools/audit/check_typepassive_c_mirror.py",
        ),
    ),
    HazardRule(
        id="farcall_clobber",
        title="farcall hl/a clobber",
        why=(
            "farcall clobbers caller hl before the target runs and returns a via c, "
            "not a. Both have shipped as live bugs (asm_authoring_guide §3.2/§3.3)."
        ),
        path_contains=(),
        code_contains=("farcall", "callfar"),
        commands=(
            "python tools/audit/check_farcall_hl_clobber.py",
            "python tools/audit/check_farcall_a_clobber.py",
        ),
    ),
    HazardRule(
        id="cross_bank_call",
        title="Plain call to a label in another bank",
        why=(
            "A bare `call` to a `::` label in another ROMX bank assembles but jumps "
            "to whatever is paged in (May 2026 type-immunity softlock class)."
        ),
        path_contains=("engine/", "home/", "macros/"),
        code_contains=(),
        commands=("python tools/audit/check_cross_bank_call.py",),
    ),
    HazardRule(
        id="save_format",
        title="WRAM/SRAM field layout = save format",
        why=(
            "ram/ offsets are part of the save format; reordering/resizing silently "
            "misaligns old saves (no migration code). Bump SAVE_FORMAT_VERSION + escalate."
        ),
        path_contains=("ram/",),
        code_contains=(),
        commands=("python tools/audit/check_save_format_version.py",),
    ),
    HazardRule(
        id="boss_ai",
        title="Boss AI policy / selector invariants",
        why="engine/battle/ai/ feeds the boss-AI decision corpus and selector replay.",
        path_contains=("engine/battle/ai/",),
        code_contains=(),
        commands=("python tools/audit/check_boss_ai_debugger_done.py",),
    ),
    HazardRule(
        id="balance_data",
        title="Balance data delta (stats / moves / rosters / encounters)",
        why="Balance tables drive computed damage and trainer difficulty; regen the audit.",
        path_contains=(
            "data/pokemon/base_stats",
            "data/pokemon/evos_attacks",
            "data/moves/",
            "data/trainers/parties.asm",
            "data/trainers/ai_tiers.asm",
            "data/wild/",
        ),
        code_contains=(),
        commands=(
            "python scripts/generate_balance_audit.py",
            "python tools/audit/balance_diff.py --output audit/damage_debugger/damage_heatmap.md",
        ),
    ),
    HazardRule(
        id="vram_timing",
        title="Queued VRAM tile request timing",
        why="Queued tile copies are VBlank-timing sensitive; callers must wait for the ack.",
        path_contains=(
            "home/gfx.asm",
            "home/video.asm",
            "home/vblank.asm",
            "engine/movie/evolution_animation.asm",
        ),
        code_contains=(),
        commands=("python tools/audit/check_vram_request_contract.py",),
    ),
    HazardRule(
        id="navigation_floor",
        title="Docs / dev-index integrity",
        why="Doc edits must keep the navigation spine and dev_index citations valid.",
        path_contains=("docs/",),
        code_contains=(),
        commands=("python tools/audit/check_navigation_floor.py",),
    ),
)


# Blind spots that no static pass over this codebase can resolve. Always
# printed so a consequence report is never mistaken for a completeness proof.
UNIVERSAL_BLIND_SPOTS: tuple[str, ...] = (
    "Indirect control flow (`jp hl`, jump tables, computed call targets) -- "
    "callees reached only at runtime are invisible to the static call graph.",
    "Computed WRAM/HRAM addresses (`ld hl, base` + dynamic offset) -- reads/writes "
    "to a symbol via a runtime-built pointer are not in the static reference set.",
    "UNION aliasing -- co-tenant fields sharing the same WRAM bytes can be clobbered "
    "without naming this symbol; only static `UNION` neighbors are detectable.",
    "Data interpreted as code / self-modified dispatch -- bytes executed as code are "
    "not analyzed as instructions.",
    "Runtime bank state -- which ROMX/WRAMX bank is paged in at the moment of access "
    "is a dynamic fact; static analysis assumes nothing about it.",
)


def build_consequence_report(
    *,
    symbol: str | None = None,
    file: str | None = None,
    register: str | None = None,
    symbols_path: str = "pokegold.sym",
    root: Path = ROOT,
) -> dict[str, Any]:
    if not symbol and not file:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "valid": False,
            "errors": ["provide --symbol or --file"],
        }

    errors: list[str] = []
    warnings: list[str] = []

    target = _classify_target(symbol=symbol, file=file, root=root)
    path = target.get("path") or (file or "")
    body_text = _read_text(root / path) if path and (root / path).exists() else ""

    forward_abi: dict[str, Any] | None = None
    transitive_clobber: dict[str, Any] | None = None
    if target["kind"] == "function" and symbol:
        rf = register_flow.analyze_function(symbol, root=root)
        if rf.get("valid"):
            forward_abi = {
                "clobber_set": rf.get("clobber_set", []),
                "call_count": len(rf.get("calls", [])),
                "ret_count": len(rf.get("rets", [])),
                "push_pop_pairs": rf.get("push_pop_pairs", []),
                "opaque_branch_warnings": [
                    w for w in rf.get("warnings", []) if "opaque" in w.lower()
                ],
            }
        else:
            warnings.extend(rf.get("errors", []))
        chain = clobber_chain.build_clobber_chain_report(
            function=symbol, register=(register or None), root=root
        )
        if chain.get("valid"):
            transitive_clobber = _summarize_clobber_chain(chain)
        else:
            warnings.extend(f"clobber-chain: {e}" for e in chain.get("errors", []))

    reference_closure = _reference_closure(
        symbol=symbol, file=file, symbols_path=symbols_path, root=root
    )

    hazard_gates = _match_hazards(path=path, body_text=body_text, target_kind=target["kind"])
    data_delta = _data_delta(path=path)

    blind_spots = list(UNIVERSAL_BLIND_SPOTS)
    if forward_abi and forward_abi["opaque_branch_warnings"]:
        for warning in forward_abi["opaque_branch_warnings"]:
            blind_spots.append(f"This function has an opaque branch: {warning}")

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "valid": True,
        "proof_mode": "source",
        "target": target,
        "forward_abi": forward_abi,
        "transitive_clobber": transitive_clobber,
        "reference_closure": reference_closure,
        "data_delta": data_delta,
        "hazard_gates": hazard_gates,
        "blind_spots": blind_spots,
        "proof_commands": _proof_commands(target=target, symbol=symbol, file=file),
        "errors": errors,
        "warnings": warnings,
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _classify_target(*, symbol: str | None, file: str | None, root: Path) -> dict[str, Any]:
    if file and not symbol:
        return {"kind": "file", "file": file, "path": file}
    assert symbol is not None
    location = register_flow.find_function(symbol, root=root)
    if location is not None:
        rel = (
            str(location.path.relative_to(root))
            if location.path.is_relative_to(root)
            else str(location.path)
        )
        return {
            "kind": "function",
            "symbol": symbol,
            "path": rel,
            "line": location.start_line,
        }
    if symbol.startswith("w") or symbol.startswith("h") or symbol.startswith("s"):
        # Convention: wXxx = WRAM, hXxx = HRAM, sXxx = SRAM symbol.
        return {"kind": "data", "symbol": symbol, "path": file or ""}
    return {"kind": "symbol", "symbol": symbol, "path": file or ""}


def _reference_closure(
    *, symbol: str | None, file: str | None, symbols_path: str, root: Path
) -> dict[str, Any]:
    symbols = (symbol,) if symbol else ()
    source_files = (file,) if file else ()
    slice_report = slicing.build_slice_report(
        symbols_path=symbols_path, symbols=symbols, source_files=source_files, root=root
    )
    prov_report = provenance.build_provenance_report(
        symbols_path=symbols_path, symbols=symbols, source_files=source_files, root=root
    )
    provenance_symbols = prov_report.get("symbols") or []
    slice_targets = slice_report.get("targets") or []
    return {
        "source_references": sum(_count(s.get("source_hit_count")) for s in provenance_symbols),
        "related_files": sum(_count(s.get("related_files")) for s in provenance_symbols),
        "incoming_refs": sum(_count(t.get("incoming")) for t in slice_targets),
        "outgoing_refs": sum(_count(t.get("outgoing")) for t in slice_targets),
        "impact_files": sum(_count(t.get("impact_files")) for t in slice_targets),
        "slice": slice_report,
        "provenance": prov_report,
    }


def _count(value: Any) -> int:
    """Some slice/provenance fields carry a list; their `*_count` siblings carry an int.
    Accept either shape so the closure summary stays correct if the schema shifts."""
    if isinstance(value, (list, dict)):
        return len(value)
    if isinstance(value, int):
        return value
    return 0


def _summarize_clobber_chain(chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "function": chain.get("function"),
        "clobbered_registers": chain.get("clobbered_registers")
        or chain.get("clobber_set")
        or chain.get("registers"),
        "max_depth_reached": chain.get("max_depth_reached") or chain.get("depth"),
        "callees_analyzed": chain.get("callees_analyzed") or chain.get("call_count"),
        "warnings": chain.get("warnings", []),
    }


def _match_hazards(*, path: str, body_text: str, target_kind: str) -> list[dict[str, Any]]:
    normalized_path = path.replace("\\", "/").lower()
    body_lower = body_text.lower()
    gates: list[dict[str, Any]] = []
    for rule in HAZARD_RULES:
        always = not rule.path_contains and not rule.code_contains
        path_hit = any(token.lower() in normalized_path for token in rule.path_contains)
        code_hit = any(token.lower() in body_lower for token in rule.code_contains)
        if always or path_hit or code_hit:
            gates.append(
                {
                    "id": rule.id,
                    "title": rule.title,
                    "why": rule.why,
                    "commands": list(rule.commands),
                }
            )
    return gates


def _data_delta(*, path: str) -> dict[str, Any] | None:
    normalized = path.replace("\\", "/").lower()
    is_balance = any(
        token in normalized
        for token in (
            "data/pokemon/base_stats",
            "data/pokemon/evos_attacks",
            "data/moves/",
            "data/trainers/parties",
            "data/wild/",
        )
    )
    if not is_balance:
        return None
    return {
        "note": (
            "This is a balance-data edit. Mechanical (damage/stat) consequences are "
            "computable exactly; gameplay feel is a taste call and is NOT derivable here."
        ),
        "recompute_commands": [
            "python scripts/generate_balance_audit.py",
            "python tools/audit/balance_diff.py --output audit/damage_debugger/damage_heatmap.md",
            "python -m tools.damage_debugger.matchup <ATTACKER>:<lvl> <DEFENDER>:<lvl> <MOVE>",
        ],
    }


def _proof_commands(
    *, target: dict[str, Any], symbol: str | None, file: str | None
) -> list[str]:
    """Dynamic commands that close the static blind spots for this target."""
    commands: list[str] = []
    if symbol:
        commands.append(f"python -m tools.debugger watch --watch-symbol {symbol} --execute")
        commands.append(
            f"python -m tools.debugger trace-instructions --symbol {symbol} "
            f"--watch-symbol {symbol} --execute --require-hit"
        )
        commands.append(f"python -m tools.debugger reverse-query --symbol {symbol}")
    if file:
        commands.append(f"python -m tools.debugger triage --changed-file {file}")
        commands.append(f"python -m tools.debugger gate --changed-file {file} --execute")
    commands.append(
        "python -m tools.debugger auto-watch --rebuild  # unsolicited bug surfacing on the next build"
    )
    return commands


def render_text(report: dict[str, Any]) -> str:
    if not report.get("valid"):
        out = ["consequence: INVALID"]
        for err in report.get("errors", []):
            out.append(f"  error: {err}")
        return "\n".join(out) + "\n"

    target = report["target"]
    out: list[str] = []
    label = target.get("symbol") or target.get("file") or "(unknown)"
    out.append(f"consequence report: {label}  [{target['kind']}, proof_mode={report['proof_mode']}]")
    if target.get("path"):
        loc = target["path"] + (f":{target['line']}" if target.get("line") else "")
        out.append(f"  defined at: {loc}")

    abi = report.get("forward_abi")
    if abi:
        out.append("  forward register ABI:")
        out.append(f"    clobbers: {', '.join(abi['clobber_set']) or '(none)'}")
        out.append(f"    calls: {abi['call_count']}   rets: {abi['ret_count']}")
        if abi["opaque_branch_warnings"]:
            out.append(f"    OPAQUE branches: {len(abi['opaque_branch_warnings'])} (see blind spots)")

    chain = report.get("transitive_clobber")
    if chain and chain.get("clobbered_registers"):
        out.append(f"  transitive callee clobber: {chain['clobbered_registers']}")

    closure = report["reference_closure"]
    out.append("  static reference closure:")
    out.append(
        f"    source references: {closure['source_references']}"
        f"   incoming: {closure['incoming_refs']}   outgoing: {closure['outgoing_refs']}"
    )
    out.append(
        f"    files touched by this slice: {closure['impact_files']}"
        f"   (related: {closure['related_files']})"
    )

    if report.get("data_delta"):
        out.append("  data delta:")
        out.append(f"    {report['data_delta']['note']}")

    out.append("  hazard gates to run as proof:")
    for gate in report["hazard_gates"]:
        out.append(f"    [{gate['id']}] {gate['title']}")
        for command in gate["commands"]:
            out.append(f"      $ {command}")

    out.append("  BLIND SPOTS (this report is not a completeness proof):")
    for spot in report["blind_spots"]:
        out.append(f"    - {spot}")

    out.append("  close blind spots with runtime proof:")
    for command in report["proof_commands"]:
        out.append(f"    $ {command}")

    for warning in report.get("warnings", []):
        out.append(f"  warning: {warning}")
    return "\n".join(out) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger consequence",
        description=(
            "Forward consequence / impact oracle: what could change if I edit a "
            "symbol or file, and which known-failure-class audits prove it. "
            "Source-static; always prints an explicit blind-spot list."
        ),
    )
    parser.add_argument("--symbol", default=None, help="asm label, function, or wXxx/hXxx/sXxx data symbol")
    parser.add_argument("--file", default=None, help="changed source file (e.g. engine/battle/late_gen_held_items.asm)")
    parser.add_argument("--register", default=None, help="narrow transitive clobber to one register (e.g. c)")
    parser.add_argument("--symbols", default="pokegold.sym", help="symbol table path")
    parser.add_argument("--json", action="store_true", help="machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = build_consequence_report(
        symbol=args.symbol,
        file=args.file,
        register=args.register,
        symbols_path=args.symbols,
    )
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_text(report))
    return 0 if report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
