# Positive Selection Correction Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not fresh replay-transfer
evidence and does not count as proof of broad improvement.

Parent artifact:
`quick_tests/positive_selection_transfer_001_smogtours-gen2ou-760016_2026-05-14.md`

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-760016`

Selected action:
Convert the four main positive-selection misses from the parent replay into
compact decision boundaries, then answer them with ranked candidates and
hidden-information tiers.

## Docs Checked

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`

No new web search was needed for this correction probe because the
decision-relevant source is the parent fresh replay above. Use fresh web search
again before selecting the next unseen replay or extracting a new source rule.

## Score Summary

Scenarios: 4.

Correct top action: 4 / 4.

Ranked top-three present: 4 / 4.

Positive-selection: 4 / 4.

Route-converting move chosen: 4 / 4.

Branch-punish chosen: 4 / 4.

Hidden-info errors: 0.

Severe blunders: 0.

Measurement status: regression only. The next countable test must be a fresh
unseen replay segment with the same tags.

## Scenario 1 - Coverage Over Visible STAB

Public state:
Zapdos is active against Cloyster. Opponent has a revealed Steelix in back that
has been used as the Electric absorber. Our Zapdos has Thunder and Hidden
Power Water revealed to us as own-side knowledge. Cloyster is valuable but is
not the opponent's only remaining route piece.

Frozen answer:
Top action: Hidden Power Water, confidence medium-high.

Route reason: Thunder only beats the active target; Hidden Power Water punishes
the named Steelix branch while still keeping Zapdos in control if Cloyster
stays.

Ranked candidates:

1. Hidden Power Water into Steelix.
2. Thunder if the Cloyster stay-in is now the largest branch.
3. Switch or double only if Zapdos must be preserved from a revealed punish.

Worst branch:
Cloyster stays and uses Spikes or Explosion while Hidden Power gets lower
value than Thunder. This is acceptable only if the Steelix branch is priced as
the opponent's best route.

Score:
Correct. This fixes the parent turn 5 pattern: name the absorber, then choose
the move that affects that absorber instead of defaulting to visible STAB.

## Scenario 2 - Setup Over Safe Damage On A Forced Switch

Public state:
Vaporeon is at full HP and already at +1 Special Attack against Steelix.
Steelix is in range of +1 Surf and is slower. The opponent has a revealed
Cloyster and sleeping Vaporeon as Water answers. Vaporeon has Growth, Surf,
and Protect.

Frozen answer:
Top action: Growth, confidence medium.

Route reason: Steelix cannot safely stay into faster Surf, so Growth punishes
the Water-answer switch and makes the next board better than simply damaging
the current target.

Ranked candidates:

1. Growth on the forced switch.
2. Surf if Steelix staying is the largest branch or the switch is not forced.
3. Protect only if Explosion or a timing scout is the material branch.

Worst branch:
Steelix stays with a move that invalidates the boost before Surf converts.
Because Surf threatens to KO first in this constructed state, that branch is
lower than the forced-switch route.

Score:
Correct. This fixes the parent turn 8 pattern: if the current target is forced
out, ask which move improves the expected receiving board, not which move is
safest into the active Pokemon.

## Scenario 3 - Protect As Converter Preservation

Public state:
Vaporeon is full HP and boosted against Cloyster at low HP. Cloyster has
revealed Spikes and can plausibly use Explosion. Vaporeon has Protect and Surf.
Keeping boosted Vaporeon healthy is the current win route.

Frozen answer:
Top action: Protect, confidence medium-high.

Route reason: Protect is not passive here; it preserves the boosted converter
and makes the Explosion branch spend itself into no progress.

Ranked candidates:

1. Protect to scout and punish Explosion.
2. Surf if Cloyster cannot meaningfully explode or support.
3. Switch Gengar only if Protect is unavailable or the scout turn has no route
   value.

Worst branch:
Cloyster uses Spikes or another support move and Protect gives it a free turn.
That is still less costly than losing the boosted Vaporeon to Explosion when
Vaporeon is the current converter.

Score:
Correct. This fixes the parent turn 10 pattern: do not call every scouting move
passive; ask whether the blocked turn preserves the actual converter.

## Scenario 4 - Explosion Into Sleeping Target With Unknown Last

Public state:
Gengar faces a sleeping Vaporeon. The opponent has one unrevealed last Pokemon.
Gengar has Explosion, Ice Punch, and Dynamic Punch. Sleep Clause is active, but
there is no public proof that the last Pokemon cannot absorb or punish
Explosion.

Frozen answer:
Top action: Ice Punch as the midground pressure move, confidence medium-low.

Route reason: Explosion only converts if the sleeping Vaporeon is the right
target and no hidden absorber changes the trade. With an unrevealed last slot,
use pressure that still covers common Gengar-answer branches instead of
anchoring the line on no absorber.

Ranked candidates:

1. Ice Punch as midground pressure into the switch while keeping Explosion.
2. Dynamic Punch as a high-risk Tyranitar/Rock read, with Ice Punch fallback if
   the read is only possible.
3. Explosion only if team context or prior turns make "no useful absorber" a
   strong prior and the fallback is named.

Worst branch:
The sleeping Vaporeon stays asleep and Ice Punch does less immediate route
work than Explosion. That branch is acceptable because Explosion can still be
used later, while a failed Explosion cannot be recovered.

Score:
Correct. This fixes the parent turn 13 hidden-info error: possible-only "no
absorber" cannot be the main reason for spending Explosion.

## Transfer Rule

Before recommending a safe-looking active move, answer these in order:

1. Which named branch is the opponent's best route?
2. Does my top move affect that branch?
3. If the move is a scout or setup move, what route piece or next board does it
   preserve or improve?
4. If the move spends Explosion or another one-time trade, what public evidence
   says the target is right and the absorber branch is covered?

If the answer to question 2 is no, either change the move or explicitly mark
the branch as an accepted priced loss.
