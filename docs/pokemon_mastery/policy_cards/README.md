# Policy Cards

Purpose: keep live decision context small without deleting the evidence archive.
Policy cards are compact summaries of active decision boundaries. They point
back to quick tests, reviews, and source-to-policy entries instead of copying
the full history.

Use cards when a work block needs a current rule fast. Use the full artifacts
when auditing evidence, scoring a replay, or revising the card.

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

Rules:

- Keep each card short enough to load beside `active_context.md`.
- Include an opposite boundary before promoting a rule into live-turn context.
- Do not paste long replay analysis. Link to evidence.
- Do not use a card as romhack truth unless local status is verified.
- If a card causes the opposite error within two fresh replay runs, revise it.

## Active Cards

- `cashout_boundary.md`
- `sleep_absorber_and_set_ambiguity.md`
- `hazard_loop_spin_window.md`
- `support_handoff_after_job.md`
- `active_pressure_before_status.md`
- `branch_action_after_naming.md`
- `hidden_role_voluntary_entry.md`
- `romhack_mechanics_firewall.md`
