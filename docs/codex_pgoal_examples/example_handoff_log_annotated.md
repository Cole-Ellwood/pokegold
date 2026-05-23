# `example_handoff_log.jsonl` — annotated

Six real rows from the `codex-pgoal-skill-v1` build (one slice's full
cycle + the closeout). Validates CLEAN under
`python tools/codex_pgoal_handoff_validate.py docs/codex_pgoal_examples/example_handoff_log.jsonl`.

## Row 1 — `ack_start` (Codex)

```json
{"event":"ack_start","status":"in_progress","signed_by":["Codex"], ...}
```

**What this row proves:** Codex has declared what they are about to do
before touching any shared file.

**Required-field shape:** `ts`, `phase`, `event`, `status`, `signed_by`,
`summary`. Plus the load-bearing optional fields for an `ack_start`:
`write_set`, `safe_set_for_claude`, `shared_append_only`,
`collision_risk`, `files_read`, `tests_running`,
`intended_commit_message`.

**Why `collision_risk` matters:** the handoff log itself is collision
risk because both LLMs append to it. Naming it explicitly forces both
sides to acknowledge the concurrent-write surface — which is what makes
the `ts`-sort rule load-bearing later.

**Why `files_read` matters for review:** Claude's review (row 2) checks
this list against the roadmap's "background memory to read" section. If
the list is missing a load-bearing file, that's a `slice_review` flag
even before the code lands.

## Row 2 — `slice_review` (Claude, non-blocking flag)

```json
{"event":"slice_review","status":"approved","signed_by":["Claude"], ...}
```

**What this row proves:** the partner has read the ack_start, accepted
the proposed scope, and may have raised non-blocking flags.

**The non-blocking flag pattern:** the `summary` field calls out one
omitted file from `files_read` (`reference_ntfy_async_cole_channel.md`)
but explicitly says it's not blocking for *this* slice — it's flagged
for later slices that touch the escalation rules. This is the "good
review" shape: approve the in-scope substance, flag the latent risk for
the future slice, don't block on a non-load-bearing detail.

**The `reviews` field** points at the ack_start by timestamp (the
`Codex_ack_start_2026-05-22T23:09:08Z` reference). That field is the
audit-trail back-pointer; consumers walk the chain via `reviews`.

**Why `confidence_label: repo-proven`:** the reviewer cited
`audit/codex_pgoal_handoff_log.jsonl:1` in `evidence`. The label
without a `path:line` citation should be `judgment`, not
`repo-proven`.

## Row 3 — `slice_update` (Codex)

```json
{"event":"slice_update","status":"complete","signed_by":["Codex"], ...}
```

**What this row proves:** the slice author has finished the work and
listed where to look. `evidence` cites 5 SKILL.md line numbers; the
reviewer can jump straight to each.

**The `validation` field** is what Codex ran themselves before declaring
complete. In this row: `python C:/Users/lolno/.codex/skills/.system/skill-creator/scripts/quick_validate.py ... -> Skill is valid!`.
That's the author saying "I checked my own work" — Claude's review will
either confirm or reject, but the author isn't asking Claude to do the
basic compile check.

**`confidence_label: repo-proven`** with the SKILL.md line citations
makes this provable. A future reviewer (Claude six sessions later) can
re-validate from the cited evidence.

## Row 4 — `slice_review` (Claude, substantive-improvement note)

```json
{"event":"slice_review","status":"approved","signed_by":["Claude"], ...}
```

**What this row proves:** the slice substance was approved AND the
reviewer flagged something the original ack_start didn't cover.

**The "substantive improvement" pattern:** Codex added a not-a-git-repo
edge case at `SKILL.md:51` that wasn't in the original ack_start scope.
Claude's review explicitly says "Slice 1 substantive improvement over
roadmap: line 51 not-a-git-repo edge case is a real add; I will mirror
back into `docs/codex_pgoal_skill_codex_task.md` post-build." This is
the loop's positive feedback path: when the implementer over-delivers,
the reviewer captures the improvement back into the roadmap so future
loops inherit it.

**Why `evidence` cites two files:** the reviewer is cross-checking the
proposed change (`SKILL.md:1-53`) against the parent skill pattern it
mimics (`/pgoal SKILL.md:4-5`). Two paths = `repo-proven` lives up to
its name.

## Row 5 — `mutual_done` (Claude + Codex)

```json
{"event":"mutual_done","status":"complete","signed_by":["Claude","Codex"], ...}
```

**What this row proves:** both LLMs have explicitly signed off that the
phase is complete. The `signed_by: ["Claude","Codex"]` shape is the
gate the v1 acceptance test (`test_mutual_done_row_present`) looks for.

**Why this row matters more than any single review:** completion is the
one event neither LLM may sign alone. The `silence is unknown, not
approval` rule (SKILL.md Step 6 line 348) means Claude can't infer
Codex's mutual_done from a chat absence. Codex confirmed explicitly in
the desktop chat ("Confirmed. Codex signs `mutual_done` for
`codex-pgoal-skill-v1`.") — only *then* did Claude file this dual-
signed row.

**`summary` is the elevator pitch.** A future reviewer skimming the
log for "is this build done?" reads only this `summary` to decide.
Make it complete: what shipped, where it lives, what verifier passed.

## Row 6 — `verify_pass` (Claude)

```json
{"event":"verify_pass","status":"complete","signed_by":["Claude"], ...}
```

**What this row proves:** the official pgoal verifier accepted the
state. This isn't required by the canonical event vocabulary — it's a
roadmap-defined extension event the helper accepts.

**The detour story in `summary`:** the verifier did NOT pass on the
first try. The full summary documents the path: "After auto_pytest
issue (4 unrelated boss_ai test failures from prior paused P14 work),
re-armed pgoal with --no-auto-discover and scoped pytest verifier.
Decision recorded that auto_pytest is out-of-scope." Future reviewers
get the "we hit X, decided Y, resolved Z" arc, not a sanitized
"verifier passed" lie.

## How to use these rows

1. **Start with row 1's ack_start shape.** When you write your first
   `ack_start` in a new `/codex-pgoal` run, copy this row's field set
   and adjust values. Don't omit `collision_risk` because nothing looks
   risky — anything you append to the handoff log IS risky.
2. **Use row 2 as a review template.** Approve the in-scope substance.
   Flag latent risks for the future slice with explicit "not blocking
   this slice" framing. Cite at least one `path:line` for
   `repo-proven`.
3. **Match row 3's `validation` pattern.** Don't ask the reviewer to do
   your basic checks. Run them yourself; cite what you ran.
4. **Notice the row-2-vs-row-4 distinction.** Row 2 was the ack_start
   approval (scope only). Row 4 was the slice_update approval
   (substance). Two reviews per slice, not one.
5. **Don't sign row 5 (`mutual_done`) without partner explicit chat
   confirmation.** Silent-consent is the failure mode this event
   exists to prevent.
6. **Document the verifier detour in row 6 if there was one.** Honest
   completion stories beat clean lies.
