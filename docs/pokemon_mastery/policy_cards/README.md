# Policy Cards: Expanded Reference

Purpose: preserve expanded decision-boundary evidence without making it default
fresh move-choice context.

The old long policy cards are retained as reference/provenance. For fresh
unseen replay decisions, load `../live_core.md`, the current prompt, and at
most one tiny `../heuristic_core/*.md` card before freezing an answer.

Use these expanded cards after scoring, during postmortem review, or when a
tiny heuristic needs evidence-backed revision. Do not load them pre-freeze
unless the task is explicitly open-book practice or non-fresh analysis.

## Card Format

```text
# Policy Card: [name]

Status:
Use when:

Trigger:
Default:
Opposite boundary:
Exceptions:
Worst branch:
Local status:
Evidence:
Drill:
```

Reference rules:

- Treat these cards as archive/reference, not live default context.
- Include an opposite boundary before promoting a rule into live-turn context.
- Do not paste long replay analysis. Link to evidence.
- Do not use a card as romhack truth unless local status is verified.
- If a card causes the opposite error within two fresh replay runs, revise it.

## Expanded Reference Cards

- `cashout_boundary.md`
- `sleep_absorber_and_set_ambiguity.md`
- `hazard_loop_spin_window.md`
- `support_handoff_after_job.md`
- `active_pressure_before_status.md`
- `branch_action_after_naming.md`
- `hidden_role_voluntary_entry.md`
- `romhack_mechanics_firewall.md`

## Live Replacement

Compressed live heuristics now live in `../heuristic_core/`. The migration map
there links repeated old lessons to the new small rules while preserving this
directory as searchable evidence.
