from __future__ import annotations

import unittest

from tools.debugger.canonical_state_class import (
    build_canonical_state_class,
    validate_canonical_state_class,
)


IDENTITY = {
    "rom_sha256": "A" * 64,
    "symbols_sha256": "B" * 64,
    "map_sha256": "C" * 64,
    "rule_map_sha256": "D" * 64,
    "source_tree_sha256": "commit",
    "dirty_diff_hash": "E" * 64,
}


class CanonicalStateClassTests(unittest.TestCase):
    def test_equivalent_public_facts_have_stable_class_id(self) -> None:
        first = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"tier": 2, "rule_id": "move.select", "tags": ["a", "b"]},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            backend="static",
            proof_status="missing_proof_artifact",
            missing_evidence=["rom proof"],
        )
        second = build_canonical_state_class(
            surface="boss_ai",
            identity=dict(reversed(list(IDENTITY.items()))),
            public_facts={"tags": ["a", "b"], "rule_id": "move.select", "tier": 2},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            backend="static",
            proof_status="missing_proof_artifact",
            missing_evidence=["different proof gap"],
        )

        self.assertTrue(first["valid"])
        self.assertEqual(first["class_id"], second["class_id"])
        self.assertEqual(first["class_fingerprint"], second["class_fingerprint"])

    def test_class_id_changes_on_public_fact_rng_or_backend(self) -> None:
        base = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"rule_id": "move.select"},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            rng_assumptions={"seed": 1},
            backend="static",
            proof_status="missing_proof_artifact",
        )
        changed_rng = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"rule_id": "move.select"},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            rng_assumptions={"seed": 2},
            backend="static",
            proof_status="missing_proof_artifact",
        )
        changed_backend = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"rule_id": "move.select"},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            rng_assumptions={"seed": 1},
            backend="pyboy",
            proof_status="missing_proof_artifact",
        )

        self.assertNotEqual(base["class_id"], changed_rng["class_id"])
        self.assertNotEqual(base["class_id"], changed_backend["class_id"])

    def test_hidden_public_only_facts_fail_closed(self) -> None:
        record = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"hidden_moves": ["SURF"]},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            proof_status="missing_proof_artifact",
        )

        self.assertFalse(record["valid"])
        self.assertEqual(record["class_id"], "")
        self.assertTrue(
            any("hidden/private fact" in error for error in record["validation_errors"])
        )

    def test_unknown_surface_fact_bucket_fails_closed(self) -> None:
        record = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"rule_id": "move.select"},
            surface_facts={"not_a_surface": {}},
            proof_status="missing_proof_artifact",
        )

        self.assertFalse(record["valid"])
        self.assertTrue(
            any("unsupported surface_facts buckets" in error for error in record["validation_errors"])
        )

    def test_missing_identity_basis_rejects_before_class_id(self) -> None:
        identity = dict(IDENTITY)
        identity["map_sha256"] = ""
        record = build_canonical_state_class(
            surface="boss_ai",
            identity=identity,
            public_facts={"rule_id": "move.select"},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            proof_status="missing_proof_artifact",
        )

        self.assertFalse(record["valid"])
        self.assertEqual(record["class_id"], "")
        self.assertIn("identity.map_sha256 must be a non-empty string", record["validation_errors"])

    def test_validation_rejects_unknown_top_level_fields(self) -> None:
        record = build_canonical_state_class(
            surface="boss_ai",
            identity=IDENTITY,
            public_facts={"rule_id": "move.select"},
            surface_facts={"boss_ai": {"decision_surface": "move_score"}},
            proof_status="missing_proof_artifact",
        )
        record["surprise"] = True

        errors = validate_canonical_state_class(record)

        self.assertTrue(any("unknown top-level fields" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
