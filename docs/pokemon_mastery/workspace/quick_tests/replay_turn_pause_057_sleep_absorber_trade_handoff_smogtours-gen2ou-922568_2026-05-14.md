# Replay Turn-Pause 057 Sleep Absorber Trade Handoff - smogtours-gen2ou-922568 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-922568`.

Mode: spectator-public vanilla GSC replay practice. Lead species were read
only from the public pre-turn-1 switch lines because the replay used custom
nicknames.

Selected measurable action: fresh transfer after
`cashout_boundary_converter_probe_001_2026-05-14.md`. The target was the
cash-out boundary: low-support preservation versus immediate converter-defined
Explosion. The replay produced a mixed transfer around Snorlax set ambiguity,
sleep absorber preservation, route-trade absorber choice, and support handoff
after Spikes.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- The selected replay was the next fresh metadata-only candidate:
  `smogtours-gen2ou-922568`, a 28-turn Gen 2 OU replay.
- Only public pre-turn-1 switch lines were inspected to map nicknames to lead
  species: Snorlax mirror.
- Turns 1-7 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_056_immediate_route_trade_converter_smogtours-gen2ou-922569_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/cashout_boundary_converter_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the lead article frames early crippling or trading as a way to
enable sweepers, and the Explosion source reinforces that the target should be
specific. This replay adds two practical boundaries: Curse does not rule out
Lovely Kiss, and the defending side may preserve the boosted Snorlax by
absorbing Explosion with a different route piece.

## Score Summary

Scored decisions: 14 side decisions.

Top-match: 7 / 14.

Acceptable-match: 10 / 14.

Classification hits: 9 / 14.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 2 p1. I treated p1 Snorlax as needing to
attack or switch after Curse, but it revealed Lovely Kiss into the Forretress
absorber.

Main improvement:

- Turn 3 transferred the user's sleep-clause point cleanly: sleeping
  Forretress switched out immediately and remained Sleep Clause/support
  material.
- Turn 4 correctly identified Exeggutor Explosion as live into the boosted
  Snorlax route.
- Turn 5 correctly called Cloyster Spikes into Tyranitar.

Main errors:

- Turn 2 p1: missed that Curse Snorlax could still reveal Lovely Kiss.
- Turn 4 p1: named Explosion but expected a generic Ghost/Steel absorber; the
  actual line preserved Snorlax by sacking Zapdos.
- Turn 6 p1: wanted Cloyster Surf after Spikes, but the expert line handed off
  immediately to Machamp while p2 pivoted to Zapdos.
- Turn 7 p2: expected Thunder from Zapdos, but the actual Hidden Power hit the
  Raikou switch; this was a side-known or read-heavy branch, not a public-state
  certainty.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | Snorlax mirror | p1 attack preferred, Curse acceptable; p2 Double-Edge | p1 Curse; p2 Double-Edge | p1 acceptable, p2 top | Curse route started, but set not fixed. |
| 2 | +1 Snorlax 81 vs Snorlax 99 | p1 attack; p2 support pivot/pressure | p2 Forretress; p1 Lovely Kiss | p1 miss, p2 top | Curse does not rule out Lovely Kiss. |
| 3 | +1 LK Snorlax vs sleeping Forretress | p1 Double-Edge/progress; p2 switch sleeper out | p2 Exeggutor; p1 Double-Edge | both top | Preserve the sleeper as Sleep Clause/support material. |
| 4 | +1 Snorlax 82 vs Exeggutor 46 | p1 absorber switch; p2 Explosion | p1 Zapdos; p2 Explosion | p1 acceptable, p2 top | Explosion target was real, but absorber was Zapdos to preserve Snorlax. |
| 5 | Cloyster vs Tyranitar | p1 Spikes; p2 Rock Slide | p1 Spikes; p2 Rock Slide | both top | Support first. |
| 6 | Cloyster 58 vs Tyranitar | p1 Surf; p2 continue/switch | p1 Machamp; p2 Zapdos | p1 miss, p2 acceptable | After Spikes, handoff can beat spending support HP. |
| 7 | Machamp vs Zapdos | p1 Raikou/Snorlax; p2 Thunder | p1 Raikou; p2 Hidden Power | p1 top, p2 miss | Correct answer switch; Zapdos used a read/midground into it. |

## Reusable Lessons

Do not lock Snorlax's set after one reveal. Curse first can still become
Lovely Kiss on the next turn. Keep sleep, Rest, coverage, and attack branches
live until public moves force the set narrower.

Sleeping support should usually leave immediately unless its active job is
better. Forretress absorbed Lovely Kiss, then switched out as Sleep Clause and
future support material rather than burning wake turns.

Explosion can be correct while the defender also makes a correct preservation
switch. Exeggutor's Explosion was the right route trade into the boosted
Snorlax line, but p1 preserved Snorlax by losing Zapdos instead.

After Spikes, handoff can beat the obvious direct attack. Cloyster did not Surf
Tyranitar; it handed to Machamp while p2 moved Zapdos into the expected
Fighting pressure.

## Source-To-Policy Extraction

Trigger:
  Early Snorlax has revealed only one or two moves, support sleep absorber is
  available, and Explosion or handoff could decide the next route.

Default:
  Keep Snorlax set branches live until moves are public. Preserve induced
  sleepers as Sleep Clause/support material. When Explosion is live, also price
  which route piece the defender should preserve. After support lands, name
  whether direct damage or handoff gives the better next board.

Exceptions:
  Narrow the set when the fourth move is forced by public information or team
  sheet; keep the sleeper active when Sleep Talk, wake/action, or immediate
  support beats preserving it; cash out into the active target when no
  acceptable absorber exists.

Worst branch:
  The advisor assumes the first Snorlax reveal fixed the set, burns a sleeping
  support piece, or names Explosion without naming the defender's best
  absorber and the next converter.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  local Lovely Kiss/Sleep Clause behavior, Explosion damage, Ghost immunity,
  Spikes timing, and boss AI public-information limits.

Drill:
  Build a four-prompt regression: Curse Snorlax reveals Lovely Kiss; sleeping
  Forretress switches out; Exeggutor Explodes while Snorlax is preserved with
  Zapdos; Cloyster sets Spikes then hands off instead of Surfing.

## Next Rep

Run a fresh replay transfer on mixed cash-out decisions: set ambiguity,
sleeper preservation, absorber selection, and support handoff. The regression
artifact is `workspace/quick_tests/mixed_cashout_sleep_handoff_probe_001_2026-05-14.md`.
