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

    python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup
        Also capture CPU registers plus mem[HL-2..HL] at each hook hit.

    python -m tools.damage_debugger.find --self-test
        Assert the mid-Stab hook boundaries still bucket type-effectiveness
        scenarios correctly, and assert the DM hl-clobber repro's hook
        window shows one real type-table row instead of stack garbage.

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
    DRAGON,
    FIRE,
    GHOST,
    GROUND,
    NORMAL,
    predict_damage_trace,
)
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked


# --- ROM-side per-step trace -------------------------------------------------

def _read_wcurdamage(pyboy, syms) -> int:
    s = syms["wCurDamage"]
    return read_be_u16_banked(pyboy, s[1], s[0])


@dataclass
class InstrumentHit:
    seq: int
    symbol: str
    bank: int
    pc: int
    a: int
    f: int
    b: int
    c: int
    d: int
    e: int
    h: int
    l: int
    sp: int
    hl: int
    window_start: int
    window: list[int]


@dataclass
class InstrumentReport:
    hook: str
    bank: int
    address: int
    hits: list[InstrumentHit]
    call_failures: list[str]


class HookRecorder:
    """Reusable single-symbol hook recorder for focused debugger probes."""

    def __init__(self, pyboy, syms: dict, symbol: str):
        if symbol not in syms:
            raise KeyError(symbol)
        self.pyboy = pyboy
        self.symbol = symbol
        self.bank, self.address = syms[symbol]
        self.hits: list[InstrumentHit] = []
        self._installed = False

    def install(self) -> None:
        def cb(_):
            self.capture()

        self.pyboy.hook_register(self.bank, self.address, cb, None)
        self._installed = True

    def close(self) -> None:
        if not self._installed:
            return
        try:
            self.pyboy.hook_deregister(self.bank, self.address)
        finally:
            self._installed = False

    def capture(self) -> None:
        rf = self.pyboy.register_file
        h = int(rf.H) if hasattr(rf, "H") else (int(rf.HL) >> 8) & 0xFF
        l = int(rf.L) if hasattr(rf, "L") else int(rf.HL) & 0xFF
        hl = ((h << 8) | l) & 0xFFFF
        window_start = (hl - 2) & 0xFFFF
        window = [int(self.pyboy.memory[(window_start + i) & 0xFFFF]) for i in range(3)]
        self.hits.append(InstrumentHit(
            seq=len(self.hits) + 1,
            symbol=self.symbol,
            bank=self.bank,
            pc=int(rf.PC),
            a=int(rf.A),
            f=int(rf.F),
            b=int(rf.B),
            c=int(rf.C),
            d=int(rf.D),
            e=int(rf.E),
            h=h,
            l=l,
            sp=int(rf.SP),
            hl=hl,
            window_start=window_start,
            window=window,
        ))


FIND_CHAIN = (
    "BattleCommand_DamageStats",
    "BattleCommand_DamageCalc",
    "BattleCommand_Stab",
)


def run_instrumented_hook(pyboy, syms, seed_callable, hook_symbol: str) -> InstrumentReport:
    """Run the normal find chain while recording one hook symbol.

    This promotes the old probe5 pattern: each hit captures CPU registers
    plus the three bytes at [hl-2, hl-1, hl], which makes table-pointer
    clobbers visible without adding a custom one-off script.
    """
    recorder = HookRecorder(pyboy, syms, hook_symbol)
    recorder.install()
    call_failures: list[str] = []
    try:
        seed_callable(pyboy, syms)
        for fn in FIND_CHAIN:
            ticks, returned, post_pc = call_function_safe(pyboy, syms, fn)
            if not returned:
                call_failures.append(
                    f"{fn} did not reach the HRAM sentinel within {ticks} ticks "
                    f"(PC=${post_pc:04x})"
                )
    finally:
        recorder.close()
    return InstrumentReport(
        hook=hook_symbol,
        bank=recorder.bank,
        address=recorder.address,
        hits=recorder.hits,
        call_failures=call_failures,
    )


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


def _format_instrument_hit(hit: InstrumentHit) -> str:
    window = " ".join(f"${b:02x}" for b in hit.window)
    row = (
        f"row=(att=${hit.window[0]:02x}, def=${hit.window[1]:02x}, mult=${hit.window[2]:02x})"
        if len(hit.window) == 3 else "row=(unavailable)"
    )
    return (
        f"  #{hit.seq:<3d} PC=${hit.pc:04x} "
        f"A={hit.a:02x} F={hit.f:02x} "
        f"BC={hit.b:02x}{hit.c:02x} DE={hit.d:02x}{hit.e:02x} "
        f"HL=${hit.hl:04x} SP=${hit.sp:04x} "
        f"mem[HL-2..HL]@${hit.window_start:04x}={window} {row}"
    )


def format_instrument_report(report: InstrumentReport) -> str:
    lines = [
        "",
        f"instrument-hook: {report.hook} @ ${report.bank:02x}:{report.address:04x} "
        f"hits={len(report.hits)}",
    ]
    for failure in report.call_failures:
        lines.append(f"  call warning: {failure}")
    if not report.hits:
        lines.append("  (hook did not fire)")
    else:
        lines.extend(_format_instrument_hit(hit) for hit in report.hits)
    return "\n".join(lines)


def instrument_report_to_dict(report: InstrumentReport) -> dict:
    return {
        "hook": report.hook,
        "bank": report.bank,
        "address": report.address,
        "hits": [asdict(hit) for hit in report.hits],
        "call_failures": report.call_failures,
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

    dm_inp = BattleInputs(
        attacker_level=3, move_bp=27, move_type=GROUND, is_physical=True,
        attacker_atk=62, defender_def=5,
        attacker_types=(NORMAL, DRAGON), defender_types=(GHOST, GROUND),
        is_critical=True,
    )

    def seed_dm(pyboy, syms):
        _seed_inputs(pyboy, syms, dm_inp)

    bugs["dm_hl_clobber"] = (
        "Dragon's Majesty immunity reroute in CheckTypeMatchup.Yup. This "
        "was originally broken by an hl-clobber across "
        "CheckTypeMatchup_ApplyDragonsMajestyMultiplier, making the matchup "
        "loop read stack garbage after the first hit. Fixed via push/pop hl; "
        "kept as a regression guard and as the reference case for "
        "--instrument-hook CheckTypeMatchup.Yup.",
        dm_inp,
        seed_dm,
    )
    return bugs


# --- Entrypoint --------------------------------------------------------------

def _scenario_to_inputs(sc: Scenario) -> BattleInputs:
    """Map a clobber_smoke Scenario to BattleInputs for the oracle.

    The hand-coded Scenario.seed callables don't carry their oracle-level
    inputs as data -- they're imperative WRAM writes. For registered
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
        "physical_type_boost_item": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIGHTING, is_physical=True,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.FIRE, _oracle.WATER),
            user_item=_oracle.HELD_BLACKBELT_I,
        ),
        "physical_muscle_band": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIGHTING, is_physical=True,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.FIRE, _oracle.WATER),
            user_item=_oracle.HELD_MUSCLE_BAND,
        ),
        "special_wise_glasses": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.NORMAL, _oracle.NORMAL),
            user_item=_oracle.HELD_WISE_GLASSES,
        ),
        "special_expert_belt": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.GRASS, _oracle.NORMAL),
            user_item=_oracle.HELD_EXPERT_BELT,
        ),
        "special_metronome_item": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.NORMAL, _oracle.NORMAL),
            user_item=_oracle.HELD_METRONOME,
            metronome_count=3,
        ),
        "special_life_orb_damage": BattleInputs(
            attacker_level=50, move_bp=60, move_type=_oracle.FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(_oracle.WATER, _oracle.WATER),
            defender_types=(_oracle.NORMAL, _oracle.NORMAL),
            user_item=_oracle.HELD_LIFE_ORB,
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
        "physical_type_boost_item": {"Stab": 41, "TypeMatchup": 41, "TypePassive": 41},
        "special_expert_belt": {"Stab": 41, "TypeMatchup": 82, "TypePassive": 82},
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

        _desc, _inp, dm_seed = _known_bugs()["dm_hl_clobber"]
        pyboy = cache.restore()
        dm_report = run_instrumented_hook(pyboy, syms, dm_seed, "CheckTypeMatchup.Yup")
        expected_window = [GROUND, GHOST, 0]
        matching_hits = [hit for hit in dm_report.hits if hit.window == expected_window]
        stack_hits = [hit for hit in dm_report.hits if 0xDF00 <= hit.hl <= 0xDFFF]
        if len(dm_report.hits) != 1 or not matching_hits or stack_hits or dm_report.call_failures:
            failures += 1
            print("dm_hl_clobber instrument-hook: FAIL")
            print(f"  hits={len(dm_report.hits)} matching_expected={len(matching_hits)}")
            for failure in dm_report.call_failures:
                print(f"  call failure: {failure}")
            for hit in dm_report.hits:
                print(_format_instrument_hit(hit))
        else:
            print("dm_hl_clobber instrument-hook: ok")
    finally:
        cache.stop()

    if failures:
        print(f"\n{failures} find self-test scenario(s) failed")
        return 1
    print(f"\nall {len(expected_steps)} bucket checks and instrument-hook check passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Damage-chain divergence diagnostic")
    parser.add_argument("scenario", nargs="?", default=None,
                        help="Scenario name from clobber_smoke.SCENARIOS")
    parser.add_argument("--bug", default=None,
                        help="Run a known-bug repro (try: hp_d_clobber)")
    parser.add_argument("--json", action="store_true",
                        help="JSON output for AI-loop consumption")
    parser.add_argument("--instrument-hook", metavar="SYMBOL", default=None,
                        help="Capture registers and mem[HL-2..HL] every time SYMBOL fires")
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
    if args.instrument_hook is not None and args.instrument_hook not in syms:
        print(
            f"unknown hook symbol {args.instrument_hook!r}; "
            f"check {sym.name} or run against a freshly built .sym",
            file=sys.stderr,
        )
        return 2

    cache = BootStateCache(rom)
    cache.prime()
    pyboy = cache.restore()

    rom_trace = run_rom_trace(pyboy, syms, seed)
    instrument_report = None
    if args.instrument_hook is not None:
        pyboy_instrument = cache.restore()
        try:
            instrument_report = run_instrumented_hook(
                pyboy_instrument, syms, seed, args.instrument_hook
            )
        except KeyError:
            cache.stop()
            print(
                f"unknown hook symbol {args.instrument_hook!r}; "
                f"check {sym.name} or run against a freshly built .sym",
                file=sys.stderr,
            )
            return 2
    oracle_trace = predict_damage_trace(inp)
    diffs = diff_traces(rom_trace, oracle_trace)

    final_rom = next((v for n, v in rom_trace if n == "TypePassive"), rom_trace[-1][1])
    final_oracle = next((v for n, v in oracle_trace if n == "TypePassive"),
                        oracle_trace[-1][1] if oracle_trace else 0)

    if args.json:
        report = report_to_dict(scenario_name, inp, diffs,
                                final_rom=final_rom, final_oracle=final_oracle)
        if instrument_report is not None:
            report["instrumentation"] = instrument_report_to_dict(instrument_report)
        print(json.dumps(report, indent=2))
    else:
        text = format_report(scenario_name, inp, diffs,
                             final_rom=final_rom, final_oracle=final_oracle)
        if instrument_report is not None:
            text += format_instrument_report(instrument_report)
        print(text)

    cache.stop()
    # Exit nonzero if there's a divergence -- so this can run as a CI gate.
    return 1 if any(d.diverged for d in diffs) else 0


if __name__ == "__main__":
    sys.exit(main())
