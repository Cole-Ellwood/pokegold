# Replay Turn-Pause 056 Immediate Route Trade Converter - smogtours-gen2ou-922569 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-922569`.

Mode: spectator-public vanilla GSC replay practice. Lead species were read
only from the public pre-turn-1 switch lines because the replay used custom
nicknames.

Selected measurable action: fresh transfer after
`low_support_preserve_before_cashout_probe_001_2026-05-14.md`. The target was
low-support preservation before cash-out. The replay instead gave the opposite
boundary: immediate Explosion was correct when it removed the exact route
piece and handed a converter a clear next board.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- The selected replay was the next fresh metadata-only candidate:
  `smogtours-gen2ou-922569`, a 22-turn Gen 2 OU replay.
- Only public pre-turn-1 switch lines were inspected to map nicknames to lead
  species: p1 Exeggutor and p2 Zapdos.
- Turns 1-5 were answered before reveal.
- Turn 3 p2 is unscored because p2's Snorlax fainted before it could choose a
  logged move.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_055_low_cloyster_preserve_ghost_pivot_smogtours-gen2ou-922579_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/low_support_preserve_before_cashout_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, Thief:
  `https://www.smogon.com/forums/threads/thief.3543261/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Explosion source fits this replay cleanly: Explosion is not a
low-HP reflex, but it is correct when the target is the current route piece and
the post-trade converter is ready. The prior low-Cloyster lesson was an
anti-overcall, not an anti-Explosion rule.

## Score Summary

Scored decisions: 9 side decisions.

Top-match: 4 / 9.

Acceptable-match: 6 / 9.

Classification hits: 5 / 9.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Unscored: turn 3 p2, because Snorlax fainted before a move was logged.

Earliest meaningful error: turn 1 p1. I preserved Exeggutor, but the actual
line immediately Exploded into Zapdos.

Main improvement:

- Turn 2 correctly called Forretress Spikes before any cash-out.
- Turn 4 correctly expected Snorlax to leave for a Fighting immunity after the
  Forretress trade enabled Machamp.
- Turn 5 conditionally named Machamp coverage into the Ghost/pivot branch.

Main errors:

- Turn 1 p1: undercalled lead Explosion. Exeggutor traded immediately into
  Zapdos, removing the Electric and creating the support-to-Machamp sequence.
- Turn 3 p1: overcorrected from the low-support preservation lesson and called
  Toxic from Forretress. Actual Forretress Exploded after setting Spikes,
  reducing boosted Snorlax for Machamp.
- Turn 5 p2: over-kept Gengar active after it had absorbed Cross Chop. The
  actual line pivoted to Marowak while Machamp used Hidden Power.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | Exeggutor vs Zapdos | p1 switch; p2 Thunder | p2 Thunder miss; p1 Explosion | p1 miss, p2 top | Immediate lead Explosion can remove the exact route piece. |
| 2 | Forretress vs Snorlax after lead trade | p1 Spikes/Toxic by setup pressure; p2 coverage/Curse | p1 Spikes; p2 Curse | p1 top, p2 acceptable | Support first before route trade. |
| 3 | Forretress vs +1 Snorlax | p1 Toxic before boom; p2 unscored | p1 Explosion; p2 fainted | p1 miss, p2 unscored | Cash out when the converter is ready and delay lets Snorlax route continue. |
| 4 | Machamp vs 51% +1 Snorlax | p1 Cross Chop; p2 Fighting answer | p2 Gengar; p1 Cross Chop | both top | The trade named Machamp as converter. |
| 5 | Machamp vs Gengar | p1 switch or coverage conditional; p2 Hypnosis/Thunder | p2 Marowak; p1 Hidden Power | p1 acceptable, p2 miss | Coverage into the Ghost/pivot branch can keep converter pressure. |

## Reusable Lessons

Do not turn "preserve low support" into "avoid Explosion." Immediate
Explosion is correct when the target is exact, the exploder's job is complete
or expendable, and the post-trade converter is obvious.

The converter must be named before the cash-out. In this replay, lead
Exeggutor removed Zapdos, Forretress laid Spikes and then damaged boosted
Snorlax, and Machamp entered as the concrete converter.

Support before Explosion still mattered. Forretress did not Explode on turn 2;
it set Spikes first. The cash-out became correct only after Snorlax used Curse
and the layer was already established.

## Source-To-Policy Extraction

Trigger:
  A one-time trade can remove or cripple the exact blocker, and the next
  converter is already visible or strongly implied by the support sequence.

Default:
  Deliver necessary support first, then cash out if delay lets the target
  set up, Rest, switch, or escape and the converter has a clean board.

Exceptions:
  Preserve when Toxic, Spin, Thief, phazing, Ghost pivot, or handoff produces
  more route value; when a Ghost/absorber is likely and cheap; or when the
  converter is not actually ready.

Worst branch:
  The advisor overcorrects from preservation lessons, declines the route trade,
  and lets the target keep the exact board the trade was supposed to deny.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  local Explosion damage, Ghost immunity, Spikes entry timing, stat stages,
  and boss AI public-information limits.

Drill:
  Build a four-prompt regression: lead Exeggutor trades into Zapdos; Forretress
  sets Spikes first; Forretress Explodes into boosted Snorlax; Machamp uses
  coverage into the Ghost/pivot branch.

## Next Rep

Run a fresh replay transfer on the cash-out boundary: low-support preservation
versus immediate converter-defined Explosion. The regression artifact is
`quick_tests/cashout_boundary_converter_probe_001_2026-05-14.md`.
