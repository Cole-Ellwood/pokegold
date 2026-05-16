# Replay Turn-Pause 078 Branch Counter-Switch Transfer - smogtours-gen2ou-925823 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-925823`.

Context source:
`https://www.smogon.com/forums/threads/adpl-ix-week-4.3780197/page-2`.

Mode: spectator-public vanilla GSC replay turn-pause. No team sheet was
supplied, and no Team Preview was assumed.

Selected measurable action: continue the fresh no-keyword-screen transfer after
`replay_turn_pause_077`, using the updated controlled-spinner checklist if the
board appeared. The selected replay was fresh locally; `rg` found no prior
`925823` use before opening the raw log.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/spinner_removed_hazard_cashout_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon ADPL IX Week 4, page 2.
- Replay source `smogtours-gen2ou-925823`.

Contamination control:

- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was not screened for move or species keywords before selection.
- Turns were revealed only after frozen answers.

## Score Summary

Decisions: 30 side decisions from turns 1-15.

Top-match: 10 / 30.

Acceptable-match: 18 / 30.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest meaningful error: turn 1. I wanted Cloyster to set Spikes into Raikou
while both players switched to Snorlax, showing an early preservation and
counter-switch read that I did not price.

Target error: turns 14 and 15. I named the likely Raikou and Skarmory branches
but still chose active pressure instead of the counter-switch. This is the
known `branch_action_after_naming` failure mode.

Stop reason: the same branch-action error appeared twice in adjacent turns, so
the run stopped under the replay protocol.

## Turn Notes

### Turn 1

Public state: p1 Cloyster 100% vs p2 Raikou 100%.

Frozen answers: p1 Spikes; p2 Thunder. Confidence: medium on p1, medium-high
on p2. Serious alternatives: p1 Snorlax if preserving Cloyster matters more
than the first layer; p2 Snorlax if expecting that switch.

Actual choices: both switched Snorlax.

Grade: p1 acceptable, p2 miss. Lesson: lead Cloyster does not always cash the
first layer; preserving the setter and meeting Electric with Snorlax can be the
opening route.

### Turn 2

Public state: Snorlax mirror.

Frozen answers: both use immediate physical pressure, with Curse and switch as
serious alternatives.

Actual choices: p1 switched Tyranitar; p2 used Curse.

Grade: p1 miss, p2 acceptable. Lesson: the first Snorlax mirror can be about
bringing in the setup answer, not trading damage.

### Turn 3

Public state: p1 Tyranitar vs p2 Snorlax at `atk+1 def+1`.

Frozen answers: p1 Roar if available; p2 attack, with Earthquake or
Double-Edge as the main class.

Actual choices: p1 switched Cloyster; p2 used Double-Edge.

Grade: p1 acceptable, p2 acceptable. Lesson: public own-move uncertainty
matters; if the phaze is not established, the actual route can be a physical
resist instead.

### Turn 4

Public state: p1 Cloyster 56% vs p2 boosted Snorlax 99%.

Frozen answers: p1 Spikes; p2 switch out or continue Double-Edge.

Actual choices: p1 Toxic; p2 Double-Edge.

Grade: p1 miss, p2 acceptable. Lesson: Toxic can be the first job into boosted
Snorlax because it changes the Rest clock before the hazard layer matters.

### Turn 5

Public state: p1 Cloyster 12% vs p2 poisoned boosted Snorlax 92%.

Frozen answers: p1 Spikes before dying; p2 Double-Edge or Rest.

Actual choices: p2 switched Tentacruel; p1 used Explosion, KOing both.

Grade: both miss. Lesson: a low support piece with no future entry may cash
out into the incoming absorber instead of forcing the visible field job.

### Turn 6

Public state: p1 Tyranitar vs p2 Skarmory after double faint.

Frozen answers: p1 switch to a pressure piece; p2 Toxic.

Actual choices: p1 switched Steelix; p2 used Toxic into immunity.

Grade: p1 miss, p2 top. Lesson: the switch was correct, but the exact branch
was Toxic immunity rather than direct special pressure.

### Turn 7

Public state: p1 Steelix vs p2 Skarmory.

Frozen answers: p1 Roar; p2 Whirlwind or direct low-risk utility.

Actual choices: p2 used Sand Attack; p1 used Roar, dragging Heracross.

Grade: p1 top, p2 miss. Lesson: Sand Attack is a real Skarmory utility branch
in this replay and must be treated as revealed set information afterward.

### Turn 8

Public state: p1 Steelix at accuracy-1 vs p2 Heracross.

Frozen answers: p1 Roar to deny setup; p2 switch out.

Actual choices: p1 switched Zapdos; p2 used Seismic Toss.

Grade: p1 acceptable, p2 miss. Lesson: after accuracy is dropped, handoff to
the pressure piece can beat continuing the Steelix phaze loop.

### Turn 9

Public state: p1 Zapdos 80% vs p2 Heracross.

Frozen answers: p1 Thunder; p2 switch Raikou.

Actual choices: p2 switched Raikou; p1 used Thunder and missed.

Grade: both top.

### Turn 10

Public state: p1 Zapdos 86% vs p2 Raikou.

Frozen answers: p1 switch Snorlax; p2 Thunder or Roar.

Actual choices: p1 switched Snorlax; p2 used Hidden Power.

Grade: p1 top, p2 miss. Lesson: Raikou's branch-action into expected Ground or
Steelix entry matters even when Snorlax is the actual receiver.

### Turn 11

Public state: p1 Snorlax 96% vs p2 Raikou.

Frozen answers: p1 Double-Edge; p2 switch Skarmory.

Actual choices: p2 switched Skarmory; p1 used Double-Edge.

Grade: both top.

### Turn 12

Public state: p1 Snorlax 99% vs p2 Skarmory 90%.

Frozen answers: p1 switch Zapdos, with Steelix a serious Toxic-immune
alternative; p2 Toxic.

Actual choices: p1 switched Steelix; p2 used Sand Attack.

Grade: p1 acceptable, p2 miss. Lesson: revealed Sand Attack shifts Skarmory's
utility branch; do not keep treating it as only Toxic.

### Turn 13

Public state: p1 Steelix at accuracy-1 vs p2 Skarmory 96%.

Frozen answers: p1 switch Zapdos; p2 Sand Attack, with Toxic as serious
alternative.

Actual choices: p1 switched Zapdos; p2 used Toxic.

Grade: p1 top, p2 acceptable.

### Turn 14

Public state: p1 poisoned Zapdos 92% vs p2 Skarmory 100%.

Frozen answers: p1 Thunder; p2 switch Raikou.

Actual choices: both switched, p1 to Snorlax and p2 to Raikou.

Grade: p1 miss, p2 top. Lesson: after naming the Raikou switch, p1 needed the
counter-switch, not Thunder into the receiver.

### Turn 15

Public state: p1 Snorlax 100% vs p2 Raikou 100%.

Frozen answers: p1 Double-Edge; p2 switch Skarmory.

Actual choices: both switched, p1 to Steelix and p2 to Skarmory.

Grade: p1 miss, p2 top. Lesson: the error repeated immediately: after naming
Skarmory, p1 again needed the counter-switch instead of active pressure.

## Error Classes

- Branch-action after naming: repeated on turns 14 and 15.
- Low support cash-out timing: missed Cloyster Explosion into the incoming
  Tentacruel on turn 5.
- Status-before-hazard ordering: missed Toxic before Spikes into boosted
  Snorlax on turn 4.
- No severe blunders, mechanics errors, hidden-info errors, or state errors
  were scored.

## Policy Update

This run reinforces `branch_action_after_naming.md`: naming the receiver is not
enough. The answer must choose the action that beats the receiver when that
receiver is the main branch.

## Next Rep

Run a short focused branch-action transfer. Use a fresh replay or early replay
segment, stop at 20-30 side decisions, and score only cases where I explicitly
name a likely receiver, absorber, or switch. The pass condition is at least 80%
acceptable on those named-branch turns with no repeated failure to
counter-switch, cover, phaze, Toxic, or set up into the named branch.
