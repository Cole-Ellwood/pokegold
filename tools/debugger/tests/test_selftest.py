from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from tools.debugger.catalog import ROOT
from tools.debugger.selftest import (
    CHECKS,
    NAMED_CHECKS,
    CheckResult,
    SelftestReport,
    _format_text,
    check_bgb_sym_export,
    check_bisect,
    check_context_packet,
    check_coverage,
    check_dap_server,
    check_hypothesis_tracker,
    check_probe,
    check_register_flow,
    check_shrink_battle,
    check_shrink_input_log,
    check_shrink_map_script,
    check_save_state_lab,
    check_vram_decode,
    main,
    run_selftest,
)


class CheckResultTests(unittest.TestCase):
    def test_to_jsonable_round_trips(self) -> None:
        r = CheckResult(
            component="x",
            ok=False,
            next_command="cmd",
            error="boom",
            traceback="tb",
        )
        payload = r.to_jsonable()
        self.assertEqual(payload["component"], "x")
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["next_command"], "cmd")
        self.assertEqual(payload["error"], "boom")


class SelftestRunTests(unittest.TestCase):
    def test_named_checks_registry_is_aligned_with_checks_tuple(self) -> None:
        names = [name for name, _ in NAMED_CHECKS]
        # Distinct names, same order as CHECKS.
        self.assertEqual(len(set(names)), len(names))
        self.assertEqual(len(NAMED_CHECKS), len(CHECKS))

    def test_failing_check_captured_with_traceback(self) -> None:
        def raising(_: Path) -> CheckResult:
            try:
                raise RuntimeError("synthetic failure")
            except Exception:
                from tools.debugger.selftest import _capture

                return _capture("synthetic", "echo retry", lambda: (_ for _ in ()).throw(RuntimeError("synthetic failure")))

        report = run_selftest(checks=(raising,))
        self.assertFalse(report.ok)
        self.assertEqual(len(report.results), 1)
        r = report.results[0]
        self.assertFalse(r.ok)
        self.assertEqual(r.component, "synthetic")
        self.assertEqual(r.next_command, "echo retry")
        self.assertIn("synthetic failure", r.error)
        self.assertIn("Traceback", r.traceback)

    def test_all_passing_checks_yield_ok_report(self) -> None:
        def healthy(_: Path) -> CheckResult:
            from tools.debugger.selftest import _capture

            return _capture("healthy", "echo retry", lambda: "ok detail")

        report = run_selftest(checks=(healthy, healthy))
        self.assertTrue(report.ok)
        self.assertEqual(len(report.results), 2)
        self.assertTrue(all(r.ok for r in report.results))
        self.assertEqual(report.results[0].detail, "ok detail")


class HypothesisTrackerCheckTests(unittest.TestCase):
    """Lived smoke for the V2 surface: the hypothesis_tracker check runs
    cleanly against the real module."""

    def test_hypothesis_tracker_check_passes_in_isolation(self) -> None:
        result = check_hypothesis_tracker(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "hypothesis_tracker")


class ContextPacketCheckTests(unittest.TestCase):
    """P5 lived smoke: a temp hypothesis packs into a context packet."""

    def test_context_packet_check_passes_in_isolation(self) -> None:
        result = check_context_packet(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "context_packet")
        self.assertIn("within budget", result.detail)


class CoverageCheckTests(unittest.TestCase):
    def test_coverage_check_passes_and_asserts_canonical_schema(self) -> None:
        result = check_coverage(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "coverage")
        self.assertIn("targets", result.detail)


class SaveStateLabCheckTests(unittest.TestCase):
    """Lived smoke for the V2 save-state surface: trusted raw WRAM decodes
    named symbols, while .sgm candidates fail closed."""

    def test_save_state_lab_check_passes_in_isolation(self) -> None:
        result = check_save_state_lab(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "save_state_lab")
        self.assertIn("fail-closed", result.detail)


class VramDecodeCheckTests(unittest.TestCase):
    """P6 lived smoke: raw state bytes decode into structured VRAM evidence."""

    def test_vram_decode_check_passes_in_isolation(self) -> None:
        result = check_vram_decode(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "vram_decode")
        self.assertIn("structured diff", result.detail)


class BgbSymExportCheckTests(unittest.TestCase):
    """P7 lived smoke: BGB symbols and memory map export with parity audit."""

    def test_bgb_sym_export_check_passes_in_isolation(self) -> None:
        result = check_bgb_sym_export(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "bgb_sym_export")
        self.assertIn("parity ok", result.detail)


class ProbeCheckTests(unittest.TestCase):
    """P8 lived smoke: a declared probe counts hits in a trace."""

    def test_probe_check_passes_in_isolation(self) -> None:
        result = check_probe(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "probe")
        self.assertIn("fired 2 times", result.detail)


class ShrinkInputLogCheckTests(unittest.TestCase):
    """P10 lived smoke: a long input log shrinks to a minimal reproducer."""

    def test_shrink_input_log_check_passes_in_isolation(self) -> None:
        result = check_shrink_input_log(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "shrink_input_log")
        self.assertIn("30 events", result.detail)


class ShrinkBattleCheckTests(unittest.TestCase):
    """P10 lived smoke: a noisy battle scenario shrinks to the trigger facts."""

    def test_shrink_battle_check_passes_in_isolation(self) -> None:
        result = check_shrink_battle(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "shrink_battle")
        self.assertIn("6 Pokemon", result.detail)


class ShrinkMapScriptCheckTests(unittest.TestCase):
    """P10 lived smoke: a map-script reproducer shrinks to trigger steps."""

    def test_shrink_map_script_check_passes_in_isolation(self) -> None:
        result = check_shrink_map_script(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "shrink_map_script")
        self.assertIn("9 steps", result.detail)


class BisectCheckTests(unittest.TestCase):
    """Lived smoke for the V2 bisect surface: a synthetic regression is
    localized and the temp repo exits bisect state."""

    def test_bisect_check_passes_in_isolation(self) -> None:
        result = check_bisect(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "bisect")
        self.assertIn("synthetic regression", result.detail)


class DapServerCheckTests(unittest.TestCase):
    """P14 lived smoke: DAP framing covers success and boundary failures."""

    def test_dap_server_check_passes_in_isolation(self) -> None:
        result = check_dap_server(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "dap_server")
        self.assertIn("fail-closed/no-request ok", result.detail)


class RegisterFlowCheckTests(unittest.TestCase):
    """P15 lived smoke: register-flow covers the GetUserItem clobber class."""

    def test_register_flow_check_passes_in_isolation(self) -> None:
        result = check_register_flow(ROOT)
        self.assertTrue(result.ok, result.error or result.detail)
        self.assertEqual(result.component, "register_flow")
        self.assertIn("GetUserItem", result.detail)


class JsonOutputTests(unittest.TestCase):
    def test_to_jsonable_shape(self) -> None:
        report = SelftestReport(
            ok=False,
            results=[
                CheckResult(component="a", ok=True, next_command="cmd-a"),
                CheckResult(component="b", ok=False, next_command="cmd-b", error="x"),
            ],
        )
        data = report.to_jsonable()
        self.assertFalse(data["ok"])
        self.assertEqual(data["components_total"], 2)
        self.assertEqual(data["components_failed"], 1)
        self.assertEqual(len(data["results"]), 2)
        # round-trips through json without loss
        encoded = json.dumps(data, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded, data)


class TextFormatTests(unittest.TestCase):
    def test_failure_text_includes_next_command(self) -> None:
        report = SelftestReport(
            ok=False,
            results=[
                CheckResult(component="x", ok=False, next_command="run me", error="boom"),
            ],
        )
        text = _format_text(report)
        self.assertIn("Selftest FAIL", text)
        self.assertIn("[FAIL]", text)
        self.assertIn("run me", text)
        self.assertIn("boom", text)

    def test_pass_text_includes_per_component_detail(self) -> None:
        report = SelftestReport(
            ok=True,
            results=[
                CheckResult(component="x", ok=True, next_command="run me", detail="nice"),
            ],
        )
        text = _format_text(report)
        self.assertIn("Selftest PASS", text)
        self.assertIn("[ok]", text)
        self.assertIn("nice", text)
        self.assertNotIn("[FAIL]", text)


class CliFilterTests(unittest.TestCase):
    def test_main_filters_to_one_component_and_passes(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--component", "capability_audit"])
        self.assertEqual(rc, 0)
        text = captured.getvalue()
        self.assertIn("capability_audit", text)
        self.assertIn("(1/1 components healthy)", text)

    def test_main_unknown_component_returns_2(self) -> None:
        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            rc = main(["--component", "does_not_exist"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown component", captured_err.getvalue())

    def test_main_json_emits_machine_readable(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--component", "capability_audit", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(captured.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["components_total"], 1)
        self.assertEqual(payload["results"][0]["component"], "capability_audit")

    def test_main_can_filter_to_save_state_lab(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--component", "save_state_lab"])
        self.assertEqual(rc, 0)
        text = captured.getvalue()
        self.assertIn("save_state_lab", text)
        self.assertIn("(1/1 components healthy)", text)

    def test_main_can_filter_to_bisect(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--component", "bisect"])
        self.assertEqual(rc, 0)
        text = captured.getvalue()
        self.assertIn("bisect", text)
        self.assertIn("(1/1 components healthy)", text)

class IntegrationSelftestTests(unittest.TestCase):
    """Pairing rule #5: workflow test (not just audit) for done. Run the
    real full selftest against the live codebase. Expensive, but proves
    every wired check actually exercises its component cleanly."""

    def test_full_selftest_passes_on_current_branch(self) -> None:
        report = run_selftest()
        failed = [r for r in report.results if not r.ok]
        if failed:
            details = "; ".join(
                f"{r.component}: {r.error or r.detail}" for r in failed
            )
            self.fail(
                f"selftest had {len(failed)} failing component(s) on this branch: {details}"
            )
        # Sanity: every check is exercised.
        component_names = {r.component for r in report.results}
        expected = {name for name, _ in NAMED_CHECKS}
        self.assertEqual(component_names, expected)


if __name__ == "__main__":
    unittest.main()
