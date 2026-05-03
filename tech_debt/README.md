# tech_debt/

Workstream folder for paying down tech debt in this hack. Designed so a fresh
agent session — no prior context — can pick up the work, do something useful,
and let the next session verify the work.

The deliverable target: when every finding here has been closed (fixed or
explicitly accepted), the codebase is as maintained as we can reasonably make
it without scope creep.

## The 10 commandments rule

`TECH_DEBT_REPORT.md` and `FINDINGS_DETAIL.md` are **immutable**. They are the
ground truth that lets future agents check past agents' work — answering
"does the claimed fix actually address what was identified?"

- Do **not** edit either file. Not to mark items as fixed, not to "clarify"
  wording, not to rephrase. Status lives in `AGENT_LOG.md`, never in the
  report.
- If you discover a new tech debt item not in the report, add it to a new
  file `TECH_DEBT_REPORT_ADDENDUM.md` (mirroring the same format) — never
  modify the original.
- If you believe a finding is wrong, stale, or already false at the time of
  writing, do **not** delete or edit it. Add an `AGENT_LOG.md` entry tagged
  `disputed:` explaining the disagreement with evidence. The human will
  reconcile.

## Workflow

1. Read `PROJECT_CONTEXT.md` if you don't already have project context loaded.
2. Open `TECH_DEBT_REPORT.md` — pick a finding by ID (TD-001..TD-013).
3. Open `FIX_PROPOSALS.md` — find the matching proposal. Read the recipe and
   the verification commands.
4. Open `AGENT_LOG.md` — confirm no other agent has claimed or completed this
   finding. If "claimed" but stale (>24h with no progress), you may take it.
5. Append a `claimed:` entry to `AGENT_LOG.md` before starting (one line —
   ID, your session marker, timestamp).
6. Execute the fix. Run every verification command listed in the proposal.
   Re-read the edited file(s) — "I edited it" is not verification.
7. Append a `done:` entry to `AGENT_LOG.md` with the standard format
   (template at the top of that file).
8. Stop. Hand off. Do not chain into the next finding in the same session
   unless explicitly instructed.

If you discover the proposal is wrong, the fix is harder than scoped, or the
work uncovers a deeper issue: **stop**, log a `blocked:` entry explaining
what you found, and surface to the human. Do not silently expand scope.

## Authority

Per `CLAUDE.md`, technical decisions, git, audits, and doc edits are
delegated to you. You can:
- Edit any source file required by the proposal.
- Run any audit script.
- Commit on your own branch (do not merge to master without human approval).
- Edit `FIX_PROPOSALS.md` to refine recipes (preserve original — add an
  "Updated YYYY-MM-DD" section, don't overwrite).
- Edit `PROJECT_CONTEXT.md` to keep it current with the project.

You cannot:
- Edit `TECH_DEBT_REPORT.md` or `FINDINGS_DETAIL.md`. Ever.
- Skip verification.
- Mark a finding `done:` without the audit floor passing.

## File map

| File | Purpose | Mutability |
|------|---------|-----------|
| `README.md` | This file — orientation + workflow | Editable for clarity |
| `PROJECT_CONTEXT.md` | What the hack is, where code lives, build & verify | Editable as project evolves |
| `TECH_DEBT_REPORT.md` | The 13 findings by severity | **IMMUTABLE** |
| `FINDINGS_DETAIL.md` | Raw evidence backing each finding | **IMMUTABLE** |
| `FIX_PROPOSALS.md` | Recipe per finding; ranked order | Editable; preserve history |
| `AGENT_LOG.md` | Append-only record of agent work | Append-only |

## Recommended order

The proposals are ranked 1..13 inside `FIX_PROPOSALS.md`. Default behavior:
take the lowest-numbered open item whose verification floor you can meet.

Quick wins first (TD-010, TD-011, TD-009) → byte-recovery refactors
(TD-005, TD-013) → selective pruning (TD-007) → readability (TD-006) →
structural (TD-004) → tooling (TD-012, TD-008) → strategic monitoring
(TD-001) → release-gated (TD-002, TD-003).

## Definition of done

Every TD-### in `TECH_DEBT_REPORT.md` has a terminal `AGENT_LOG.md` entry —
either:
- `done:` with verification evidence, **or**
- `accepted:` (with human approval logged) explaining why this finding is
  intentionally left as debt.

When that holds, this folder's job is done.
