# Status board

**Updated:** 2026-05-03

Projection of `AGENT_LOG.md` for fast lookup. The log is the
authoritative audit trail; this table is the index. Read this **first**
in any session — it tells you what's open, what's claimed, what's
blocked, what's done.

## State

| ID | Sev | State | Last entry | Notes |
|----|-----|-------|------------|-------|
| TD-001 | CRIT | partial | 2026-05-03 | re-evaluated 2026-05-03; bank-pressure picture refreshed in ADDENDUM 2026-05-03 — 0x0e no longer canary (568 free), 0x0d (Effect Commands, 6 free) is new tight battle bank; pic-bank guard shipped 2026-05-03 (`tools/audit/check_pic_bank_pressure.py`); remaining work: TD-005 P2 + P3 (P3 enumerated 2026-05-03, conversion still open), TD-009a |
| TD-002 | CRIT | pending-trigger | — | gated on `SAVE_FORMAT_VERSION` bump |
| TD-003 | CRIT | partial | 2026-05-03 | Option 1 + Option 2 shipped 2026-05-03 (`tools/audit/check_layout_orgs.py` validates 5 known pins; `docs/layout_pins.md` documents each pin's purpose). Option 3 (Stadium 2 relocation) remains release-gated — needs hardware/emulator verification |
| TD-004 | HIGH | open | — | do **after** TD-005 (needs bank headroom) |
| TD-005 | HIGH | partial | 2026-05-03 | Pattern 1 closed (41 bytes recovered in bank 0e); Pattern 2 gated on user WIP in experience.asm; Pattern 3 enumerated 2026-05-03 (66 Class A sites in `tech_debt/EVIDENCE/td_005_pattern3_sites.md`, 27 of which sit in canary bank 0x0d) — conversion to `_GetSidedAddr` still open |
| TD-006 | HIGH | open | — | escalation on values **and** names |
| TD-007 | MED | **done** | 2026-05-03 | 47 Beta\*_Blocks pruned; 5,854 bytes recovered (banks 0x2a +3500, 0x2b +2259, 0x37 +95). SHA1/dist update needs user playtest |
| TD-008 | MED | partial | 2026-05-03 | research step shipped (`tech_debt/EVIDENCE/td_008_rgbds_changelog.md`); current pin v1.0.1 IS upstream's latest stable, **no upgrade available now** — re-scoped to watch-item gated on next upstream release (see FIX_PROPOSALS "Updated 2026-05-03") |
| TD-009 | MED | open | 2026-05-02 (escalation) | TD-009a needs user approval — dead writes expand scope to vblank.asm, intro_menu.asm, events.asm; see ADDENDUM |
| TD-010 | MED | **done** | 2026-05-02 | corrected recipe executed; see ADDENDUM and AGENT_LOG done entry |
| TD-011 | LOW | **disputed** | 2026-05-02 | script IS used by docs/manifest.md; see ADDENDUM |
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

5 open + 4 partial + 2 done + 1 disputed + 1 pending-trigger = 13 total
(matches `TECH_DEBT_REPORT.md` index).

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
