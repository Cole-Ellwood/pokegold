# Replay Turn-Pause 004 Branch-Quality Canary - smogtours-gen2ou-917826 - 2026-05-14

Source: Smogon GSC OU Winter Seasonal #8 Round 6 post linking
`https://replay.pokemonshowdown.com/smogtours-gen2ou-917826`.

Mode: spectator public.

Purpose: retest `STP-058` after the previous canary showed that naming branch
categories was not enough. This run specifically checked whether the branch
bundle included status/support roles, preserving the punisher, and double
re-solve after the visible support matchup was priced.

Contamination control:

- Local docs were searched for `917826`; no prior reference was found.
- The raw log was downloaded to `tmp/` and accessed only through
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Each prediction was frozen in chat before reveal.
- The replay helper no-leak unit test was run before the segment.

## Score Summary

Turns: 1-6.

Decisions scored: 12 side-decisions.

Branch-bundle compliance: 6 / 6 turns.

Top-match: 5 / 12.

Acceptable-match: 8 / 12.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Targeted improvement: compared with the previous re-solve canary, I did better
on the support map. I expected the Cloyster mirror to move from Spikes to Toxic
or switching, then correctly identified the Rapid Spin / preserve-spinner
sequence on turns 4-5.

Remaining miss: I still over-called status on turn 1 and missed simple fast
Spikes into a support mirror. On turn 6 I correctly switched p1 Snorlax into
Raikou, but p2 used Hidden Power rather than Thunder, showing that coverage
pressure can be the better active punish once the switch is expected.

## Turn 1

Public state: p1 Snorlax vs p2 Cloyster.

Branch bundle:

- obvious punish: Cloyster Toxic or Explosion into Snorlax;
- route-preserving switch: p1 goes to a Cloyster support answer;
- greed/support: p1 uses Curse or Lovely Kiss while Cloyster sets Spikes.

My answer: p1 Lovely Kiss if available, otherwise Curse; p2 Toxic.

Actual choices: p1 switched Cloyster; p2 Spikes.

Grade: p1 acceptable because the support-answer switch was in the bundle; p2
miss. I overcalled Toxic and underweighted immediate Spikes as the simplest
route start.

Reusable lesson: against lead Snorlax, a Cloyster can choose fast Spikes before
status if the opponent is likely to answer with a support mirror.

## Turn 2

Public state: p1 Cloyster 100% with Spikes on own side vs p2 Cloyster 100%.

Branch bundle:

- obvious punish: mirror Toxic or Explosion;
- route-preserving switch: either side goes to a spinner, Electric, or special
  breaker after hazards;
- greed/support: p1 sets Spikes while p2 uses Toxic to win the support mirror.

My answer: p1 Spikes; p2 Toxic if available, otherwise switch.

Actual choices: p2 Surf; p1 Spikes.

Grade: p1 top-match; p2 miss. Surf was simple chip rather than the status line
I expected.

Reusable lesson: in support mirrors, not every turn has to be a high-leverage
status or trade. Chip can keep the opposing setter in range while both sides
complete basic support.

## Turn 3

Public state: p1 Cloyster 82% vs p2 Cloyster 100%; both sides have Spikes.

Branch bundle:

- obvious punish: p2 Surf or Explosion into p1 Cloyster;
- route-preserving switch: p1 brings Electric or spinner pressure; p2 can do
  the same;
- greed/support: Toxic or Spin if available.

My answer: p1 switch to pressure; p2 Toxic if available, otherwise switch.

Actual choices: p1 Toxic; p2 Surf.

Grade: p1 miss; p2 acceptable. p1 chose status-as-route-stopper after Spikes
were established, poisoning the opposing spinner/setter.

Reusable lesson: the status branch can be delayed until after both sides have
set hazards. Do not treat "missed Toxic turn 1" as "Toxic is no longer the
route."

## Turn 4

Public state: p1 Cloyster 63% vs p2 poisoned Cloyster 100%; both sides have
Spikes.

Branch bundle:

- obvious punish: p2 Surf or Explosion while p1 Cloyster gets worn down;
- route-preserving switch: p1 leaves after winning status advantage; p2
  preserves poisoned Cloyster if it still needs Explosion, spin, or check role;
- greed/support: p1 stays in the mirror, p2 stays too.

My answer: p1 switch to special pressure; p2 switch as well.

Actual choices: p1 switched Zapdos; p2 Rapid Spin, clearing p2's side.

Grade: p1 top-match; p2 acceptable. I correctly left the support mirror, but
the stronger p2 line was immediate Spin before leaving.

Reusable lesson: after being poisoned, the spinner can still take the exact
turn it needs if the opposing active is forced out. Preservation comes after
the removal if the removal is safe now.

## Turn 5

Public state: p1 Zapdos 100% vs p2 poisoned Cloyster 95%; p1 side has Spikes,
p2 side is clear.

Branch bundle:

- obvious punish: Zapdos Thunder into the revealed spinner;
- route-preserving switch: p2 leaves to an Electric absorber or special wall,
  preserving Cloyster's spin/explosion role;
- greed/support: Cloyster stays for Toxic or Explosion.

My answer: p1 Thunder; p2 switch.

Actual choices: p2 switched Raikou; p1 Thunder.

Grade: both top-match.

Reusable lesson: once a spinner has completed the key spin, preserving it from
the obvious electric punish is part of the same route, not a separate
defensive afterthought.

## Turn 6

Public state: p1 Zapdos 100% vs p2 Raikou 86%; p1 side has Spikes, p2 side is
clear.

Branch bundle:

- obvious punish: Raikou Thunder into Zapdos;
- route-preserving switch: p1 goes Snorlax or Ground if known;
- greed/support: Zapdos stays for chip or pressure.

My answer: p1 switch Snorlax; p2 Thunder.

Actual choices: p1 switched Snorlax; p2 Hidden Power.

Grade: p1 top-match; p2 miss. The p2 punish was coverage into the expected
switch, not STAB into the visible active.

Reusable lesson: after the route-preserving switch is obvious, the opponent's
best punish may be coverage into that switch rather than the strongest move
into the current active.

## Next Study Target

Add "coverage into the route-preserving switch" to future branch bundles when
the active matchup makes the switch obvious. Keep practicing support mirrors:
status and spin can be delayed until the exact turn they are safe, not just
used at the first legal opportunity.
