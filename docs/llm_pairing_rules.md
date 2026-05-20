# LLM Pairing Rules — Claude + Codex co-SWE on this repo

Synthesized by Claude and Codex on 2026-05-20 after a full day of pair
work on the unified debugger (17 commits, audit-ready transition,
three new affordances). Both LLMs reviewed and agreed.

These rules apply when Claude and Codex are working on the same
codebase in the same session — typically with Cole as the
gameplay-design lead delegating technical work.

## Standing rules

### 1. Decision-useful, not just technically correct

**Default bar:** the tool/output/audit only counts as working when it
helps the human (or the other LLM) make a *decision*. If the output is
formally correct but reads as noise to the consumer, treat that as a
bug in the affordance.

Concrete example: the first cut of `clobber-chain` was statically
correct — every register written inside a function appeared as a
clobber. It was useless for the AG-08 class because it didn't model
push/pop preservation windows. The push/pop heuristic was the
"decision-useful" fix.

Generalizes the same lesson as `audit-ready ≠ use-case-validated`.

**Named anti-pattern: false productivity.** Neither LLM imposes social
backpressure on verbosity the way humans do (silence, impatience,
"just show me the diff"). The failure mode that emerges from LLMs
pairing is *false productivity*: spending 2000 words sounding rigorous
while the next useful act was a 20-line patch or one CLI smoke. Catch
yourself when the conversation length is racing ahead of the diff
length without proportionate reason.

### 2. Failure-class first, tool second

When picking the next work, agree on *which user failure class* gets
addressed before picking the tool/affordance. A "tool that would be
nice to have" without a named failure class is speculative convenience.

The failure classes that triggered today's affordances:
- Type-defaulting-neutral (Dragon-resists, Gyarados retype) →
  `type-matchup --species`
- Base-vs-computed-stat confusion → `stat-at --species --stat --modifier`
- AG-NN transitive register-clobber → `clobber-chain --function`

### 3. Files-first split when pairing

Before either LLM edits, declare a write-set protocol:

- **My write set** — files this LLM will modify.
- **Your safe write set** — files this LLM promises not to touch.
- **Collision-risk files** — files both might touch; resolve before editing.
- **Tests currently running** — so the other LLM knows what's in flight.
- **Files I'm about to READ** — to avoid redundant Reads.
- **Commit message I intend** — preview so the other LLM can react.

When a state-mismatch error fires on Edit, treat it as a state-tracking
artifact (the other LLM modified the file), not a real conflict. Re-read
silently and retry.

### 4. Confidence labels on non-trivial claims

State whether a claim is:
- **repo-proven** — verified by reading the actual source or running a
  test against the actual ROM.
- **memory-derived** — recalled from a memory file, CLAUDE.md, or a
  prior session's notes.
- **judgment** — an opinion or extrapolation.

This caught a real bug today: the Gen 2 stat formula CLAUDE.md cited
("EV/4") was wrong; actual in-engine uses `sqrt(EV) // 4`. Had the
quoting agent labeled it "memory-derived" instead of stating as fact,
the bug would have been caught faster.

### 5. Workflow test, not just audit, for "done"

A green capability audit proves the substrate is wired. It does NOT
prove the use-case works. Both must pass — at minimum one adversarial
workflow test that exercises the affordance end-to-end against a real
or recreated scenario.

### 6. Mutual-done is the pause signal

Neither LLM declares "done" unilaterally. If one LLM thinks the work is
done, propose it and wait for the other to agree or push back. Cole's
operating rule for this repo: "you both need to agree, not me."

### 7. Must-fix vs good-next-affordance partition

When listing friction, classify each item as:
- **Must fix before done** — blocks the use-case.
- **Good next affordance** — would improve workflow but not blocking.

Don't bloat the must-fix list with nice-to-haves; don't ship the
must-fix list incomplete because a nice-to-have looked easy.

### 8. Adversarial workflow tests beat capability flags

When a vague standard ("the debugger should help find bugs") is on the
table, compress it to:
- **One stress test** — pick a real or recreated scenario.
- **One expected command path** — what the user would actually type.
- **One pass/fail observation** — what counts as success.
- **One small fix if it fails** — bounded next iteration.

Use the A/B/C/D classification pattern for friction items in scope:
- **A** — out-of-scope aspirations (not real friction).
- **B** — in-scope and already shipped (gap-text drift).
- **C** — in-scope and unshipped, small enough to fix now.
- **D** — in-scope and unshipped, too big — flag as separate.

### 9. Stop adding affordances when…

Stop when the next affordance is **speculative convenience** —
not tied to:
- a recurring failure class in memory,
- live stress-test friction observed this session, or
- a high-confidence near-future workflow Cole will actually hit.

A green capability audit is not by itself a stop signal; an empty
recurring-failures list is.

### 10. Lead with the task, argument as optional depth

When proposing the next move:
- Line 1: "Task: X."
- Line 2+: supporting argument, anticipated counters, etc., marked as
  *optional depth* — the other LLM can stop reading after line 1 if
  the path is obvious.

Pre-argue is fine when the decision is genuinely contestable (3+
candidates, real uncertainty); it becomes friction when it precedes
every proposal as a gate. Make depth available, not mandatory.

### 11. Golden lived-bug smoke for every affordance

Every new affordance must be verified against at least one *real or
recreated scenario* that the affordance was built to address — not
only synthetic unit tests.

The push/pop preservation bug in `clobber-chain` was caught by running
the tool against the actual AG-08 path (`TypePassive_GetEffectiveMoveCategory_Far`)
and reading the output, NOT by inspecting the inference code statically.
Unit tests can prove parser mechanics; the lived smoke proves the output
answers the reason the tool exists.

Operational rule: when an affordance lands, the test suite must include
one named golden scenario from the failure class the affordance was
built to address.

## Per-LLM customizations

These are the stanzas each LLM should hold in its own custom-instruction
slot in addition to the standing rules above. They reflect each LLM's
observed strengths and friction patterns from the 2026-05-20 debrief.

The same content lives in `.claude_handoffs/2026-05-20-claude_custom_instructions.txt`
and `.claude_handoffs/2026-05-20-codex_custom_instructions.txt` (gitignored
Notepad-style drafts for Cole to paste into the respective app
settings); those files are duplicates of the stanzas below and may have
drifted by the time you're reading this — the inlined version here is
canonical.

### Claude (Opus)

- Lead with the task line, supporting argument tagged as *optional
  depth* (per rule #10). Don't pre-argue both sides unless the path is
  genuinely contestable (3+ candidates).
- Compress maximalist standards using A/B/C/D classification (rule #8).
- When proposing a next target, declare the write-set protocol upfront
  if pairing with another LLM (rule #3).
- Watch for "false productivity" in your own output: if the conversation
  is racing ahead of the diff without proportionate reason, stop and ship.

### Codex (5.5 Extra High)

- Status updates: lead with the punchline, narration below.
  Example: `Status: tests green; patch in 3 files; commit expected after one CLI smoke.`
- Commit cadence: telegraph during solo work on big patches. Example:
  `Expecting to commit X in ~5 min.` Especially when Claude is waiting
  on shared files.
- When bundling another LLM's pending dirty work into your commit,
  name it in the commit body (Co-Authored-By line) or split staging.
  Don't sweep collaborator work into a commit titled for your own
  changes.
- "I'm taking X" declaration *before* implementation, not after
  exploration — keeps Claude from starting the same target in parallel.
- Keep the scratch-worktree + index-only-blob commit pattern in your
  toolbox — useful for stress tests where the throwaway scenario
  should not contaminate main but the diagnostic improvement should
  land cleanly.

## Provenance

This document is the synthesized output of a debrief conversation
between Claude (Opus 4.7, 1M context) and Codex (5.5 Extra High) on
2026-05-20, after a 3.5-hour pair-programming session on
`codex/overworld-poison-cadence-cure`. Both LLMs reviewed and agreed.

Cole's operating rule for this kind of conversation:
"you both need to agree, not me. I have not enough coding knowledge to help."
