# Remove `outbox/` And Codex Doc Framing

Date: 2026-04-29

## Decision

Delete `outbox/` from the repo and rename `docs/codex_review_playbook.md`
to `docs/review_playbook.md`. (`docs/codex_context.md` was already renamed
to `docs/project_context.md` earlier the same day.)

The user cancelled their Codex/GPT subscription on 2026-04-29, making Claude
the sole executor. The roles `outbox/` filled — exported handoff prompts and
running notes for a separate AI — no longer have a target audience.

The active surfaces that absorbed outbox/'s former responsibilities:

- per-session handoff prompts → `.claude_handoffs/YYYY-MM-DD-HHMM-<slug>.md`
  (gitignored, see `CLAUDE.md`);
- durable judgment calls → `decisions/`;
- per-session diary observations → `journal/`;
- evidence and reproducible artifacts → `audit/`.

Doc updates: every active reference in `docs/`, `docs/agent_navigation/`, and
`tools/audit/check_docs_navigation.py` was rewritten to point at the new
surfaces. Historical roadmap evidence references to specific outbox files
were stripped to keep the prose self-contained.

Audit fix: `clean_ref()` in `tools/audit/check_docs_navigation.py` strips
leading dots from path tokens, so `OPTIONAL_LOCAL_PATH_PREFIXES` now contains
both dotted and undotted forms (`.claude_handoffs` and `claude_handoffs`,
`.local` and `local`). The pre-existing `.local` entry was effectively dead.

## Rejected

- Keeping `outbox/` as a generic scratch dir with no Codex framing. The
  decisions log explicitly named outbox as "handoffs and exported prompts";
  repurposing it would just create another underowned pile.
- Migrating outbox contents into `decisions/` or `journal/` wholesale. Most
  outbox files were stale handoffs (work done) or Codex prompts; the
  speculative drift diaries were unused for 3+ days. Git history preserves
  anything worth recovering.
- Leaving the playbook named `codex_review_playbook.md`. The body of the
  playbook is generic review guidance, not Codex orchestration — the name
  was misleading.

## What Would Change My Mind

If Codex (or another second AI) re-enters the workflow, recreate a tracked
exported-prompt directory then. Don't resurrect `outbox/` as a graveyard for
historical Codex prompts — those live in git history.

If `decisions/` and `journal/` start drifting toward the same overload that
killed `outbox/` (mixed content, no clear ownership, accumulating without
review), revisit the doc-role split.
