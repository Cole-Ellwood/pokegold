"""Per-PC coverage report for the damage debugger scenarios.

M3 goal: make the remaining untested damage-path surface visible. The
collector walks selected SM83 functions, installs a PyBoy hook at every
instruction PC, runs the supported `clobber_smoke` scenarios, and renders
a Markdown table under `audit/damage_debugger/coverage.md`.

The report is not a correctness proof. It is a visibility tool: after H4,
it should show which functions have smoke coverage and which still need
future scenarios or fuzz axes.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .boot_cache import BootStateCache
from .clobber_smoke import SCENARIOS, Scenario, parse_sym
from .disasm import Instruction, walk_function
from .emulator import DebugSession
from .paths import find_rom, find_sym
from .safe_call import call_function_safe


DEFAULT_TARGETS = (
    "BattleCommand_DamageStats",
    "BattleCommand_DamageCalc",
    "BattleCommand_Stab",
    "BattleCommand_DamageVariation",
    # CheckTypeMatchup can be targeted explicitly, but per-PC hooks inside
    # its long table loop make the full H4 scenario set too slow for the
    # default report. BattleCommand_Stab still covers the main matchup loop;
    # M2's --instrument-hook covers focused CheckTypeMatchup.Yup probes.
    "ApplyLateGenDamageStatsItemMods_Far",
    "TypePassive_ApplyDamageModifiers_Far",
    "HandleLateGenAfterHitEffects_Far",
)

DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "audit"
    / "damage_debugger"
    / "coverage.md"
)


@dataclass
class FunctionCoverage:
    name: str
    instructions: list[Instruction]
    hits: set[int] = field(default_factory=set)
    scenario_hits: dict[str, set[int]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len({instr.pc for instr in self.instructions})

    @property
    def covered(self) -> int:
        return len(self.hits)

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 100.0
        return self.covered * 100.0 / self.total

    @property
    def scenarios(self) -> list[str]:
        return sorted(name for name, hits in self.scenario_hits.items() if hits)


@dataclass
class CoverageReport:
    functions: list[FunctionCoverage]
    scenario_count: int
    rom: Path
    sym: Path

    @property
    def total_instructions(self) -> int:
        return sum(f.total for f in self.functions)

    @property
    def covered_instructions(self) -> int:
        return sum(f.covered for f in self.functions)

    @property
    def total_percent(self) -> float:
        total = self.total_instructions
        if total == 0:
            return 100.0
        return self.covered_instructions * 100.0 / total

    def to_dict(self) -> dict:
        return {
            "rom": str(self.rom),
            "sym": str(self.sym),
            "scenario_count": self.scenario_count,
            "total": {
                "instructions": self.total_instructions,
                "covered": self.covered_instructions,
                "percent": round(self.total_percent, 2),
            },
            "functions": [
                {
                    "name": f.name,
                    "instructions": f.total,
                    "covered": f.covered,
                    "percent": round(f.percent, 2),
                    "scenarios": f.scenarios,
                    "missed_pcs": [
                        f"${instr.bank:02x}:{instr.pc:04x}"
                        for instr in f.instructions
                        if instr.pc not in f.hits
                    ],
                }
                for f in self.functions
            ],
        }


def _load_instructions(targets: Iterable[str]) -> dict[str, list[Instruction]]:
    with DebugSession.open("pokegold_debug") as sess:
        def read_byte(bank: int, addr: int) -> int:
            if addr < 0x4000:
                return int(sess.pyboy.memory[addr])
            return int(sess.pyboy.memory[bank, addr])

        out: dict[str, list[Instruction]] = {}
        for target in targets:
            if target not in sess.symbols:
                out[target] = []
                continue
            out[target] = walk_function(
                read_byte,
                sess.symbols,
                target,
                max_bytes=0x1000,
            )
        return out


def _install_hooks(
    pyboy,
    coverages: dict[str, FunctionCoverage],
    current_scenario: list[str],
) -> list[tuple[int, int]]:
    installed: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    for fc in coverages.values():
        for instr in fc.instructions:
            key = (instr.bank, instr.pc)
            if key in seen:
                continue
            seen.add(key)

            def make_cb(function_name: str, pc: int):
                def cb(_):
                    sc_name = current_scenario[0]
                    fc_inner = coverages[function_name]
                    fc_inner.hits.add(pc)
                    fc_inner.scenario_hits.setdefault(sc_name, set()).add(pc)
                return cb

            pyboy.hook_register(instr.bank, instr.pc, make_cb(fc.name, instr.pc), None)
            installed.append(key)
    return installed


def _deregister_hooks(pyboy, hooks: list[tuple[int, int]]) -> None:
    for bank, pc in hooks:
        try:
            pyboy.hook_deregister(bank, pc)
        except Exception:
            pass


def _run_scenario_for_coverage(
    pyboy,
    syms: dict,
    scenario: Scenario,
) -> list[str]:
    failures: list[str] = []
    scenario.seed(pyboy, syms)
    for fn in scenario.chain:
        ticks, returned, post_pc = call_function_safe(pyboy, syms, fn, budget=scenario.call_budget)
        if not returned and not scenario.allow_nonreturn:
            failures.append(
                f"{scenario.name}: {fn} did not return in {ticks} ticks (PC=${post_pc:04x})"
            )
    return failures


def collect_coverage(targets: Iterable[str] = DEFAULT_TARGETS) -> CoverageReport:
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    instructions = _load_instructions(targets)
    coverages = {
        name: FunctionCoverage(name=name, instructions=instrs)
        for name, instrs in instructions.items()
    }

    cache = BootStateCache(rom)
    cache.prime()
    current_scenario = [""]
    failures: list[str] = []
    try:
        for scenario in SCENARIOS:
            current_scenario[0] = scenario.name
            pyboy = cache.restore()
            hooks = _install_hooks(pyboy, coverages, current_scenario)
            try:
                failures.extend(_run_scenario_for_coverage(pyboy, syms, scenario))
            finally:
                _deregister_hooks(pyboy, hooks)
    finally:
        cache.stop()

    if failures:
        raise RuntimeError("; ".join(failures))
    return CoverageReport(
        functions=list(coverages.values()),
        scenario_count=len(SCENARIOS),
        rom=rom,
        sym=sym,
    )


def render_markdown(report: CoverageReport) -> str:
    lines: list[str] = []
    lines.append("# Damage Debugger Coverage")
    lines.append("")
    lines.append("Generated by `python -m tools.damage_debugger.coverage --write`.")
    lines.append("")
    lines.append(f"- ROM: `{report.rom}`")
    lines.append(f"- SYM: `{report.sym}`")
    lines.append(f"- Scenarios: {report.scenario_count}")
    lines.append(
        f"- Total: {report.covered_instructions}/{report.total_instructions} "
        f"PCs ({report.total_percent:.1f}%)"
    )
    lines.append("")
    lines.append("| Function | Covered PCs | Total PCs | Coverage | Scenario Hits |")
    lines.append("| --- | ---: | ---: | ---: | --- |")
    for fc in report.functions:
        scenarios = ", ".join(fc.scenarios) if fc.scenarios else "-"
        lines.append(
            f"| `{fc.name}` | {fc.covered} | {fc.total} | {fc.percent:.1f}% | {scenarios} |"
        )
    lines.append("")
    lines.append("## Missed PCs")
    lines.append("")
    for fc in report.functions:
        missed = [instr for instr in fc.instructions if instr.pc not in fc.hits]
        if not missed:
            continue
        preview = ", ".join(f"`${instr.bank:02x}:{instr.pc:04x}`" for instr in missed[:24])
        more = "" if len(missed) <= 24 else f" ... (+{len(missed) - 24} more)"
        lines.append(f"- `{fc.name}`: {preview}{more}")
    if all(fc.covered == fc.total for fc in report.functions):
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def threshold_failures(report: CoverageReport, fail_under: float | None) -> list[str]:
    if fail_under is None:
        return []
    return [
        f"{fc.name}: {fc.percent:.1f}% below {fail_under:.1f}%"
        for fc in report.functions
        if fc.percent < fail_under
    ]


def write_report(report: CoverageReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")


def _synthetic_report() -> CoverageReport:
    instrs_a = [
        Instruction(0, 0x1000, 0x00, b"", 1, "nop"),
        Instruction(0, 0x1001, 0x00, b"", 1, "nop"),
    ]
    instrs_b = [
        Instruction(0, 0x2000, 0x00, b"", 1, "nop"),
        Instruction(0, 0x2001, 0x00, b"", 1, "nop"),
    ]
    fc_a = FunctionCoverage("A", instrs_a, hits={0x1000, 0x1001},
                            scenario_hits={"synthetic": {0x1000, 0x1001}})
    fc_b = FunctionCoverage("B", instrs_b, hits={0x2000},
                            scenario_hits={"synthetic": {0x2000}})
    return CoverageReport(
        functions=[fc_a, fc_b],
        scenario_count=1,
        rom=Path("synthetic.gbc"),
        sym=Path("synthetic.sym"),
    )


def _self_test() -> int:
    report = _synthetic_report()
    md = render_markdown(report)
    data = report.to_dict()
    failures: list[str] = []
    if "| Function | Covered PCs | Total PCs | Coverage | Scenario Hits |" not in md:
        failures.append("markdown table header missing")
    if "## Missed PCs" not in md or "`$00:2001`" not in md:
        failures.append("missed-PC section missing expected PC")
    if data["total"]["instructions"] != 4 or data["total"]["covered"] != 3:
        failures.append("JSON summary totals wrong")
    if not threshold_failures(report, 75.1):
        failures.append("threshold failure behavior did not trigger")
    if threshold_failures(report, 49.0):
        failures.append("threshold failure behavior triggered unexpectedly")

    if failures:
        print("coverage self-test: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("coverage self-test: PASS")
    print("  markdown shape, JSON schema, missed-PC list, and threshold behavior")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate damage-debugger per-PC coverage")
    parser.add_argument("--write", nargs="?", const=str(DEFAULT_OUTPUT), default=None,
                        help="Write Markdown coverage report (default path if no value)")
    parser.add_argument("--json", action="store_true",
                        help="Print JSON summary to stdout")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="Exit 1 if any target function is below this coverage percent")
    parser.add_argument("--target", action="append", default=None,
                        help="Function symbol to include; can be repeated")
    parser.add_argument("--self-test", action="store_true",
                        help="Run synthetic output/threshold self-tests")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    targets = tuple(args.target) if args.target else DEFAULT_TARGETS
    report = collect_coverage(targets)
    if args.write is not None:
        out = Path(args.write)
        write_report(report, out)
        print(f"coverage: wrote {out}")
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    if args.write is None and not args.json:
        print(render_markdown(report))

    failures = threshold_failures(report, args.fail_under)
    if failures:
        for failure in failures:
            print(f"coverage threshold: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
