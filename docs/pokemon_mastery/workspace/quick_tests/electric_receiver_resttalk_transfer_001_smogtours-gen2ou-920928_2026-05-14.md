# Electric Receiver RestTalk Transfer 001 - smogtours-gen2ou-920928 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920928`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer for Electric receiver handoff identity plus
RestTalk-stay rejection when another piece owns the branch.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/ghost_electric_trap_phaze_transfer_001_smogtours-gen2ou-920777_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`

Web/current sources:

- Smogon GSC OU Winter Seasonal #8 Round 8, used for this fresh replay.
- Smogon GSC OU Winter Seasonal #8 Round 9 and GSC OU Global Championship 2026
  search results, checked for current replay-source context.

## Contamination Control

Local search found no prior `920928` artifact. The raw log was downloaded to
`tmp/pokemon_mastery_replays/` without printing the log. The first public state
seen was the turn 1 prompt. No keyword screening was used.

Unscored no-move outcomes:

- Turn 20 p2 Snorlax was fully paralyzed, so its selected move was not logged.
- Turn 21 p2 Snorlax was fully paralyzed, so its selected move was not logged.

## Score Summary

Turns scored: 1-22.

Scorable decisions: 42.

Top-match: 12 / 42.

Acceptable-match: 19 / 42.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 1.

Hidden-info errors: 2.

Earliest meaningful error: turn 3. I rejected RestTalk stay before any teammate
had been revealed to own the Zapdos mirror branch, even though RestTalk Zapdos
was the actual set and active route.

Hidden-info errors:

- Turn 11: I wanted Earthquake or coverage from Belly Drum Snorlax instead of
  pricing the revealed Double-Edge route through Tyranitar.
- Turn 14: I assumed Miltank should use Heal Bell from species role, but this
  Miltank revealed Thunder and punished Cloyster directly.

State error:

- Turn 22: I missed the Rest wake timing and called Sleep Talk when Zapdos was
  able to wake and use Thunder.

## Focused Transfer Scores

Electric receiver handoff identity: 2 / 6.

- Missed turn 3: p1 should stay with revealed RestTalk Zapdos in the mirror;
  no teammate had yet been revealed to own the branch.
- Missed turn 4: after the RestTalk route created pressure, p1 and p2 both
  handed off to Snorlax; I only found p2's side.
- Missed turn 13: Quagsire forced Tyranitar out, but p1 handed off to Miltank
  as p2 went Cloyster.
- Hit turn 16: Miltank handed off to Quagsire on Gengar, and Ice Punch revealed
  the counter-coverage.
- Missed turn 17: Quagsire drew Exeggutor while p1 handed off to RestTalk
  Zapdos.
- Hit turn 19 by class: RestTalk Zapdos handed off to the Snorlax answer,
  Skarmory, though I named the support-wall class rather than exact Skarmory.

RestTalk-stay rejection: 2 / 4.

- Missed turn 3: rejected RestTalk stay too early.
- Hit turn 18: stayed with revealed RestTalk Zapdos when no cleaner handoff
  owned the Exeggutor/Snorlax branch.
- Hit turn 19 by class: switched RestTalk Zapdos out once Snorlax became the
  live branch and a physical answer owned it.
- Missed turn 22: wrong wake count caused a Sleep Talk call instead of Thunder.

Active pressure into receiver: 2 / 3.

- Hit turn 6: Snorlax Double-Edge punished Cloyster after the receiver entered.
- Hit turn 15: Miltank's Thunder still damaged Gengar after the Ghost handoff.
- Missed turn 20: I wanted setup while Skarmory used Drill Peck pressure into
  paralyzed Snorlax.

Hidden-role correction: 0 / 2.

- Missed Belly Drum Snorlax as a live set on turn 10.
- Missed Thunder Miltank as a live lure on turn 14.

## Turn Notes

### Turns 1-4 - Zapdos Mirror And RestTalk Boundary

Public shape:
Zapdos mirror. p1 Zapdos was paralyzed by Thunder, used Rest, then revealed
Sleep Talk. Both sides handed off to Snorlax after RestTalk Thunder crit p2
Zapdos down to low HP.

Frozen answer quality:
I hit Thunder on turn 1, accepted preservation on turn 2, then overcorrected
on turn 3 by trying to switch before a better branch-owner was public. On turn
4, after Sleep Talk was revealed, I still missed p1's Snorlax handoff.

Lesson:
The correction is not "reject RestTalk." It is "do not invent RestTalk before
it is revealed, but once it is revealed, stay only until a better branch-owner
is public."

### Turns 5-9 - Spikes, Spinner Handoff, And Support Timing

Public shape:
Snorlax mirrored, p2 handed to Cloyster, Cloyster set Spikes, p1 handed to
Starmie after Toxic pressure, then Starmie paralyzed Snorlax before spinning.

Frozen answer quality:
I missed the initial Snorlax Double-Edge into Cloyster, then hit Double-Edge
and Spikes on turn 6. I missed Starmie before Toxic and Thunder Wave before
Rapid Spin, then hit Rapid Spin and Snorlax Double-Edge on turn 9.

Lesson:
Spinner handoff is not always immediate Spin. Sometimes the spinner's first
job is to status the incoming pressure piece, then remove Spikes.

### Turns 10-14 - Hidden Role Errors

Public shape:
p1 Snorlax revealed Belly Drum as Tyranitar entered. Tyranitar forced a
Quagsire handoff with Pursuit, then p1 used Miltank into Cloyster and revealed
Thunder.

Frozen answer quality:
I called ordinary Curse rather than Belly Drum, then assumed unrevealed
coverage into Tyranitar. I also assumed Miltank was a cleric by role when the
actual route was Thunder into Cloyster.

Lesson:
Do not import the standard role when a move reveal or odd voluntary entry is
more important. Belly Drum Snorlax and Thunder Miltank both changed the board.

### Turns 15-17 - Ghost And Grass Receiver Map

Public shape:
Cloyster at 7% handed off to Gengar as Miltank used Thunder. Miltank then
handed to Quagsire on Gengar's Ice Punch. Quagsire drew Exeggutor while p1
handed back to sleeping Zapdos.

Frozen answer quality:
I hit Thunder into the Gengar receiver and hit Quagsire on Gengar, but missed
the Gengar handoff itself and then missed Exeggutor as the Quagsire receiver.

Lesson:
Active pressure into a receiver is only clean when I first name that receiver.
The Gengar turn was good for p1, but bad for my branch map because I expected
Explosion instead of the Ghost handoff.

### Turns 18-22 - RestTalk Handoff Re-Scored

Public shape:
RestTalk Zapdos faced Exeggutor, then p2 Snorlax. p1 handed to Skarmory for
the Snorlax branch, then later returned Zapdos and woke into Thunder as Snorlax
Rested.

Frozen answer quality:
I hit Sleep Talk on turn 18 and found the Snorlax-answer handoff by class on
turn 19. I then missed Skarmory's active Drill Peck pressure, missed Zapdos
returning on turn 21, and made a wake-count state error on turn 22.

Lesson:
The RestTalk policy improved but is still noisy. I no longer always force the
sleeping piece out, but I need exact wake-count tracking and exact branch owner
identity.

## Error Classes Found

- RestTalk overcorrection: rejected staying before a public teammate owned the
  branch, then later missed the wake turn.
- Electric receiver identity still weak: Snorlax, Miltank, Zapdos, and
  Exeggutor handoffs were all missed or only found by class.
- Hidden-role import: assumed Belly Drum Snorlax had unshown Earthquake and
  assumed Miltank had Heal Bell.
- Active pressure into receiver improved: Thunder Miltank into Gengar was a
  correct active pressure case even though I missed the receiver.

## Next Rep

Run a short correction probe before the next fresh replay:

1. RestTalk revealed and no better branch-owner public: stay.
2. RestTalk revealed but Snorlax or Electric branch has a known owner: switch.
3. Odd voluntary support entry with hidden-role possibility: price lure or
   off-standard move before assigning the standard role.
4. Active pressure into a receiver: only count it cleanly if the receiver is
   named before the move.
