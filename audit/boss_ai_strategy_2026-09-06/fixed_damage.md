# Fixed-damage KO follow-up

This implements the first bounded increment of `next_stage_plan.md`, not its full
shared outgoing/incoming damage estimator. The previously approved consistency
pass remains in the working tree, preserved in `.local/tmp/strategy_v1_baseline`
for before/after comparisons. Its historical evidence files are unchanged.

## Changes

- `fixed_damage_ko.asm`: exact on-hit lethality for static damage, attacker-level
  damage and Super Fang using public current HP, typing, Substitute and Foresight.
  Immunity comes from the actual chart without Dragon's Majesty, which combat
  excludes for these effects. No private player fields or RNG are consulted.
- `boss_policy_move.asm`: current-move and available-moveset KO consumers use this
  result for supported effects. Lookahead now shares the same KO predicate rather
  than duplicating the old quarter/half-HP thresholds. Ordinary nonlethal pressure
  rewards remain unchanged.
- `main.asm`: floating 151-byte helper section. Removing the duplicated lookahead
  thresholds saves a net 22 bytes in bank 0e, including the added farcall wrapper.
- `cases.py`: 78 additional ROM fixtures cover exact boundaries, immunity,
  Foresight, Substitute, HP above 255, fainted targets, move availability and the
  lookahead consumer, with an ordinary-move control. Synthetic move assignments
  isolate arithmetic and policy branches; they do not represent authored rosters.
- `check_boss_ai_no_cheat.py`: scan the new helper as part of the audit floor.
- API/design documentation and generated navigation/index reflect the new helper
  and the explicitly incomplete shared-estimator roadmap.

## Validation

Gold, Silver, debug Gold and trace Gold built successfully. Full normal/trace
fixture evidence is in `pokegold_fixed_damage_fixtures.json` and
`pokegold_trace_fixed_damage_fixtures.json`; the 12 audit results are in
`fixed_damage_checks.json`. Preference evidence remains 45/45 strict labels;
9 non-strict labels are skipped, not counted as passes.

Independent Astra combat differential checks used ConstantDamage followed by
ResetTypeMatchup on nine synthesized positions: static damage under resistance
and weakness, level damage through Ghost/Foresight, Night Shade's Steel immunity,
Super Fang at 1/2/256 HP, and a Substitute position. The helper matched lethal
amounts with Substitute excluded, and preserved BC=$1234, DE=$5678, HL=$9abc.

Lookahead's synthetic Pidgey/Dragon Rage case changes from -4/-4 at 40/41 target
HP in the approved baseline to -4/-2 now. The Tackle control remains -4/-4. These
are signed score deltas, where negative favors the move. The initial Tackle test
expectation mistakenly used a non-STAB control's value; it was corrected after
both baseline and current ROMs independently showed -4.

Fresh maps: Enemy Trainers normal 0e:4000–7f46 (185 bytes free), trace
0e:4000–7fe3 (28 bytes free). WRAM remains 112/140 normal and 140/140 trace.
Save format 3 and all 1450 saved-field offsets remain unchanged. No speedup,
win-rate improvement, full battle simulation or natural-roster acceptance result
is claimed from this increment.

## Retention and deferral inventory

- F1: Retain every approved consistency-pass change and R1–R8 in
  `implementation.md`, except for the KO/lookahead refinement described here.
  They solve independent availability, scoring, scouting, setup, speed, threat
  memory and switch problems; the regression corpus still covers them.
- F2: Retain ordinary outgoing KO bands and incoming-priority heuristics for this
  bounded increment. They have known level/HP/rounding deficiencies and are
  explicitly unfinished work under roadmap stage 1, not approved as exact facts.
- F3: Retain nonlethal pressure ranking, dominance, and the separate strong-matchup
  status backstop. These can still overvalue fixed damage's type multiplier.
  This increment fixes KO premises; it does not make all fixed-damage valuation
  exact. Their replacement needs shared damage/action valuation evidence.
- F4: Retain hit reliability, Psychic negation, survival effects and action order
  outside this helper. Its contract is lethal damage on a successful unblocked
  hit, never a guaranteed finish. Protect/Endure flags do not establish what the
  player will do on the next turn. Unknown held items remain private.
- F5: Preserve authored rosters, tiers, variety, persistent memory/save layout and
  the battle engine. No balance changes are needed to correct these KO premises.
- F6: Defer joint move/switch valuation, real successor search, contextual outcome
  learning and natural-roster ablations in the documented order. None is claimed
  implemented, and helper regression success does not establish their benefits.

Final approval and immutable reviewed-state identifiers are recorded separately
in `fixed_damage_review.md` and `fixed_damage_manifest.json`.
