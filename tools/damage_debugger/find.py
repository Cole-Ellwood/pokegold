"""Unified diagnostic CLI: where does this scenario diverge from the oracle?

Tier 3.5 of the damage_debugger roadmap. Wraps the boot cache (Tier 1.1),
oracle (Tier 2.1), and the same per-scenario seed paths used by
`clobber_smoke` and `fuzz` into a single entrypoint that:

1. Runs the scenario on the ROM, capturing wCurDamage at each step
   boundary (DamageStats / DamageCalc / Stab / TypeMatchup-end /
   TypePassive-end).
2. Runs the same scenario through `oracle.predict_damage_trace`.
3. Diffs the two traces. The first divergent bucket is where the bug
   lives.
4. Emits a structured report -- text by default, JSON with --json -- so
   an LLM agent (Claude / Codex) can act on the file:line hint without
   re-deriving it.

Modes:

    python -m tools.damage_debugger.find <scenario_name>
        Run a named scenario from clobber_smoke.SCENARIOS.

    python -m tools.damage_debugger.find --bug hp_d_clobber
        Run the known FIRE-low-HP TypePassive bug repro
        (engine/battle/type_passive_damage_mods.asm:322 d-clobber).
        See BUG_CHECK.md for the asm fix.

    python -m tools.damage_debugger.find --json <scenario_name>
        Same as above, JSON-formatted for AI-loop consumption.

    python -m tools.damage_debugger.find --self-test
        Assert the mid-Stab hook boundaries still bucket type-effectiveness
        scenarios correctly.

The "first divergent step" is the diagnostic: when ROM and oracle agree
at step N but disagree at step N+1, the bug is in the asm code that
runs between those labels.

Buckets and their on-ROM hook labels (wCurDamage read at each):

    DamageStats   : after BattleCommand_DamageStats
    DamageCalc    : after BattleCommand_DamageCalc (post-Q + +MIN_DAMAGE)
    Stab          : pre-matchup, post-STAB (BattleCommand_Stab.SkipStab)
    TypeMatchup   : after the matchup loop, before TypePassive farcall
    TypePassive   : final, after TypePassive_ApplyDamageModifiers_Far

For the known HP d-clobber bug, the diff shows ROM=oracle through the
TypeMatchup bucket, then divergence at TypePassive (oracle expects
boost/resist, ROM doesn't apply it because IsUserBelowOneThirdHP /
IsOpponentAboveHalfHP read MaxHP wrong).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass

from .boot_cache import BootStateCache
from .clobber_smoke import (
    SCENARIOS,
    Scenario,
    parse_sym,
)
from .oracle import (
    BattleInputs,
    FIRE,
    NORMAL,
    predict_damage_trace,
)
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked


# --- ROM-side per-step trace -------------------------------------------------

def _read_wcurdamage(pyboy, syms) -> int:
    s = syms["wCurDamage"]
    return read_be_u16_banked(pyboy, s[1], s[0])


def run_rom_trace(pyboy, syms, seed_callable) -> list[tuple[str, int]]:
    """Run the seed + 3-phase chain, capturing wCurDamage at each top-level
    boundary and at two mid-Stab boundaries.

    Inside `BattleCommand_Stab`, hook `.SkipStab` to read wCurDamage
    after STAB/weather/badge work but before the matchup loop, and hook
    `.end` to read after the matchup loop but before the TypePassive
    farcall. Without both hooks, type-effective scenarios can be
    misbucketed as STAB bugs even when final ROM/oracle damage agrees.
    """
    seed_callable(pyboy, syms)

    trace: list[tuple[str, int]] = []
    pre_matchup_dmg = [None]
    matchup_end_dmg = [None]

    # Hook `.SkipStab` (pre-matchup after the optional STAB block) and
    # `.end` (matchup-loop end). Both are local labels resolved through
    # the sym table.
    sym_skip_stab = syms.get("BattleCommand_Stab.SkipStab")
    sym_end = syms.get("BattleCommand_Stab.end")

    def cb_skip_stab(_):
        pre_matchup_dmg[0] = _read_wcurdamage(pyboy, syms)

    def cb_end(_):
        matchup_end_dmg[0] = _read_wcurdamage(pyboy, syms)

    if sym_skip_stab:
        pyboy.hook_register(sym_skip_stab[0], sym_skip_stab[1], cb_skip_stab, None)
    if sym_end:
        pyboy.hook_register(sym_end[0], sym_end[1], cb_end, None)

    try:
        for step_name, fn in [
            ("DamageStats", "BattleCommand_DamageStats"),
            ("DamageCalc",  "BattleCommand_DamageCalc"),
            ("Stab",        "BattleCommand_Stab"),
        ]:
            call_function_safe(pyboy, syms, fn)
            trace.append((step_name, _read_wcurdamage(pyboy, syms)))
    finally:
        if sym_skip_stab:
            try:
                pyboy.hook_deregister(sym_skip_stab[0], sym_skip_stab[1])
            except Exception:
                pass
        if sym_end:
            try:
                pyboy.hook_deregister(sym_end[0], sym_end[1])
            except Exception:
                pass

    # Reshape to match oracle's bucket order: DamageStats / DamageCalc /
    # Stab (pre-matchup, ~equal to post-DamageCalc + STAB) / TypeMatchup
    # (post-matchup, captured via .end hook) / TypePassive (final, after
    # the BattleCommand_Stab call returns).
    rom_damage_stats = trace[0][1]
    rom_damage_calc = trace[1][1]
    rom_final = trace[2][1]
    rom_pre_matchup = pre_matchup_dmg[0] if pre_matchup_dmg[0] is not None else rom_damage_calc
    rom_matchup_end = matchup_end_dmg[0] if matchup_end_dmg[0] is not None else rom_final

    return [
        ("DamageStats", rom_damage_stats),
        ("DamageCalc",  rom_damage_calc),
        ("Stab",        rom_pre_matchup),
        ("TypeMatchup", rom_matchup_end),
        ("TypePassive", rom_final),
    ]


# --- Diff + report -----------------------------------------------------------

@dataclass
class StepDiff:
    step: str
    rom: int
    oracle: int
    diverged: bool


def diff_traces(
    rom_trace: list[tuple[str, int]],
    oracle_trace: list[tuple[str, int]],
) -> list[StepDiff]:
    out: list[StepDiff] = []
    by_name = {name: val for name, val in oracle_trace}
    for name, rom_val in rom_trace:
        oracle_val = by_name.get(name, rom_val)
        out.append(StepDiff(
            step=name,
            rom=rom_val,
            oracle=oracle_val,
            diverged=(rom_val != oracle_val),
        ))
    return out


def _hint_for_bucket(step: str) -> str:
    """One-line "look here next" hint when a divergence is bucketed at `step`."""
    return {
        "DamageStats":
            "Bug between BattleCommand_DamageStats entry and exit. Likely sites: "
            "ApplyLateGenDamageStatsItemMods (Choice/Eviolite/AV item-stat mods), "
            "DittoMetalPowder, TruncateHL_BC.",
        "DamageCalc":
            "Bug between BattleCommand_DamageStats and BattleCommand_DamageCalc end. "
            "Likely sites: TypeBoostItems, ApplyLateGenDamageMultipliers_Far, "
            ".CriticalMultiplier, the cap-then-add-MIN_DAMAGE block.",
        "Stab":
            "Bug between DamageCalc end and BattleCommand_Stab matchup loop entry. "
            "Likely site: STAB +50% scaling block at BattleCommand_Stab.stab.",
        "TypeMatchup":
            "Bug between STAB application and matchup-loop end (effect_commands.asm:1305). "
            "Likely sites: matchup table iteration, Dragon's Majesty multiplier, "
            "BattleCheckTypeMatchup.",
        "TypePassive":
            "Bug between matchup-loop end and TypePassive_ApplyDamageModifiers_Far return "
            "(type_passive_damage_mods.asm:44). Likely sites: any of the 9 V1 mod branches "
            "(NORMAL STAB, FIRE-low-HP, GHOST status, DRAGON resist, GROUND-super-eff, "
            "ROCK-crit, BUG-physical, WATER-special, ICE-above-half-HP). The known "
            "GetUserHPAndMax/GetOpponentHPAndMax d-clobber bug lives here.",
    }.get(step, "Unknown step.")


def format_report(
    name: str,
    inp: BattleInputs,
    diffs: list[StepDiff],
    *,
    final_rom: int,
    final_oracle: int,
) -> str:
    lines: list[str] = []
    lines.append(f"find: scenario {name!r}")
    lines.append(f"  inputs: lvl={inp.attacker_level} BP={inp.move_bp} "
                 f"move_type={inp.move_type:#04x} {'physical' if inp.is_physical else 'special'} "
                 f"atk={inp.attacker_atk} def={inp.defender_def} "
                 f"crit={inp.is_critical}")
    lines.append(f"          attacker_types={inp.attacker_types} "
                 f"defender_types={inp.defender_types}")
    lines.append(f"          user_item={inp.user_item:#04x} opponent_item={inp.opponent_item:#04x}")
    lines.append(f"          weather={inp.weather:#04x} move_effect={inp.move_effect:#04x} "
                 f"johto_badges={inp.johto_badges:#04x} kanto_badges={inp.kanto_badges:#04x}")
    lines.append(f"          initial_cur_damage={inp.initial_cur_damage}")
    lines.append("")
    lines.append(f"  step-by-step (ROM | oracle):")
    for d in diffs:
        marker = "  ✗ DIVERGE" if d.diverged else "  ✓"
        lines.append(f"    {d.step:<14s}  ROM={d.rom:>4d}  oracle={d.oracle:>4d}{marker}")
    lines.append("")

    first_div = next((d for d in diffs if d.diverged), None)
    if first_div is None:
        lines.append(f"  result: ROM ({final_rom}) matches oracle ({final_oracle}). No bug.")
    else:
        lines.append(
            f"  result: first divergence at bucket {first_div.step!r}: "
            f"ROM={first_div.rom} oracle={first_div.oracle}"
        )
        lines.append(f"  hint:   {_hint_for_bucket(first_div.step)}")
        lines.append(
            f"  final:  ROM={final_rom} oracle={final_oracle} "
            f"(delta={final_rom - final_oracle:+d})"
        )

    return "\n".join(lines)


def report_to_dict(name: str, inp: BattleInputs, diffs: list[StepDiff],
                   *, final_rom: int, final_oracle: int) -> dict:
    first_div = next((d for d in diffs if d.diverged), None)
    return {
        "scenario": name,
        "inputs": asdict(inp),
        "trace": [{"step": d.step, "rom": d.rom, "oracle": d.oracle,
                   "diverged": d.diverged} for d in diffs],
        "final": {"rom": final_rom, "oracle": final_oracle,
                  "delta": final_rom - final_oracle},
        "first_divergence": (
            {"step": first_div.step, "rom": first_div.rom,
             "oracle": first_div.oracle,
             "hint": _hint_for_bucket(first_div.step)}
            if first_div else None
        ),
    }


# --- Known-bug repros --------------------------------------------------------

def _known_bugs() -> dict[str, tuple[str, BattleInputs, callable]]:
    """Pre-canned bug repros with their seed callables.

    Adding a new bug: write a `seed_<bug>(pyboy, syms)` and a BattleInputs
    that the oracle scores; register both here. `find --bug <name>` runs
    the repro and points at the file:line for the asm fix.
    """
    from .fuzz import _seed_inputs
    bugs: dict[str, tuple[str, BattleInputs, callable]] = {}

    # The 2026-05-05 fuzz finding: FIRE-low-HP TypePassive boost never
    # fires due to .GetUserHPAndMax d-clobber.
    hp_inp = BattleInputs(
        attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
        attacker_atk=20, defender_def=10,
        attacker_types=(FIRE, FIRE), defender_types=(NORMAL, NORMAL),
        attacker_below_third_hp=True,
    )

    def seed_hp(pyboy, syms):
        _seed_inputs(pyboy, syms, hp_inp)

    bugs["hp_d_clobber"] = (
        "FIRE-low-HP TypePassive boost. Originally broken by a d-clobber in "
        "engine/battle/type_passive_damage_mods.asm:322 .GetUserHPAndMax "
        "(found by Tier 2.2 fuzz, 2026-05-05). Fixed via push/pop af around "
        "the high-byte read in the same session. This entry is kept as a "
        "regression guard: a passing run (no divergence) proves the fix is "
        "still in place.",
        hp_inp,
        seed_hp,
    )
    return bugs


# --- Entrypoint --------------------------------------------------------------

def _scenario_to_inputs(sc: Scenario) -> BattleInputs:
    """Map a clobber_smoke Scenario to BattleInputs for the oracle.

    The hand-coded Scenario.seed callables don't carry their oracle-level
    inputs as data -- they're imperative WRAM writes. For the eight
    pre-canned scenarios we copy from the known table; future scenarios
    that want to use `find` directly should attach a `.inputs` field.
    """
    from . import oracle as _oracle
    table = {
        "physical_no_items": BattleInputs(
            attacker_level=2, move_bp=40, move_type=_oracle.NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=(_oracle.NORMAL, _oracle.FLYING),
            defender_types=(_oracle.FIRE, _oracle.FIRE),
        ),
        "physical_critical": BattleInputs(
            attacker_level=2, move_bp=40, move_type=_oracle.NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=(_oracle.NORMAL, _oracle.FLYING),
            defender_types=(_oracle.FIRE, _oracle.FIRE),
            is_critical=True,
        ),
        "physical_choice_band": BattleInputs(
            attacker_level=2, move_bp=40, move_type=_oracle.NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=(_oracle.NORMAL, _oracle.FLYING),
            defender_types=(_oracle.FIRE, _oracle.FIRE),
            user_item=_oracle.HELD_CHOICE_BAND,
        ),
        "physical_eviolite_def": BattleInputs(
            attacker_level=2, move_bp=40, move_type=_oracle.NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=(_oracle.NORMAL, _oracle.FLYING),
            defender_types=(_oracle.FIRE, _oracle.FIRE),
            opponent_item=_oracle.HELD_EVOLITE, can_evolve_defender=True,
        ),
        "special_no_items": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
        ),
        "special_choice_specs": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            user_item=_oracle.HELD_CHOICE_SPECS,
        ),
        "special_assault_vest": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            opponent_item=_oracle.HELD_ASSAULT_VEST,
        ),
        "special_eviolite_spd": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            opponent_item=_oracle.HELD_EVOLITE, can_evolve_defender=True,
        ),
        "special_sun_fire": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            weather=_oracle.WEATHER_SUN,
        ),
        "special_rain_fire": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            weather=_oracle.WEATHER_RAIN,
        ),
        "special_fire_badge": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.NORMAL, _oracle.FLYING),
            kanto_badges=1 << 6,
        ),
        "special_super_effective": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.GRASS, _oracle.BUG),
        ),
        "special_not_very_effective": BattleInputs(
            attacker_level=5, move_bp=40, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=(_oracle.FIRE, _oracle.FIRE),
            defender_types=(_oracle.WATER, _oracle.FIRE),
        ),
        "physical_immune": BattleInputs(
            attacker_level=2, move_bp=40, move_type=_oracle.NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=(_oracle.NORMAL, _oracle.FLYING),
            defender_types=(_oracle.GHOST, _oracle.GHOST),
        ),
    }
    if sc.name not in table:
        raise KeyError(
            f"scenario {sc.name!r} has no three-phase oracle inputs registered. "
            f"Add it to _scenario_to_inputs in find.py if it runs the normal "
            f"DamageStats -> DamageCalc -> Stab chain."
        )
    return table[sc.name]


def _self_test() -> int:
    """Debugger self-check for the mid-Stab hook boundaries.

    These cases fail if `.SkipStab` is not hooked correctly: final damage
    may still match, but the Stab and TypeMatchup buckets get swapped or
    collapsed and the diagnostic points at the wrong asm site.
    """
    expected_steps = {
        "special_super_effective": {"Stab": 13, "TypeMatchup": 52, "TypePassive": 52},
        "special_not_very_effective": {"Stab": 13, "TypeMatchup": 3, "TypePassive": 2},
        "physical_immune": {"Stab": 4, "TypeMatchup": 0, "TypePassive": 0},
    }

    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    cache = BootStateCache(rom)
    cache.prime()

    failures = 0
    try:
        by_name = {sc.name: sc for sc in SCENARIOS}
        for name, expected in expected_steps.items():
            sc = by_name[name]
            inp = _scenario_to_inputs(sc)
            pyboy = cache.restore()
            rom_trace = run_rom_trace(pyboy, syms, sc.seed)
            oracle_trace = predict_damage_trace(inp)
            diffs = diff_traces(rom_trace, oracle_trace)

            rom_by_step = {step: value for step, value in rom_trace}
            mismatches = [
                f"{step}: expected ROM {want}, got {rom_by_step.get(step)}"
                for step, want in expected.items()
                if rom_by_step.get(step) != want
            ]
            divergences = [d for d in diffs if d.diverged]
            if mismatches or divergences:
                failures += 1
                print(f"{name}: FAIL")
                for msg in mismatches:
                    print(f"  {msg}")
                for d in divergences:
                    print(f"  divergence {d.step}: ROM={d.rom} oracle={d.oracle}")
            else:
                print(f"{name}: ok")
    finally:
        cache.stop()

    if failures:
        print(f"\n{failures} find self-test scenario(s) failed")
        return 1
    print(f"\nall {len(expected_steps)} find self-test scenarios passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Damage-chain divergence diagnostic")
    parser.add_argument("scenario", nargs="?", default=None,
                        help="Scenario name from clobber_smoke.SCENARIOS")
    parser.add_argument("--bug", default=None,
                        help="Run a known-bug repro (try: hp_d_clobber)")
    parser.add_argument("--json", action="store_true",
                        help="JSON output for AI-loop consumption")
    parser.add_argument("--list", action="store_true",
                        help="List available scenarios and known bugs")
    parser.add_argument("--self-test", action="store_true",
                        help="Run debugger self-checks for the find bucket hooks")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.self_test:
        return _self_test()

    bugs = _known_bugs()

    if args.list:
        print("scenarios:")
        for sc in SCENARIOS:
            try:
                _scenario_to_inputs(sc)
                suffix = ""
            except KeyError:
                suffix = " (no three-phase oracle trace)"
            print(f"  {sc.name}{suffix}")
        print("known bugs:")
        for name, (desc, _, _) in bugs.items():
            print(f"  --bug {name}")
            print(f"      {desc}")
        return 0

    if args.bug is not None:
        if args.bug not in bugs:
            print(f"unknown bug repro {args.bug!r}; --list to see options", file=sys.stderr)
            return 2
        desc, inp, seed = bugs[args.bug]
        scenario_name = f"bug:{args.bug}"
    elif args.scenario is not None:
        sc = next((s for s in SCENARIOS if s.name == args.scenario), None)
        if sc is None:
            print(f"unknown scenario {args.scenario!r}; --list to see options",
                  file=sys.stderr)
            return 2
        seed = sc.seed
        inp = _scenario_to_inputs(sc)
        scenario_name = sc.name
    else:
        parser.error("specify a scenario, --bug <name>, or --list")

    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    cache = BootStateCache(rom)
    cache.prime()
    pyboy = cache.restore()

    rom_trace = run_rom_trace(pyboy, syms, seed)
    # When running a known-bug repro, score the oracle in "pristine" mode
    # (model the AS-INTENDED behavior, ignore the documented ROM bugs)
    # so the diff actually surfaces the bug as a divergence. For regular
    # scenario runs the oracle stays in default (bug-mirroring) mode so
    # no false positives appear.
    pristine = args.bug is not None
    oracle_trace = predict_damage_trace(inp, pristine=pristine)
    diffs = diff_traces(rom_trace, oracle_trace)

    final_rom = next((v for n, v in rom_trace if n == "TypePassive"), rom_trace[-1][1])
    final_oracle = next((v for n, v in oracle_trace if n == "TypePassive"),
                        oracle_trace[-1][1] if oracle_trace else 0)

    if args.json:
        report = report_to_dict(scenario_name, inp, diffs,
                                final_rom=final_rom, final_oracle=final_oracle)
        print(json.dumps(report, indent=2))
    else:
        print(format_report(scenario_name, inp, diffs,
                            final_rom=final_rom, final_oracle=final_oracle))

    cache.stop()
    # Exit nonzero if there's a divergence -- so this can run as a CI gate.
    return 1 if any(d.diverged for d in diffs) else 0


if __name__ == "__main__":
    sys.exit(main())
