# Codex Task — Build `/codex-pgoal` Synthesis Skill

**Status:** v0 spec, Cole-approved 2026-05-22 via /pgoal AskUserQuestion intake.
**Pairing:** Claude (prompter, ~30%) + Codex (implementer, ~70%) under mutual approval.
**Artifact:** `~/.claude/skills/codex-pgoal/SKILL.md` (user-level, works in any repo).
**Roadmap home:** this file (`docs/codex_pgoal_skill_codex_task.md`) — canonical contract, both LLMs read it, update it before drift.

## Goal

Build a new Claude Code skill, `/codex-pgoal`, that synthesizes `/pgoal`'s durable verifier-gated harness with `/codex-task`'s Codex desktop-pairing protocol. The skill keeps Claude working non-stop on a user-supplied objective while pairing with Codex as the implementing partner under the 30/70 split and mutual-approval rule from `feedback_30_70_split_mutual_approval.md`.

Cole's exact ask: *"i love how powerful pgoal is. make a synthesis skill please? in fact work with codex to build that new ultra skill"* — so the synthesis itself is paired work, not a Claude-solo write.

## Locked decisions (from AskUserQuestion intake)

| Question | Answer | Implication |
|---|---|---|
| Skill name | `codex-pgoal` | Directory `~/.claude/skills/codex-pgoal/`; invoked as `/codex-pgoal <objective>` |
| Location | User-level | Works in any project, not just Pokemon repo |
| Codex's role | Equal partner, 70/30 work split (Codex codes, Claude prompts/reviews), mutual approval on major decisions | Mirrors today's debrief rules |
| Loop model | Hybrid — drive between slices, poll mid-slice | Per `feedback_poll_codex_progress.md` cadence |

## In scope (v1 MVP)

1. `~/.claude/skills/codex-pgoal/SKILL.md` with valid YAML frontmatter (`name: codex-pgoal`, `description: ...` covering when to trigger).
2. **Step 0** — Front-load roadmap via AskUserQuestion (scope, acceptance, edge cases, verification floor, branching, stop conditions, disagreement resolution, time budget, async channel). Write committed roadmap to `docs/<kebab-slug>_codex_task.md`. Commit before opening Codex. Mirror the `/codex-task` Step 0 discipline.
3. **Step 1** — Arm `/pgoal` under the hood by shelling its CLI (`pgoal set --objective ... --replace`, `pgoal prd save --approved`, `pgoal acceptance init`). Do **not** invoke `/pgoal` as a nested skill — pgoal's safety rule forbids nesting.
4. **Step 2** — Load computer-use tools via `ToolSearch({ query: "computer-use", max_results: 30 })`. Request the 12-app bundle (Codex, Claude, VLC, Spotify, Discord, Chrome, File Explorer, Notepad, Snipping Tool, Steam, Terminal, PowerShell) with `clipboardWrite/Read/systemKeyCombos`. Per `/codex-task` Step 2 verbatim.
5. **Step 3** — `open_application Codex`, screenshot, orient to the right chat (left sidebar, project name). Click into existing or create new chat.
6. **Step 4** — Compose the task block in `---CODEX-TASK---` format pointing at the committed roadmap file; send via clipboard paste (`write_clipboard` → `left_click` chat input → `key ctrl+v` → `left_click` send button at the chat-specific coordinates).
7. **Step 5** — Hybrid loop body:
   - Each pgoal iteration begins with a screenshot.
   - Classify Codex state: `idle` (last slice acked, ready for next) / `mid-slice` (Thinking indicator, code edits in progress) / `waiting-on-review` (Codex posted a slice review request) / `blocked` (error, asking question).
   - If `idle` → compose next slice from the roadmap + handoff log, send via Ctrl+Enter (steer) for load-bearing messages, Enter (queue) for follow-ups.
   - If `mid-slice` → screenshot every ~15s active / ~120s idle (per `feedback_poll_codex_progress.md`). Do NOT block on `pgoal note` — note progress with timestamps so the Stop hook keeps firing.
   - If `waiting-on-review` → read Codex's reply, run adversarial review per `reference_llm_pairing_rules.md` decision-useful bar, post verdict via clipboard.
   - If `blocked` → escalate per the disagreement-resolution rule below.
8. **Step 6** — Mutual approval gates. Every major decision (slice spec, slice review, scope change, commit, accept, completion) requires both Claude and Codex sign-off. Use the handoff log substrate (project-local `audit/<slug>_handoff_log.jsonl` or whatever exists for the goal) with the `ack_start → slice_update → slice_review → mutual_done` event sequence. Silence is unknown, not approval. Per today's `feedback_30_70_split_mutual_approval.md` operational-protocol section.
9. **Step 7** — Failure modes documented. Replicate `/codex-task`'s "Failure modes to avoid" section, plus today's lessons: hard-stop reflex on unapproved collision-risk ack_starts; 2-commits-or-1-hour surfacing cadence; "don't want to interrupt their good run" warning sign; queue-alarm signal from growing Steer-chip column.
10. **Composes with `/pgoal`**, not parallel to it. Skill defers to pgoal's completion gate; never unilaterally declares done. Skill defers to pgoal's tamper-protected proof surface; doesn't bypass.

## Out of scope (deferred)

- Project-level variant (user-level only for v1).
- Multi-Codex / multi-LLM beyond Claude+Codex.
- Cross-emulator / cross-machine pairing.
- Voice or video integration.
- Auto-spawning Codex from CLI (assume desktop app installed + chat reachable).
- An `/codex-pgoal-doctor` self-check (nice-to-have).
- Auto-detection of which Codex chat to use (skill orients via screenshot, surfaces what it landed on, user fixes if wrong).
- In-repo backup of the user-level skill file (skip for v1; user-level path is canonical).

## Acceptance criteria

Mirrored from `acceptance.lock.json`. All 5 must pass for `pgoal verify --run --record` to green-light completion:

1. **`skill_exists`** — `~/.claude/skills/codex-pgoal/SKILL.md` exists and is readable.
2. **`skill_frontmatter`** — File contains `name: codex-pgoal` and `description:` in YAML frontmatter.
3. **`skill_sections`** — File contains literal markers for `Step 0` through `Step 7` (eight required sections).
4. **`roadmap_committed`** — `git log --oneline -- docs/codex_pgoal_skill_codex_task.md` returns at least one commit.
5. **`mutual_done`** — `audit/codex_pgoal_handoff_log.jsonl` contains a row `event=mutual_done phase=codex-pgoal-skill-v1 status=complete`.

## Approach preference

Use today's debrief operational protocol verbatim:

- **Files-first split.** Declare write-set before edits land. The write-set for v1: `~/.claude/skills/codex-pgoal/SKILL.md` (Codex authors); `docs/codex_pgoal_skill_codex_task.md` (Claude authors, this file); `audit/codex_pgoal_handoff_log.jsonl` (both append).
- **Confidence labels.** `repo-proven` (with at least one `path:line` citation), `memory-derived`, or `judgment`. Stated explicitly on every load-bearing claim.
- **Adversarial review.** Each LLM reviews the other's drafts; "first-draft acceptance" is the failure mode to avoid. Default review stance: assume the draft has a bug, prove it doesn't.
- **2-commits-or-1-hour cadence.** Surface direction (current commits, pending reviews, proposed next lane, collision files) at that cadence regardless of momentum.

## Edge cases

- **Skill already exists.** If `~/.claude/skills/codex-pgoal/SKILL.md` is present from a prior attempt, treat as iterate-on-existing rather than fresh-create. Read first, diff intent, propose changes.
- **Codex desktop not running.** Step 3 should `open_application Codex` and handle the load delay. If app doesn't respond after a screenshot + 10s wait, surface to user (don't loop forever).
- **Wrong chat selected.** Step 3 includes screenshot orient. If the visible chat name doesn't match the expected project, click into the sidebar to find the right one or new-chat.
- **Codex's reply parser fails.** If screenshot-based classification of Codex state is ambiguous (e.g., Thinking + post in same view), default to `mid-slice` and poll again rather than risk an unwanted steer.
- **PRD/acceptance already armed.** If `pgoal status` shows an active goal at skill-creation time, the skill must `--replace` cleanly (per pgoal's `set --replace` semantics) and warn the user about the replaced goal in the chat output.
- **Skill is being invoked recursively** (user types `/codex-pgoal` inside an active `/codex-pgoal` session). Refuse with a clear error; the pgoal nesting rule applies transitively.

## Verification floor

Before declaring done:

1. `pgoal verify --run --record` returns green on all 5 acceptance tests.
2. `pgoal verify --discover` returns no new auto-discoverable verifiers that should be added.
3. The skill loads in a fresh Claude Code session — manual smoke: open a scratch project, type `/codex-pgoal hello`, confirm intake fires without error.
4. The roadmap doc (this file) is committed and Codex can read it via `git pull`.
5. Both LLMs sign the handoff-log row.

## Branching / commits

- Work on the current branch (`claude/debugger-masterpiece-roadmap` or wherever Cole's HEAD is when the skill starts). Do not cut a new branch unless Cole requests one.
- Codex commits the skill file directly (it's at `~/.claude/skills/...`, outside this repo — Codex uses Write tool, no commit needed; the version is whatever's on disk).
- Codex commits the roadmap doc + handoff-log rows to this repo.
- Push to `claude/*` or `codex/*` branches per the pre-authorized list (no force-push to main).
- Do NOT open a PR without Cole's explicit ask — this isn't a release.

## Stop conditions

Per `/codex-task` convention, escalate rather than push through if:

- `pgoal verify --run` fails 3 times in a row with the same root cause.
- The skill spec needs a load-bearing change that wasn't in this roadmap (e.g., turns out we need a separate `scripts/` dir, or the hybrid loop model breaks down in practice).
- Claude and Codex can't reach mutual approval after two adversarial-review passes.
- A new edge case lands that requires Cole's taste call (e.g., naming, scope cut).

## Disagreement resolution

- **Tiebreak:** pause and ask Cole via the chat interface if reachable. If Cole is away (default to "away" if no chat input in last 30 min), use ntfy (`The-CCC-Boys` topic per `reference_ntfy_async_cole_channel.md`).
- **Bar for ntfy:** load-bearing disagreement that blocks both LLMs. Don't ntfy for ordinary preferences — pick defaults, log via `pgoal decision`, continue.
- **Codex-defaults-win cases:** code style, idiomatic Python/shell patterns, file layout inside Codex's write-set.
- **Claude-defaults-win cases:** spec/scope interpretation, when to surface to Cole, when to mark done.

## Time / scope budget

- Standard pgoal duration (240 minutes, 50 iterations, 500 tool calls). Cole said "non stop until done" — that's a directive against premature stop, not a license to spin.
- If at iteration 30 we're nowhere near acceptance, surface the slowdown reason to Cole. Don't burn the full budget silently.
- The skill itself is ~1-3 hours of work (it's a focused single-artifact build), so 50-iteration budget is generous.

## Async channel

- Cole reachable via chat: assume yes unless he says otherwise.
- Cole reachable via ntfy (`The-CCC-Boys`): yes — load-bearing only (directive conflict, locked-decision change, disagreement-can't-resolve). Not for ordinary status pings. Per `feedback_ntfy_directive_conflict.md` + Cole's "rate-limit, he's at work" guardrail.

## Background memory to read before pairing

These are auto-loaded for the Pokemon project but Codex must `git pull` and read directly when pairing on this skill:

- `docs/llm_pairing_rules.md` — committed pairing rules, the substrate.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/feedback_30_70_split_mutual_approval.md` — 30/70 split + operational protocol (silence=unknown, shared-files-need-approval, hard-stop reflex, 2-commits-or-1-hour, "good run" warning).
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/feedback_boundary_hardening_rule.md` — three-test rule.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/reference_codex_send_vs_steer.md` — Enter (queue) vs Ctrl+Enter (steer); growing chip column = queue alarm.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/feedback_poll_codex_progress.md` — 15s active / 120s idle screenshot cadence.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/feedback_telemetry_masquerade.md` — banned process-vocabulary in self-reports.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/reference_ntfy_async_cole_channel.md` — async channel mechanics.
- `C:/Users/lolno/.claude/projects/C--Users-lolno-Downloads-pokemon-gold-hack/memory/feedback_verify_delivery_before_blaming_compaction.md` — diagnostic discipline.
- `/codex-task` skill source: `C:/Users/lolno/Downloads/pokemon gold hack/.claude/skills/codex-task/SKILL.md`.
- `/pgoal` skill source: `C:/Users/lolno/.claude/skills/pgoal/SKILL.md`.

## Specific construction guidance (for Codex's draft pass)

The SKILL.md must NOT just copy-paste from `/codex-task` + `/pgoal`. The synthesis adds these load-bearing things:

1. **Pgoal as durability substrate.** Step 1 of the skill shells `pgoal set ... --replace` and saves a PRD via `pgoal prd save --approved`. This is what makes the skill non-stop — pgoal's Stop hook keeps Claude looping.
2. **Codex-task as pairing substrate.** Steps 2-4 import the access bundle + open + send-task-block pattern verbatim.
3. **Hybrid loop body (Step 5)** is the NEW glue. Neither parent skill has this — `/pgoal` has the Stop-hook loop but no Codex awareness; `/codex-task` has Codex awareness but no Stop-hook durability. Step 5 is where the two meet.
4. **Mutual-approval gates (Step 6)** import from today's debrief, which neither parent skill had.
5. **Composes-not-nests** — the skill must shell `pgoal` CLI rather than invoking `/pgoal` as a sub-skill. Pgoal's `Do not nest /pgoal inside /pgoal` safety rule applies.

## Handoff-log conventions

- File: `audit/codex_pgoal_handoff_log.jsonl` (this repo).
- Phase tag for v1: `codex-pgoal-skill-v1`.
- Events: `ack_start` (LLM about to start a slice), `slice_update` (mid-slice progress), `slice_review` (other LLM reviewed), `mutual_done` (both signed off).
- Required fields per row: `ts` (ISO UTC), `phase`, `event`, `status` (in_progress/complete/blocked), `signed_by` (list), `summary` (one line).
- The acceptance test `mutual_done` looks for `event=mutual_done`, `phase=codex-pgoal-skill-v1`, `status=complete`.

## Iteration plan

- **Iter 1-3:** Codex drafts v0 SKILL.md (frontmatter + Steps 0-7). Claude reviews adversarially. Iterate to mutual approval on structure.
- **Iter 4-6:** Polish content of each step. Codex authors examples, Claude verifies citations resolve and the steps actually compose with `/pgoal` CLI.
- **Iter 7-9:** Smoke test — Claude invokes the skill mentally / dry-runs Step 0 / verifies pgoal CLI calls would work.
- **Iter 10:** Append mutual_done row, run `pgoal verify --run --record`, emit pgoal-complete nonce.

If we're past iter 15 without acceptance green, surface to Cole.

---

**End of roadmap.** Both Claude and Codex work from this file. If something changes during the build, update this file first, then act.
