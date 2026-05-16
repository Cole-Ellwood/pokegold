"""Unified debugger CLI.

Entry point: ``python -m tools.debugger <command> [args]``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


TOOL_REGISTRY: list[dict[str, str]] = [
    {
        "name": "damage_debugger",
        "entry": "python -m tools.damage_debugger.clobber_smoke",
        "description": "Battle-engine step tracer, oracle, fuzz, clobber smoke",
        "readme": "tools/damage_debugger/README.md",
    },
    {
        "name": "boss_ai_debugger",
        "entry": "python -m tools.boss_ai_debugger",
        "description": "Boss AI decision debugger: fixtures, scoring, traces, coverage",
        "readme": "tools/boss_ai_debugger/README.md",
    },
    {
        "name": "boss_ai_preference",
        "entry": "python -m tools.boss_ai_preference",
        "description": "Preference-labeling side app for boss AI pairwise judgments",
        "readme": "tools/boss_ai_preference/README.md",
    },
    {
        "name": "pokemon_mastery",
        "entry": "python -m tools.pokemon_mastery",
        "description": "Case library and compounding-loop infrastructure",
        "readme": "",
    },
    {
        "name": "trace",
        "entry": "tools/trace/",
        "description": "PyBoy state factory, trace batch capture, replay plumbing",
        "readme": "",
    },
    {
        "name": "audit",
        "entry": "python tools/audit/check_release_smoke.py",
        "description": "40+ static audit scripts (release-smoke floor)",
        "readme": "",
    },
]


def cmd_status(args: argparse.Namespace) -> int:
    print("=== Pokemon Gold Hack — Debugger Status ===\n")
    print(f"Project root: {ROOT}\n")

    print("Registered tools:\n")
    for tool in TOOL_REGISTRY:
        readme_path = ROOT / tool["readme"] if tool["readme"] else None
        has_readme = readme_path.exists() if readme_path else False
        readme_tag = " [README]" if has_readme else ""
        print(f"  {tool['name']:<25} {tool['description']}")
        print(f"    entry: {tool['entry']}{readme_tag}")

    print("\nBuild artifacts:")
    for variant in ("pokegold", "pokegold_debug"):
        for ext in (".gbc", ".sym", ".map"):
            artifact = ROOT / f"{variant}{ext}"
            exists = artifact.exists()
            tag = "found" if exists else "MISSING"
            print(f"  {variant}{ext:<8} {tag}")

    print("\nAudit scripts:")
    audit_dir = ROOT / "tools" / "audit"
    if audit_dir.is_dir():
        scripts = sorted(audit_dir.glob("check_*.py"))
        for s in scripts:
            print(f"  {s.name}")
        print(f"  ({len(scripts)} total)")
    else:
        print("  tools/audit/ not found")

    print("\nDebugger roadmap: docs/debugger_roadmap.md")
    roadmap = ROOT / "docs" / "debugger_roadmap.md"
    if roadmap.exists():
        print(f"  size: {roadmap.stat().st_size:,} bytes")
    else:
        print("  NOT FOUND")

    return 0


def cmd_symbol_resolve(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    sym = svc.resolve(args.name)
    if sym is None:
        candidates = svc.prefix_search(args.name)
        if candidates:
            print(f"Symbol '{args.name}' not found. Did you mean:")
            for c in candidates[:10]:
                print(f"  {c}")
        else:
            print(f"Symbol '{args.name}' not found.")
        return 1

    print(f"name:    {sym.name}")
    print(f"bank:    ${sym.bank:02x} ({sym.bank})")
    print(f"address: ${sym.address:04x} ({sym.address})")
    return 0


def cmd_symbol_render(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    spec = args.spec
    if ":" not in spec:
        print(f"error: expected bank:addr format (e.g. 01:4000), got '{spec}'")
        return 1

    bank_s, addr_s = spec.split(":", 1)
    try:
        bank = int(bank_s, 16)
        addr = int(addr_s, 16)
    except ValueError:
        print(f"error: invalid hex in '{spec}'")
        return 1

    label = svc.render(bank, addr)
    print(label)
    return 0


def cmd_macro_classify(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .instrumentation.macro_resolver import MacroResolver

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rom_path = None
    for name in (f"{args.variant}.gbc", f"{args.variant}_debug.gbc"):
        candidate = ROOT / name
        if not candidate.exists():
            for p in ROOT.parents:
                candidate = p / name
                if candidate.exists():
                    break
        if candidate.exists():
            rom_path = candidate
            break

    if rom_path is None:
        print("error: ROM not found. Build first.", file=sys.stderr)
        return 1

    rom = rom_path.read_bytes()
    resolver = MacroResolver(svc)

    spec = args.spec
    if ":" not in spec:
        sym = svc.resolve(spec)
        if sym is None:
            print(f"Symbol '{spec}' not found.", file=sys.stderr)
            return 1
        bank, pc = sym.bank, sym.address
    else:
        bank_s, addr_s = spec.split(":", 1)
        bank = int(bank_s, 16)
        pc = int(addr_s, 16)

    ctx = resolver.classify(rom, bank, pc)
    print(f"PC:    ${bank:02x}:{pc:04x} ({svc.render(bank, pc)})")
    print(f"Macro: {ctx}")
    if ctx.is_macro:
        print(f"  target: ${ctx.target_bank:02x}:{ctx.target_addr:04x} {ctx.target_label}")
        print(f"  expansion: ${ctx.expansion_start_pc:04x}-${ctx.expansion_end_pc:04x}")
        print(f"  position: byte {ctx.position_in_expansion}")
    return 0


def cmd_schema_show(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .kernel.state_schema import WorldState

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    ws = WorldState.from_symbol_service(svc)
    print(ws.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger",
        description="Unified debugger for the Pokemon Gold hack",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="List all tool entry-points and build artifacts")

    sym_parser = sub.add_parser("symbol", help="Symbol service commands")
    sym_sub = sym_parser.add_subparsers(dest="sym_command")

    resolve_p = sym_sub.add_parser("resolve", help="Resolve symbol name to bank:addr")
    resolve_p.add_argument("name", help="Symbol name (e.g. wBattleMonHP)")
    resolve_p.add_argument("--variant", default="pokegold", help="ROM variant")

    render_p = sym_sub.add_parser("render", help="Render bank:addr as label name")
    render_p.add_argument("spec", help="Bank:addr in hex (e.g. 01:4000)")
    render_p.add_argument("--variant", default="pokegold", help="ROM variant")

    macro_parser = sub.add_parser("macro", help="Macro resolver commands")
    macro_sub = macro_parser.add_subparsers(dest="macro_command")

    classify_p = macro_sub.add_parser("classify", help="Classify PC as macro expansion")
    classify_p.add_argument("spec", help="bank:addr or symbol name")
    classify_p.add_argument("--variant", default="pokegold", help="ROM variant")

    schema_parser = sub.add_parser("schema", help="State schema commands")
    schema_sub = schema_parser.add_subparsers(dest="schema_command")

    show_p = schema_sub.add_parser("show", help="Print region summary")
    show_p.add_argument("--variant", default="pokegold", help="ROM variant")

    mcp_parser = sub.add_parser("mcp", help="MCP server / tool dispatch")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command")

    mcp_list_p = mcp_sub.add_parser("list", help="List available MCP tools")
    mcp_call_p = mcp_sub.add_parser("call", help="Call an MCP tool")
    mcp_call_p.add_argument("tool", help="Tool name")
    mcp_call_p.add_argument("params", nargs="*", help="key=value params")
    mcp_sub.add_parser("stdio", help="Run MCP server over stdin/stdout (JSON-RPC)")

    # --- battle subcommand ---
    battle_parser = sub.add_parser("battle", help="Battle analysis commands")
    battle_sub = battle_parser.add_subparsers(dest="battle_command")

    damage_p = battle_sub.add_parser("damage", help="Damage chain diagram")
    damage_p.add_argument("attacker", help="SPECIES:LEVEL")
    damage_p.add_argument("defender", help="SPECIES:LEVEL")
    damage_p.add_argument("move", help="Move name")
    damage_p.add_argument("--explain", action="store_true", help="Full breakdown")
    damage_p.add_argument("--format", choices=["text", "arrow", "markdown"], default="text")
    damage_p.add_argument("--bp", type=int, help="Move base power (required if no move DB)")
    damage_p.add_argument("--atk", type=int, help="Attacker's attack stat")
    damage_p.add_argument("--dfn", type=int, help="Defender's defense stat")
    damage_p.add_argument("--move-type", type=int, default=0, help="Move type index")
    damage_p.add_argument("--physical", action="store_true", default=True, help="Physical move (default)")
    damage_p.add_argument("--special", action="store_true", help="Special move")

    # --- static subcommand ---
    static_parser = sub.add_parser("static", help="Static analysis commands")
    static_sub = static_parser.add_subparsers(dest="static_command")

    clobber_p = static_sub.add_parser("clobber-summary", help="Infer register clobber set")
    clobber_p.add_argument("function", help="Function name")
    clobber_p.add_argument("--variant", default="pokegold", help="ROM variant")

    pressure_p = static_sub.add_parser("bank-pressure", help="Bank free-space report")
    pressure_p.add_argument("--threshold", type=int, default=256, help="Free-byte threshold")
    pressure_p.add_argument("--variant", default="pokegold", help="ROM variant")
    pressure_p.add_argument("--full", action="store_true", help="Show all banks")

    savelock_p = static_sub.add_parser("save-lock", help="Save format lock check")
    savelock_p.add_argument("--lockfile", default="save_format.lock", help="Lockfile path")
    savelock_p.add_argument("--generate", action="store_true", help="Generate new lockfile")
    savelock_p.add_argument("--variant", default="pokegold", help="ROM variant")

    analyze_p = static_sub.add_parser("analyze", help="Run all static analyses")
    analyze_p.add_argument("--variant", default="pokegold", help="ROM variant")

    query_parser = sub.add_parser("query", help="Search symbols by prefix")
    query_parser.add_argument("expression", help="Symbol prefix to search")
    query_parser.add_argument("--variant", default="pokegold", help="ROM variant")
    query_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # --- selftest ---
    sub.add_parser("selftest", help="Run all component self-tests")

    # --- metamorphic ---
    meta_parser = sub.add_parser("metamorphic", help="Run damage metamorphic relations")
    meta_parser.add_argument("--count", type=int, default=10, help="Number of random scenarios")

    # --- fuzz ---
    fuzz_parser = sub.add_parser("fuzz", help="Run Hypothesis battle fuzz")
    fuzz_parser.add_argument("--examples", type=int, default=200, help="Max examples")

    # --- bisect ---
    bisect_parser = sub.add_parser("bisect", help="Git bisect with scenario criterion")
    bisect_parser.add_argument("--scenario", required=True, help="Shell command returning 0=good")
    bisect_parser.add_argument("--good", required=True, help="Known-good commit")
    bisect_parser.add_argument("--bad", default="HEAD", help="Known-bad commit")
    bisect_parser.add_argument("--build-cmd", help="Build command to run before test")

    # --- tournament ---
    tour_parser = sub.add_parser("tournament", help="Run trainer tournament")
    tour_parser.add_argument("--dry-run", action="store_true", help="List trainers without running")
    tour_parser.add_argument("--emulate", action="store_true", help="Run matches in PyBoy emulator")

    # --- savelab ---
    savelab_parser = sub.add_parser("savelab", help="Save-state lab commands")
    savelab_sub = savelab_parser.add_subparsers(dest="savelab_command")
    decode_p = savelab_sub.add_parser("decode", help="Decode a VBA .sgm save state")
    decode_p.add_argument("path", help="Path to .sgm file")
    diff_save_p = savelab_sub.add_parser("diff", help="Diff two save states")
    diff_save_p.add_argument("left", help="First state file")
    diff_save_p.add_argument("right", help="Second state file")

    # --- web ---
    web_parser = sub.add_parser("web", help="Start web UI")
    web_parser.add_argument("--port", type=int, default=8765, help="Port number")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host address")

    # --- hypothesis ---
    hyp_parser = sub.add_parser("hypothesis", help="Hypothesis tracker commands")
    hyp_sub = hyp_parser.add_subparsers(dest="hyp_command")
    hyp_add = hyp_sub.add_parser("add", help="Add a hypothesis")
    hyp_add.add_argument("statement", help="Hypothesis statement")
    hyp_add.add_argument("--tag", action="append", default=[], help="Tags")
    hyp_list = hyp_sub.add_parser("list", help="List hypotheses")
    hyp_list.add_argument("--status", help="Filter by status")
    hyp_tree = hyp_sub.add_parser("tree", help="Show hypothesis tree")

    return parser


def cmd_static_clobber(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .analysis.static.clobber_inference import infer_summary

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rom_path = None
    for name in (f"{args.variant}.gbc", f"{args.variant}_debug.gbc"):
        for root_dir in (ROOT,) + tuple(ROOT.parents[:5]):
            candidate = root_dir / name
            if candidate.exists():
                rom_path = candidate
                break
        if rom_path:
            break

    if rom_path is None:
        print("error: ROM not found. Build first.", file=sys.stderr)
        return 1

    rom = rom_path.read_bytes()
    summary = infer_summary(args.function, svc, rom)
    if summary is None:
        print(f"Symbol '{args.function}' not found.", file=sys.stderr)
        return 1

    import json
    print(json.dumps(summary.to_dict(), indent=2))
    return 0


def cmd_static_bank_pressure(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .analysis.static.bank_pressure import BankPressureChecker

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    checker = BankPressureChecker(svc)
    report = checker.check(threshold=args.threshold)
    if args.full:
        print(report.full_report())
    else:
        print(report.summary())
    return 0 if report.ok else 1


def cmd_static_save_lock(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .analysis.static.save_format_lock import SaveFormatChecker

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    checker = SaveFormatChecker(svc)
    if args.generate:
        checker.write_lockfile(args.lockfile)
        fields = checker.current_fields()
        print(f"Wrote lockfile with {len(fields)} fields to {args.lockfile}")
        return 0

    result = checker.check(args.lockfile)
    print(result.summary())
    return 0 if result.ok else 1


def cmd_static_analyze(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService
    from .analysis.static.bank_pressure import BankPressureChecker
    from .analysis.static.save_format_lock import SaveFormatChecker

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print("=== Static Analysis Report ===\n")

    bp_checker = BankPressureChecker(svc)
    bp_report = bp_checker.check()
    print(bp_report.summary())
    print()

    sf_checker = SaveFormatChecker(svc)
    sf_result = sf_checker.check("save_format.lock")
    print(sf_result.summary())
    print()

    ok = bp_report.ok and sf_result.ok
    print(f"\nOverall: {'PASS' if ok else 'FINDINGS DETECTED'}")
    return 0 if ok else 1


def cmd_mcp_list(args: argparse.Namespace) -> int:
    from .llm.mcp_server import list_tools
    tools = list_tools()
    print("Available MCP tools:\n")
    for t in tools:
        print(f"  {t['name']:<20} {t['description']}")
    return 0


def cmd_mcp_call(args: argparse.Namespace) -> int:
    from .llm.mcp_server import dispatch
    kwargs: dict[str, str] = {}
    for p in args.params:
        if "=" in p:
            k, v = p.split("=", 1)
            try:
                kwargs[k] = int(v)
            except ValueError:
                kwargs[k] = v
        else:
            kwargs[p] = ""
    result = dispatch(args.tool, **kwargs)
    print(result.to_json())
    return 0 if result.ok else 1


def cmd_battle_damage(args: argparse.Namespace) -> int:
    def _parse_spec(spec: str) -> tuple[str, int]:
        if ":" in spec:
            name, lvl = spec.rsplit(":", 1)
            try:
                return name, int(lvl)
            except ValueError:
                pass
        return spec, 50

    attacker_name, atk_level = _parse_spec(args.attacker)
    defender_name, def_level = _parse_spec(args.defender)
    move_name = args.move.replace("_", " ").title()

    bp = getattr(args, "bp", None)
    atk = getattr(args, "atk", None)
    dfn = getattr(args, "dfn", None)
    is_physical = not getattr(args, "special", False)
    move_type = getattr(args, "move_type", 0) or 0

    if bp is None or atk is None or dfn is None:
        print(f"  {attacker_name} L{atk_level} vs {defender_name} L{def_level}")
        print(f"  Move: {move_name}")
        print()
        print("Provide --bp, --atk, --dfn for oracle calculation.")
        print("  Example: python -m tools.debugger battle damage CROBAT:44 ALAKAZAM:44 WING_ATTACK --bp 60 --atk 130 --dfn 90")
        return 0

    try:
        from tools.damage_debugger.oracle import BattleInputs, predict_damage
        inp = BattleInputs(
            attacker_level=atk_level,
            move_bp=bp,
            move_type=move_type,
            is_physical=is_physical,
            attacker_atk=atk,
            defender_def=dfn,
            attacker_types=(move_type, move_type),
            defender_types=(0xFF, 0xFF),
        )
        exact = predict_damage(inp)
        low = max(1, exact * 217 // 255) if exact > 0 else 0
    except ImportError:
        print("error: damage oracle not available", file=sys.stderr)
        return 1

    from .analysis.damage_chain import DamageChainDiagram
    diagram = DamageChainDiagram(
        attacker=attacker_name, defender=defender_name, move=move_name,
        final_low=low, final_high=exact,
    )
    diagram.add_step("Base power", bp)
    base = (2 * atk_level // 5 + 2) * bp * atk // dfn // 50 + 2
    diagram.add_step("Pre-modifier", base)
    diagram.add_step("Final (exact)", exact)
    diagram.add_step("DamageVariation low", low)

    if args.format == "arrow":
        print(diagram.render_arrow())
    elif args.format == "markdown":
        print(diagram.render_markdown())
    else:
        print(diagram.render_text())

    if args.explain:
        print(f"\n  Level: {atk_level}  BP: {bp}  Atk: {atk}  Def: {dfn}")
        print(f"  Physical: {is_physical}  MoveType: {move_type}")
        print(f"  Oracle exact: {exact}")
        print(f"  DamageVariation range: {low}-{exact}")

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    from .kernel.symbol_service import SymbolService

    try:
        svc = SymbolService.from_project(variant=args.variant, start=ROOT)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    matches = svc.prefix_search(args.expression)
    if not matches:
        print(f"No symbols matching '{args.expression}'")
        return 1

    shown = matches[:args.limit]
    for m in shown:
        print(f"  ${m.bank:02x}:{m.address:04x}  {m.name}")
    if len(matches) > args.limit:
        print(f"  ... and {len(matches) - args.limit} more")
    print(f"\n{len(matches)} symbols matching '{args.expression}'")
    return 0


def cmd_bisect(args: argparse.Namespace) -> int:
    import subprocess as _sp
    from .stress.bisect import bisect_scenario

    scenario_cmd = args.scenario

    def test_fn(project_root: Path, commit: str) -> bool:
        try:
            proc = _sp.run(
                scenario_cmd, shell=True, cwd=str(project_root),
                capture_output=True, timeout=120,
            )
            return proc.returncode == 0
        except _sp.TimeoutExpired:
            return False

    print(f"Bisecting {args.good}..{args.bad} with: {scenario_cmd}")
    result = bisect_scenario(
        ROOT,
        good_commit=args.good,
        bad_commit=args.bad,
        test_fn=test_fn,
        build_cmd=getattr(args, 'build_cmd', None),
    )
    print(result.summary())
    return 0 if result.ok else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "symbol":
        if args.sym_command == "resolve":
            return cmd_symbol_resolve(args)
        elif args.sym_command == "render":
            return cmd_symbol_render(args)
        else:
            parser.parse_args(["symbol", "--help"])
            return 1
    elif args.command == "macro":
        if args.macro_command == "classify":
            return cmd_macro_classify(args)
        else:
            parser.parse_args(["macro", "--help"])
            return 1
    elif args.command == "schema":
        if args.schema_command == "show":
            return cmd_schema_show(args)
        else:
            parser.parse_args(["schema", "--help"])
            return 1
    elif args.command == "mcp":
        if args.mcp_command == "list":
            return cmd_mcp_list(args)
        elif args.mcp_command == "call":
            return cmd_mcp_call(args)
        elif args.mcp_command == "stdio":
            from .llm.mcp_server import run_stdio
            run_stdio()
            return 0
        else:
            parser.parse_args(["mcp", "--help"])
            return 1
    elif args.command == "battle":
        if args.battle_command == "damage":
            return cmd_battle_damage(args)
        else:
            parser.parse_args(["battle", "--help"])
            return 1
    elif args.command == "static":
        if args.static_command == "clobber-summary":
            return cmd_static_clobber(args)
        elif args.static_command == "bank-pressure":
            return cmd_static_bank_pressure(args)
        elif args.static_command == "save-lock":
            return cmd_static_save_lock(args)
        elif args.static_command == "analyze":
            return cmd_static_analyze(args)
        else:
            parser.parse_args(["static", "--help"])
            return 1
    elif args.command == "query":
        return cmd_query(args)
    elif args.command == "selftest":
        from .selftest import run_selftest
        report = run_selftest()
        print(report.summary())
        return 0 if report.ok else 1
    elif args.command == "metamorphic":
        from .analysis.metamorphic import Scenario, run_all_damage
        import random
        total_pass = 0
        total_fail = 0
        for i in range(args.count):
            s = Scenario(
                scenario_id=f"random_{i}",
                move_power=random.randint(20, 150),
                attacker_atk=random.randint(30, 200),
                defender_def=random.randint(30, 200),
                attacker_spa=random.randint(30, 200),
                defender_spd=random.randint(30, 200),
                attacker_level=random.randint(5, 100),
                attacker_types=[random.randint(0, 27)],
                move_type=random.randint(0, 27),
            )
            results = run_all_damage(s)
            for r in results:
                if r.passed:
                    total_pass += 1
                else:
                    total_fail += 1
                    print(r)
        print(f"\n{total_pass} passed, {total_fail} failed across {args.count} scenarios")
        return 0 if total_fail == 0 else 1
    elif args.command == "fuzz":
        from .analysis.battle_fuzz import run_battle_fuzz
        result = run_battle_fuzz(max_examples=args.examples)
        import json
        print(json.dumps(result, indent=2))
        return 0 if result.get("passed") else 1
    elif args.command == "bisect":
        return cmd_bisect(args)
    elif args.command == "tournament":
        from .stress.tournament import run_tournament
        report = run_tournament(ROOT, dry_run=args.dry_run, emulate=getattr(args, 'emulate', False))
        print(report.summary())
        return 0 if report.ok else 1
    elif args.command == "savelab":
        if args.savelab_command == "decode":
            from .savelab.sgm_decoder import decode_sgm
            state = decode_sgm(args.path)
            print(state.summary())
            return 0 if state.valid else 1
        elif args.savelab_command == "diff":
            from .savelab.state_conv import convert
            from .savelab.state_diff import diff_states
            left = convert(args.left)
            right = convert(args.right)
            report = diff_states(left, right)
            print(report.summary())
            return 0
        else:
            parser.parse_args(["savelab", "--help"])
            return 1
    elif args.command == "web":
        from .presentation.web.app import main as web_main
        web_main(port=args.port, host=args.host)
        return 0
    elif args.command == "hypothesis":
        from .llm.hypothesis_tracker import HypothesisTracker, Hypothesis
        store = ROOT / "audit" / "hypothesis_tree.jsonl"
        tracker = HypothesisTracker(store)
        if args.hyp_command == "add":
            h = Hypothesis(statement=args.statement, tags=args.tag)
            tracker.add(h)
            print(f"Added hypothesis {h.id}: {h.statement}")
            return 0
        elif args.hyp_command == "list":
            for h in tracker.list_all(status=args.status):
                print(f"  [{h.status}] {h.id}: {h.statement}")
            print(f"\n{tracker.count} total hypotheses")
            return 0
        elif args.hyp_command == "tree":
            print(tracker.tree_summary())
            return 0
        else:
            parser.parse_args(["hypothesis", "--help"])
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
