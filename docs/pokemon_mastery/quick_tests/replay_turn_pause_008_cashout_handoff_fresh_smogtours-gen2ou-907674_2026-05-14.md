# Replay Turn-Pause 008 Cash-Out Or Handoff - smogtours-gen2ou-907674 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-907674`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 2`.

Mode: spectator public.

Purpose: fresh replay rep for the active 1500-Elo learning goal, targeted at
the previous miss in `replay_turn_pause_007_electric_handoff_overcorrection`:
when Explosion or Self-Destruct is plausible, decide whether the support piece
should cash out now or hand off to a recurring teammate.

Local docs checked:

- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_007_electric_handoff_overcorrection_smogtours-gen2ou-907668_2026-05-14.md`

Web sources checked:

- `https://www.smogon.com/gs/articles/guide_to_explosion`
- `https://www.smogon.com/gs/articles/gsc_threats`
- `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the web check reinforced that Explosion is a route trade, not a
default action, and that Raikou/Zapdos pressure plus Snorlax/Golem/Steelix-style
handoffs are central GSC route material.

Contamination control:

- Local docs were searched for `907674`; no prior reference was found.
- The raw log was downloaded to `.local/pokemon_mastery/replay_logs/`.
- The header check exposed only the lead matchup, which is part of the turn-1
  public prompt.
- Turns 1-8 were answered before each reveal using
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 1-8.

Decisions scored: 16 side-decisions.

Top-match: 6 / 16.

Acceptable-match: 9 / 16.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 2.

Targeted improvement: the run confirmed the previous error class. I saw the
general need to stop Snorlax and preserve support pieces, but I twice reached
too quickly for Explosion. The actual game used status, phazing, and handoffs:
Cloyster used Toxic instead of booming, Golem used Roar instead of booming, and
low Golem handed to Zapdos rather than cashing out into Exeggutor.

## Turn 1

Public state: p1 Snorlax 100% lead vs p2 Cloyster 100% lead.

My answer: p1 attack with Body Slam or the strongest Normal move to punish the
Spikes turn; p2 Spikes.

Actual choices: p2 Spikes; p1 Curse.

Grade: p1 acceptable, p2 top-match. Direct damage was defensible, but the
player chose to treat lead Cloyster as a setup window.

Reusable lesson: against lead Cloyster, Snorlax may take the Spikes turn as
setup if it has a plan for Toxic, Explosion, or later phazing.

## Turn 2

Public state: p1 +1 Snorlax at 100% vs p2 Cloyster 100%; p1 side has Spikes.

My answer: p1 attack now; p2 Explosion or other immediate anti-setup cash-out.

Actual choices: p2 Toxic; p1 Curse.

Grade: both miss. I overcalled the one-time trade and undercalled Toxic as the
route stopper.

Reusable lesson: if the setup threat is not immediately lethal and status will
put it on a timer, the support move can be better than cashing out.

## Turn 3

Public state: p1 +2 toxic Snorlax at 100% vs p2 Cloyster 100%; p1 side has
Spikes.

My answer: p1 attack now; p2 Explosion to stop the boosted Snorlax.

Actual choices: p2 switched Golem; p1 used Curse.

Grade: both miss. The actual answer was handoff to a normal-resist phazer,
not the support cash-out.

Reusable lesson: after Toxic lands, the next anti-setup step can be a handoff
to phazing or resistance instead of a self-KO.

## Turn 4

Public state: p1 +3 toxic Snorlax at 94% vs p2 Golem 100%.

My answer: p1 Earthquake or best attack; p2 Roar to remove boosts.

Actual choices: p1 Earthquake; p2 Roar dragged Exeggutor.

Grade: both top-match.

Reusable lesson: once the normal-resist phazer is in, spend the phazing turn
before considering Explosion. Roar preserved Golem's one-time trade while
resetting the immediate Snorlax route.

## Turn 5

Public state: p1 Exeggutor 94% vs p2 Golem 16%; p1 side has Spikes.

My answer: p1 Sleep Powder if available; p2 Explosion or a sleep-absorber
handoff.

Actual choices: p2 switched Zapdos; p1 Psychic.

Grade: both miss. I was still too focused on boom/sleep branches. The player
used low Golem's preserved existence to hand off to Zapdos, and p1 took direct
Psychic damage rather than gambling sleep immediately.

Reusable lesson: a nearly spent Golem can still be worth preserving if a
recurring Electric route enters cleanly and Golem's Explosion/Roar remains
available later.

## Turn 6

Public state: p1 Exeggutor 99% with Psychic revealed vs p2 Zapdos 74%.

My answer: p1 Sleep Powder if available, with switch to an Electric/special
wall as the main alternative; p2 Hidden Power or Thunder.

Actual choices: p1 switched Raikou; p2 Hidden Power.

Grade: p1 acceptable, p2 top-match. I named the special-wall switch but still
ranked sleep first.

Reusable lesson: when the opponent's Electric enters after the phaze sequence,
preserving Exeggutor and going to the Electric answer can be cleaner than
trying to force the next status immediately.

## Turn 7

Public state: p1 Raikou 76% vs p2 Zapdos 80%; p1 side has Spikes.

My answer: p1 Thunder or direct attack; p2 switch to a special sponge or
Electric answer.

Actual choices: p1 Thunder; p2 switched Raikou.

Grade: p1 top-match, p2 acceptable. The exact switch was Raikou rather than
Snorlax or Golem, but the class was right: hand off to a recurring special
answer instead of keeping Zapdos in.

Reusable lesson: Electric mirrors often start as route-preserving handoffs,
not attempts to win the current one-on-one immediately.

## Turn 8

Public state: p1 Raikou 82% vs p2 Raikou 87%; p1 side has Spikes.

My answer: p1 switch to Snorlax despite its Toxic timer; p2 Thunder.

Actual choices: both Raikou used Thunder; p2 Raikou was paralyzed.

Grade: p1 miss, p2 top-match. I over-respected the mirror and missed the value
of fishing damage/status before exposing the already-toxic Snorlax to Spikes.

Reusable lesson: if the backup special sponge is toxic and hazard-taxed, the
active Electric may need to fight the mirror long enough to create status or
damage before handing off.

## Error Classes

- Explosion overcall: turns 2 and 3 repeated the prior mistake by treating
  Cloyster's anti-setup job as immediate Explosion instead of status plus
  handoff.
- Handoff undervaluation: turn 5 missed that low Golem could preserve Roar or
  Explosion while Zapdos entered to continue the route.
- Resource identity error: turn 8 overvalued switching to a toxic Snorlax and
  undervalued Raikou staying active to fish damage or paralysis.

## Next Study Target

Run a small source-to-policy extraction or drill for this exact rule:

```text
When a support Pokemon can explode, first ask whether status, phazing, or a
handoff to a recurring teammate solves the current route while preserving the
one-time trade.
```

Do not add this to the cookbook yet; this is a repeated observed error, but it
needs one more source-backed compression or drill before becoming canonical.
