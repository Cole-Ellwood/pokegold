# Replay Turn-Pause 053 Curselax Phaze Cashout - smogtours-gen2ou-922830 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-922830`.

Mode: spectator-public vanilla GSC replay practice with side-known conditionals
marked when my recommendation depended on unrevealed own-team slots.

Selected measurable action: fresh transfer after
`unassigned_sleep_source_snorlax_pricing_probe_001_2026-05-14.md`. The target
was unassigned sleep source, post-sleep doubles, and damage/recoil pricing
into Snorlax.

The replay became a useful anti-overfit test: after learning Lovely Kiss
Snorlax, I over-weighted it. This lead Snorlax was a Curse + Body Slam + Rest
set, and the real early route was Cloyster Toxic into Steelix Roar, not
immediate sleep or immediate Explosion.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- The selected replay was the next fresh metadata-only candidate:
  `smogtours-gen2ou-922830`, a 37-turn Gen 2 OU replay.
- Turns 1-5 and 7-12 were answered before reveal.
- Turn 6 is unscored because I revealed it after an incomplete freeze while
  diagnosing the Starmie route.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_052_lovely_kiss_snorlax_sleep_pivot_smogtours-gen2ou-923076_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/unassigned_sleep_source_snorlax_pricing_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, Double-Edge Sucks on Snorlax:
  `https://www.smogon.com/forums/threads/double-edge-sucks-on-snorlax.3560326/`
- Smogon Forums, GSC Introduction to Status:
  `https://www.smogon.com/forums/threads/gsc-introduction-to-status-sleep-paralysis-and-poison-gp-2-2.103998/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Snorlax source emphasizes Double-Edge + Earthquake pressure
and Rest support, while the Double-Edge discussion makes recoil against Zapdos
and Raikou a real route cost. This replay adds the other side of the prior
Lovely Kiss lesson: Snorlax can own the sleep job, but it can also be a normal
Curse/Rest anchor, so the advisor must not overfit to either set before the
move is shown.

## Score Summary

Scored decisions: 22 side decisions.

Top-match: 11 / 22.

Acceptable-match: 15 / 22.

Classification hits: 14 / 22.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Unscored: turn 6, because the reveal happened after an incomplete freeze.

Earliest meaningful error: turn 1 p1. I expected Lovely Kiss if available,
but the actual lead Snorlax used Curse.

Main improvement:

- Turn 2 correctly transferred Toxic before cash-out: Cloyster used Toxic
  into boosted Snorlax and Snorlax attacked.
- Turns 8-12 transferred the support-order and final-gate idea: Cloyster set
  Spikes, switched out of Raikou pressure, absorbed Snorlax Double-Edge, then
  Exploded only after future re-entry was fake.

Main errors:

- Turn 1 p1: overfit the previous Lovely Kiss Snorlax lesson instead of
  keeping Curse/Rest Snorlax live.
- Turn 3 p2: overcalled Cloyster Explosion. The actual line preserved Cloyster
  after Toxic and handed to Steelix, whose Roar denied the toxic Curselax
  route.
- Turn 5 p1: missed the Starmie hazard-control attempt and over-centered
  Zapdos coverage.
- Turn 7 p1: missed Cloyster as the lower-value Snorlax damage absorber that
  preserved Zapdos and set up a later Explosion.
- Turn 11 p1: inferred Sleep Talk too quickly after Rest. Resting Snorlax
  switched out while Cloyster absorbed Double-Edge and converted to Explosion.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | Lead Snorlax vs Cloyster | p1 Lovely Kiss if assigned sleep; p2 Spikes | p2 Spikes; p1 Curse | p1 miss, p2 top | Lovely Kiss is live, not guaranteed; keep Curse/Rest lead Snorlax live. |
| 2 | +1 Snorlax vs Cloyster after Spikes | p1 attack; p2 Toxic before cash-out | p2 Toxic; p1 Body Slam | both top | Status can be the support action before phaze or Explosion. |
| 3 | +1 toxic Snorlax vs Cloyster 74 | p1 Body Slam/Ghost conditional; p2 Explosion | p2 Steelix; p1 Body Slam | p1 acceptable, p2 miss | Toxic enabled hard phazer handoff; Explosion was not forced. |
| 4 | toxic Snorlax vs Steelix | p1 switch unless Earthquake known; p2 Roar | p1 Cloyster; p2 Roar dragging Zapdos | both top | Steelix converted Toxic into phazing pressure. |
| 5 | Zapdos vs Steelix after Roar | p1 Hidden Power; p2 switch/Roar branch | p1 Starmie; p2 Roar dragging Zapdos | p1 miss, p2 acceptable | Starmie hazard control was the route, not only Zapdos coverage. |
| 6 | Zapdos vs Steelix reset | unscored incomplete freeze | p2 Snorlax; p1 Hidden Power | unscored | Prompt discipline failure; do not count. |
| 7 | Zapdos vs Snorlax 94 | p1 Thunder; p2 Double-Edge | p1 Cloyster; p2 Double-Edge | p1 miss, p2 top | Cloyster was the lower-value absorber preserving Zapdos. |
| 8 | Cloyster 50 vs Snorlax 96 | p1 Spikes; p2 leave to cover cash-out | p2 Raikou; p1 Spikes | p1 top, p2 acceptable | Support before cash-out transferred. |
| 9 | Cloyster 56 vs Raikou | p1 switch; p2 Thunder | p1 Snorlax; p2 Thunder | p1 acceptable, p2 top | Raikou denied immediate Explosion; switch to Electric sponge. |
| 10 | poisoned Snorlax 49 vs Raikou | p1 Rest; p2 Thunder | p2 Snorlax; p1 Rest | p1 top, p2 miss | Snorlax reset poison, but p2 preserved Raikou and re-entered Snorlax. |
| 11 | Resting Snorlax vs Snorlax | p1 Sleep Talk if fourth; p2 Double-Edge | p1 Cloyster; p2 Double-Edge | p1 miss, p2 top | Do not infer Sleep Talk; use a lower-value absorber if that preserves the anchor. |
| 12 | Cloyster 16 vs Snorlax 91 | p1 Explosion; p2 absorber if available | p1 Explosion; p2 stayed Snorlax | p1 top, p2 miss | Final-gate Explosion was correct once re-entry was fake. |

## Reusable Lessons

Unassigned sleep source must stay balanced. Lovely Kiss Snorlax is a real
current option, but it is not a default that overrides revealed route pressure.
If Snorlax shows Curse first, re-rank it as a Curse/Rest anchor until Lovely
Kiss or another fourth move appears.

Cloyster Toxic can be the support move before Explosion. Against Curselax,
Toxic into Steelix Roar may do more route work than immediately Exploding,
because it forces the boosted anchor to switch or burn Rest while Spikes tax
re-entry.

Hazard control can be the hidden route behind an odd switch. The Zapdos into
Steelix position invited Hidden Power, but p1 first tried to bring Starmie
through Roar to contest Spikes. When Starmie is revealed on the Spikes side,
include Rapid Spin or spin pressure before reducing the board to coverage.

Do not infer Sleep Talk just because Snorlax used Rest. If no Sleep Talk is
revealed and a lower-value piece can absorb the hit, preserve the resting
anchor and convert the absorber afterward.

## Source-To-Policy Extraction

Trigger:
  Lead or early Snorlax has not revealed its fourth move, while Cloyster and
  Steelix are available to sequence Spikes, Toxic, Roar, and Explosion.

Default:
  Treat Lovely Kiss, Curse/Rest, and coverage as live branches until revealed.
  After Cloyster lands Toxic on Curselax, price the hard-phazer handoff before
  Explosion. After Rest, do not assume Sleep Talk unless it is revealed or the
  set structure is forced.

Exceptions:
  Immediate Explosion when the boosted target is the route blocker and no
  phazer or recurring answer can enter; immediate sleep when Snorlax has
  revealed Lovely Kiss or the team sheet assigns it the sleep job; staying
  asleep when Sleep Talk is revealed or the wake route is the plan.

Worst branch:
  The advisor overfits one Snorlax set, calls the wrong one-time trade, and
  misses the support handoff that actually controls the route.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  local Toxic reset, Roar timing, Rest/Sleep Talk, and Sleep Clause behavior.

Drill:
  Build a five-prompt regression: lead Snorlax vs Cloyster, Toxic into
  Curselax, Steelix Roar after Toxic, Starmie hazard-control reveal, and Rest
  Snorlax without confirmed Sleep Talk.

## Next Rep

Run another fresh replay transfer focused on Snorlax set ambiguity and support
handoff before Explosion. The regression artifact is
`quick_tests/snorlax_set_ambiguity_phaze_cashout_probe_001_2026-05-14.md`.
