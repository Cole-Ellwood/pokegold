# Replay Turn-Pause 001 - smogtours-gen2ou-912131 - 2026-05-14

Source: Smogon GSC OU Winter Seasonal #8 Round 4 post linking
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912131`.

Mode: spectator public.

Contamination control:

- Local docs were searched for `912131`; no prior reference was found.
- The raw log was downloaded to `tmp/` and accessed through
  `tools/pokemon_mastery/replay_turn_pause.py`.
- I revealed each turn only after freezing predictions in the chat.
- This is a smoke run for the protocol, not a sealed final exam.

## Score Summary

Decisions scored: 10 side-decisions across turns 1-5.

Top-match: 3 / 10.

Acceptable-match: 6 / 10.

Severe blunders: 0.

State errors: 1.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest meaningful error: turn 2.

Main error class: underpricing early Rest / phazer positioning. I saw the
obvious immediate pressure lines, but missed that p2's paralyzed Snorlax should
prioritize restoring long-game function and that p2 could bring Tyranitar in
before Forretress spent the Spikes turn.

## Turn 1

Public state: Zapdos mirror, no bench revealed.

My p1 answer: Thunder, medium confidence.

My p2 answer: Thunder, medium confidence; switching to an Electric answer if
available was the serious alternative.

Actual choices: p1 Thunder; p2 switched Snorlax. Thunder hit, dealt 30%, and
paralyzed Snorlax.

Grade: p1 top-match. p2 acceptable class but not top-match: Snorlax is a common
Zapdos answer, but the para branch immediately mattered.

Reusable lesson: in lead Electric mirrors, the first switch can be both normal
and very punishable; compare the route after the status branch, not only the
type chart.

## Turn 2

Public state: p1 Zapdos 100% vs p2 Snorlax 76% paralyzed.

My p1 answer: Thunder unless p1 has a clean Snorlax pivot.

My p2 answer: Lovely Kiss if available, otherwise Curse or attack.

Actual choices: p1 switched Golem; p2 used Rest.

Grade: p1 prompt-limited miss, because spectator mode did not reveal Golem
before the turn. p2 miss. Rest was the important role-preservation line for the
paralyzed Snorlax.

Reusable lesson: when a central wall is already statused and chunked, restoring
its long-game role can outrank immediate disruption even before it is in KO
range.

## Turn 3

Public state: p1 Golem 100% vs p2 Snorlax 100% asleep.

My p1 answer: Earthquake; do not spend Explosion into an easy switch.

My p2 answer: preserve sleeping Snorlax and pivot to a Golem answer.

Actual choices: p1 switched Snorlax; p2 switched Forretress.

Grade: p1 miss; p2 acceptable class. The p1 switch correctly anticipated that
p2 would not leave sleeping Snorlax exposed.

Reusable lesson: after Rest, the active matchup may be less important than who
gets to choose the next support hub.

## Turn 4

Public state: p1 Snorlax 100% vs p2 Forretress 100%.

My p1 answer: Fire Blast if available; otherwise Curse.

My p2 answer: Spikes.

Actual choices: p1 Curse; p2 switched Tyranitar.

Grade: p1 acceptable conditional match. p2 miss. p2 prioritized a phazer/Normal
resist before spending Forretress's support turn.

Reusable lesson: Spikes is not automatic when the active threat can begin a
setup route; bring the route-stopper first if one bad support turn lets the
opponent own the board.

## Turn 5

Public state: p1 Snorlax 100% at +1 Attack / +1 Defense vs p2 Tyranitar 100%.

My p1 answer: Earthquake if Snorlax has it.

My p2 answer: Roar if Tyranitar has it.

Actual choices: p1 Earthquake; p2 Roar. Tyranitar took heavy damage and phazed
Snorlax out to Zapdos.

Grade: both top-match.

Reusable lesson: the phazer can take heavy damage if it resets a setup route;
that trade is coherent when the alternative is letting boosted Snorlax continue
claiming turns.

## Segment 2 Score Summary

Turns: 6-15.

Decisions scored: 20 side-decisions.

Top-match: 11 / 20.

Acceptable-match: 14 / 20.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest meaningful error: turn 6.

Main error class: I still overvalue direct active matchup pressure over the
support-map switch. The strong-player lines repeatedly used switches to choose
which support or control piece would own the next exchange: Golem into Snorlax,
Cloyster into Forretress, Starmie into hazards, and Zapdos into Cloyster after
Marowak forced Zapdos out.

Mode limitation: on turn 14, p2's Marowak switch was an excellent own-team
answer to Thunder, but spectator-public mode had not revealed Marowak. That is
not a hidden-information error for player-side advice; it is a reminder that
side-known reconstructed mode is better when the goal is to match a player's
actual turn.

## Turn 6

Public state: p1 Zapdos 100% vs p2 Tyranitar 43%. No hazards on p1 side; p2
has no active Spikes after the earlier phaze sequence.

My p1 answer: Thunder.

My p2 answer: preserve Tyranitar, likely by switching Snorlax or Zapdos.

Actual choices: p1 switched Golem; p2 switched Snorlax.

Grade: p1 miss, p2 top-match. My Thunder would have damaged the incoming
Snorlax, but p1's Golem switch better contested the next Snorlax/Forretress
support sequence.

Reusable lesson: after a phazer has taken the necessary damage, the opponent
may try to win the next support exchange instead of immediately cashing damage.

## Turn 7

Public state: p1 Golem 100% vs p2 Snorlax 100% asleep.

My p1 answer: switch Snorlax to meet the expected Forretress/support pivot.

My p2 answer: switch Forretress.

Actual choices: p1 switched Cloyster; p2 switched Forretress.

Grade: p1 acceptable but not top-match; p2 top-match. Cloyster was the more
specific support mirror because it could set Spikes and pressure Forretress
with Surf.

Reusable lesson: "meet the support pivot" is not precise enough. Identify
which support piece wins the mirror, not only that a support pivot is coming.

## Turn 8

Public state: p1 Cloyster 100% vs p2 Forretress 100%, no hazards yet.

My p1 answer: Spikes.

My p2 answer: Spikes, with Rapid Spin as the sharper anti-Cloyster line.

Actual choices: p1 Spikes; p2 Toxic.

Grade: p1 top-match; p2 miss. Toxic limited Cloyster's ability to keep owning
the hazard seat.

Reusable lesson: poisoning the opposing setter can be the retention move when
direct removal is delayed or assigned to another teammate.

## Turn 9

Public state: p1 Cloyster 100% badly poisoned vs p2 Forretress 100%; p2 side
has Spikes.

My p1 answer: Surf.

My p2 answer: Rapid Spin if available.

Actual choices: p1 Surf; p2 Spikes.

Grade: p1 top-match; p2 miss. Forretress took heavy Surf damage but created
symmetrical Spikes, setting up Starmie to clear later.

Reusable lesson: a team can split the hazard job: one Pokemon sets or poisons,
another removes. Do not assume the active setter is also the spinner.

## Turn 10

Public state: p1 Cloyster 100% badly poisoned vs p2 Forretress 62%; both sides
have Spikes.

My p1 answer: Surf.

My p2 answer: Rapid Spin if available; Explosion if not.

Actual choices: p1 switched Golem; p2 switched Starmie.

Grade: p1 miss; p2 acceptable route match but not top-match. Starmie was the
real removal piece, and p1 tried to meet it with Golem rather than keep
attacking Forretress.

Reusable lesson: when both sides have hazards, the next switch can be about
who controls the spinner entry, not about the visible setter matchup.

## Turn 11

Public state: p1 Golem 94% vs p2 Starmie 94%; both sides have Spikes.

My p1 answer: switch Zapdos.

My p2 answer: Surf to punish Golem before it can trade or spin.

Actual choices: p1 switched Zapdos; p2 Rapid Spin.

Grade: p1 top-match; p2 miss. Starmie correctly used the forced switch to
remove Spikes immediately.

Reusable lesson: a spinner can take the removal turn when the active opponent
is forced out; the punish does not matter if it cannot happen before the spin.

## Turn 12

Public state: p1 Zapdos 100% vs p2 Starmie 100%; p1 side has Spikes, p2 side
is clear.

My p1 answer: Thunder.

My p2 answer: switch sleeping Snorlax.

Actual choices: p1 Thunder; p2 switched Snorlax. Thunder crit Snorlax to 46%.

Grade: both top-match.

Reusable lesson: after a successful spin, Starmie should leave before it gives
back the route by taking a direct Thunder.

## Turn 13

Public state: p1 Zapdos 100% vs p2 Snorlax 52% asleep.

My p1 answer: Thunder.

My p2 answer: stay if Sleep Talk exists.

Actual choices: p1 Thunder; p2 Sleep Talk into Body Slam.

Grade: both top-match.

Reusable lesson: Sleep Talk can turn a low-tempo Rest cycle back into contact,
but the special wall is still being spent if the damage race continues.

## Turn 14

Public state: p1 Zapdos 76% vs p2 Snorlax 29% asleep.

My p1 answer: Thunder.

My p2 answer: stay and Sleep Talk, or Rest if awake.

Actual choices: p2 switched Marowak; p1 Thunder did nothing.

Grade: p1 top-match; p2 miss under side-known scoring, spectator-public
limitation under this run's mode. The player knew Marowak existed and could use
the Ground immunity to flip the Zapdos pressure.

Reusable lesson: no-Team-Preview advice must separate spectator uncertainty
from player-side own-team knowledge. The boss AI cannot know hidden player
Marowak; the player controlling Marowak can and should use it.

## Turn 15

Public state: p1 Zapdos 82% vs p2 Marowak 100%.

My p1 answer: switch Cloyster.

My p2 answer: Rock Slide.

Actual choices: p1 switched Cloyster; p2 switched Zapdos.

Grade: p1 top-match; p2 miss. p2 predicted the Cloyster answer and reset into
Zapdos instead of taking the obvious attack.

Reusable lesson: after revealing a route-flipping hidden piece, the next best
turn may be the double out of the obvious answer, not the strongest coverage
move into it.

## Next Study Target

Run the same protocol for a longer segment, but pay special attention to:

- when a statused anchor should Rest instead of making immediate progress;
- when a support Pokemon should delay Spikes to route-stop first;
- when a phazer can accept damage because resetting setup is the real job.
- when the active support Pokemon is not the actual future spinner;
- when a hidden own-team answer creates a valid player-side double that
  spectator-public mode cannot infer as certainty.
