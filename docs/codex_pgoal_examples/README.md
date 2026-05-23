# `/codex-pgoal` Examples

Annotated artifacts derived from the actual `codex-pgoal-skill-v1` and
`codex-pgoal-skill-v1-hardening` builds. Real coordination data, not
fictional templates. Use these as the "show, don't just tell" reference
when writing a new `/codex-pgoal` roadmap or coordinating with Codex.

## Files

| File | What it shows |
|---|---|
| [`example_roadmap.md`](example_roadmap.md) | A distilled, annotated `<slug>_codex_task.md` roadmap. Each section has an inline note explaining its load-bearing purpose. |
| [`example_handoff_log.jsonl`](example_handoff_log.jsonl) | A clean six-row excerpt showing the canonical `ack_start → slice_review → slice_update → slice_review → mutual_done → verify_pass` cycle. |
| [`example_handoff_log_annotated.md`](example_handoff_log_annotated.md) | Companion that walks each row by line number, explaining what it proves and what triggered it. |

## When to read these

- **Before writing a new roadmap.** See what fields actually carry weight versus what's ceremonial.
- **When unsure what a `slice_review` should contain.** The annotated log shows real decision-useful summaries, real `repo-proven` evidence shapes, and a real non-blocking-flag review (row 2) that didn't block but did improve a later slice.
- **When recovering from a Codex crash.** `example_handoff_log.jsonl` is exactly the row sequence you reconstruct from after re-opening Codex (per `SKILL.md` Step 3 recovery procedure).
- **After validator complaints.** Compare against `example_handoff_log.jsonl` to see what a CLEAN log looks like at the schema level (`python tools/codex_pgoal_handoff_validate.py docs/codex_pgoal_examples/example_handoff_log.jsonl` returns 0 errors).

## What's *not* here

- A full Step-0-through-Step-7 SKILL.md clone. The skill itself is the canonical reference at `~/.claude/skills/codex-pgoal/SKILL.md` — don't duplicate it here, just point at it.
- Bug-free perfection. The real handoff log this is derived from has 4 documented `ts`-order warnings from concurrent appends, plus a real-world recovery from `auto_pytest` blocker. Those are the kind of friction this skill is built to handle, not hide.

## Cross-references

- Canonical skill: `~/.claude/skills/codex-pgoal/SKILL.md`
- Roadmap that built the skill: `docs/codex_pgoal_skill_codex_task.md`
- Handoff log this excerpt is from: `audit/codex_pgoal_handoff_log.jsonl`
- Helper script: `tools/codex_pgoal_handoff_append.py`
- Validator: `tools/codex_pgoal_handoff_validate.py`
