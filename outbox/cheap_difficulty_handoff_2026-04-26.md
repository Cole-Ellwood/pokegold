# Cheap Difficulty Handoff - 2026-04-26

This session chose the cheap-difficulty lane.

Why:

- Release confidence was already green.
- Early player communication had just been improved.
- `DIFFICULTY-001` was still `UNTOUCHED`, and cheapness is exactly the kind of
  problem that can hide behind "the audits pass."

What changed:

- Added `tools/audit/check_cheap_difficulty.py`.
- Routed it from `docs/agent_navigation/task_router.md`,
  `docs/agent_navigation/verification_matrix.md`, and
  `docs/codex_review_playbook.md`.
- Added `audit/cheap_difficulty_2026-04-26.md`.
- Updated `docs/project_roadmap.md` for `DIFFICULTY-001`.

What the audit checks:

- Early-tier late-item leakage.
- Choice item timing.
- Life Orb / Assault Vest tier timing.
- Light Ball ownership.
- Party-size pressure by tier.
- Rival starter-branch pressure parity.
- Johto Gym peak-level curve.

Current result:

- `python tools\audit\check_cheap_difficulty.py` passed.
- Adjacent AI tier, boss item, and boss move audits passed.
- `python tools\audit\bug_hunt_triage.py --max-leads 10` found no ranked leads.

Next good move:

Use this script after trainer-party edits, especially any boss itemization pass.
For actual cheapness, the scarce proof is still manual or trace-backed fight
feel: a player losing and saying "I see why" instead of "the game lied."
