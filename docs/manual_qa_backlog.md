# Manual QA Backlog

Things that **a human playing the ROM** needs to verify, because audits can't.
Coding agents cannot read this off the source.

If audits cover it, **don't list it here** — point at the audit instead.
This file is the inventory of *unaudited* surface area, not a re-statement
of what `tools/audit/check_release_smoke.py` already proves.

## How to read a row

Each item:
- **What** — concrete in-game scenario (specific Pokemon, level, move, map).
- **Why** — the audit gap. What can't be proven from source alone.
- **How to test** — the steps a player runs.
- **Last verified** — date + ROM SHA1 + outcome, or `pending`.

Rows live under one of the **Areas** below. Add new rows under the right
area; create a new area only when none of the existing ones fit.

## Areas

### Save format

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Fresh save → quit → load on same ROM | `SAVE_FORMAT_VERSION=1` was just wired; round-trip never been played. | New game → save → reset → load. Confirm party / location / time match. | pending |
| Hall of Fame survives save/load | HoF lives in its own SRAM section that the marker doesn't touch; no audit confirms layout-stable across builds. | Beat E4 → enter HoF → save → reset → re-enter HoF screen, confirm team renders. | pending |
| Active Box survives save/load | Box layout sits immediately after the new marker byte in SRAM bank 1. Audit fingerprints the labels but not on-cart byte alignment. | Deposit a Pokemon → save → reset → withdraw, confirm the same Pokemon. | pending |
| Legacy save (pre-marker SHA `7de0879a`) loads or rejects cleanly | `$FF` graceful migration path is implemented but never run on a real legacy save. Wrong outcome = silent data corruption, not a crash. | Apply `dist/pokegold-data-rebalance.bps` to the baseline and load with the current ROM. Either it loads with no glitches OR it shows "no save" — anything in between is a bug. | pending |

### Boss AI fairness

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Each gym leader feels fair at intended level | Boss AI overlay is on top of vanilla scoring; "feel" is not an audit-able property. The full list with rationales lives in `docs/boss_ai_bug_testing_plan.md`. | Run the per-leader scenarios from `docs/boss_ai_bug_testing_plan.md`. | pending |
| Whitney with a level-18 Geodude wipes (still) | Cited as a deliberate difficulty case in `CLAUDE.md`. If she stops wiping, the rebalance overshot. | Train a Geodude to level 18, fight Whitney, record outcome. | pending |
| Rival fights show the right plan flavor per stage | Plan/role logic per boss lives in `boss.asm` `.rival:2101` etc. — code is audited, *intent* isn't. | Fight rival at each appearance; note whether his lead picks and switches feel deliberate. | pending |
| Champion fight uses ace-timing hook visibly | `BossAI_AceTimingHook:3794` exists but no audit proves the timing reads as intended. | Reach Lance, observe whether his ace switch-in feels paced. | pending |

### Pokemon balance / role expression

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Each "buffed" Pokemon feels usable in its intended role | Role intent lives in `docs/balance_intent.md` and `docs/buff_backlog.md`; numbers can be audited (`scripts/generate_balance_audit.py`) but feel cannot. | Run a small playthrough with one buffed mon per archetype; note whether role reads. | pending |
| Evolution timings still pace early-mid game | `docs/evolution_policy.md` has the design intent. Audits check stats and methods but not pacing. | Note when each starter/early mon hits its first/second evo in normal play. | pending |
| TM/HM availability matches intended pacing | Audits check that TMs exist and that learnsets reference real moves; they don't check *when* the player gets them. | Track which TMs are accessible by each badge; compare to `docs/balance_intent.md`. | pending |

### QoL features (already audited; need UX confirmation)

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Default text speed reads as `FAST` from a fresh game | Source audited; player perception not. | New game → check Options menu → confirm text crawl speed at default. | pending |
| Move Reminder shows 4 moves per page (not 3) | Audited at compile time; menu rendering not. | Reach Move Reminder NPC → confirm 4 entries fit per page. | pending |
| Goldenrod Bike Shop auto-registers bicycle if Select slot empty | Audited at compile time; UI flow not. | Empty the Select-registered item → enter Bike Shop → confirm bike registers automatically. | pending |

### Maps / events / scripts

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Bug Contest exit flow doesn't softlock | `tools/audit/check_release_smoke.py` validates script shape, not runtime behavior. | Enter Bug Contest, withdraw mid-contest, confirm map state restores. | pending |
| Itemballs deliver the items the audit says they should | Audits check labels and table consistency; runtime delivery is separate. | Pick up itemballs along Route 30 / 31 / Sprout Tower; confirm each gives the audited item. | pending |
| Phone calls don't repeat after a deletion | `tools/audit/check_release_smoke.py` checks the deletion-guard flag; behavior isn't sim'd. | Add an NPC to phone, delete, advance time, confirm they don't re-call. | pending |

### Audio / visual

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| (Add as needed) | | | |

## How to add to this file

When you (a coding agent) ship a change that has *gameplay-visible* behavior
no audit can prove, add a row to the right area. Keep the **What** column
specific enough that a player can act on it without re-reading source. If
the change is purely internal (refactor, audit, doc), no row is needed —
this file is for surface that requires human eyes.

When the user reports a manual verification result, update **Last verified**
with date + ROM SHA1 + one-word outcome (`pass`, `fail`, `partial`). Don't
delete the row even after pass — keep the history so future regressions
have a baseline to compare against.

A fresh agent can rebuild or extend this file using the seed prompt at
the bottom of this file.

## Seed prompt for a fresh Claude session

Paste this verbatim into a new Claude Code session in this repo. It tells
the session to read the codebase top-to-bottom and add anything missing
from the table above.

```
Goal: extend `docs/manual_qa_backlog.md` so it covers every gameplay-visible
behavior in this repo that a coding agent cannot verify from source. The
file is for things a *human playing the ROM* needs to confirm, because
audits can't.

Read first (in this order):
  1. `docs/manual_qa_backlog.md` (the file you're extending — match its
     row format and respect its "don't list audited things" rule).
  2. `CLAUDE.md` (workflow + escalation contract; lists known design taste
     calls like the Whitney difficulty case).
  3. `docs/project_context.md` and `docs/project_roadmap.md` (project
     intent and current scope).
  4. `docs/boss_ai_spec.md`, `docs/boss_ai_post_patch_notes.md`,
     `docs/boss_ai_bug_testing_plan.md` (boss AI design + the existing
     per-boss test scenarios — DO reference rather than duplicate).
  5. `docs/balance_intent.md`, `docs/buff_backlog.md`,
     `docs/evolution_policy.md` (Pokemon balance design intent).
  6. `docs/qol_handoff.md` (QoL changes shipped + still-pending).
  7. `docs/smoke_test.md` and `tools/audit/check_release_smoke.py` (what's
     ALREADY audited — don't list any of this in the backlog).
  8. `git log --oneline -50` and `git log --since="6 weeks ago" --stat`
     (what's changed recently that may not be playtested yet).

Then, for every category below, decide whether the existing rows in
`manual_qa_backlog.md` cover the surface area. If a gap exists, add a row.
If a row is too vague ("test Boss AI"), tighten it ("fight Whitney with
a level-18 Geodude and confirm she still wipes you"). Do NOT delete rows
that are already there — only add or sharpen.

Categories to sweep:
  - Save format (any SRAM layout change since last full playthrough).
  - Boss AI fairness per leader / rival / champion.
  - Pokemon balance / role expression for buffed mons.
  - Evolution / TM / HM pacing.
  - QoL features (UX confirmation, not source).
  - Map scripts and event triggers (especially anything in
    `engine/events/` or `maps/` touched in the last 8 weeks).
  - Itemball delivery, mart inventories, phone scripts.
  - Audio / visual (cries, palettes, tilemaps) where source recently moved.
  - Anything in `docs/project_completion_todo.md` not yet marked done.

Hard rules:
  - If `python tools/audit/check_release_smoke.py` (or any other audit in
    `tools/audit/`) already proves the property, do NOT add it. Audits are
    the source of truth for what's verified — this file is only for the
    *unaudited* surface.
  - Each row's "What" column must name a concrete in-game scenario a
    player can act on without re-reading source. If you can't write that
    sentence, you don't understand the test yet — read more before adding.
  - Each row's "Why" column must name the audit gap. If the gap is "no
    audit exists yet", say so; that's a signal someone could write one.
  - Do not add rows for hypothetical features. Only ship behavior.
  - Keep "Last verified" set to `pending` for new rows. The user updates
    that column after they playtest.

Output: a single edit to `docs/manual_qa_backlog.md`. No new files. Don't
narrate; just do the edit and tell the user how many rows you added per
category.

Stop and ask if: more than 30 candidate rows pile up (the file is meant
to be reviewable, not exhaustive — at that point the user should triage
first), or if you find an audit gap so severe that an audit script is
the right answer instead of a manual row.
```
