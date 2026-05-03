# tech_debt/ changelog

Meta-changes to this folder itself: addendums added, proposals
updated, status mutations, audit-script additions, workflow tweaks.
**Not** a log of TD-### work — that lives in `AGENT_LOG.md`.

Append-only. Newest entries on top within each date. Reverse-chronological
between dates.

---

## 2026-05-02

- **`d6ac595d`** — TD-005 / TD-009 / TD-013 verification floors tightened
  via `FIX_PROPOSALS.md` "Updated 2026-05-02" subsections (META_AUDIT
  TD-A03, A04, A05). TD-005 byte-recovery target dropped from "500-700"
  to realistic "150-450 conditional on measurement." TD-009 split into
  TD-009a (HRAM-safe) and TD-009b (WRAM, escalation-gated). TD-013
  requires SHA1 match.
- **`d2ec59ca`** — TD-010 corrected. Added
  `TECH_DEBT_REPORT_ADDENDUM.md` (new file) with TD-010 supersession,
  TD-013 severity revision (LOW → effective MEDIUM), TD-009 risk
  reframe. `FIX_PROPOSALS.md` TD-010 gained "Updated 2026-05-02"
  subsection scoping the recipe to safely-actionable changes only.
  Closes META_AUDIT TD-A01.
- **`8a9aaefc`** — Added `STATUS.md` board (META_AUDIT TD-A02). Updated
  `README.md` workflow to read STATUS first; appended blocked-handling
  rules (META_AUDIT TD-A12). File-map table updated to include
  `STATUS.md`, `META_AUDIT.md`, `TECH_DEBT_REPORT_ADDENDUM.md`.
- **`56e88c7c`** — `META_AUDIT.md` added (this audit). 12 defects
  identified (TD-A01..TD-A12) with ranked fix list. Verdict: not
  ship-ready until items 1-6 land.
- **`bb23e2d6`** — Added `tools/audit/check_tech_debt_freshness.py`
  (META_AUDIT fix-list item 7). Catches stale file:line citations,
  STATUS/REPORT orphans, ADDENDUM cross-link gaps, and STATUS state
  out-of-sync with AGENT_LOG. Initial run clean.
- **`e0fa619d`** — `python` → `python3` in audit commands across
  `PROJECT_CONTEXT.md` and `FIX_PROPOSALS.md` (META_AUDIT TD-A11).
  Mechanical sed; 25 lines.

## 2026-05-03 (UTC; pre-meta-audit)

- **`a5004b9b`** — TD-010 claimed and immediately blocked by
  `claude-unruffled-khayyam-35aa2d`. Proposal premise wrong; the
  blocked entry catalogues three errors. This entry is what triggered
  the meta-audit pass.

## 2026-05-02 (initial commit)

- **`02889a87`** + **`723057e4`** — Folder created. Six files:
  README, PROJECT_CONTEXT, TECH_DEBT_REPORT (immutable, 13 findings),
  FINDINGS_DETAIL (immutable), FIX_PROPOSALS, AGENT_LOG.

---

## How to append

After a meta-change ships, add an entry above with:
- The commit SHA in backticks
- One-sentence summary referencing the META_AUDIT TD-A### or other
  driver
- Cross-link to relevant file changes if non-obvious

Don't log TD-### finding work here — that goes in `AGENT_LOG.md`.
This file is for changes to the **scaffolding** (workflow, audits,
templates, addenda, status board, etc.).
