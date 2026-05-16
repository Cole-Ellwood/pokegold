# Ghost Electric Trap Phaze Transfer 001 - smogtours-gen2ou-920777 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920777`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer for paired handoff into Ghost or Electric
receiver plus trap/phaze timing.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/rest_sleeper_cleric_trade_transfer_001_smogtours-gen2ou-920770_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`

Web/current sources:

- Smogon GSC OU Winter Seasonal #8 Round 8, used for this fresh replay.
- Smogon GSC OU Winter Seasonal #8 Round 9 search results, checked for current
  replay-source context before falling back to the unused Round 8 pool.

## Contamination Control

Local search found no prior `920777` artifact. The raw log was downloaded to
`tmp/pokemon_mastery_replays/` without printing the log. The first public state
seen was the turn 1 prompt. No keyword screening was used.

Unscored no-move outcomes:

- Turn 12 p1 Exeggutor was fully paralyzed, so the selected move was not
  logged.
- Turns 24-25 p1 Cloyster was asleep and did not log a selected move. The stay
  or sack line is discussed, but not counted in top or acceptable agreement.

## Score Summary

Turns scored: 1-25.

Scorable decisions: 47.

Top-match: 19 / 47.

Acceptable-match: 29 / 47.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 1.

Earliest meaningful error: turn 1. I missed Zapdos handing off to Exeggutor
against lead Snorlax and missed Snorlax using Curse.

Hidden-info error:
Turn 20, I over-assigned Sleep Talk to Rest Zapdos and recommended staying,
instead of preserving the Rested Zapdos while Cloyster absorbed Lovely Kiss.

## Focused Transfer Scores

Ghost receiver handoff: not tested cleanly.

Electric receiver handoff: 1 / 4.

- Missed turn 3: Exeggutor should hand off to Steelix on Zapdos's Thunder.
- Missed turn 6: Cloyster should hand off to Snorlax on Zapdos pressure.
- Missed turn 11: Cloyster should hand off to Exeggutor on Zapdos's Thunder.
- Partial turn 16: I attacked as Raikou entered, but did not name the Raikou
  receiver or choose the actual Hidden Power.

Trap/phaze timing: 0 / 2.

- Missed turn 4: Steelix used Roar into Zapdos instead of setup.
- Missed turn 15: Steelix cashed out with Explosion into RestTalk Zapdos
  instead of using Roar.

Rest-sleeper handoff: 2 / 3.

- Missed turn 20: Rested Zapdos should switch out and be saved while Cloyster
  absorbs Lovely Kiss.
- Hit turn 22: sleeping Cloyster handed back to Zapdos as Snorlax used Curse.
- Hit turns 24-25 as unscored strategic line: sleeping Cloyster stayed and was
  spent after the safe handoff cycle, but no selected move was logged.

Support before sleep/cash-out: 2 / 3.

- Hit turn 21: Cloyster set Spikes before taking Lovely Kiss.
- Hit turn 22: switch to Zapdos preserved the slept Cloyster after Spikes
  landed.
- Missed turn 13: low Exeggutor correctly stayed to land Sleep Powder before
  being removed.

## Turn Notes

### Turns 1-4 - Early Electric Handoff And Roar Miss

Public shape:
Zapdos led into Snorlax, then Exeggutor faced a Curse Snorlax. Zapdos entered
as the sleep absorber, Sleep Powder missed, and Exeggutor later handed to
Steelix on Zapdos.

Frozen answer quality:
I missed the first handoff from Zapdos to Exeggutor, hit Sleep Powder into the
Zapdos switch on turn 2, then missed Exeggutor to Steelix on turn 3 and Steelix
Roar on turn 4.

Lesson:
After an Electric receiver enters on sleep pressure, do not only ask whether
the active status move can be repeated. Price the ground or steel handoff and
the phaze option immediately.

### Turns 5-11 - Snorlax Trade And Missed Electric Handoffs

Public shape:
Steelix and Golem both left, Cloyster and Zapdos met, Snorlax came in on
Zapdos, then Golem exploded into Snorlax. Cloyster then faced low Zapdos and
handed off to Exeggutor.

Frozen answer quality:
I hit Curse on Snorlax, hit Double-Edge into Golem, and hit Golem Explosion as
the route trade. I missed Cloyster to Snorlax on turn 6 and Cloyster to
Exeggutor on turn 11.

Lesson:
The repeated miss is not naming Electric pressure; it is naming the exact
teammate that should take the Electric turn before clicking generic progress.

### Turns 12-15 - Low Exeggutor And Cash-Out Boundary

Public shape:
Paralyzed Exeggutor stayed in against Zapdos, survived Hidden Power, and landed
Sleep Powder. Steelix then entered against sleeping RestTalk Zapdos.

Frozen answer quality:
I tried to preserve low Exeggutor instead of spending it for Sleep Powder, then
wanted Explosion too early on turn 14 and Roar on turn 15. Actual Steelix used
Explosion only after Zapdos showed Sleep Talk.

Lesson:
Low support can be worth spending when the status lands before death. Against
RestTalk Zapdos, Steelix's Explosion can be the route action even when Roar
looks like the normal phaze response.

### Turns 16-19 - Electric Endgame Pressure

Public shape:
The opponent preserved the 9% sleeping Zapdos by switching to Raikou. Our
Zapdos attacked Raikou, traded Thunder and Thunderbolt, then Rested as Snorlax
entered.

Frozen answer quality:
I attacked into the receiver but did not name Raikou. I then hit the repeated
Thunder/Thunderbolt exchange, but missed Rest on turn 19.

Lesson:
Active pressure into the Electric receiver is acceptable only when the receiver
has been named and the damage changes the route. Here I was still reacting
rather than planning the receiver map.

### Turns 20-25 - Rest Sleeper Handoff Correction

Public shape:
Rested Zapdos faced Lovely Kiss Snorlax. Cloyster entered, set Spikes before
being slept, then Zapdos returned as Snorlax Cursed. Cloyster later came back
to absorb Double-Edge and be spent.

Frozen answer quality:
I missed turn 20 by assuming Sleep Talk from Rest and staying. After that, I
hit Spikes before Lovely Kiss, hit the Zapdos handoff after Cloyster slept, and
correctly treated low sleeping Cloyster as spendable route material.

Lesson:
The user correction remains important: Rest plus possible Sleep Talk is not a
stay script. Once the sleeping or Rested piece has a later job and another
piece owns the immediate sleep or setup branch, switch it out.

## Error Classes Found

- Electric receiver handoff is still weak: missed Steelix, Snorlax, and
  Exeggutor handoffs into Zapdos pressure.
- RestTalk over-assignment returned on turn 20.
- Cash-out timing is still imprecise: overcalled Explosion on turn 14, missed
  Explosion over Roar on turn 15.
- Improved sleep handoff after the miss: hit Spikes before Lovely Kiss and
  saved the slept Cloyster by going back to Zapdos.

## Next Rep

Do one fresh transfer focused specifically on Electric receiver handoff
identity. Score: receiver named, handoff chosen, active pressure chosen for a
named reason, and RestTalk-stay rejected when another piece owns the branch.
