# Pokemon Mastery Playbook Manifest

Purpose: keep decision-time context small without throwing away evidence.
Future sessions should use this as the load contract before touching the
larger archive.

## Work-Block Startup

Open first:

- `active_context.md`
- `live_core.md`
- `master_index.md`

These files route the task. They are not proof of improvement and should stay
small.

## Fresh Move Choice

Before freezing an unseen replay answer, use only:

- `live_core.md`
- the public prompt/log state
- the smallest useful set of `heuristic_core/*.md` cards
- compact `canon/*.md` or `romhack_deltas/*.md` lookups only when the current
  public board needs that fact

Do not load broad archives before the answer is frozen.

## Topic Retrieval Library

Use these only by topic, not by folder glob:

- `canon/` for compact Smogon GSC facts.
- `romhack_deltas/` for local mechanics forks and pending-status guards.
- `policy_cards/` for expanded boundary references after scoring or during
  open-book analysis.
- `cookbook.md` for reusable recipes after using `master_index.md` to locate
  the relevant topic.
- `source_to_policy_ledger.md` for provenance and rule bodies after the
  relevant STP entry is known.

## Workspace Provenance

These are measurement or research trails, not playbook context:

- `workspace/quick_tests/`
- `workspace/pro_notes/`
- `workspace/external_research_returns/`
- `workspace/measurement_reports/`
- `workspace/battle_captures/`
- scored review retrospectives, long practice drills, and date-stamped
  process handoffs unless a postmortem specifically asks for them

Preserve workspace files. Move or filter them out of default selection; do not
delete them.

## Promotion Gate

One miss goes to workspace evidence. A new live heuristic or policy card is
promoted only when the same miss class appears across at least two fresh
unseen decisions, or when a verified mechanics fact directly changes legal
move advice.

Progress requires fresh-score movement: severe errors stay low while
top-match, acceptable-match, route conversion, branch-punish obedience, and
positive selection improve. Cleaner notes are not progress by themselves.
