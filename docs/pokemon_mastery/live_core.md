# Pokemon Mastery Live Core

Hard cap: 100 lines. This is the only default pre-freeze move-choice entrypoint.

## Fresh Replay Routing

Before answering a fresh unseen replay turn, load only:

1. This file.
2. The current replay prompt and public log state.
3. Any `heuristic_core/*.md` cards forced by the Load-Required Triggers
   section below; otherwise the smallest discretionary set that answers
   the live uncertainty.

After answers are frozen, load scoring rules, old policy cards, reviews,
ledger rows, cookbook entries, or source notes for scoring and postmortem only.

Do not load pre-freeze: `cookbook.md`, `source_to_policy_ledger.md`,
`paused_turn_atlas.md`, `worked_examples/live_turn_drills.md`, old long
`policy_cards/*.md`, scored quick tests, reviews, or external research returns.

## Load-Required Triggers

For these boards, the listed card MUST be in pre-freeze context. The
selector below is mandatory for these triggers, not discretionary:

- Spikes (either side), Rest in any package, Sleep Talk, any sleeping
  target, or any phaze move in any revealed package
  → `heuristic_core/reset_loop_denial.md`
- Unique-role piece (spinner, phazer, RestTalker, breaker, last typed
  absorber) at <80% HP, statused, or facing future Spikes-entry tax
  → `heuristic_core/spend_or_save_piece.md`
- Tempted by Toxic / Spikes / Rapid Spin / safe-switch when a converter
  (damage, coverage, phaze-on-sleeping-target, cash-out, lower-cost
  handoff) is available
  → `heuristic_core/converter_before_script.md`

Pre-freeze audit: for each top-three candidate, name the branch it
beats AND the branch it loses to. A dead move into a named branch
(Toxic into a sleeping target, status into a Steel that blanks it,
Electric into a Ground, generic phaze when direct chip on the named
receiver is available) demotes itself.

Record the actual loaded-card set in the packet per turn so H1
(card-not-loaded) and H2 (card-loaded-but-ignored) misses are
distinguishable in post-score diagnosis.

## Pre-Move Solve

1. Name current owner: who owns the board right now, and by what route?
2. Name next-board owner: if the active target leaves, who owns that board?
3. Rank converter before script: damage, coverage, item removal, setup, phaze,
   cash-out, handoff, or status only if it changes the named route.
4. Rank branch punish: if a branch is named, promote the action that beats it.
5. Spend or save piece: preserve a route job; spend only for a named converter.
6. Deny reset loops: Spikes, Spin, Rest, Recover, phaze, Sleep Talk, and
   Baton Pass matter only if the loop converts or is denied in time.
7. Re-score after reveal: Growth, Substitute, Baton Pass, Curse, RestTalk,
   lure coverage, Thief, Roar, or Whirlwind can reclassify the whole package.
8. State public tiers: `revealed`, `strong prior`, or `possible only`.

## Guardrails

- No Team Preview: do not use hidden teams, moves, items, PP, or future turns.
- Possible-only information can shape a branch, not anchor the main line.
- Side-known information must be labeled when spectator-public prompts omit it.
- Vanilla GSC knowledge is source material; romhack advice needs local status.
- Do not claim mastery or progress from document cleanup.

## Answer Shape

- Top move or switch, with the route it converts.
- Two ranked alternatives and why each loses or stays acceptable.
- Named branch punish: receiver/absorber/reset loop and the action into it.
- Route piece decision: preserve, spend, sack, or hand off.
- Public-info tier and fallback for any unrevealed assumption.

## One-Card Selector

- `name_current_owner.md`: unclear current converter or defensive owner.
- `name_next_board_owner.md`: active may leave or a handoff is likely.
- `converter_before_script.md`: safe status, Spikes, Spin, or switch tempts.
- `public_info_tiers.md`: lure, item, coverage, or hidden teammate ambiguity.
- `spend_or_save_piece.md`: low support, Explosion, sack, or preservation.
- `reset_loop_denial.md`: Spikes/Spin/Rest/Recover/phaze/pass loop.
- `rescore_after_reveal.md`: package move or set detail just became public.
- `branch_punish_ranking.md`: the branch is named but not yet punished.

## Post-Score Route

Use `heuristic_core/migration_map.md` to find the compressed old lessons. Use
`policy_cards/` as expanded reference, not live default context. Keep measured
progress tied to fresh top-match, acceptable-match, route-conversion, and
branch-punish movement, not note volume.
