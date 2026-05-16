# Replay Turn-Pause 025 Route Trade Timing Transfer - smogtours-gen2ou-934874 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934874`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer test for `route_trade_timing_probe_001`: in a real
replay, choose among Toxic first, Spikes first, absorber pivot, and Explosion
when Forretress faces a boosting Snorlax route.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused logs: Explosion, Self-Destruct, Snorlax, Cloyster, Forretress,
  Curse, Toxic, Spikes, Rest, Sleep Talk, Zapdos, and Raikou.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.
- The helper omitted species for nicknamed Pokemon, so the public lead species
  were checked from the initial switch lines only. No future turn order was
  exposed by that check.

Local docs checked:

- `docs/pokemon_mastery/workspace/quick_tests/route_trade_timing_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`

Source note: the timing ladder transferred through Toxic and Spikes, but the
fresh replay added a preservation boundary: even after support is delivered,
Forretress should not blindly explode if the opponent can reveal or pivot to a
better absorber.

## Score Summary

Context turns: 1-21, unscored. They established Raikou RestTalk, Lovely Kiss
Snorlax, Sleep Talk Skarmory, Cloyster Spikes, Starmie Substitute/Rapid Spin,
and the switch loop that brought Snorlax into Forretress.

Target turns scored: 22-25.

Target decisions scored: 8 side-decisions.

Top-match: 4 / 8.

Acceptable-match: 6 / 8.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest target error: turn 22.

Largest target error: turn 25.

## Target Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 22 | Snorlax 100 vs sleeping Raikou; p1 has Curse/Lovely Kiss | p1 Curse; p2 switch to a control answer | p2 Forretress; p1 Curse | p1 top, p2 miss | Correctly used the free turn; missed that Forretress, not Skarmory/Snorlax, was the anti-Curse pivot. |
| 23 | +1 Snorlax vs Forretress 100 | p1 attack if no Fire move; p2 Toxic before Explosion | p2 Toxic; p1 Earthquake | p1 acceptable, p2 top | Good transfer: Forretress used Toxic first to put Curselax on a clock. |
| 24 | +1 poisoned Snorlax vs Forretress 77 | p1 Earthquake; p2 Spikes before cash-out | p2 Spikes; p1 Earthquake crit | both top | Good transfer: after status, Forretress got the field job before considering Explosion. |
| 25 | +1 poisoned Snorlax 94 vs Forretress 23; Spikes on p1 side | p2 Explosion; p1 maybe stay or switch a lower-value absorber | p2 Skarmory; p1 Golem | p1 acceptable, p2 miss | Overcall: after the crit left Forretress low, the expert line preserved it and both players pivoted. Golem revealed the absorber branch. |

## Error Classes

- Improved: Forretress timing was correct through Toxic first and Spikes first.
- Remaining miss: I treated low Forretress plus completed support as "explode
  now" without pricing the opponent's absorber/double-switch branch.
- Hidden-information discipline held: Golem was not public before turn 25, so
  the correct policy is not "predict Golem" but "do not force Explosion when a
  plausible absorber or pivot makes preservation better."
- Sleep rule transfer held: sleeping Skarmory stayed active because Sleep Talk
  was revealed, so the earlier "preserve sleep-clause material" heuristic did
  not become a script.

## Policy Update

Add a final gate to the timing ladder: after Toxic and Spikes are delivered,
cash out only if the target is likely to stay or the absorber branch still
leaves the post-trade route favorable. If the opponent can pivot into a
revealed or plausible absorber while the exploder still has future utility,
preserve and re-solve.

## Next Study Target

Run a compact regression probe for the final gate: after support is delivered,
choose between Explosion, preservation, or double-switch when a possible
absorber exists.
