# Agent Log — append-only

Every agent that touches a TD-### finding logs here. **Do not edit existing
entries.** Append at the bottom in chronological order.

The log lets future agents (and the human) verify whether a claimed fix
actually addresses what `TECH_DEBT_REPORT.md` and `FINDINGS_DETAIL.md`
identified.

---

## Entry format

Use this exact template. Copy, fill, append.

```markdown
## YYYY-MM-DD HH:MM — TD-### — <state>

- **Agent / session:** <model name + session marker, e.g. "Opus 4.6 / sonnet-claude-zen-kilby-de2004">
- **State:** claimed | done | partial | blocked | accepted | disputed | pending-trigger
- **Branch / commit:** <branch name @ short SHA, or "uncommitted">
- **Files touched:** <comma-separated list, or "(none yet)">
- **Summary:** <1-3 sentences of what was done or attempted>
- **Verification run:**
  - `<command>` → <PASS / FAIL / N/A> <(any notable output)>
  - `<command>` → <PASS / FAIL / N/A>
- **Bytes recovered (if applicable):** <number, or N/A>
- **Bank impact (if applicable):** <which bank's free count changed, before/after>
- **Issues / followups:** <anything not done, deferred, or surfaced for human>
- **Verifier check:** <how a future agent can independently confirm the fix; usually a re-run of the verification commands>
```

### State definitions

- **claimed** — agent is starting work; appended at session start to claim the finding so two agents don't collide.
- **done** — fix implemented, full verification floor passed, finding closed.
- **partial** — fix partially implemented (e.g. macros defined but not all sites replaced); next agent can continue. Include exactly where to pick up.
- **blocked** — agent stopped; cannot proceed without input or because a dependency isn't met. Surface to human.
- **accepted** — finding is intentionally left as debt. Requires human approval (note who approved and when).
- **disputed** — agent believes the finding is wrong, stale, or already false. Provide evidence; human reconciles.
- **pending-trigger** — finding is gated on an external event (e.g. TD-002 waits for `SAVE_FORMAT_VERSION` bump). Log this once to indicate awareness; don't re-log on every session.

---

## Example entry (illustrative — delete the example block once real entries exist)

```markdown
## 2026-05-03 14:22 — TD-010 — done

- **Agent / session:** Opus 4.6 / claude-zen-kilby-de2004
- **State:** done
- **Branch / commit:** claude/td-010-gitignore @ abc1234
- **Files touched:** .gitignore
- **Summary:** Removed 6 entries for non-existent paths and 3 duplicate save-state lines from `.gitignore`. Kept `dist/*.gb` defensively (per FIX_PROPOSALS recommendation).
- **Verification run:**
  - `git status` → PASS (no previously-ignored files now tracked)
  - `ls -la rgbds-1.0.1/ .local/ .claude_handoffs/ .rebalance_chain/` → PASS (all four absent, removal of their gitignore entries is safe)
- **Bytes recovered:** N/A
- **Bank impact:** N/A
- **Issues / followups:** None.
- **Verifier check:** `git log -p .gitignore` shows the diff; `grep -n 'rgbds-1.0.1' .gitignore` returns empty.
```

---

## Real entries below (append here)

<!-- No agent has logged work yet. First agent to take a finding starts here. -->
