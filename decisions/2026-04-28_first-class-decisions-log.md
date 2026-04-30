# First-Class Decision Log

## Choice

Create a `decisions/` directory for durable judgment calls that future Codex
sessions could reasonably make differently.

Each file should stay short: what changed, what was rejected, and what would
change the decision later. The decision log is not another roadmap, handoff
folder, audit ledger, or design spec. It is the place for small architectural
and project-shape calls that need to be easy to find after the session context
is gone.

## Rejected

Do not keep putting these calls only into `docs/project_roadmap.md`,
`audit/*.md`, or `outbox/*.md`.

Those files are doing useful work, but they are already overloaded:

- `docs/project_roadmap.md` owns current workstream status.
- `audit/` owns evidence and review notes.
- `outbox/` owns handoffs and exported prompts.

None of those is the quiet, obvious home for "we chose this shape over that
shape, and here is the reason."

## Why

The repo has become good at routing work, but not quite as good at preserving
reversible judgment. A future helper can find the next task quickly, yet still
has to infer past taste and structure decisions from long status prose.

This directory makes those calls explicit without changing ROM behavior.

## What Would Change My Mind

If the decision files become another diary, duplicate roadmap status, or require
frequent maintenance to stay true, fold them back into the existing doc-role
system.

If they stay sparse and useful, link them from the navigation docs later.
