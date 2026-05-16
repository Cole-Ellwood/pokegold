# Replay Turn-Pause 005 Status Route - smogtours-gen2ou-903666 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-903666`.

Mode: spectator public.

Purpose: fresh turn-pause rep after the boss-AI spinner audit, with special
attention to route-preserving switches, hazard retention, and status as a
route-stopper.

Contamination control:

- Local docs were searched for `903666`; no prior reference was found.
- The raw log was downloaded to `.local/pokemon_mastery/replay_logs/`.
- The first download check printed turns 1-2, so turns 1-2 were excluded.
- Turns 3-12 were answered before each reveal using
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 3-12.

Decisions scored: 20 side-decisions.

Top-match: 5 / 20.

Acceptable-match: 12 / 20.

Severe blunders: 1.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 3.

Targeted improvement: the run kept hidden-information discipline and handled
Rest/Sleep Talk timing correctly once revealed. The weak area was still
prioritization: I underweighted route-preserving switches before damage, and I
missed Toxic as the route-stopper into Curse Snorlax because I was too focused
on Spikes/Rapid Spin.

## Turn 3

Public state: p1 Snorlax 100% with Double-Edge revealed, p2 Cloyster 45% with
Spikes revealed; p1 side has Spikes.

My answer: p1 Double-Edge, with Ghost switch as an important Explosion-punish
alternative if available; p2 Explosion.

Actual choices: p1 switched Gengar; p2 switched Steelix.

Grade: p1 acceptable, p2 miss/severe branch. I named the Ghost switch but did
not let it dominate p2's Explosion risk. Explosion into that branch would lose
Cloyster for no value.

Reusable lesson: do not call Explosion automatic after Spikes if the opponent's
route-preserving switch can blank it.

## Turn 4

Public state: p1 Gengar 94% vs p2 Steelix 100%.

My answer: p1 switch out to preserve Gengar; p2 Earthquake.

Actual choices: p1 switched Exeggutor; p2 switched Zapdos.

Grade: p1 acceptable, p2 miss. I got the preservation switch but missed the
double-switch into the expected Ground answer.

Reusable lesson: when the active punishes the current target so clearly that a
switch is likely, the best answer may be moving into the incoming route piece.

## Turn 5

Public state: p1 Exeggutor 94% vs p2 Zapdos 100%.

My answer: p1 switch Snorlax; p2 Thunder, with Hidden Power as a serious
alternative.

Actual choices: p2 Hidden Power; p1 Sleep Powder.

Grade: p1 miss, p2 acceptable. I over-preserved Exeggutor and missed that it
could survive the public punish long enough to create the sleep route.

Reusable lesson: sleep can justify accepting one survivable hit when it changes
the whole local route.

## Turn 6

Public state: p1 Exeggutor 60%, Sleep Powder revealed, vs sleeping p2 Zapdos.

My answer: p1 Psychic/chip, with switch Snorlax as an alternative; p2 switch
out to preserve sleeping Zapdos.

Actual choices: p1 switched Snorlax; p2 switched Tyranitar.

Grade: both acceptable. The important idea was preserving the sleeping Zapdos;
the exact target was not knowable from spectator public.

Reusable lesson: after sleep lands, both sides often reclassify immediately:
the sleeper becomes a preserved resource, and the sleep user may hand off
instead of staying for low-value chip.

## Turn 7

Public state: p1 Snorlax 94% vs p2 Tyranitar 100%; p1 side has Spikes.

My answer: p1 Earthquake if available, otherwise Double-Edge; p2 Rock Slide.

Actual choices: p2 Rock Slide; p1 Earthquake.

Grade: p1 acceptable, p2 top-match.

Reusable lesson: own unrevealed coverage matters to the player but is absent
from spectator-public prompts; score exact move modestly in this mode.

## Turn 8

Public state: p1 Snorlax 44% with Double-Edge/Earthquake revealed vs p2
Tyranitar 70%.

My answer: p1 Rest if available; p2 Rock Slide.

Actual choices: p2 Rock Slide; p1 Rest.

Grade: both top-match.

Reusable lesson: preserve Snorlax before the hazard tax and Rock Slide pressure
turn a central piece into a forced sack.

## Turn 9

Public state: p1 Snorlax asleep at 100%, Sleep Talk not yet revealed, vs p2
Tyranitar 76%.

My answer: p1 Sleep Talk if available; p2 Curse/Roar pressure.

Actual choices: p2 switched Snorlax; p1 Sleep Talk called Double-Edge.

Grade: p1 top-match, p2 miss. Switching to Snorlax preserved Tyranitar from
Sleep Talk Earthquake while still exploiting the sleeping target.

Reusable lesson: against RestTalk Snorlax, the opponent can preserve the
current punish piece before trying to convert the sleep turns.

## Turn 10

Public state: p1 sleeping Snorlax 97% vs p2 Snorlax 68%.

My answer: p1 Sleep Talk; p2 Curse.

Actual choices: p1 switched Forretress; p2 Curse.

Grade: p1 miss, p2 top-match. I missed the dedicated CurseLax answer because I
was still thinking from the sleeping Snorlax's current move options.

Reusable lesson: when the opponent starts a setup route, check for the team's
public or soon-revealed stopper before continuing the old RestTalk script.

## Turn 11

Public state: p1 Forretress 94% vs p2 +1 Snorlax 74%.

My answer: p1 Spikes or Rapid Spin; p2 switch or continue pressure.

Actual choices: p1 Toxic; p2 Double-Edge.

Grade: both miss. Toxic was the route-stopper; I over-prioritized hazard economy
while a setup anchor was still live.

Reusable lesson: status can be more urgent than Spikes or Spin when it stops
the current setup route from becoming permanent.

## Turn 12

Public state: p1 Forretress 75%, Toxic revealed, vs p2 toxic +1 Snorlax 70%;
p1 side has Spikes, p2 side has none.

My answer: p1 Rapid Spin; p2 Rest.

Actual choices: p1 Spikes; p2 Double-Edge.

Grade: p1 acceptable, p2 miss. Rapid Spin was defensible, but the pro line
created reciprocal Spikes while the Toxic clock was already pressuring Snorlax.

Reusable lesson: once status has started the clock, the support Pokemon may set
hazards before spinning if the opponent's current pressure is contained.

## Next Study Target

Do a targeted support-turn drill where the candidate moves are Toxic, Spikes,
Rapid Spin, Explosion, and switching. The key question is not "which support
move is legal?" but "which support move changes the current route before the
opponent's route converts?"
