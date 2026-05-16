# Boss AI Debugger Changed-AI Run: 20260515_121426_changed_ai

Created: `2026-05-15T12:14:26.700574+00:00`
Git commit: `fda90e2bb57d41a523a33ea5965686abf47710e4`

## Gates

- scenarios: `200`
- reviewable: `0`
- route classifications: `{'route_pass': 200}`
- differential: `{'mismatch_count': 0, 'mismatch_class_counts': {}, 'contribution_comparison': {'matched_trace_count': 0, 'mismatch_count': 0, 'mismatch_class_counts': {}}}`
- metamorphic: `{'passed': True, 'pass_count': 106, 'relation_count': 106}`
- mutation: `{'killed_count': 4, 'survived_count': 1, 'not_exercised_count': 0, 'mutation_score': 0.8}`
- invariants: `{'candidate_count': 13, 'violation_count': 0}`
- trace replay: `{'trace_count': 19, 'checked_count': 19, 'failure_count': 0, 'agreement_rate': 1.0}`
- ROM contribution: `{'available': True, 'artifact_count': 8, 'event_count': 70, 'changed_event_count': 70, 'covered_rule_count': 15, 'changed_rule_count': 15, 'unmapped_event_count': 0}`
- ROM score materialization: `{'checked_count': 0, 'error_count': 0, 'score_bytes_match_count': 0, 'selector_top_match_count': 0, 'contribution_matched_count': 0, 'contribution_mismatch_count': 0, 'hook_equivalence_checked_count': 0, 'hook_equivalence_mismatch_count': 0, 'skipped_reason': 'not requested; pass --refresh-rom-score-materialization to run generated score-model materialization'}`
- ROM rebuild: `{'requested': False, 'passed': True, 'command_count': 0, 'failed_count': 0, 'skipped_reason': 'not requested; pass --rebuild-roms to rebuild normal and trace ROMs'}`
- live trace refresh: `{'requested': False, 'passed': True, 'command_count': 0, 'failed_count': 0, 'skipped_reason': 'not requested; pass --refresh-live-traces to rebuild state-factory states and live trace captures'}`
- previous run diff: `{'available': False, 'changed_metric_count': 0, 'artifact_hash_change_count': 0, 'changed_file_added_count': 0, 'changed_file_removed_count': 0}`
- rule map errors: `[]`

## Known Gaps

- changed-ai suite records ROM rebuild as skipped unless explicitly requested.
- changed-ai suite records live trace refresh as skipped unless explicitly requested.
- changed-ai suite ingests existing ROM contribution trace artifacts but does not refresh them.
- changed-ai suite records generated score materialization as skipped unless explicitly requested.
- ROM/Python contribution traces are compared only when trace ids match.
- pre-choice replay remains a separate audit until trace timing is stable.

## Top Review Items

None.
