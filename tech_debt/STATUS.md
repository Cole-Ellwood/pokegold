# Status board

**Updated:** 2026-05-02

Projection of `AGENT_LOG.md` for fast lookup. The log is the
authoritative audit trail; this table is the index. Read this **first**
in any session — it tells you what's open, what's claimed, what's
blocked, what's done.

## State

| ID | Sev | State | Last entry | Notes |
|----|-----|-------|------------|-------|
| TD-001 | CRIT | open | — | strategic; depends on TD-005 + TD-007 closing first |
| TD-002 | CRIT | pending-trigger | — | gated on `SAVE_FORMAT_VERSION` bump |
| TD-003 | CRIT | open | — | release-gated; partial fix possible after TD-005 |
| TD-004 | HIGH | open | — | do **after** TD-005 (needs bank headroom) |
| TD-005 | HIGH | open | — | byte-recovery lever; see "Updated 2026-05-02" in FIX_PROPOSALS |
| TD-006 | HIGH | open | — | escalation on values **and** names |
| TD-007 | MED | open | — | selective in tight banks only |
| TD-008 | MED | open | — | research current RGBDS version first |
| TD-009 | MED | open | — | save-format risk; see "Updated 2026-05-02" in FIX_PROPOSALS |
| TD-010 | MED | **done** | 2026-05-02 | corrected recipe executed; see ADDENDUM and AGENT_LOG done entry |
| TD-011 | LOW | open | — | quick win |
| TD-012 | LOW | open | — | optional polish |
| TD-013 | LOW * | open | — | * mis-ranked; see ADDENDUM. Severity is effectively MEDIUM (EXP curve risk) |

## State definitions (mirrors AGENT_LOG.md)

- **open** — no agent has claimed or completed; available to take.
- **claimed** — an agent appended a `claimed:` entry within the last 24h
  and is presumably still working. Do not collide.
- **claimed-stale** — `claimed:` entry is >24h old with no follow-up.
  May be taken; log a new `claimed:` entry first.
- **partial** — work in progress, agent stopped at a defined checkpoint
  the next agent can pick up. Read the partial entry for the handoff.
- **blocked** — finding cannot be worked as written (proposal premise
  wrong, dependency missing, etc.). **Do not re-attempt** without
  either (a) explicit user un-block, or (b) `FIX_PROPOSALS.md` shows
  an "Updated YYYY-MM-DD" subsection addressing the block.
- **done** — fix shipped, full verification passed, finding closed.
- **accepted** — finding intentionally left as debt; user-approved.
- **disputed** — agent believes the finding is wrong; awaiting human
  reconciliation. Same handling as blocked: don't re-attempt.
- **pending-trigger** — gated on an external event (e.g. TD-002 waits
  on `SAVE_FORMAT_VERSION` bump). Don't claim until trigger fires.

## How to update this file

When you append a terminal `done` / `blocked` / `accepted` / `disputed`
entry to `AGENT_LOG.md`, also update this table in the **same commit**:

1. Set the `State` cell to the terminal state.
2. Set the `Last entry` cell to the AGENT_LOG entry's timestamp.
3. Add a one-line note in `Notes` if the state needs context (blocker
   summary, "see ADDENDUM", etc.).

For `claimed:` entries (non-terminal), do **not** update STATUS — too
churny. Other agents check by reading the log directly.

## Open count

11 open + 1 done + 1 pending-trigger = 13 total (matches
`TECH_DEBT_REPORT.md` index).

When the open count reaches **0** (or all remaining are `accepted` /
`pending-trigger`), the folder's job is done per `README.md`.

## Drift check

Run before claiming any finding:

```bash
python3 tools/audit/check_tech_debt_freshness.py
```

This catches:
- Stale `path/to/file.ext:NN` citations in the immutable docs.
- Orphan rows in this STATUS table (TD-### present here but not in
  `TECH_DEBT_REPORT.md`, or vice versa).
- ADDENDUM entries not cross-referenced from STATUS notes.
- STATUS state out of sync with the latest terminal `AGENT_LOG` entry.

Exit 0 = fresh. Exit 1 = drift; the script prints the offending
references. Fix the source/cite or update STATUS/FIX_PROPOSALS/ADDENDUM
per the workflow. Never edit `TECH_DEBT_REPORT.md` or
`FINDINGS_DETAIL.md`.
