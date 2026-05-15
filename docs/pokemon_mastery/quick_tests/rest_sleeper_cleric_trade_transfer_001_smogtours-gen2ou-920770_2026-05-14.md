# Rest Sleeper Cleric Trade Transfer 001 - smogtours-gen2ou-920770 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920770`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Transfer `rest_sleeper_cleric_trade_probe_001` to a fresh unused replay and
score safe sleep-turn burn, sleeper preservation handoff, support handoff into
hard answer, support-before-cashout, and setup after handoff-out.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/quick_tests/rest_sleeper_cleric_trade_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`

Web/current sources:

- Smogon GSC OU Winter Seasonal #8 Round 8, used for this fresh replay.
- Smogon GSC OU Global Championship 2026 Round 2 search results, checked for
  current replay-source context.

## Contamination Control

Local search found no prior `920770` artifact. The raw log was downloaded to
`tmp/pokemon_mastery_replays/` without printing the log. The first public state
seen was the turn 1 prompt. No keyword screening was used.

Unscored no-move outcomes:

- Turn 4 p1 Forretress was KOed by Explosion before its selected move was
  logged.
- Turn 14 p1 Skarmory was fully paralyzed, so the selected move was not logged.

## Score Summary

Turns scored: 1-22.

Scorable decisions: 42.

Top-match: 11 / 42.

Acceptable-match: 20 / 42.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 1. I defaulted to ordinary Spikes mirror play
and missed the Clamp/Toxic opening shape.

## Focused Transfer Scores

Safe sleep-turn burn: not tested cleanly.

Sleeper preservation handoff: not tested cleanly.

Support handoff into hard answer: 1 / 2.

- Hit turn 17: Blissey handed off to Skarmory into poisoned Snorlax.
- Missed turn 18: Skarmory should hand off to Umbreon as Gengar entered.

Support-before-cashout or removal threat: 1 / 1.

- Hit turn 16: Blissey used Heal Bell before the opponent's Gengar/Snorlax
  branch could remove or overload the support route.

Setup after handoff-out: 1 / 2.

- Missed turn 12: Skarmory should exploit poisoned Snorlax with Curse instead
  of immediately phazing.
- Hit turn 13: after seeing the route, Skarmory continued Curse correctly.

Spin sacrifice as route trade: 1 / 1.

- Hit turn 22: Starmie used Rapid Spin and accepted Zapdos's Thunderbolt KO to
  clear the entry map.

## Turn Notes

### Turns 1-4 - Clamp/Screech Into Explosion

Public shape:
Forretress versus Cloyster lead, then Cloyster revealed Clamp and Screech while
Forretress revealed Toxic and Spikes.

Frozen answer quality:
I over-defaulted to Spikes mirror lines, then overcalled immediate Explosion on
turn 3 and missed that the actual cash-out came on turn 4 after both Spikes
were up.

Actual route:
Cloyster used Clamp, Screech, Spikes, then Explosion. Forretress used Toxic,
Toxic, Spikes, then died before a move was logged.

Lesson:
When a lead reveals Clamp plus Screech, do not collapse into either "always
Spikes" or "Explosion now." Price whether the trap sequence is buying status,
hazards, defense drop, or a specific cash-out turn.

### Turns 5-7 - Umbreon Trap Versus Forretress

Public shape:
Umbreon came in versus Snorlax. Snorlax handed off to Forretress as Umbreon
used Mean Look. Umbreon then used Growl while Forretress spun and exploded.

Frozen answer quality:
I missed Mean Look on turn 5, then hit the attack-drop class and Rapid Spin on
turn 6, then hit Growl on turn 7 but missed Forretress Explosion.

Actual route:
Mean Look trapped the support piece, Growl reduced the Explosion trade, and
Forretress removed Spikes before cashing out.

Lesson:
Trapping support can be route progress even when it looks passive. After a
support piece is trapped and its attack is lowered, still price Spin then
Explosion as the route trade.

### Turns 8-11 - Blissey/Skarmory Handoff

Public shape:
Umbreon faced Zapdos, then Blissey entered and set Light Screen as Snorlax came
in. Blissey handed off to Skarmory, which Toxic'd Snorlax.

Frozen answer quality:
I missed the initial Blissey handoff and Thunder Wave, accepted Light Screen as
a serious alternative rather than top, then found the physical-wall handoff
class and hit Skarmory Toxic.

Lesson:
When the special wall exists and the active support piece is mid-HP with Spikes
up, the handoff may be the route even before damage becomes urgent.

### Turns 12-16 - Setup And Heal Bell

Public shape:
Skarmory had Toxic on Snorlax. The opponent kept Body Slamming, later brought
Gengar into Skarmory, and Blissey entered on Thunderbolt.

Frozen answer quality:
I missed the first Skarmory Curse on turn 12, then hit Curse on turn 13, hit
Blissey into Gengar on turn 15, and hit Heal Bell on turn 16.

Actual route:
Skarmory used Curse while Snorlax stayed, Gengar entered later, Blissey took
Thunderbolt, then Heal Bell happened before the opponent pivoted back to
Snorlax.

Lesson:
The regression did transfer once: with Blissey active and multiple statused
route pieces, use Heal Bell before the removal or overload branch can deny the
support action.

### Turns 17-22 - Remaining Handoff Miss

Public shape:
After Heal Bell, Blissey handed to Skarmory versus poisoned Snorlax. Gengar
then entered, Umbreon entered on Gengar, Zapdos entered into Mean Look, and
Starmie was dragged into Zapdos.

Frozen answer quality:
I hit Blissey to Skarmory and Body Slam on turn 17, but missed the Skarmory to
Umbreon handoff on turn 18. I then missed Mean Look, Rest, and Whirlwind
sequencing before correctly using Starmie to Rapid Spin even though Zapdos
could KO it.

Actual route:
Skarmory handed off to Umbreon as Gengar entered. Umbreon trapped Zapdos and
used Rest before Zapdos Whirlwind dragged Skarmory. Later Zapdos dragged
Starmie, and Starmie cleared Spikes before dying.

Lesson:
The main remaining error is still paired handoff. I can find the obvious
support action once it is active, but I still under-switch to the teammate that
owns a newly revealed Gengar or trap/phaze board.

## Error Classes Found

- Clamp/Screech route pricing weak: over-defaulted to Spikes mirror and then
  overcalled Explosion one turn early.
- Support handoff partially improved: hit Blissey to Skarmory, missed Skarmory
  to Umbreon.
- Setup after status clock partially improved: missed first Skarmory Curse, hit
  second.
- Support-before-removal improved: hit Heal Bell before the Gengar/Snorlax
  branch could overload the support route.
- Trap/phaze sequencing weak: missed Mean Look, Umbreon Rest, and Zapdos
  Whirlwind timing.

## Next Rep

Build a tiny Gengar-entry handoff add-on only if needed, but do not split the
thread into more probes by default. The next higher-value fresh transfer should
score paired handoff into Ghost or Electric receiver, plus trap/phaze timing.
