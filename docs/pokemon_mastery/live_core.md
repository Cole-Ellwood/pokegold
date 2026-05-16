# Pokemon Mastery Live Core

Hard cap: 80 lines. This is the only default pre-freeze move-choice entrypoint.

## Fresh Replay Routing

Before answering a fresh unseen replay turn, load only:

1. This file.
2. The current replay prompt and public log state.
3. Any tiny `heuristic_core/*.md` cards that are decision-relevant.
4. Compact `canon/*.md` or `romhack_deltas/*.md` lookups only when public
   mechanics, matchup, or route facts are decision-relevant.

After answers are frozen, load scoring rules, old policy cards, reviews,
ledger rows, cookbook entries, or source notes for scoring and postmortem only.

Do not load pre-freeze: `cookbook.md`, `source_to_policy_ledger.md`,
`paused_turn_atlas.md`, `worked_examples/live_turn_drills.md`, old long
`policy_cards/*.md`, scored `workspace/quick_tests/`, reviews, or raw
`workspace/external_research_returns/`.

## Pre-Move Solve

1. Name current owner: who owns the board right now, and by what route?
2. Update public package: what revealed move, entry, or pattern changed a role?
3. Mark critical counters: sleep/wake, passed boosts/speed, cash-out/self-KO, immediate lethal/miss/crit risk.
4. Name next-board owner and, after handoff, the counter-owner it invites.
5. Price one-cycle converters: revealed setup, coverage, or cash-out before
   making the owner handoff automatic.
6. Rank converter before script: damage, coverage, item removal, setup, phaze,
   cash-out, handoff, or status only if it changes the named route.
7. Rank branch punish: if a branch is named, promote the action that beats it.
8. Spend or save piece: preserve a route job; spend only for a named converter.
9. Deny reset loops: Spikes, Spin, Rest, Recover, phaze, Sleep Talk, and
   Baton Pass matter only if the loop converts or is denied in time. In Rest
   races, compare boost-now/attack-next against attack-now/reset-next.
10. Re-score after reveal: Growth, Substitute, Baton Pass, Curse, RestTalk,
   lure coverage, Thief, Roar, or Whirlwind can reclassify the whole package.
11. State public tiers: `revealed`, `strong prior`, or `possible only`.

## Guardrails

- No Team Preview: do not use hidden teams, moves, items, PP, or future turns.
- Possible-only information can shape a branch, not anchor the main line.
- Side-known information must be labeled when spectator-public prompts omit it.
- Vanilla GSC knowledge is source material; romhack advice needs local status.
- Do not claim mastery or progress from document cleanup.

## Answer Shape

- Route transaction: their package -> our absorber/converter -> their next
  owner -> our punish.
- Top move or switch after active/next/counter-owner comparison.
- Two ranked alternatives and why each loses or stays acceptable.
- Named branch punish: receiver/absorber/reset loop and the action into it.
- Route piece decision: preserve, spend, sack, or hand off.
- Public-info tier and fallback for any unrevealed assumption.

## Tiny-Card Selector

There is no fixed minimum or maximum card count. Use the smallest set that
answers the live uncertainty; load more when separate route questions matter,
and load none when this core is enough.

- `name_current_owner.md`: unclear current converter or defensive owner.
- `name_next_board_owner.md`: active may leave or a handoff is likely.
- `converter_before_script.md`: safe status, Spikes, Spin, or switch tempts.
- `public_info_tiers.md`: lure, item, coverage, or hidden teammate ambiguity.
- `role_package_ledger.md`: reveal, entry, or switch pattern changes a job;
  pair with spend/reset cards for cash-out, support jobs, or Rest loops.
- `spend_or_save_piece.md`: low support, Explosion, sack, or preservation.
- `reset_loop_denial.md`: Spikes/Spin/Rest/Recover/phaze/pass loop.
- `rest_curse_tempo_window.md`: setup/damage/phaze timing in Rest races.
- `rescore_after_reveal.md`: package move or set detail just became public.
- `branch_punish_ranking.md`: the branch is named but not yet punished.

## Post-Score Route

Use `heuristic_core/migration_map.md` to find the compressed old lessons. Use
`policy_cards/` as expanded reference, not live default context. Keep measured
progress tied to fresh top-match, acceptable-match, route-conversion, and
branch-punish movement, not note volume.
