"""End-to-end synthetic-input health check for the unified debugger.

``python -m tools.debugger.selftest`` exercises each registered
capability against synthetic inputs to confirm the substrate actually
works — not just that the catalog *claims* it works. This is a
deeper contract than ``python -m tools.debugger audit``: audit
verifies the capability is registered and the evidence paths exist;
selftest verifies the underlying functions accept input and return
without crashing.

Per ``docs/omni_debugger_v2.md`` Selftest Infrastructure scope:

- Per-component pass/fail.
- Names the failing component and the next command to run.
- Exit nonzero on any component failure.
- Existing ``python -m tools.debugger audit`` remains the v1 readiness
  gate (this selftest is additive, not a replacement).

CLI wiring into the top-level ``python -m tools.debugger`` is held
pending a Codex sync on ``__main__.py`` (per the collision-risk list
in ``docs/omni_debugger_v2.md``). For now the module is callable via
``python -m tools.debugger.selftest``.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from .catalog import ROOT, build_capability_report


@dataclass
class CheckResult:
    component: str
    ok: bool
    next_command: str
    detail: str = ""
    error: str = ""
    traceback: str = ""

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "ok": self.ok,
            "next_command": self.next_command,
            "detail": self.detail,
            "error": self.error,
            "traceback": self.traceback,
        }


@dataclass
class SelftestReport:
    ok: bool
    results: list[CheckResult] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "components_total": len(self.results),
            "components_failed": sum(1 for r in self.results if not r.ok),
            "results": [r.to_jsonable() for r in self.results],
        }


Check = Callable[[Path], CheckResult]


def _capture(component: str, next_command: str, fn: Callable[[], str]) -> CheckResult:
    """Run a check, capture exceptions into a failed result."""

    try:
        detail = fn() or "ok"
        return CheckResult(component=component, ok=True, next_command=next_command, detail=detail)
    except Exception as exc:  # noqa: BLE001 — selftest deliberately catches all
        return CheckResult(
            component=component,
            ok=False,
            next_command=next_command,
            error=f"{type(exc).__name__}: {exc}",
            traceback=traceback.format_exc(),
        )


def check_capability_audit(root: Path) -> CheckResult:
    def inner() -> str:
        report = build_capability_report(root=root)
        if not report.get("ready", False):
            raise AssertionError(
                f"capability audit reports ready=False with {report.get('blocking_gap_count', 0)} gaps"
            )
        complete = report.get("status_counts", {}).get("complete", 0)
        return f"capability audit ready=True, complete={complete}"

    return _capture(
        component="capability_audit",
        next_command="python -m tools.debugger audit",
        fn=inner,
    )


def check_inventory(root: Path) -> CheckResult:
    from .catalog import build_inventory

    def inner() -> str:
        inv = build_inventory(root=root)
        subsystems = inv.get("subsystems") or []
        if not subsystems:
            raise AssertionError("inventory returned no subsystems")
        return f"inventory ok ({len(subsystems)} subsystems)"

    return _capture(
        component="inventory",
        next_command="python -m tools.debugger inventory",
        fn=inner,
    )


def check_ingest(root: Path) -> CheckResult:
    from .ingest import ingest_artifacts

    def inner() -> str:
        manifest = ingest_artifacts(root=root)
        if not isinstance(manifest, dict):
            raise AssertionError(f"ingest returned {type(manifest).__name__}, not dict")
        return "ingest empty-input round-trip ok"

    return _capture(
        component="ingest",
        next_command="python -m tools.debugger ingest --rom pokegold.gbc --symbols pokegold.sym --input-log <inputs>",
        fn=inner,
    )


def check_triage(root: Path) -> CheckResult:
    from .catalog import triage_request

    def inner() -> str:
        # Triage against a known damage path should select damage rules.
        result = triage_request(
            changed_files=("engine/battle/late_gen_held_items.asm",),
            symptom="damage",
            root=root,
        )
        matches = result.get("matches") or []
        if not matches:
            raise AssertionError("triage returned no matches for damage-chain change")
        damage_hit = any(m.get("id") == "damage_chain" for m in matches)
        if not damage_hit:
            raise AssertionError(
                f"triage failed to route damage-chain change to damage_chain rule "
                f"(got: {[m.get('id') for m in matches]})"
            )
        return f"triage routed {len(matches)} rule(s) including damage_chain"

    return _capture(
        component="triage",
        next_command="python -m tools.debugger triage --changed-file <file> --symptom <symptom>",
        fn=inner,
    )


def check_coverage(root: Path) -> CheckResult:
    from .coverage import build_coverage_report

    def inner() -> str:
        report = build_coverage_report(symbols=("wCurDamage",), root=root)
        if not isinstance(report, dict):
            raise AssertionError(f"coverage returned {type(report).__name__}, not dict")
        if report.get("kind") != "unified_debugger_coverage_report":
            raise AssertionError(f"coverage returned unexpected kind {report.get('kind')!r}")
        if not report.get("valid", False):
            raise AssertionError(f"coverage returned invalid report: {report.get('errors', [])}")
        targets = report.get("targets")
        if not isinstance(targets, list):
            raise AssertionError("coverage report missing canonical list key: targets")
        if not targets:
            raise AssertionError("coverage returned no targets for wCurDamage")
        if not any(target.get("id") == "wCurDamage" for target in targets):
            raise AssertionError("coverage targets did not include requested symbol wCurDamage")
        return f"coverage round-trip ok ({len(targets)} targets)"

    return _capture(
        component="coverage",
        next_command="python -m tools.debugger coverage --symbol <symbol>",
        fn=inner,
    )


def check_provenance(root: Path) -> CheckResult:
    from .provenance import build_provenance_report

    def inner() -> str:
        report = build_provenance_report(root=root)
        if not isinstance(report, dict):
            raise AssertionError(f"provenance returned {type(report).__name__}, not dict")
        return "provenance empty-input round-trip ok"

    return _capture(
        component="provenance",
        next_command="python -m tools.debugger provenance --symbol <symbol>",
        fn=inner,
    )


def check_mirrors(root: Path) -> CheckResult:
    from .mirrors import build_compare_plan

    def inner() -> str:
        plan = build_compare_plan(symbols=("wCurDamage",), root=root)
        if not isinstance(plan, dict):
            raise AssertionError(f"compare plan returned {type(plan).__name__}, not dict")
        return "compare empty-input round-trip ok"

    return _capture(
        component="mirrors_compare",
        next_command="python -m tools.debugger compare --symbol <symbol>",
        fn=inner,
    )


def check_fuzz(root: Path) -> CheckResult:
    from .fuzz import build_fuzz_plan

    def inner() -> str:
        plan = build_fuzz_plan(symbols=("wCurDamage",), root=root)
        if not isinstance(plan, dict):
            raise AssertionError(f"fuzz plan returned {type(plan).__name__}, not dict")
        return "fuzz plan round-trip ok"

    return _capture(
        component="fuzz",
        next_command="python -m tools.debugger generate --symbol <symbol>",
        fn=inner,
    )


def check_trace_index(root: Path) -> CheckResult:
    from .trace_index import build_trace_index_report

    def inner() -> str:
        report = build_trace_index_report(symbols=("wCurDamage",), root=root)
        if not isinstance(report, dict):
            raise AssertionError(f"trace_index returned {type(report).__name__}, not dict")
        return "trace_index empty-input round-trip ok"

    return _capture(
        component="trace_index",
        next_command="python -m tools.debugger trace-index --symbol <symbol>",
        fn=inner,
    )


def check_visualization(root: Path) -> CheckResult:
    from .visualization import build_visualization_report

    def inner() -> str:
        report = build_visualization_report(root=root)
        if not isinstance(report, dict):
            raise AssertionError(f"visualization returned {type(report).__name__}, not dict")
        return "visualization empty-input round-trip ok"

    return _capture(
        component="visualization",
        next_command="python -m tools.debugger visualize --report <report.json>",
        fn=inner,
    )


def check_hypothesis_tracker(root: Path) -> CheckResult:
    """Round-trip through a temp JSONL store.

    Validates that add/list/show/render still produce a coherent tree
    after the round trip. The durable ``audit/hypothesis_tree.jsonl`` is
    never touched.
    """

    import tempfile

    from .hypothesis_tracker import (
        add_claim,
        add_verification,
        fold_history,
        list_hypotheses,
        load_events,
        render_tree,
    )

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "selftest_hypothesis_tree.jsonl"
            claim = add_claim(
                symptom="selftest synthetic symptom",
                claim="selftest synthetic claim",
                confidence="judgment",
                session_id="selftest",
                store=store,
                root=root,
            )
            add_verification(
                parent_id=claim["id"],
                command="echo ok",
                expected="ok",
                verdict="pass",
                store=store,
                root=root,
            )
            events = load_events(store=store, root=root)
            folded = fold_history(events, claim["id"])
            # Judgment-confidence claims must NOT promote to verified on
            # a pass verdict (the gate is enforced at moment-of-verify).
            # The blocked pass surfaces via blocked_pass_count.
            if folded["status"] != "open":
                raise AssertionError(
                    f"expected status=open for judgment+pass, got {folded['status']!r}"
                )
            if folded["blocked_pass_count"] != 1:
                raise AssertionError(
                    f"expected blocked_pass_count=1 for judgment+pass, "
                    f"got {folded['blocked_pass_count']!r}"
                )
            rows = list_hypotheses(store=store, root=root)
            if len(rows) != 1:
                raise AssertionError(f"expected 1 hypothesis, got {len(rows)}")
            tree = render_tree(events, claim["id"])
            if "selftest" not in tree:
                raise AssertionError("rendered tree missing claim id segment")
        return "hypothesis_tracker round-trip ok"

    return _capture(
        component="hypothesis_tracker",
        next_command="python -m tools.debugger.hypothesis_tracker list --refresh-citations",
        fn=inner,
    )


def check_context_packet(root: Path) -> CheckResult:
    """Exercise P5 context-packet generation against a real temp hypothesis."""

    import tempfile

    from .context_packet import build_context_packet
    from .hypothesis_tracker import add_claim

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            store = tmp_root / "hypothesis_tree.jsonl"
            (tmp_root / "engine").mkdir()
            (tmp_root / "engine" / "damage.asm").write_text(
                "; line 1\n; line 2\n",
                encoding="utf-8",
            )
            claim = add_claim(
                symptom="5x physical damage on wild encounter",
                claim="GetUserItem clobbers de",
                confidence="repo-proven",
                citations=("engine/damage.asm:2",),
                session_id="selftest",
                store=store,
                root=tmp_root,
            )
            packet = build_context_packet(
                claim["id"],
                target="codex",
                max_tokens=4000,
                root=tmp_root,
                store=store,
            )
        if not packet.get("valid"):
            raise AssertionError(f"context packet invalid: {packet.get('errors')}")
        if not packet.get("within_budget"):
            raise AssertionError(f"context packet exceeded budget: {packet.get('token_count')}")
        if packet.get("structured", {}).get("claim") != "GetUserItem clobbers de":
            raise AssertionError(f"context packet lost claim: {packet.get('structured')}")
        if not str(packet.get("markdown", "")).startswith("Status: open | Confidence: repo-proven"):
            raise AssertionError("codex target packet did not use punchline-first header")
        return f"context packet valid and within budget ({packet.get('token_count')} tokens)"

    return _capture(
        component="context_packet",
        next_command="python -m tools.debugger pack --hypothesis <id> --target codex",
        fn=inner,
    )


def check_heatmap(root: Path) -> CheckResult:
    """Exercise P9 heatmap generation against a synthetic IO trace.

    The selftest builds a tiny effect-trace JSONL with three writes
    across two frames in the IO region, runs build_heatmap, and asserts
    the per-cell counts, the last-write PC tie-breaker (highest seq
    wins), the ASCII grid renders rows for both addresses, and a
    frame-range filter clips correctly. The cross-check that
    last_write_pc matches the P2 when-wrote query for the same address
    is queued for a P9 follow-up slice.
    """

    import json
    import tempfile

    from .heatmap import build_heatmap

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            trace = tmp_root / "effect.jsonl"
            trace.write_text(
                "\n".join(
                    json.dumps(ev)
                    for ev in (
                        {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 0, "pc_bank_address": "00:0150", "pc_label": "WriteLCDC"},
                        {"kind": "write", "address": "0xFF40", "frame": 1, "seq": 1, "pc_bank_address": "00:0180", "pc_label": "WriteLCDC_alt"},
                        {"kind": "write", "address": "0xFF42", "frame": 1, "seq": 2, "pc_bank_address": "00:0160", "pc_label": "ScrollY"},
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_heatmap(traces=(trace,), region="io", root=tmp_root)
            clipped = build_heatmap(
                traces=(trace,),
                region="io",
                frame_range=(1, 2),
                root=tmp_root,
            )
        if not report.get("valid"):
            raise AssertionError(f"heatmap invalid: {report.get('errors')}")
        if report.get("cell_count") != 3:
            raise AssertionError(f"expected 3 cells; got {report.get('cell_count')}")
        ff40_cells = sorted(
            (c for c in report["cells"] if c["address_hex"] == "$FF40"),
            key=lambda c: c["frame"],
        )
        if len(ff40_cells) != 2:
            raise AssertionError(f"expected 2 $FF40 cells; got {len(ff40_cells)}")
        last_ff40 = ff40_cells[-1]
        if last_ff40.get("last_write_pc_label") != "WriteLCDC_alt":
            raise AssertionError(
                f"highest-seq writer should win; got {last_ff40.get('last_write_pc_label')!r}"
            )
        if "$FF40" not in report.get("grid", "") or "$FF42" not in report.get("grid", ""):
            raise AssertionError("grid missing one or both address rows")
        if clipped.get("frames") != [1]:
            raise AssertionError(f"frame_range filter failed: got {clipped.get('frames')}")
        return (
            f"heatmap valid; {report['cell_count']} cells across "
            f"{report['frame_count']} frames; tie-breaker + filter ok"
        )

    return _capture(
        component="heatmap",
        next_command="python -m tools.debugger heatmap --trace effect.jsonl --region io",
        fn=inner,
    )


def check_vram_decode(root: Path) -> CheckResult:
    """Exercise P6 structured VRAM/OAM decode and diff against raw state bytes."""

    import tempfile

    from .vram_diff import build_vram_diff_report
    from .vram_snapshot import build_vram_snapshot_report

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            base = tmp_root / "base.raw"
            other = tmp_root / "other.raw"
            base_data = bytearray(0x10000)
            other_data = bytearray(0x10000)
            base_data[0x9800] = 0x11
            other_data[0x9800] = 0x22
            base_data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x00))
            other_data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x00))
            base_data[0xFF40] = 0x93
            other_data[0xFF40] = 0x93
            base.write_bytes(bytes(base_data))
            other.write_bytes(bytes(other_data))
            snapshot = build_vram_snapshot_report(state_path=str(base), decode=True, root=tmp_root)
            diff = build_vram_diff_report(
                base_state_path=str(base),
                other_state_path=str(other),
                root=tmp_root,
            )
        if not snapshot.get("valid"):
            raise AssertionError(f"vram snapshot invalid: {snapshot.get('errors')}")
        decoded = snapshot.get("decoded", {})
        if decoded.get("tilemaps", {}).get("9800", {}).get("cells", [{}])[0].get("tile_hex") != "11":
            raise AssertionError("tilemap cell 0 did not decode from raw state")
        if decoded.get("oam", {}).get("visible_guess_count") != 1:
            raise AssertionError("OAM visible sprite count did not decode")
        if not diff.get("valid"):
            raise AssertionError(f"vram diff invalid: {diff.get('errors')}")
        structured = diff.get("diff", {})
        if structured.get("tilemap_changed_cell_count") != 1:
            raise AssertionError(f"expected one tilemap delta; got {structured.get('tilemap_changed_cell_count')}")
        if "tilemap_changed_oam_stable" not in {flag["id"] for flag in structured.get("scenario_flags", [])}:
            raise AssertionError("diff did not mark tilemap-changed/OAM-stable scenario")
        return "vram decode valid; raw snapshot + structured diff smoke ok"

    return _capture(
        component="vram_decode",
        next_command="python -m tools.debugger vram-snapshot --decode --save-state <raw64k>",
        fn=inner,
    )


def check_bgb_sym_export(root: Path) -> CheckResult:
    """Exercise P7 BGB/Emulicious symbol export and parity audit."""

    import tempfile

    from scripts.emit_bgb_sym import write_bgb_sym
    from scripts.emit_wram_map import write_wram_map
    from tools.audit.check_bgb_sym_parity import build_parity_report

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            symbols = tmp_root / "unit.sym"
            bgb = tmp_root / "unit.bgb.sym"
            map_txt = tmp_root / "unit.map.txt"
            symbols.write_text(
                "01:D141 wCurDamage\n"
                "03:4000 BattleCommand_DamageCalc\n"
                "00:FF9F hROMBank\n",
                encoding="utf-8",
            )
            bgb_report = write_bgb_sym(symbols_path=symbols, out_path=bgb)
            map_report = write_wram_map(symbols_path=symbols, out_path=map_txt)
            parity = build_parity_report(symbols_path=symbols, bgb_symbols_path=bgb)
            bgb_text = bgb.read_text(encoding="utf-8")
            map_text = map_txt.read_text(encoding="utf-8")
        if bgb_report.get("symbol_count") != 3:
            raise AssertionError(f"expected 3 BGB symbols; got {bgb_report}")
        if map_report.get("label_count") != 2:
            raise AssertionError(f"expected 2 WRAM/HRAM labels; got {map_report}")
        if not parity.get("ok"):
            raise AssertionError(f"parity failed: {parity}")
        if "01:D141 wCurDamage" not in bgb_text:
            raise AssertionError("BGB export missing wCurDamage")
        if "WRAM 01 D141 wCurDamage" not in map_text or "HRAM 00 FF9F hROMBank" not in map_text:
            raise AssertionError("WRAM/HRAM map missing expected rows")
        return "BGB/Emulicious symbol export parity ok (3 symbols, 2 memory labels)"

    return _capture(
        component="bgb_sym_export",
        next_command="make bgb_sym && python tools/audit/check_bgb_sym_parity.py",
        fn=inner,
    )


def check_probe(root: Path) -> CheckResult:
    """Exercise P8 named probes against a synthetic trace."""

    import json
    import tempfile

    from .probe import build_probe_stats_report, declare_probe

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            symbols = tmp_root / "pokegold.sym"
            trace = tmp_root / "trace.jsonl"
            store = tmp_root / "probes.jsonl"
            symbols.write_text("01:5A00 BattleCommand_DamageCalc\n", encoding="utf-8")
            trace.write_text(
                "\n".join(
                    json.dumps(event)
                    for event in (
                        {"pc_bank_address": "01:5A00", "pc_label": "BattleCommand_DamageCalc", "frame": 2, "seq": 0},
                        {"pc_bank_address": "01:5A00", "pc_label": "BattleCommand_DamageCalc+3", "frame": 6, "seq": 1},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            declare = declare_probe(
                name="damage_calc_entry",
                pc="BattleCommand_DamageCalc",
                store_path=str(store),
                symbols_path=str(symbols),
                root=tmp_root,
            )
            stats = build_probe_stats_report(traces=(trace,), store_path=str(store), root=tmp_root)
        if not declare.get("valid"):
            raise AssertionError(f"probe declare invalid: {declare.get('errors')}")
        if not stats.get("valid"):
            raise AssertionError(f"probe stats invalid: {stats.get('errors')}")
        item = stats["stats"][0]
        if item.get("fire_count") != 2:
            raise AssertionError(f"expected 2 fires; got {item}")
        if item.get("average_inter_fire_interval") != 4:
            raise AssertionError(f"expected 4-frame interval; got {item}")
        return "probe stats valid; damage_calc_entry fired 2 times across frames 2:6"

    return _capture(
        component="probe",
        next_command="python -m tools.debugger probe stats --trace <trace.jsonl>",
        fn=inner,
    )


def check_shrink_input_log(root: Path) -> CheckResult:
    """Exercise P10 input-log shrinking against a canonical input log."""

    import tempfile

    from .shrink_input_log import shrink_input_log

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            log = tmp_root / "ag08_inputs.txt"
            log.write_text(
                "\n".join(
                    [
                        *["WAIT 1" for _ in range(12)],
                        "A",
                        *["WAIT 1" for _ in range(12)],
                        "START",
                        *["WAIT 1" for _ in range(4)],
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            report = shrink_input_log(
                input_log="ag08_inputs.txt",
                root=tmp_root,
                out_log=".local/tmp/shrunk/ag08_inputs.txt",
                predicate=lambda candidate: "A" in candidate and "START" in candidate,
            )
            out_log = tmp_root / ".local/tmp/shrunk/ag08_inputs.txt"
            out_lines = out_log.read_text(encoding="utf-8").splitlines()
        if not report.get("valid"):
            raise AssertionError(f"shrink_input_log invalid: {report.get('errors')}")
        if report.get("shrunk_event_count") != 2:
            raise AssertionError(f"expected 2 shrunk events; got {report}")
        if out_lines != ["A", "START"]:
            raise AssertionError(f"unexpected shrunk log: {out_lines}")
        return "shrink_input_log reduced 30 events to canonical A/START reproducer"

    return _capture(
        component="shrink_input_log",
        next_command="python -m tools.debugger minimize --domain input_log --input-log <log>",
        fn=inner,
    )


def check_shrink_battle(root: Path) -> CheckResult:
    """Exercise P10 battle shrinking against a canonical six-Pokemon scenario."""

    from .shrink_battle import shrink_battle_scenario

    scenario = {
        "id": "selftest_battle_repro",
        "family": "battle",
        "enemy_party": [
            {"species": "PIDGEY", "moves": ["GUST", "SAND_ATTACK"]},
            {"species": "MILTANK", "moves": ["TACKLE", "ROLLOUT", "MILK_DRINK"]},
            {"species": "ZUBAT", "moves": ["LEECH_LIFE"]},
            {"species": "HAUNTER", "moves": ["LICK", "MEAN_LOOK", "CURSE"]},
            {"species": "RATTATA", "moves": ["QUICK_ATTACK"]},
            {"species": "GEODUDE", "moves": ["DEFENSE_CURL", "ROCK_THROW"]},
        ],
        "modifiers": ["rain", "critical_window", "badge_boost_noise"],
    }

    def predicate(candidate: dict[str, Any]) -> bool:
        party = candidate.get("enemy_party")
        if not isinstance(party, list):
            return False
        by_species = {
            str(mon.get("species")): mon
            for mon in party
            if isinstance(mon, dict)
        }
        miltank = by_species.get("MILTANK")
        haunter = by_species.get("HAUNTER")
        if not miltank or not haunter:
            return False
        return (
            "ROLLOUT" in miltank.get("moves", [])
            and "MEAN_LOOK" in haunter.get("moves", [])
            and "critical_window" in candidate.get("modifiers", [])
        )

    def inner() -> str:
        report = shrink_battle_scenario(scenario, predicate=predicate, root=root)
        if not report.get("valid"):
            raise AssertionError(f"shrink_battle invalid: {report.get('errors')}")
        shrunk_counts = report.get("shrunk_counts", {})
        if not isinstance(shrunk_counts, dict) or shrunk_counts.get("pokemon_count") != 2:
            raise AssertionError(f"expected 2 retained Pokemon; got {report}")
        shrunk = report.get("shrunk_scenario", {})
        party = shrunk.get("enemy_party", []) if isinstance(shrunk, dict) else []
        species = {mon.get("species") for mon in party if isinstance(mon, dict)}
        if species != {"MILTANK", "HAUNTER"}:
            raise AssertionError(f"unexpected retained party: {party}")
        return "shrink_battle reduced 6 Pokemon to canonical MILTANK/HAUNTER reproducer"

    return _capture(
        component="shrink_battle",
        next_command="python -B -m unittest tools.debugger.tests.test_shrink_battle",
        fn=inner,
    )


def check_shrink_map_script(root: Path) -> CheckResult:
    """Exercise P10 map-script shrinking against a canonical script reproducer."""

    from .shrink_map_script import shrink_map_script_scenario

    scenario = {
        "id": "selftest_script_repro",
        "scenario_type": "map_script",
        "steps": [
            {"op": "load_map", "map": "UnitHouse1F"},
            {"op": "walk", "direction": "UP"},
            {"op": "face_object", "object": "UnitNpc"},
            {"op": "open_text", "text": "noise"},
            {"op": "set_flag", "flag": "EVENT_UNIT_NPC_READY"},
            {"op": "jump_script", "label": "UnitNpcScript"},
            {"op": "show_text", "text": "hello"},
            {"op": "close_text"},
            {"op": "wait", "frames": 8},
        ],
        "events": [
            {"kind": "warp", "id": "noise"},
            {"kind": "bg_event", "id": "unit_signpost"},
            {"kind": "object_event", "id": "noise_npc"},
        ],
        "state_preconditions": [
            {"kind": "map_position", "map": "UnitHouse1F"},
            {"kind": "script_entry", "symbol": "UnitNpcScript"},
            {"kind": "time_of_day", "value": "day"},
        ],
    }

    def predicate(candidate: dict[str, Any]) -> bool:
        steps = candidate.get("steps")
        if not isinstance(steps, list):
            return False
        ops = [step.get("op") for step in steps if isinstance(step, dict)]
        events = candidate.get("events") if isinstance(candidate.get("events"), list) else []
        preconditions = (
            candidate.get("state_preconditions")
            if isinstance(candidate.get("state_preconditions"), list)
            else []
        )
        return (
            "face_object" in ops
            and "jump_script" in ops
            and "show_text" in ops
            and any(event.get("id") == "unit_signpost" for event in events if isinstance(event, dict))
            and any(
                item.get("kind") == "script_entry" and item.get("symbol") == "UnitNpcScript"
                for item in preconditions
                if isinstance(item, dict)
            )
        )

    def inner() -> str:
        report = shrink_map_script_scenario(scenario, predicate=predicate, root=root)
        if not report.get("valid"):
            raise AssertionError(f"shrink_map_script invalid: {report.get('errors')}")
        shrunk_counts = report.get("shrunk_counts", {})
        if not isinstance(shrunk_counts, dict) or shrunk_counts.get("step_count") != 3:
            raise AssertionError(f"expected 3 retained script steps; got {report}")
        shrunk = report.get("shrunk_scenario", {})
        steps = shrunk.get("steps", []) if isinstance(shrunk, dict) else []
        ops = [step.get("op") for step in steps if isinstance(step, dict)]
        if ops != ["face_object", "jump_script", "show_text"]:
            raise AssertionError(f"unexpected retained steps: {steps}")
        return "shrink_map_script reduced 9 steps to canonical face/jump/text reproducer"

    return _capture(
        component="shrink_map_script",
        next_command="python -B -m unittest tools.debugger.tests.test_shrink_map_script",
        fn=inner,
    )


def check_chaos(root: Path) -> CheckResult:
    """Exercise P11 chaos mode against stable and synthetic flake scenarios."""

    from .chaos import run_named_chaos_scenario

    def inner() -> str:
        stable = run_named_chaos_scenario(
            scenario="stable",
            runs=100,
            seed=1,
            frames=8,
        )
        if not stable.get("valid"):
            raise AssertionError(f"chaos stable invalid: {stable.get('errors')}")
        if stable.get("diverged"):
            raise AssertionError(f"stable chaos scenario diverged: {stable}")
        if stable.get("stable_count", 0) < 99:
            raise AssertionError(f"stable chaos scenario below 99/100 stable: {stable}")

        flake = run_named_chaos_scenario(
            scenario="synthetic_flake",
            runs=100,
            seed=1,
            frames=8,
        )
        if not flake.get("valid"):
            raise AssertionError(f"chaos synthetic flake invalid: {flake.get('errors')}")
        if not flake.get("diverged"):
            raise AssertionError(f"chaos synthetic flake did not diverge: {flake}")
        if not flake.get("candidate_input_log"):
            raise AssertionError(f"chaos synthetic flake did not capture input log: {flake}")
        return "chaos stable scenario stayed stable and synthetic flake produced replay seed"

    return _capture(
        component="chaos",
        next_command="python -m tools.debugger fuzz --chaos --runs 100 --seed 1 --chaos-scenario synthetic_flake",
        fn=inner,
    )


def check_save_state_lab(root: Path) -> CheckResult:
    """Round-trip trusted raw WRAM and fail-closed .sgm handling."""

    import tempfile

    from .save_state_lab import build_save_state_inspect_report

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            symbols = tmp_root / "unit.sym"
            symbols.write_text("00:D141 wCurDamage\n", encoding="utf-8")

            raw_wram = tmp_root / "unit.wram"
            data = bytearray(0x2000)
            data[0xD141 - 0xC000] = 0x34
            data[0xD142 - 0xC000] = 0x12
            raw_wram.write_bytes(data)

            inspect = build_save_state_inspect_report(
                state_path="unit.wram",
                symbols_path="unit.sym",
                symbols=("wCurDamage",),
                root=tmp_root,
            )
            if not inspect.get("valid", False):
                raise AssertionError(f"raw WRAM inspect invalid: {inspect.get('errors', [])}")
            fmt = inspect.get("format") or {}
            if fmt.get("id") != "raw_wram_8k":
                raise AssertionError(f"expected raw_wram_8k, got {fmt.get('id')!r}")
            if fmt.get("decode_supported") is not True:
                raise AssertionError("raw WRAM inspect did not report decode_supported=true")
            if inspect.get("symbol_count", 0) <= 0:
                raise AssertionError("raw WRAM inspect decoded no symbols")
            values = {item.get("symbol"): item for item in inspect.get("symbols", [])}
            cur_damage = values.get("wCurDamage")
            if cur_damage is None:
                raise AssertionError("raw WRAM inspect missing wCurDamage")
            if cur_damage.get("value_hex") != "34 12":
                raise AssertionError(
                    f"expected wCurDamage value_hex='34 12', got {cur_damage.get('value_hex')!r}"
                )

            sgm = tmp_root / "debug1.sgm"
            sgm.write_bytes(b"\x0c\x00\x00\x00POKEMON_GLDAAUE\x00" + bytes(256))
            sgm_report = build_save_state_inspect_report(
                state_path="debug1.sgm",
                symbols_path="unit.sym",
                symbols=("wCurDamage",),
                root=tmp_root,
            )
            sgm_fmt = sgm_report.get("format") or {}
            if sgm_fmt.get("id") != "vba_sgm_candidate":
                raise AssertionError(f"expected vba_sgm_candidate, got {sgm_fmt.get('id')!r}")
            if sgm_fmt.get("decode_supported") is not False:
                raise AssertionError(".sgm candidate did not fail closed with decode_supported=false")
            if not any(item.get("status") == "unmapped" for item in sgm_report.get("symbols", [])):
                raise AssertionError(".sgm candidate unexpectedly decoded requested symbol")
        return "save_state_lab raw WRAM + .sgm fail-closed round-trip ok"

    return _capture(
        component="save_state_lab",
        next_command="python -m tools.debugger.save_state_lab inspect <state> --symbol <symbol>",
        fn=inner,
    )


def check_bisect(root: Path) -> CheckResult:
    """Run the bisect harness against a synthetic git regression."""

    import subprocess
    import tempfile

    from .bisect import run_bisect

    def git(repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo),
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "bisect_selftest_repo"
            repo.mkdir()
            git(repo, "init", "--quiet")
            git(repo, "config", "user.email", "selftest@example.com")
            git(repo, "config", "user.name", "Debugger Selftest")
            git(repo, "config", "commit.gpgsign", "false")
            git(repo, "checkout", "-b", "main")

            commits: list[str] = []
            for index in range(5):
                (repo / "marker.txt").write_text(
                    "broken" if index >= 3 else "good",
                    encoding="utf-8",
                )
                (repo / "seq.txt").write_text(str(index), encoding="utf-8")
                git(repo, "add", "marker.txt", "seq.txt")
                git(repo, "commit", "-m", f"commit-{index}", "--quiet")
                commits.append(git(repo, "rev-parse", "HEAD").strip())

            scenario = [
                sys.executable,
                "-c",
                "import pathlib,sys; "
                "sys.exit(0 if pathlib.Path('marker.txt').read_text()=='good' else 1)",
            ]
            result = run_bisect(
                good_ref=commits[0],
                bad_ref=commits[-1],
                scenario_argv=scenario,
                repo=repo,
            )
            if result.first_bad_commit != commits[3]:
                raise AssertionError(
                    f"expected first bad commit {commits[3]}, got {result.first_bad_commit}"
                )
            if (repo / ".git" / "BISECT_LOG").exists():
                raise AssertionError("bisect state remained after run")
        return f"bisect synthetic regression localized in {result.steps} steps"

    return _capture(
        component="bisect",
        next_command="python -m tools.debugger.bisect --good <good> --bad <bad> -- <argv...>",
        fn=inner,
    )


def check_handoff_log(root: Path) -> CheckResult:
    """Exercise the two-LLM handoff log gate end-to-end on a temp store."""

    import tempfile

    from .handoff_log import HandoffRow, append_row, audit_store

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "handoff.jsonl"

            def add(model: str, event: str, status: str, **extras: object) -> None:
                append_row(
                    HandoffRow(
                        phase="selftest",
                        event=event,
                        status=status,
                        model=model,
                        primary="codex",
                        reviewer=str(extras.pop("reviewer", "")) if event == "slice_review" else "",
                        confidence="repo-proven",
                        claim=f"selftest {event} by {model}",
                    ),
                    store=store,
                    root=Path(tmp),
                )

            add("codex", "ack_start", "in_progress")
            add("codex", "slice_update", "ready_for_review")
            report_before = audit_store(store=store, root=Path(tmp))
            if report_before["phase_status"]["selftest"]["mutual_verified"]:
                raise AssertionError(
                    "mutual_verified must be False before non-primary review"
                )

            add("claude", "slice_review", "slice_accepted", reviewer="claude")
            report_after = audit_store(store=store, root=Path(tmp))
            if not report_after["phase_status"]["selftest"]["mutual_verified"]:
                raise AssertionError(
                    "mutual_verified must be True after repo-proven cross-model review"
                )
            if report_after["row_errors"]:
                raise AssertionError(
                    f"unexpected row errors: {report_after['row_errors']}"
                )
        return "handoff_log mutual-agreement gate round-trip ok"

    return _capture(
        component="handoff_log",
        next_command="python -m tools.debugger handoff verify",
        fn=inner,
    )


def check_when_wrote(root: Path) -> CheckResult:
    """Run the when-wrote query against a synthetic effect trace."""

    import json
    import tempfile

    from .when_wrote import run_when_wrote

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            key = "wramx:01:D141"
            trace = {
                "schema_version": 1,
                "kind": "unified_debugger_effect_trace",
                "valid": True,
                "proof_status": "instruction_observed",
                "write_index": [
                    {
                        "address": "D141",
                        "address_key": key,
                        "space": "wramx",
                        "bank": 1,
                        "write_count": 1,
                        "last_writer_seq": 4,
                        "last_writer_pc": "01:5A00",
                        "last_value_hex": "2A",
                    }
                ],
                "events": [
                    {
                        "seq": 4,
                        "pc_bank_address": "01:5A00",
                        "pc_label": "BattleCommand_DamageCalc+6",
                        "bank_state": {"wram": 1},
                        "bank_state_sources": {"wram": "bank_state.wram"},
                        "effects": [
                            {
                                "access": "write",
                                "kind": "memory_write",
                                "operation": "ld [hl], a",
                                "address_hex": "D141",
                                "address_key": key,
                                "value_hex": "2A",
                                "value_source": "A",
                                "bank": 1,
                                "bank_source": "bank_state.wram",
                                "space": "wramx",
                                "post_value_hex": "2A",
                                "post_value_status": "matched",
                                "post_observed_seq": 5,
                                "post_observed_pc": "01:5A03",
                                "proof_status": "instruction_observed",
                            }
                        ],
                    }
                ],
            }
            (tmp_root / "pokegold.sym").write_text("01:5A00 BattleCommand_DamageCalc\n", encoding="utf-8")
            (tmp_root / "effect.json").write_text(json.dumps(trace), encoding="utf-8")
            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                root=tmp_root,
            )
            if not report.get("valid"):
                raise AssertionError(f"when-wrote report invalid: {report}")
            if report.get("answer_count") != 1:
                raise AssertionError(f"expected one answer, got {report.get('answer_count')}")
            answer = report["answers"][0]
            if answer.get("proof_status") != "instruction_observed":
                raise AssertionError(
                    f"expected instruction_observed, got {answer.get('proof_status')}"
                )
            writer = answer.get("last_writer") or {}
            if writer.get("pc") != "01:5A00":
                raise AssertionError(f"unexpected writer pc: {writer}")
        return "when-wrote returns concrete observed writer with exact bank key"

    return _capture(
        component="when_wrote",
        next_command="python -m tools.debugger.when_wrote --address D141 --report <effect.json>",
        fn=inner,
    )


def check_sm83_model_parity(root: Path) -> CheckResult:
    """Exercise both SM83 consumers on a shared-model-backed trace."""

    import tempfile

    from .dynamic_taint import build_dynamic_taint_report
    from .effect_trace import build_effect_trace_report
    from .sm83_model import SM83_MODEL_SOURCE

    def inner() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "test.sym").write_text("01:4000 UnitFunc\n", encoding="utf-8")
            (tmp_root / "instruction_trace.jsonl").write_text(
                "\n".join(
                    json.dumps(record)
                    for record in [
                        {
                            "seq": 0,
                            "bank": 1,
                            "pc": 0x4000,
                            "pc_label": "LoadSeed",
                            "opcode": 0x2A,
                            "regs": {"A": 0x00, "HL": 0xC200, "SP": 0xDFF0},
                            "watch_values": {"$C200": "37"},
                        },
                        {
                            "seq": 1,
                            "bank": 1,
                            "pc": 0x4001,
                            "pc_label": "StoreSeed",
                            "opcode": 0xEA,
                            "operand": [0x41, 0xD1],
                            "regs": {"A": 0x37, "HL": 0xC201, "SP": 0xDFF0},
                        },
                        {
                            "seq": 2,
                            "bank": 1,
                            "pc": 0x4004,
                            "pc_label": "RlB",
                            "opcode": 0xCB,
                            "operand": [0x10],
                            "regs": {"B": 0x7F, "F": 0x10, "SP": 0xDFF0},
                        },
                        {
                            "seq": 3,
                            "bank": 1,
                            "pc": 0x4006,
                            "pc_label": "StoreB",
                            "opcode": 0x70,
                            "regs": {"HL": 0xC202, "B": 0xFF, "SP": 0xDFF0},
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            effect = build_effect_trace_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                watch_addresses=("C200", "D141", "C202"),
                root=tmp_root,
            )
            dynamic = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                source_mems=("C200=seed_byte",),
                source_regs=("b=seed_b",),
                sink_addresses=("D141", "C202"),
                root=tmp_root,
            )
        if not effect.get("valid"):
            raise AssertionError(f"effect trace invalid: {effect.get('errors', [])}")
        if not dynamic.get("valid"):
            raise AssertionError(f"dynamic taint invalid: {dynamic.get('errors', [])}")
        effect_ops = {
            item.get("operation"): item.get("model_source")
            for event in effect.get("events", [])
            for item in event.get("effects", [])
            if item.get("operation") in {"ld a, [hli]", "ld a, [hli] updates hl", "rl b", "rl b flags"}
        }
        for operation in ("ld a, [hli]", "ld a, [hli] updates hl", "rl b", "rl b flags"):
            if effect_ops.get(operation) != SM83_MODEL_SOURCE:
                raise AssertionError(f"effect trace missing shared model source for {operation}: {effect_ops}")
        seed_store = next(
            (item for item in dynamic.get("write_attributions", []) if item.get("address") == "D141"),
            None,
        )
        cb_store = next(
            (item for item in dynamic.get("write_attributions", []) if item.get("address") == "C202"),
            None,
        )
        if seed_store is None or cb_store is None:
            raise AssertionError(f"dynamic taint missing expected attributions: {dynamic.get('write_attributions', [])}")
        seed_provenance = seed_store.get("register_provenance") or []
        if not any(
            item.get("operation") == "ld a, [hli]"
            and item.get("model_source") == SM83_MODEL_SOURCE
            for item in seed_provenance
        ):
            raise AssertionError(f"seed store missing shared HLI provenance: {seed_provenance}")
        cb_provenance = cb_store.get("register_provenance") or []
        if not any(
            item.get("operation") == "rl b"
            and item.get("model_source") == SM83_MODEL_SOURCE
            for item in cb_provenance
        ):
            raise AssertionError(f"CB store missing shared CB provenance: {cb_provenance}")
        return "effect_trace and dynamic_taint agree on shared SM83 HLI/CB provenance"

    return _capture(
        component="sm83_model_parity",
        next_command="python tools/audit/check_sm83_shared_tables_consumers.py && python -B -m unittest tools.debugger.tests.test_sm83_shared_tables_consumers",
        fn=inner,
    )


def check_rom_edit(root: Path) -> CheckResult:
    """Exercise P12 rom-edit propose/verify/apply-to-main in a temp repo."""

    from .rom_edit import run_self_test

    def inner() -> str:
        report = run_self_test()
        if not report.get("passed"):
            raise AssertionError(f"rom-edit selftest failed: {report}")
        return "rom-edit temp repo propose/build/verify/apply-to-main round-trip ok"

    return _capture(
        component="rom_edit",
        next_command="python -m tools.debugger rom-edit --self-test",
        fn=inner,
    )


NAMED_CHECKS: tuple[tuple[str, Check], ...] = (
    ("capability_audit", check_capability_audit),
    ("inventory", check_inventory),
    ("ingest", check_ingest),
    ("triage", check_triage),
    ("coverage", check_coverage),
    ("provenance", check_provenance),
    ("mirrors_compare", check_mirrors),
    ("fuzz", check_fuzz),
    ("trace_index", check_trace_index),
    ("visualization", check_visualization),
    ("hypothesis_tracker", check_hypothesis_tracker),
    ("context_packet", check_context_packet),
    ("heatmap", check_heatmap),
    ("vram_decode", check_vram_decode),
    ("bgb_sym_export", check_bgb_sym_export),
    ("probe", check_probe),
    ("shrink_input_log", check_shrink_input_log),
    ("shrink_battle", check_shrink_battle),
    ("shrink_map_script", check_shrink_map_script),
    ("chaos", check_chaos),
    ("save_state_lab", check_save_state_lab),
    ("bisect", check_bisect),
    ("handoff_log", check_handoff_log),
    ("when_wrote", check_when_wrote),
    ("sm83_model_parity", check_sm83_model_parity),
    ("rom_edit", check_rom_edit),
)

CHECKS: tuple[Check, ...] = tuple(check for _, check in NAMED_CHECKS)


def run_selftest(*, root: Path = ROOT, checks: Sequence[Check] | None = None) -> SelftestReport:
    selected = checks if checks is not None else CHECKS
    results = [check(root) for check in selected]
    ok = all(r.ok for r in results)
    return SelftestReport(ok=ok, results=results)


def _format_text(report: SelftestReport) -> str:
    lines: list[str] = []
    failed = sum(1 for r in report.results if not r.ok)
    overall = "PASS" if report.ok else "FAIL"
    lines.append(f"Selftest {overall}  ({len(report.results) - failed}/{len(report.results)} components healthy)")
    for r in report.results:
        marker = "  [ok]  " if r.ok else "  [FAIL]"
        line = f"{marker} {r.component}"
        if r.ok and r.detail:
            line += f"  — {r.detail}"
        lines.append(line)
        if not r.ok:
            lines.append(f"           error:        {r.error}")
            lines.append(f"           next command: {r.next_command}")
    if not report.ok:
        lines.append("")
        lines.append("Selftest is the v2 health gate. Audit (python -m tools.debugger audit)")
        lines.append("remains the v1 readiness signal — selftest failure does NOT regress v1")
        lines.append("readiness; it indicates a component is broken end-to-end.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.selftest",
        description=(
            "Run end-to-end synthetic-input checks for the unified debugger. "
            "Reports pass/fail per component and a next-command hint for each. "
            "Exits nonzero on any failure."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of human text",
    )
    parser.add_argument(
        "--component",
        action="append",
        default=None,
        help="restrict to one or more components by name (repeatable)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    selected: Sequence[Check] | None = None
    if args.component:
        wanted = set(args.component)
        registry = {name: check for name, check in NAMED_CHECKS}
        unknown = wanted - set(registry)
        if unknown:
            print(
                f"error: unknown component(s): {', '.join(sorted(unknown))}",
                file=sys.stderr,
            )
            return 2
        selected = tuple(registry[name] for name in args.component if name in registry)
    report = run_selftest(checks=selected)
    if args.json:
        print(json.dumps(report.to_jsonable(), sort_keys=True))
    else:
        print(_format_text(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
