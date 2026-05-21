from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.debugger.catalog import ROOT
from tools.debugger.hypothesis_tracker import (
    Citation,
    add_claim,
    add_refinement,
    add_rejection,
    add_verification,
    detect_citation_drift,
    fold_history,
    list_hypotheses,
    load_events,
    render_tree,
    show_hypothesis,
    validate_citation,
)


class CitationParseTests(unittest.TestCase):
    def test_parse_forward_slash_path(self) -> None:
        c = Citation.parse("engine/battle/late_gen_held_items.asm:15")
        self.assertEqual(c.path, "engine/battle/late_gen_held_items.asm")
        self.assertEqual(c.line, 15)

    def test_parse_normalizes_backslashes(self) -> None:
        c = Citation.parse("engine\\battle\\late_gen_held_items.asm:15")
        self.assertEqual(c.path, "engine/battle/late_gen_held_items.asm")

    def test_parse_rejects_missing_line(self) -> None:
        with self.assertRaises(ValueError):
            Citation.parse("engine/battle/late_gen_held_items.asm")

    def test_parse_rejects_non_integer_line(self) -> None:
        with self.assertRaises(ValueError):
            Citation.parse("engine/battle/late_gen_held_items.asm:not-a-line")

    def test_parse_rejects_zero_line(self) -> None:
        with self.assertRaises(ValueError):
            Citation.parse("engine/battle/late_gen_held_items.asm:0")


class CitationValidateTests(unittest.TestCase):
    def test_validate_real_file(self) -> None:
        cite = Citation.parse("engine/battle/late_gen_held_items.asm:1")
        ok, reason = validate_citation(cite, root=ROOT)
        self.assertTrue(ok, reason)

    def test_validate_missing_file(self) -> None:
        cite = Citation.parse("does/not/exist.asm:1")
        ok, reason = validate_citation(cite, root=ROOT)
        self.assertFalse(ok)
        self.assertIn("does not exist", reason)

    def test_validate_line_out_of_range(self) -> None:
        cite = Citation.parse("engine/battle/late_gen_held_items.asm:999999")
        ok, reason = validate_citation(cite, root=ROOT)
        self.assertFalse(ok)
        self.assertIn("out of range", reason)

    def test_validate_rejects_path_outside_repo(self) -> None:
        cite = Citation.parse("../etc/passwd:1")
        ok, reason = validate_citation(cite, root=ROOT)
        self.assertFalse(ok)


class _TempStoreMixin:
    """Tests that write events spin up a temp jsonl so the durable audit
    file (``audit/hypothesis_tree.jsonl``) is never touched.
    """

    def _store(self) -> Path:
        return Path(self.tmpdir.name) / "hypothesis_tree.jsonl"

    def setUp(self) -> None:  # type: ignore[override]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)


class AddClaimTests(_TempStoreMixin, unittest.TestCase):
    def test_repo_proven_requires_citation(self) -> None:
        with self.assertRaises(ValueError):
            add_claim(
                symptom="x",
                claim="y",
                confidence="repo-proven",
                citations=[],
                store=self._store(),
            )

    def test_repo_proven_with_valid_cite_appends_one_event(self) -> None:
        event = add_claim(
            symptom="physical damage 5x too high",
            claim="something in damage chain",
            confidence="repo-proven",
            citations=["engine/battle/late_gen_held_items.asm:1"],
            session_id="t1",
            store=self._store(),
        )
        self.assertEqual(event["kind"], "claim")
        self.assertEqual(event["confidence"], "repo-proven")
        self.assertEqual(
            event["citations"],
            ["engine/battle/late_gen_held_items.asm:1"],
        )
        rows = load_events(store=self._store())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], event["id"])

    def test_memory_derived_does_not_require_cite(self) -> None:
        event = add_claim(
            symptom="x",
            claim="y",
            confidence="memory-derived",
            store=self._store(),
        )
        self.assertEqual(event["confidence"], "memory-derived")
        self.assertEqual(event["citations"], [])

    def test_judgment_does_not_require_cite(self) -> None:
        event = add_claim(
            symptom="x",
            claim="y",
            confidence="judgment",
            store=self._store(),
        )
        self.assertEqual(event["confidence"], "judgment")

    def test_repo_proven_rejects_stale_cite(self) -> None:
        with self.assertRaises(ValueError) as cm:
            add_claim(
                symptom="x",
                claim="y",
                confidence="repo-proven",
                citations=["engine/battle/late_gen_held_items.asm:999999"],
                store=self._store(),
            )
        self.assertIn("invalid", str(cm.exception))


class FoldHistoryTests(_TempStoreMixin, unittest.TestCase):
    def test_verification_pass_promotes_to_verified(self) -> None:
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="y",
            confidence="repo-proven",
            citations=["engine/battle/late_gen_held_items.asm:1"],
            store=store,
        )
        add_verification(
            parent_id=claim["id"],
            command="echo ok",
            expected="ok",
            verdict="pass",
            actual="ok",
            store=store,
        )
        events = load_events(store=store)
        folded = fold_history(events, claim["id"])
        self.assertEqual(folded["status"], "verified")
        self.assertFalse(folded["unmet_gate"])

    def test_verification_fail_promotes_to_refuted(self) -> None:
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="y",
            confidence="repo-proven",
            citations=["engine/battle/late_gen_held_items.asm:1"],
            store=store,
        )
        add_verification(
            parent_id=claim["id"],
            command="echo bad",
            expected="ok",
            verdict="fail",
            actual="bad",
            store=store,
        )
        events = load_events(store=store)
        folded = fold_history(events, claim["id"])
        self.assertEqual(folded["status"], "refuted")

    def test_rejection_promotes_to_refuted(self) -> None:
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="y",
            confidence="judgment",
            store=store,
        )
        add_rejection(
            parent_id=claim["id"],
            reason="proven wrong by direct observation",
            store=store,
        )
        events = load_events(store=store)
        folded = fold_history(events, claim["id"])
        self.assertEqual(folded["status"], "refuted")

    def test_refinement_updates_claim_and_appends_cite(self) -> None:
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="initial guess",
            confidence="judgment",
            store=store,
        )
        add_refinement(
            parent_id=claim["id"],
            claim="sharper claim",
            confidence="repo-proven",
            citations=["engine/battle/late_gen_held_items.asm:15"],
            store=store,
        )
        events = load_events(store=store)
        folded = fold_history(events, claim["id"])
        self.assertEqual(folded["claim"], "sharper claim")
        self.assertEqual(folded["confidence"], "repo-proven")
        self.assertIn("engine/battle/late_gen_held_items.asm:15", folded["citations"])

    def test_verified_with_memory_derived_confidence_flags_unmet_gate(self) -> None:
        # Pairing rule #4: memory-derived alone does not satisfy a
        # verification gate. If verified without escalating confidence,
        # the inconsistency surfaces.
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="y",
            confidence="memory-derived",
            store=store,
        )
        add_verification(
            parent_id=claim["id"],
            command="echo ok",
            expected="ok",
            verdict="pass",
            store=store,
        )
        events = load_events(store=store)
        folded = fold_history(events, claim["id"])
        self.assertEqual(folded["status"], "verified")
        self.assertTrue(folded["unmet_gate"])


class ListTests(_TempStoreMixin, unittest.TestCase):
    def test_filter_by_status_session_and_symptom(self) -> None:
        store = self._store()
        a = add_claim(
            symptom="damage too high",
            claim="a",
            confidence="judgment",
            session_id="sess-a",
            store=store,
        )
        b = add_claim(
            symptom="boss picked wrong move",
            claim="b",
            confidence="judgment",
            session_id="sess-b",
            store=store,
        )
        add_rejection(parent_id=a["id"], reason="ruled out", store=store)

        all_open = list_hypotheses(store=store, status="open")
        self.assertEqual([h["id"] for h in all_open], [b["id"]])

        only_a_session = list_hypotheses(store=store, session_id="sess-a")
        self.assertEqual([h["id"] for h in only_a_session], [a["id"]])

        damage_only = list_hypotheses(store=store, symptom_contains="damage")
        self.assertEqual([h["id"] for h in damage_only], [a["id"]])

    def test_list_returns_empty_when_store_missing(self) -> None:
        store = Path(self.tmpdir.name) / "does_not_exist.jsonl"
        rows = list_hypotheses(store=store)
        self.assertEqual(rows, [])


class TreeRenderTests(_TempStoreMixin, unittest.TestCase):
    def test_tree_shows_kind_and_id_for_each_node(self) -> None:
        store = self._store()
        claim = add_claim(
            symptom="x",
            claim="root",
            confidence="judgment",
            store=store,
        )
        refinement = add_refinement(
            parent_id=claim["id"],
            claim="sharper",
            store=store,
        )
        verification = add_verification(
            parent_id=refinement["id"],
            command="cmd",
            expected="ok",
            verdict="inconclusive",
            store=store,
        )
        events = load_events(store=store)
        out = render_tree(events, claim["id"])
        self.assertIn("[claim:judgment]", out)
        self.assertIn("[refine]", out)
        self.assertIn("[verify:inconclusive]", out)
        self.assertIn(claim["id"], out)
        self.assertIn(refinement["id"], out)
        self.assertIn(verification["id"], out)


class CitationDriftTests(_TempStoreMixin, unittest.TestCase):
    def test_show_reports_stale_when_file_disappears(self) -> None:
        # Write the store with a fabricated cite by writing the row
        # directly — bypasses validate-at-add to simulate a cite that
        # was valid when written but now points at a deleted file.
        store = self._store()
        store.parent.mkdir(parents=True, exist_ok=True)
        fabricated = {
            "id": "h_test_stale",
            "parent_id": None,
            "kind": "claim",
            "session_id": "t",
            "symptom": "x",
            "claim": "y",
            "confidence": "repo-proven",
            "citations": ["engine/battle/zzz_does_not_exist.asm:1"],
            "notes": "",
            "created_at": "2026-05-21T00:00:00Z",
        }
        store.write_text(json.dumps(fabricated) + "\n", encoding="utf-8")
        info = show_hypothesis("h_test_stale", store=store)
        self.assertTrue(info["folded"]["citation_stale"])
        reports = info["citation_reports"]
        self.assertEqual(len(reports), 1)
        self.assertFalse(reports[0]["ok"])


class Ag08LivedSmokeTests(_TempStoreMixin, unittest.TestCase):
    """Pairing rule #11 — every affordance must answer at least one real
    or recreated lived scenario. The AG-08 c-mirror clobber (May 2026
    5x physical damage in wild encounters) is the named lived-smoke
    case for the hypothesis tracker.

    The full investigation chain — initial judgment, memory recall,
    source localization with citation, ROM-verified gate — must round
    trip cleanly and produce a final ``verified`` status grounded in a
    real ``path:line`` citation.
    """

    def test_full_ag08_investigation_round_trips(self) -> None:
        store = self._store()
        session = "ag08-lived-smoke"

        # 1. Cole reports the symptom; first hypothesis is a judgment call.
        h1 = add_claim(
            symptom="physical damage 5x too high in wild encounters",
            claim="something in the damage chain dispatch is clobbering a register",
            confidence="judgment",
            session_id=session,
            store=store,
        )
        self.assertEqual(h1["confidence"], "judgment")

        # 2. We recall the AG-NN transitive-clobber pattern from memory.
        h2 = add_refinement(
            parent_id=h1["id"],
            claim="matches the AG-NN transitive register-clobber pattern (memory)",
            confidence="memory-derived",
            session_id=session,
            store=store,
        )
        self.assertEqual(h2["kind"], "refinement")

        # 3. We localize to the actual fix-site in source with a real cite.
        h3 = add_refinement(
            parent_id=h1["id"],
            claim=(
                "ApplyLateGenDamageStatsItemMods_Far farcall path clobbers `c` "
                "via TypePassive_GetEffectiveMoveCategory_Far without push/pop"
            ),
            confidence="repo-proven",
            citations=["engine/battle/late_gen_held_items.asm:15"],
            session_id=session,
            store=store,
        )
        self.assertEqual(h3["confidence"], "repo-proven")
        self.assertIn("engine/battle/late_gen_held_items.asm:15", h3["citations"])

        # 4. The damage debugger's clobber_smoke is the verification gate.
        add_verification(
            parent_id=h1["id"],
            command="python -m tools.damage_debugger.clobber_smoke",
            expected="wCurDamage in expected range across scenarios",
            verdict="pass",
            actual="all scenarios pass post-fix",
            session_id=session,
            store=store,
        )

        # Round trip the folded view.
        events = load_events(store=store)
        folded = fold_history(events, h1["id"])
        detect_citation_drift(folded, root=ROOT)

        self.assertEqual(folded["status"], "verified")
        self.assertEqual(folded["confidence"], "repo-proven")
        self.assertFalse(folded["unmet_gate"])
        self.assertFalse(folded["citation_stale"])
        self.assertIn("engine/battle/late_gen_held_items.asm:15", folded["citations"])
        # The ascii tree should name the verification command.
        tree = render_tree(events, h1["id"])
        self.assertIn("clobber_smoke", tree)


if __name__ == "__main__":
    unittest.main()
