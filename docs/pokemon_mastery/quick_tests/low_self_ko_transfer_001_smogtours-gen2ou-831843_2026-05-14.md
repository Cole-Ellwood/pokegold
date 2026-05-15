# Low Self-KO Transfer 001 - smogtours-gen2ou-831843 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-831843`

Context source:
Smogon, `GSC OU Winter Seasonal #7: Round 10`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-7-round-10.3762830/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Transfer `low_self_ko_defensive_owner_probe_001` to a fresh replay segment.
Before attacking or pivoting around a low or one-time support piece, force:
speed/order, survival, defensive owner, and whether active pressure or coverage
immediately wins a route.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/quick_tests/low_self_ko_defensive_owner_probe_001_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #7 Round 10 thread above.
- Pokemon Showdown replay source above.
- Raw log: `https://replay.pokemonshowdown.com/smogtours-gen2ou-831843.log`

## Contamination Control

Local search found no prior `831843` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not inspected;
each prompt was generated with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen.

Stopped after turn 15. Turn 9 p1 is unscored because full paralysis prevented
the selected move from appearing in the log.

## Score Summary

Turns scored: 1-15.

Scorable side decisions: 29.

Top-match: 14 / 29.

Acceptable-match: 19 / 29.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 20 / 29.

Route-converting move chosen: 12 / 20 target converter decisions.

Branch-punish chosen: 10 / 17 named-branch decisions.

Self-KO gate subset: 2 / 6 top, 2 / 6 acceptable.

Earliest meaningful error: turn 2. I did not make Exeggutor Explosion or the
Tyranitar absorber the top line, even though the replay immediately showed
both sides playing the self-KO branch.

Main result:
The severe error did not repeat, but the correction is not stable. I covered
the turn 12 Cloyster/Misdreavus mirror correctly, but missed or overcalled the
same family on turns 2 and 6.

## Focused Turn Notes

### Turn 2 - Self-KO And Absorber Both Missed

Public state:
Exeggutor was at 56% against Snorlax at 77% after Psychic plus Double-Edge.

Frozen answers:
p1 should use Sleep Powder or status pressure; p2 should keep active
Snorlax pressure unless the absorber branch is clear.

Actual:
p2 switched Tyranitar. p1 used Explosion, which Tyranitar resisted.

Score:
Both sides missed the target. Exeggutor was not low, but the same one-time
trade family was live: it could spend itself before Snorlax kept pressuring.
p2 correctly chose the lower-value absorber. I treated the self-KO as a
possible branch, not the route-defining branch.

### Turn 6 - Overcovering Explosion Into Forretress

Public state:
p1 Snorlax was at 96% with Curse and Fire Blast revealed only after the turn.
p2 Forretress was at 94% after entering through Spikes.

Frozen answers:
p1 should cover Forretress Explosion with a lower-value owner if available;
p2 should consider Explosion into boosted Snorlax before generic support.

Actual:
Forretress set Spikes. Snorlax used Fire Blast and KOed Forretress.

Score:
The self-KO gate overcorrected. Forretress had not delivered Spikes yet, was
not low, and the actual route was support first. The right p1 line was hidden
own-side coverage; spectator-public mode limits exact scoring, but the error
class is real: do not promote every Forretress entry into immediate Explosion.

### Turn 12 - Correct Mirror: Surf Into Ghost Absorber

Public state:
p1 Cloyster was at 64% against Snorlax at 72%. p2 had revealed Misdreavus, so
Explosion was dangerous for p1 and an absorber handoff was available for p2.

Frozen answers:
p1 should not make Explosion the top line; use Surf or utility while pricing
the Misdreavus branch. p2 should switch Misdreavus to cover Explosion/Rapid
Spin/Normal lines.

Actual:
p2 switched Misdreavus. p1 used Surf and dealt major damage.

Score:
Both sides hit the self-KO boundary. Surf punished the absorber without
spending Cloyster, and Misdreavus covered the cash-out branch.

## Lessons

1. The gate must distinguish "one-time move exists" from "one-time move is now
   the route." Turn 6 punished treating Forretress as an automatic Explosion
   threat before it had delivered Spikes.
2. The defensive mirror transferred better than the offensive cash-out side.
   I recognized the Misdreavus absorber on turn 12 but missed Tyranitar
   absorbing Exeggutor on turn 2.
3. Hidden-info discipline stayed intact. I did not claim Sleep Talk, Fire
   Blast, Explosion, or hidden team owners as facts before reveal.
4. The next fix should be an expert review, not another probe: compare turns 2,
   6, and 12 and extract when self-KO is route-defining versus merely possible.

## Next Rep

Short expert review of `831843` turns 2, 6, and 12:

- what public features made Explosion route-defining or not;
- whether support had already been delivered;
- whether the self-KO target was exact;
- whether the absorber was side-known, revealed, or only possible;
- what active pressure or coverage did if the self-KO branch did not happen.
