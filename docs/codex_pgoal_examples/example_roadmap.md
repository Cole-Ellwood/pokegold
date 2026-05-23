# Example `<slug>_codex_task.md` — annotated

Distilled from `docs/codex_pgoal_skill_codex_task.md` (the roadmap that
built `/codex-pgoal` itself). Each section has an inline annotation
explaining its load-bearing purpose. Use as a template for new
`/codex-pgoal` roadmaps.

The annotations are HTML comments (`<!-- ... -->`) so they don't render
in the published doc but DO show up in source for copy-paste templates.
Strip them when you write your own.

---

# Codex Task — Build `<thing>`

<!-- The H1 should name the deliverable clearly. The pair both read
this line every time they re-open the doc; don't bury intent in
sub-headers. -->

**Status:** v0 spec, Cole-approved <DATE> via /pgoal AskUserQuestion intake.
**Pairing:** Claude (prompter, ~30%) + Codex (implementer, ~70%) under mutual approval.
**Artifact:** `<absolute or repo-rooted artifact path>`.
**Roadmap home:** this file — canonical contract, both LLMs read it, update it before drift.

<!-- The 4-line status block is metadata the loop reads on every
re-open. Keep it terse. The "update it before drift" line is the
forcing function for the if-something-changes-mid-session-update-
roadmap-first rule. -->

## Goal

<!-- One paragraph. What's the bounded shipped outcome? Quote the
user's original ask if they gave one. The goal is the OBJECTIVE for
pgoal arming — paste this string into `pgoal set --objective ...`. -->

Build a new `<thing>` that does `<observable>` under `<constraints>`.

Cole's exact ask: *"<user's words verbatim>"* — so the synthesis itself
is paired work, not a Claude-solo write.

## Locked decisions (from AskUserQuestion intake)

<!-- Step 0's output. Cole answers these BEFORE the loop arms; the
table is your forcing function to surface what was decided so neither
LLM re-asks mid-loop. -->

| Question | Answer | Implication |
|---|---|---|
| Skill/feature name | `<name>` | Affects directory, command, naming |
| Location / scope | `<user-level vs project-level>` | Affects discoverability + portability |
| Codex's role | `<implementer | reviewer | both>` | Affects 30/70 split direction |
| Loop model | `<hybrid | drive | poll-only>` | Affects cadence rules |
| ... add task-specific questions ... | | |

## In scope (v1 MVP)

<!-- A numbered list of capabilities the v1 must have. Each item
should be one observable thing, not a category. The acceptance contract
later derives from this list. -->

1. `<deliverable file path>` with `<observable properties>`.
2. `<step or capability>` that handles `<edge case>`.
3. ...

## Out of scope (deferred)

<!-- The list of things you WILL NOT do in v1. This prevents scope
creep mid-loop. Add to it explicitly via `pgoal decision` if the user
asks for something later. -->

- `<deferred capability>`
- ...

## Acceptance criteria

<!-- The 3-7 mechanical tests that gate `pgoal verify --run --record`.
Each must be a command pgoal can run with an `expected_exit_code` (and
optionally `expected_output_regex`). Mirror these into
`.local/<slug>_acceptance.json` and pipe to `pgoal acceptance init`. -->

Mirrored from `acceptance.lock.json`. All must pass:

1. **`<test_id_1>`** — `<one-sentence what-it-proves>`.
2. **`<test_id_2>`** — `<...>`.
3. ...

## Approach preference

<!-- The procedural rules both LLMs follow during the loop. Copy this
section verbatim from the previous roadmap unless the user changed the
debrief rules. -->

Use today's debrief operational protocol verbatim:

- **Files-first split.** Declare write-set before edits land.
- **Confidence labels.** `repo-proven` (with at least one `path:line` citation), `memory-derived`, or `judgment`. Stated explicitly on every load-bearing claim.
- **Adversarial review.** Default review stance: assume the draft has a bug, prove it doesn't.
- **2-commits-or-1-hour cadence.** Surface direction at that cadence regardless of momentum.

## Edge cases

<!-- The known failure classes you want both LLMs to think about
upfront. List specific scenarios + the right response. -->

- **`<scenario>`.** `<response>`.
- ...

## Verification floor

<!-- Commands the loop runs before declaring done. The pgoal verifier
runs at least one of these; the others may be manual. -->

Before declaring done:

1. `pgoal verify --run --record` returns green on all acceptance tests.
2. `<additional manual check>`.
3. Both LLMs sign the handoff-log `mutual_done` row.

## Branching / commits

<!-- The git policy. Be explicit so Codex doesn't push to main by
accident. -->

- Work on `<branch name or rule>`.
- Codex commits `<which files>`; Claude commits `<which files>`.
- Push to `claude/*` or `codex/*` branches per the pre-authorized list (no force-push to main).
- Do NOT open a PR without Cole's explicit ask.

## Stop conditions

<!-- When to pause rather than push through. Each condition should be
specific enough that either LLM can recognize it. -->

Escalate rather than push through if:

- `pgoal verify --run` fails 3 times in a row with the same root cause.
- The spec needs a load-bearing change that wasn't in this roadmap.
- Claude and Codex can't reach mutual approval after two adversarial-review passes.

## Disagreement resolution

<!-- The tiebreak rule + escalation channel. Without this, the loop
can deadlock. -->

- **Tiebreak:** pause and ask Cole via chat if reachable.
- **If Cole away:** use ntfy topic `The-CCC-Boys` per `reference_ntfy_async_cole_channel.md`.
- **Bar for ntfy:** load-bearing disagreement that blocks both LLMs.
- **Codex-defaults-win cases:** code style, idiomatic patterns, file layout inside Codex's write-set.
- **Claude-defaults-win cases:** spec interpretation, when to surface, when to mark done.

## Time / scope budget

<!-- Honest budget so the loop doesn't burn forever silently. -->

- Standard pgoal duration (240 minutes, 50 iterations, 500 tool calls).
- If at iteration `<N>` we're nowhere near acceptance, surface the slowdown reason to Cole.

## Async channel

<!-- When can Cole be reached? -->

- Cole reachable via chat: assume yes unless he says otherwise.
- Cole reachable via ntfy (`The-CCC-Boys`): yes — load-bearing only.

## Pgoal arming plan

<!-- The exact CLI calls the loop will make. Putting them in the
roadmap means future re-arms don't have to re-derive them. -->

```bash
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" set \
  --objective "<objective from Goal section>" \
  --phase implementation \
  --criteria "..." \
  --constraints "..." \
  --verify "- fast: python -m pytest tools/test_<slug>_acceptance.py" \
  --no-auto-discover \
  --assume-defaults --replace --clarified
```

<!-- --no-auto-discover is on by default because unrelated repo tests
will block the verifier gate (the lesson from the v1 build's
auto_pytest detour). If the goal truly needs broad pytest, say so
explicitly in this roadmap and remove the flag. -->

## Provenance policy

<!-- Which proof artifacts get committed vs kept local. The handoff log
and acceptance tests should normally be committed; document exceptions. -->

- `docs/<slug>_codex_task.md` (this file): committed.
- `audit/<slug>_handoff_log.jsonl`: committed at completion.
- `tools/test_<slug>_acceptance.py`: committed.
- `<other artifacts>`: `<commit | local-only>`, reason: `<...>`.

## Background memory to read before pairing

<!-- Both LLMs must read these. Codex must `git pull` and read directly
when pairing on this skill. -->

- `docs/llm_pairing_rules.md` — committed pairing rules.
- `<...memory file path...>` — `<one-line why>`.

## Codex task block

<!-- The literal message Claude pastes into the Codex desktop chat. -->

```
---CODEX-TASK---
**Goal:** <one-sentence objective>

**Roadmap (canonical contract — read first):**
`@docs/<slug>_codex_task.md`

**Pairing protocol:** today's debrief rules verbatim. Files-first split. Confidence labels. Mutual approval before mutual_done. Silence=unknown not approval. Hard-stop reflex on collision risk. 2-commits-or-1-hour cadence.

**Write-set split:**
- You (Codex, primary author): <path>
- Me (Claude, prompter/reviewer): <path>
- Both: append to handoff log

**First-slice proposal:** <slice 1 scope>.

Ready when you are.
---END-TASK---
```

---

**End of roadmap.** Both Claude and Codex work from this file. If
something changes during the build, update this file first, then act.
