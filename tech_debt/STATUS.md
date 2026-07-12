# Status board

**Updated:** 2026-07-12 (second pass after user review: TD-006 done — values signed off + constants shipped SHA1-identical; TD-009 accepted — user-approved park with piggyback clause; TD-001 accepted per its 2026-05-03 closure plan. Earlier same day: TD-002 + TD-005 closed)

<!-- audit:noqa-file stale-claims — by-design date-anchored index doc; freshness enforced by tools/audit/check_tech_debt_freshness.py -->

Projection of `AGENT_LOG.md` for fast lookup. The log is the
authoritative audit trail; this table is the index. Read this **first**
in any session — it tells you what's open, what's claimed, what's
blocked, what's done.

## State

| ID | Sev | State | Last entry | Notes |
|----|-----|-------|------------|-------|
| TD-001 | CRIT | **accepted** | 2026-07-12 | closed per its own 2026-05-03 exit plan: pic-bank guard shipped, TD-005 closed (174 B), TD-009/TD-009a accepted. Bank pressure stays monitored (`check_pic_bank_pressure.py` + dev_index Tight Banks), not actively fixable; see ADDENDUM 2026-05-03 for the pressure picture |
| TD-002 | CRIT | **done** | 2026-07-12 | trigger fired: v2→v3 bump landed in `1c256cb4` and the save rework removed the `$FF` legacy accept path entirely (only v3 direct + v2 via offset-map migration load). Comment cleanup (recipe steps 3-4) shipped 2026-07-12; `check_save_format_version.py` PASS |
| TD-003 | CRIT | partial | 2026-05-03 | Option 1 + Option 2 shipped 2026-05-03 (`tools/audit/check_layout_orgs.py` validates 5 known pins; `docs/layout_pins.md` documents each pin's purpose). Option 3 (Stadium 2 relocation) remains release-gated — needs hardware/emulator verification |
| TD-004 | HIGH | **done** | 2026-05-28 | boss.asm split for navigation (commit `3ca2ecf6`) into boss_platform / boss_policy_move / boss_policy_switch / boss_thunks; whole-file monolith resolved. boss_policy_move stays 6,417 lines — a fresh finding if ever a concern. Source citations to the old path superseded; see ADDENDUM TD-A16 |
| TD-005 | HIGH | **done** | 2026-07-12 | all 3 patterns closed; 174 bytes total. Pattern 2 finished 2026-07-12: the product→dividend re-staging at 6 sites was a literal no-op (hProduct ≡ hDividend in the HRAM math UNION) — deleted for 88 bytes in bank 0x11; the ROM0 thunk idea was dropped per the recipe's own <100-byte stop rule. clobber_smoke 28/28 PASS. See `tech_debt/EVIDENCE/td_005_pattern3_sites.md` |
| TD-006 | HIGH | **done** | 2026-07-12 | all 3 sub-fixes closed. TD-006c already satisfied in source; TD-006b (GrowthRates masks) + TD-006a (type-passive status constants: ELECTRIC_SPD_*, PRZ_SPD_*, BRN_ATK_*) shipped 2026-07-12, both SHA1-identical. User signed off the values 2026-07-12: prz Speed 25/37.5/50%, brn Atk 50/62.5/75%, Electric Speed +2.5/+5% |
| TD-007 | MED | **done** | 2026-05-03 | 47 Beta\*_Blocks pruned; 5,854 bytes recovered (banks 0x2a +3500, 0x2b +2259, 0x37 +95). SHA1/dist update needs user playtest |
| TD-008 | MED | partial | 2026-05-03 | research step shipped (`tech_debt/EVIDENCE/td_008_rgbds_changelog.md`); current pin v1.0.1 IS upstream's latest stable, **no upgrade available now** — re-scoped to watch-item gated on next upstream release (see FIX_PROPOSALS "Updated 2026-05-03") |
| TD-009 | MED | **accepted** | 2026-07-12 | user-approved park 2026-07-12. Flagship deletions landed in `f2acf5c3` (45 B); remaining ~15 B stays — a v3→v4 save bump for it is a bad trade. **Piggyback clause:** fold these deletions into any future save-format bump for free. TD-009a (dead HRAM writes) folded into the same accepted state; see ADDENDUM |
| TD-010 | MED | **done** | 2026-05-02 | corrected recipe executed; see ADDENDUM and AGENT_LOG done entry |
| TD-011 | LOW | **disputed** | 2026-05-02 | script IS used by docs/manifest.md; see ADDENDUM |
| TD-012 | LOW | **done** | 2026-05-04 | 3 Makefile shell hacks (`cp -f`, `cat $^ > $@`, `tr -d '\\000'`) replaced with cross-platform Python helpers (`tools/copy_file.py`, `tools/concat_files.py`, `tools/strip_nulls.py`); SHA1 unchanged across all 6 ROM/patch outputs. |
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

1 open + 2 partial + 7 done + 1 disputed + 2 accepted = 13 total
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
