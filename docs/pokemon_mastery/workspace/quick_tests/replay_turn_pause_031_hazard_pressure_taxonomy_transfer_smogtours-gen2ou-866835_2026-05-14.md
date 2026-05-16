# Replay Turn-Pause 031 Hazard Pressure Taxonomy Transfer - smogtours-gen2ou-866835 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-866835`.

Tournament source: Smogon GSC Cup XI Quarterfinals,
`https://www.smogon.com/forums/threads/gsc-cup-xi-quarterfinals.3770008/`.

Mode: spectator public, semi-blind broad-count candidate-screened.

Purpose: fresh transfer check after
`hazard_pressure_move_taxonomy_probe_001`: on hazard-control turns, classify
the pressure move as direct damage, setup, Rest, phaze, sacrifice, or spinblock
before choosing Rapid Spin or a Ghost switch.

Contamination control:

- The replay ID was not referenced in local Pokemon mastery docs before this
  run.
- Candidate screening checked only broad counts across unused raw logs:
  Spikes, Rapid Spin, Gengar, Misdreavus, Starmie, Forretress, Cloyster,
  Donphan, Golem, Growth, Roar, Whirlwind, Explosion, Curse, Rest, and Toxic.
  The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Because the broad count screen exposed some species names, this is not a
  sealed exam. It is a semi-blind replay transfer run.
- The raw log was revealed one turn at a time with
  `tools/pokemon_mastery/replay_turn_pause.py`; answers were frozen before
  each reveal.
- The initial public switch lines before turn 1 were inspected because the
  helper currently omits species names for nicknamed active Pokemon. No future
  turn events were inspected that way.

Local docs checked:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/boss_turn_advice_template.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cross_domain_autonomy_policy.md`
- `docs/pokemon_mastery/study_roadmap_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/hazard_pressure_move_taxonomy_probe_001_2026-05-14.md`

Web sources checked:

- Smogon GSC Cup XI Quarterfinals:
  `https://www.smogon.com/forums/threads/gsc-cup-xi-quarterfinals.3770008/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Resources hub:
  `https://www.smogon.com/resources/competitive/gs/`

Source note: this replay was a useful transfer target because the early game
created both Spikes, Starmie, Cloyster, Misdreavus, Blissey, Skarmory, and
Steelix route pressure without Team Preview. The GSC Spikes article remains
the policy anchor: Spikes matter when they force movement and conversion, not
as a checkbox by themselves.

## Score Summary

Turns scored: 1-25.

Decisions scored: 50 side-decisions.

Top-match: 25 / 50.

Acceptable-match: 32 / 50.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0, with the caveat that broad candidate screening made
this only semi-blind.

Earliest meaningful error: turn 1 p2.

Earliest target-skill error: turn 10 p1.

Largest hazard-taxonomy errors: turn 11 p1 and turn 25 p1.

## Turn Notes

### Turn 1

Public state: p1 Cloyster vs p2 Snorlax lead.

Frozen answers: p1 Spikes; p2 use sleep or direct pressure if available.

Actual: p2 switched Cloyster; p1 used Spikes.

Grade: p1 top, p2 miss. I underweighted immediate support mirror against lead
Cloyster.

### Turn 2

Frozen answers: p1 Toxic opposing Cloyster; p2 Spikes.

Actual: p2 Spikes; p1 Toxic.

Grade: both top.

### Turn 3

Frozen answers: p1 Surf/direct pressure; p2 Toxic.

Actual: p1 switched Zapdos into p2 Toxic.

Grade: p1 acceptable, p2 top. Surf and Zapdos both pressure the poisoned
support piece, but the actual line handed off immediately to a stronger
pressure piece.

### Turn 4

Frozen answers: p1 Thunder; p2 switch to a special sponge.

Actual: p2 switched Blissey; p1 Thunder hit and paralyzed.

Grade: p1 top, p2 acceptable.

### Turn 5

Frozen answers: p1 switch Snorlax; p2 Heal Bell.

Actual: p1 switched Snorlax; p2 Heal Bell.

Grade: both top.

### Turn 6

Frozen answers: p1 Curse; p2 switch to a physical answer or phazer.

Actual: p2 switched Skarmory; p1 Curse.

Grade: p1 top, p2 acceptable.

### Turn 7

Frozen answers: p1 switch Zapdos; p2 Whirlwind or Toxic to punish the pivot.

Actual: p1 switched Zapdos; p2 Toxic failed into the already poisoned Zapdos.

Grade: p1 top, p2 acceptable.

### Turn 8

Frozen answers: p1 Thunder; p2 Blissey.

Actual: p2 switched Blissey; p1 Thunder missed.

Grade: both top.

### Turn 9

Frozen answers: p1 switch Snorlax; p2 Soft-Boiled.

Actual: p1 switched Snorlax; p2 Ice Beam.

Grade: p1 top, p2 miss. I overcalled recovery and undercalled chip into the
incoming physical pressure.

### Turn 10

Frozen answers: p1 Curse; p2 switch Skarmory.

Actual: p2 switched Skarmory; p1 switched Starmie.

Grade: p1 miss, p2 top. First target-skill miss: Starmie was the pressure and
hazard-control handoff into the expected Skarmory, while I stayed on the
Snorlax setup script.

### Turn 11

Public state: p1 Starmie vs p2 Skarmory, Spikes on p1's side.

Frozen answers: p1 Rapid Spin; p2 Toxic.

Actual: p1 Thunder; p2 Toxic.

Grade: p1 miss, p2 top. Largest early taxonomy miss: I defaulted to clearing
Spikes when direct damage was the pressure move. Thunder made Skarmory too low
to keep freely absorbing Snorlax or Starmie sequences.

### Turn 12

Frozen answers: p1 Thunder/direct damage; p2 switch Blissey.

Actual: p2 switched Misdreavus; p1 Surf.

Grade: p1 acceptable, p2 miss. I kept the direct-damage class but missed the
spinblocker branch and the value of Surf covering Misdreavus.

### Turn 13

Frozen answers: p1 continue attacking Misdreavus; p2 punish with its Ghost.

Actual: p1 switched Steelix; p2 switched Snorlax.

Grade: both miss. I failed to see the mutual route reset after Misdreavus had
done its spinblocker job and Starmie had become a poisoned resource.

### Turn 14

Frozen answers: p1 Roar; p2 switch Cloyster.

Actual: p2 switched Cloyster; p1 Roar dragged Snorlax through Spikes.

Grade: both top. Phaze was the hazard-conversion move.

### Turn 15

Frozen answers: p1 Roar; p2 switch to a support answer.

Actual: p2 switched Skarmory; p1 Roar dragged Cloyster through Spikes.

Grade: p1 top, p2 acceptable. Continued phazing converted the layer before
the opponent regained full control.

### Turn 16

Frozen answers: p1 switch Starmie; p2 Surf.

Actual: p1 switched Zapdos; p2 Rapid Spin cleared its own side.

Grade: p1 acceptable, p2 miss. I missed clean Spin from the opposing Cloyster
after Steelix forced it active.

### Turn 17

Frozen answers: p1 Thunder; p2 Blissey.

Actual: p2 switched Blissey; p1 Thunder.

Grade: both top.

### Turn 18

Frozen answers: p1 switch Snorlax; p2 Soft-Boiled.

Actual: p1 switched Snorlax; p2 Soft-Boiled.

Grade: both top.

### Turn 19

Frozen answers: p1 switch Starmie as the anti-Skarm hazard-control handoff;
p2 switch Skarmory.

Actual: p1 Curse; p2 switched Misdreavus.

Grade: both miss. I overfit turn 10 and failed to re-solve after Misdreavus was
revealed as the Snorlax-control branch.

### Turn 20

Frozen answers: p1 attack Misdreavus if coverage exists; p2 use Ghost control.

Actual: p2 switched Skarmory; p1 Curse again.

Grade: both miss. I overcalled immediate coverage and undercalled using Curse
to force the Skarmory response.

### Turn 21

Frozen answers: p1 Fire Blast if available, otherwise pressure Skarmory with
the best attack; p2 phaze or recover.

Actual: p1 switched Cloyster; p2 Toxic.

Grade: both miss. The route was not "attack the Skarmory"; it was re-enter
Cloyster to reestablish support while Skarmory was low.

### Turn 22

Frozen answers: p1 Spikes; p2 switch Cloyster.

Actual: p2 switched Cloyster; p1 Spikes.

Grade: both top. This was the support reset that turn 21 enabled.

### Turn 23

Frozen answers: p1 Toxic the spinner; p2 Rapid Spin.

Actual: p1 Toxic; p2 Rapid Spin.

Grade: both top. Statusing the spinner did not prevent Spin, but it converted
future Cloyster entries into a clock.

### Turn 24

Frozen answers: p1 Spikes again; p2 switch Blissey to Heal Bell later.

Actual: p1 switched Zapdos; p2 Surf crit and KOed Zapdos.

Grade: both miss. The actual line used a damaged Zapdos as direct pressure or
tempo material into the spinner; the crit made the cost look worse, but the
pre-reveal branch still existed.

### Turn 25

Public state: p1 poisoned Starmie vs p2 poisoned Cloyster; Spikes on p1's side;
p2 Misdreavus and Blissey revealed.

Frozen answers: p1 Thunder/direct damage; p2 Misdreavus to block Spin.

Actual: p2 switched Blissey; p1 Rapid Spin cleared p1's Spikes.

Grade: both miss. This is the overcorrection boundary. After turns 11-12
punished premature Spin with direct damage, I overweighted the Ghost branch and
missed the clean Spin into Blissey.

## Error Classes

1. Support handoff timing: missed p1 Starmie on turn 10 and p1 Cloyster on
   turn 21 because I stayed with the active setup/attack script.
2. Spin/direct-damage boundary: missed Thunder over Rapid Spin on turn 11,
   then missed clean Rapid Spin over Thunder on turn 25.
3. Revealed-Ghost branch pricing: after Misdreavus appeared, I sometimes priced
   it as automatic spinblocker pressure instead of asking whether Blissey or
   another support answer was more likely this exact turn.
4. Skarmory status move pricing: I undercalled Toxic from Skarmory and treated
   it too often as a pure phazer or Rest piece.

## Reusable Lesson

The six-class taxonomy is a re-solve prompt, not an anti-Spin rule.

On each hazard-control turn:

1. Ask whether direct damage makes the spinner, phazer, or spinblocker unable
   to keep answering the route.
2. Ask whether setup, phaze, status, Rest, or sacrifice converts before hazard
   removal matters.
3. Ask whether Rapid Spin is clean now because the spinblocker is pressured,
   out of position, or less likely than a support pivot.
4. Do not carry the previous turn's answer forward. A turn-11 Thunder lesson
   can become a turn-25 Rapid Spin miss if it hardens into bias.

## Next Study Target

Construct or run a short spin-vs-damage boundary probe with Starmie and
Cloyster positions:

- direct damage into a phazer or spinblocker is correct;
- clean Rapid Spin into Blissey or another non-Ghost is correct;
- statusing the spinner is correct even though Spin still resolves;
- a Ghost switch is correct only when it actually enters the Spin turn and
  the active pressure line is weaker.
