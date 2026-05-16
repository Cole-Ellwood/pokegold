"""Self-test: every debugger component has a self-test entry.

``python -m tools.debugger selftest``

Each component registers a test function. The selftest runner calls
them all, reports pass/fail, and exits nonzero if any fail.
"""

from __future__ import annotations

import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TestResult:
    name: str
    passed: bool = False
    duration_ms: float = 0.0
    error: str = ""
    detail: str = ""

    def __str__(self) -> str:
        tag = "PASS" if self.passed else "FAIL"
        time_str = f"{self.duration_ms:.0f}ms"
        line = f"  [{tag}] {self.name} ({time_str})"
        if self.error:
            line += f"\n         {self.error}"
        return line


@dataclass
class SelfTestReport:
    results: list[TestResult] = field(default_factory=list)
    duration_s: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def summary(self) -> str:
        lines = ["=== Debugger Self-Test ===", ""]
        for r in self.results:
            lines.append(str(r))
        lines.append("")
        lines.append(
            f"{self.passed}/{len(self.results)} passed, "
            f"{self.failed} failed ({self.duration_s:.1f}s)"
        )
        lines.append("PASS" if self.ok else "FAIL")
        return "\n".join(lines)


TESTS: list[tuple[str, Callable[[], Any]]] = []


def register(name: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        TESTS.append((name, fn))
        return fn
    return decorator


@register("import: kernel")
def _test_kernel() -> None:
    from .kernel import symbol_service, state_schema
    from .kernel.state_schema import WorldState, RegionType
    assert len(RegionType) > 0


@register("import: instrumentation")
def _test_instrumentation() -> None:
    from .instrumentation import macro_resolver, pc_tracer, reg_tracer, mem_tracer
    from .instrumentation.stack_reconstructor import StackReconstructor


@register("import: bus")
def _test_bus() -> None:
    from .bus import events, byte_history, call_history, branch_history
    from .bus.run_store import RunStore
    from .bus.store_jsonl import JSONLStore


@register("import: analysis.damage_chain")
def _test_damage_chain() -> None:
    from .analysis.damage_chain import DamageChainDiagram, ChainStep
    d = DamageChainDiagram(attacker="Crobat", defender="Alakazam", move="Wing Attack")
    d.add_step("Base", 60)
    d.add_step("STAB", 90, multiplier=1.5)
    assert len(d.steps) == 2


@register("import: analysis.battle_inspector")
def _test_battle_inspector() -> None:
    from .analysis.battle_inspector import BattleInspector


@register("analysis: metamorphic relations")
def _test_metamorphic() -> None:
    from .analysis.metamorphic import Scenario, run_all_damage
    s = Scenario(
        scenario_id="selftest",
        move_power=60,
        attacker_types=[0],
        move_type=0,
        attacker_atk=100,
        defender_def=80,
    )
    results = run_all_damage(s)
    assert len(results) >= 5, f"Expected >=5 relations, got {len(results)}"
    passed_count = sum(1 for r in results if r.passed)
    assert passed_count >= 4, f"Expected >=4 passing relations, got {passed_count}"


@register("analysis: battle fuzz import")
def _test_battle_fuzz() -> None:
    from .analysis.battle_fuzz import HAS_HYPOTHESIS, FuzzBattleState, FuzzMon
    state = FuzzBattleState()
    assert state.turn == 0
    assert state.player_active.alive()


@register("analysis: HDD minimize")
def _test_hdd() -> None:
    from .analysis.hdd_minimize import minimize_scenario

    scenario = {
        "scenario_id": "test",
        "a": 1, "b": 2, "c": 3,
        "nested": {"x": 10, "y": 20},
        "items": [{"q": 1}, {"q": 2}, {"q": 3}],
    }

    def bug_needs_a_and_c(s: dict) -> bool:
        return "a" in s and "c" in s

    result = minimize_scenario(scenario, bug_needs_a_and_c)
    assert result.minimized_size < result.original_size
    assert "a" in result.minimized
    assert "c" in result.minimized


@register("analysis: static.dead_code")
def _test_dead_code() -> None:
    from .analysis.static.dead_code import DeadCodeReport
    r = DeadCodeReport(total_labels=100, referenced_labels=95)
    assert "100 labels" in r.summary()


@register("analysis: static.clobber_inference")
def _test_clobber() -> None:
    from .analysis.static.clobber_inference import RegState, RegisterSummary, ALL_REGS
    assert len(ALL_REGS) == 8
    assert RegState.BOTTOM != RegState.DEFINED


@register("presentation: DAP server")
def _test_dap() -> None:
    from .presentation.dap import DapServer, DapSession
    session = DapSession()
    bp = session.add_breakpoint("test.asm", 42)
    assert bp.line == 42
    assert bp.source_file == "test.asm"

    watch = session.add_watch("wBattleMonHP")
    assert watch.expression == "wBattleMonHP"

    server = DapServer(session)
    assert "initialize" in server._handlers


@register("presentation: viewers.vram")
def _test_vram() -> None:
    from .presentation.viewers.vram_viewer import VramSnapshot, Tile
    t = Tile(index=0, data=b"\xFF\x00" * 8)
    pixels = t.pixels
    assert len(pixels) == 8
    assert len(pixels[0]) == 8


@register("presentation: viewers.oam")
def _test_oam() -> None:
    from .presentation.viewers.oam_viewer import OamSnapshot
    oam_data = bytes([50, 60, 0x10, 0x00] * 40)
    snap = OamSnapshot.from_bytes(oam_data)
    assert len(snap.entries) == 40
    assert snap.entries[0].screen_y == 34


@register("presentation: viewers.palette")
def _test_palette() -> None:
    from .presentation.viewers.palette_viewer import Color, PaletteSnapshot
    c = Color.from_raw(0xFF, 0x7F)
    assert 0 <= c.r5 <= 31
    r, g, b = c.rgb24
    assert 0 <= r <= 255


@register("presentation: viewers.map_tracer")
def _test_map_tracer() -> None:
    from .presentation.viewers.map_tracer import EventFlag
    f = EventFlag(name="EVENT_GOT_STARTER", byte_offset=5, bit=3, value=True)
    assert "SET" in str(f)


@register("presentation: viewers.audio")
def _test_audio() -> None:
    from .presentation.viewers.audio_scope import AudioSnapshot
    io_regs = bytes(128)
    snap = AudioSnapshot.from_io(io_regs)
    assert len(snap.channels) == 4


@register("savelab: sgm_decoder")
def _test_sgm_decoder() -> None:
    from .savelab.sgm_decoder import SgmState
    s = SgmState(valid=True, rom_title="TEST")
    assert "TEST" in s.summary()


@register("savelab: state_conv")
def _test_state_conv() -> None:
    from .savelab.state_conv import UnifiedState
    s = UnifiedState(source_format="test", wram=b"\x00" * 0x2000)
    assert s.read_byte(0xC000) == 0


@register("savelab: state_diff")
def _test_state_diff() -> None:
    from .savelab.state_conv import UnifiedState
    from .savelab.state_diff import diff_states
    a = UnifiedState(wram=b"\x00" * 16, hram=b"\x00" * 8)
    b = UnifiedState(wram=b"\x00" * 15 + b"\xFF", hram=b"\x00" * 8)
    report = diff_states(a, b)
    assert report.total_diffs >= 1


@register("stress: tournament")
def _test_tournament() -> None:
    from .stress.tournament import TournamentReport
    r = TournamentReport(total_trainers=10, completed=10)
    assert r.ok


@register("stress: bisect")
def _test_bisect() -> None:
    from .stress.bisect import BisectResult
    r = BisectResult(found_commit="abc123", good_commit="aaa", bad_commit="bbb", steps=5)
    assert r.ok
    assert "abc123" in r.summary()


@register("stress: vanilla_diff")
def _test_vanilla_diff() -> None:
    from .stress.vanilla_diff import VanillaDiffReport
    r = VanillaDiffReport(total_diffs=42)
    assert "42" in r.summary()


@register("llm: mcp_server")
def _test_mcp() -> None:
    from .llm.mcp_server import list_tools
    tools = list_tools()
    assert len(tools) > 0


@register("llm: hypothesis_tracker")
def _test_hypothesis_tracker() -> None:
    from .llm.hypothesis_tracker import Hypothesis, Citation, CitationGrounder
    h = Hypothesis(statement="wCurDamage is clobbered by farcall")
    h.citations.append(Citation(file="engine/battle/core.asm", line=42))
    assert h.status == "open"

    h.confirm("Verified via damage debugger trace")
    assert h.status == "confirmed"

    child = h.refine("Specifically clobbered by the ld hl, target expansion")
    assert child.parent_id == h.id


@register("compat: legacy bridges")
def _test_compat() -> None:
    from .compat import symbol_table_from_service, symbol_entry_from_legacy


def run_selftest(verbose: bool = True) -> SelfTestReport:
    """Run all registered self-tests."""
    report = SelfTestReport()
    total_start = time.monotonic()

    for name, test_fn in TESTS:
        start = time.monotonic()
        result = TestResult(name=name)
        try:
            test_fn()
            result.passed = True
        except Exception as e:
            result.error = f"{type(e).__name__}: {e}"
            if verbose:
                result.detail = traceback.format_exc()
        result.duration_ms = (time.monotonic() - start) * 1000
        report.results.append(result)

    report.duration_s = time.monotonic() - total_start
    return report


__all__ = ["TestResult", "SelfTestReport", "run_selftest", "register"]
