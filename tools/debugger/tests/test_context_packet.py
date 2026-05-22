from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger import hypothesis_tracker
from tools.debugger.context_packet import (
    DEFAULT_MAX_TOKENS,
    build_context_packet,
    estimate_token_count,
    main,
)


class ContextPacketTests(unittest.TestCase):
    def test_missing_hypothesis_returns_invalid_packet(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            store.write_text("", encoding="utf-8")

            packet = build_context_packet("h-does-not-exist", root=root, store=store)

        self.assertFalse(packet["valid"])
        self.assertEqual(packet["target"], "claude")
        self.assertEqual(packet["max_tokens"], DEFAULT_MAX_TOKENS)
        self.assertIn("not found", "\n".join(packet["errors"]))
        self.assertIn("NOT FOUND", packet["markdown"])
        self.assertTrue(packet["within_budget"], packet)

    def test_known_hypothesis_packs_claim_and_citations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            (root / "engine").mkdir()
            (root / "engine" / "damage.asm").write_text(
                "; line 1\n; line 2\n; line 3\n",
                encoding="utf-8",
            )

            claim_event = hypothesis_tracker.add_claim(
                symptom="5x physical damage on wild encounter",
                claim="GetUserItem clobbers de via _GetSidedHL helper extraction",
                confidence="repo-proven",
                citations=("engine/damage.asm:2",),
                session_id="session-test",
                store=store,
                root=root,
            )

            packet = build_context_packet(
                claim_event["id"],
                target="codex",
                root=root,
                store=store,
            )

        self.assertTrue(packet["valid"], packet)
        self.assertEqual(packet["target"], "codex")
        self.assertEqual(packet["status"], "open")
        self.assertIn("GetUserItem clobbers de", packet["markdown"])
        self.assertIn("engine/damage.asm", packet["markdown"])
        self.assertEqual(packet["structured"]["claim"], claim_event["claim"])
        self.assertEqual(packet["structured"]["target"], "codex")
        self.assertEqual(packet["structured"]["citations"][0]["path"], "engine/damage.asm")

    def test_codex_target_uses_punchline_first_form(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            claim_event = hypothesis_tracker.add_claim(
                symptom="5x physical damage on wild encounter",
                claim="GetUserItem clobbers de",
                confidence="judgment",
                citations=(),
                session_id="session-test",
                store=store,
                root=root,
            )

            codex_packet = build_context_packet(
                claim_event["id"],
                target="codex",
                root=root,
                store=store,
            )
            claude_packet = build_context_packet(
                claim_event["id"],
                target="claude",
                root=root,
                store=store,
            )

        self.assertTrue(
            codex_packet["markdown"].startswith("Status: open | Confidence: judgment")
        )
        self.assertIn("Claim: GetUserItem clobbers de", codex_packet["markdown"].splitlines()[:3])
        self.assertTrue(claude_packet["markdown"].startswith("# Hypothesis context packet"))

    def test_stale_citation_is_marked_on_specific_markdown_entry(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            (root / "engine").mkdir()
            cited = root / "engine" / "damage.asm"
            cited.write_text("; line 1\n; line 2\n", encoding="utf-8")
            claim_event = hypothesis_tracker.add_claim(
                symptom="5x physical damage on wild encounter",
                claim="GetUserItem clobbers de",
                confidence="repo-proven",
                citations=("engine/damage.asm:2",),
                session_id="session-test",
                store=store,
                root=root,
            )
            cited.unlink()

            packet = build_context_packet(claim_event["id"], root=root, store=store)

        self.assertTrue(packet["valid"], packet)
        self.assertTrue(packet["citation_stale"])
        self.assertIn("- Citation drift: YES", packet["markdown"])
        self.assertIn("- engine/damage.asm:2 (stale)", packet["markdown"])
        self.assertFalse(packet["structured"]["citations"][0]["resolved"])

    def test_token_estimate_within_budget_for_small_packet(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            claim_event = hypothesis_tracker.add_claim(
                symptom="trivial",
                claim="trivial",
                confidence="judgment",
                citations=(),
                session_id="session-test",
                store=store,
                root=root,
            )

            packet = build_context_packet(
                claim_event["id"],
                max_tokens=500,
                root=root,
                store=store,
            )

        self.assertTrue(packet["within_budget"], packet)
        self.assertLessEqual(packet["token_count"], 500)
        self.assertEqual(packet["token_count"], estimate_token_count(packet["markdown"]))

    def test_invalid_target_normalizes_to_claude(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            store.write_text("", encoding="utf-8")

            packet = build_context_packet(
                "h-anything",
                target="GROK",
                root=root,
                store=store,
            )

        self.assertEqual(packet["target"], "claude")

    def test_cli_json_emission_is_machine_parseable(self) -> None:
        import io
        import contextlib

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "hypothesis_store.jsonl"
            store.write_text("", encoding="utf-8")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exit_code = main([
                    "--hypothesis", "h-missing",
                    "--store", str(store),
                    "--json",
                ])

        self.assertEqual(exit_code, 1)
        payload = json.loads(buf.getvalue())
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["kind"], "unified_debugger_context_packet")
        self.assertEqual(payload["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
