# Replay Turn-Pause 010 PTA-057 Regression - smogtours-gen2ou-928703 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-928703`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 12 [REPLAYS Required]`.

Mode: spectator public.

Purpose: regression test for the narrower lesson from
`replay_turn_pause_009_pta057_cashout_handoff`: after a support Pokemon has
already delivered one support action and still has Explosion, re-rank preserve
and handoff before declaring the one-time trade forced.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_009_pta057_cashout_handoff_smogtours-gen2ou-928699_2026-05-14.md`

Web sources checked:

- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-12-replays-required.3781144/latest`
- `https://replay.pokemonshowdown.com/smogtours-gen2ou-928703`
- `https://pokemonshowdown.com/pages/ladderhelp`

Source note: this kept the run on a current standard Gen 2 OU tournament game.
Pokemon Showdown's ladder help was checked again only to keep "1500 Elo" framed
as a proxy for measured decision improvement rather than a completion proof.

Contamination control:

- Local docs were searched for `928703`; the only prior hit was the previous
  contamination-control note saying no prior review existed.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-20 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Turn 12 p1 and turn 20 p2 were excluded because the chosen move was not
  logged after sleep prevented action.

## Score Summary

Turns: 1-20.

Decisions scored: 38 side-decisions.

Top-match: 10 / 38.

Acceptable-match: 18 / 38.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Targeted result: partial improvement. I did not call immediate Explosion in
the two main support-cash-out spots: Forretress after Spikes on turns 7-8 and
Exeggutor into Skarmory on turn 19. The miss changed shape: I over-ranked
Rapid Spin or generic attack when the actual expert route used Spikes,
handoff, phazing, and repeated switch preservation.

## Turn 1

Public state: p1 Cloyster 100% vs p2 Exeggutor 100%.

My answer: p1 Ice Beam or switch to Snorlax; p2 Sleep Powder.

Actual choices: p1 Spikes; p2 Thief.

Grade: both miss.

Reusable lesson: lead Cloyster can take the immediate support turn even into
Exeggutor, and Exeggutor may open by stealing the support piece's item instead
of forcing sleep.

## Turn 2

Public state: p1 Cloyster 81% with Spikes set vs p2 Exeggutor 100% with Thief;
p2 side has Spikes.

My answer: p1 Ice Beam, with Snorlax switch as the preserve alternative; p2
Sleep Powder.

Actual choices: both switched Snorlax; p2 Snorlax took Spikes.

Grade: p1 acceptable, p2 miss.

Reusable lesson: once Spikes are down, both sides can hand off to the anchor
instead of continuing the lead support exchange.

## Turn 3

Public state: p1 Snorlax 100% vs p2 Snorlax 94%; p2 side has Spikes.

My answer: both Curse.

Actual choices: p1 Double-Edge; p2 switched Forretress.

Grade: both miss.

Reusable lesson: I defaulted to mirror setup and missed both direct pressure
and the normal-resist support handoff.

## Turn 4

Public state: p1 Snorlax 100% with Double-Edge vs p2 Forretress 78%; p2 side
has Spikes.

My answer: p1 coverage attack; p2 Rapid Spin.

Actual choices: p1 Double-Edge; p2 switched Zapdos.

Grade: p1 acceptable, p2 miss.

Reusable lesson: Forretress did not have to spend the support turn immediately;
it could preserve itself and use Zapdos as a recurring pressure handoff.

## Turn 5

Public state: p1 Snorlax 99% vs p2 Zapdos 65%; p2 side has Spikes.

My answer: p1 Double-Edge; p2 Thunder.

Actual choices: p2 Thunder; p1 Double-Edge.

Grade: both top-match.

Reusable lesson: the direct exchange was correct once Zapdos had been handed
in and Snorlax could put it near forced-preserve range.

## Turn 6

Public state: p1 Snorlax 66% vs p2 Zapdos 24%; p2 side has Spikes.

My answer: p1 Double-Edge; p2 switch Forretress or another Normal resist.

Actual choices: p2 switched Forretress; p1 Double-Edge.

Grade: both top-match.

Reusable lesson: low Zapdos was preserved as a later converter or sack while
Forretress re-entered as the compression piece.

## Turn 7

Public state: p1 Snorlax 69% vs p2 Forretress 55%; p2 side has Spikes.

My answer: p1 keep attacking unless a spinblocker is available; p2 Rapid Spin.

Actual choices: p1 switched Jolteon; p2 Spikes.

Grade: both miss.

Reusable lesson: this was the key support-action error. I correctly avoided
Explosion, but overcorrected into Rapid Spin. The actual support priority was
reciprocal Spikes before clearing.

## Turn 8

Public state: p1 Jolteon 100% vs p2 Forretress 61%; both sides have Spikes.

My answer: p1 setup or pressure Forretress; p2 Rapid Spin, with Explosion only
if Jolteon is the actual route blocker.

Actual choices: p1 Substitute; p2 switched Snorlax.

Grade: p1 acceptable, p2 miss.

Reusable lesson: after Forretress delivered Spikes, the actual route was a
Snorlax handoff rather than Explosion or immediate Spin.

## Turn 9

Public state: p1 Jolteon 82% behind a recently made Substitute vs p2 Snorlax
88%; both sides have Spikes.

My answer: p1 Baton Pass if available; p2 attack to break the Substitute.

Actual choices: p1 Thunderbolt; p2 Double-Edge.

Grade: p1 miss, p2 top-match.

Reusable lesson: I over-assumed Baton Pass as the route after Substitute.
Jolteon first used the free turn for damage.

## Turn 10

Public state: p1 Jolteon 88% with Substitute and Thunderbolt revealed vs p2
Snorlax 73%; both sides have Spikes.

My answer: p1 Thunderbolt; p2 Double-Edge.

Actual choices: p1 switched Misdreavus; p2 Double-Edge failed.

Grade: p1 miss, p2 top-match.

Reusable lesson: I missed the revealed route of converting Snorlax's locked
Normal pressure into a spinblocker/immune switch.

## Turn 11

Public state: p1 Misdreavus 94% vs p2 Snorlax 79%; both sides have Spikes.

My answer: p1 Mean Look, with Thunder as the switch-punish alternative; p2
switch Exeggutor or another route answer.

Actual choices: p2 switched Gengar; p1 Thunder missed.

Grade: both acceptable.

Reusable lesson: the class was right: p1 attacked the route answer instead of
blindly trapping, and p2 used a Ghost answer rather than staying Snorlax.

## Turn 12

Public state: p1 Misdreavus 100% with Thunder vs p2 Gengar 94%; both sides
have Spikes.

My answer: p1 Thunder; p2 Thunder, with Hypnosis as the status alternative.

Actual choices: p2 Hypnosis; p1 was put to sleep before acting.

Grade: p1 unscored, p2 acceptable.

Reusable lesson: Gengar valued status over damage in the Ghost mirror.

## Turn 13

Public state: p1 sleeping Misdreavus 100% vs p2 Gengar 100%; both sides have
Spikes.

My answer: p1 stay and burn sleep; p2 Thunder.

Actual choices: p2 switched Tyranitar; p1 woke and used Thunder.

Grade: p1 top-match, p2 miss.

Reusable lesson: staying with Misdreavus avoided the obvious switch-into-boom
or switch-into-Pursuit punish, but I missed Tyranitar as the p2 handoff.

## Turn 14

Public state: p1 Misdreavus 100% vs p2 Tyranitar 73%; both sides have Spikes.

My answer: p1 switch Snorlax; p2 Pursuit or Crunch.

Actual choices: p2 switched Gengar; p1 Hypnosis missed.

Grade: both miss.

Reusable lesson: I over-respected Tyranitar as a stay-in trapper and missed
the Ghost re-entry sequence.

## Turn 15

Public state: p1 Misdreavus 100% with Hypnosis, Thunder vs p2 Gengar 94% with
Hypnosis; both sides have Spikes.

My answer: p1 switch Snorlax to absorb status; p2 Hypnosis.

Actual choices: p2 switched Snorlax; p1 Psychic.

Grade: both miss.

Reusable lesson: Misdreavus had Psychic as a direct punish for switch routes;
I stayed too locked onto the sleep exchange.

## Turn 16

Public state: p1 Misdreavus 100% with Hypnosis, Psychic, Thunder vs p2 Snorlax
60%; both sides have Spikes.

My answer: p1 Hypnosis; p2 switch Tyranitar.

Actual choices: p1 switched Donphan; p2 Rest.

Grade: both miss.

Reusable lesson: the actual p1 route was to introduce spinner pressure as
Snorlax reset, not keep chasing sleep with Misdreavus.

## Turn 17

Public state: p1 Donphan 94% vs p2 Resting Snorlax 100%; both sides have
Spikes.

My answer: p1 Rapid Spin; p2 switch Gengar to block Spin.

Actual choices: p2 switched Exeggutor; p1 Rapid Spin cleared p1's Spikes.

Grade: p1 top-match, p2 miss.

Reusable lesson: p1 correctly used the sleep-reset window to remove Spikes.
The p2 side accepted Spin and used Exeggutor as the next pressure handoff.

## Turn 18

Public state: p1 Donphan 99% vs p2 Exeggutor 85%; p1 side clear, p2 side
Spikes.

My answer: p1 switch to preserve Donphan; p2 Psychic or Giga Drain.

Actual choices: p1 switched Skarmory; p2 Psychic crit.

Grade: p1 acceptable, p2 top-match.

Reusable lesson: Donphan's spinner job remained material after Spin, so the
correct class was preservation into a resist.

## Turn 19

Public state: p1 Skarmory 60% vs p2 Exeggutor 91%; p1 side clear, p2 side
Spikes.

My answer: p1 Drill Peck; p2 hand off to Zapdos, Tyranitar, or another Skarmory
pressure route before Explosion.

Actual choices: p2 switched Zapdos; p1 Whirlwind dragged Snorlax.

Grade: p1 miss, p2 top-match.

Reusable lesson: this was the second PTA-057 success. I avoided overcalling
Exeggutor Explosion and correctly preferred a handoff, but I missed Skarmory's
hazard-phazing route.

## Turn 20

Public state: p1 Skarmory 66% with Whirlwind vs p2 sleeping Snorlax 94%; p1
side clear, p2 side Spikes.

My answer: p1 Whirlwind; p2 switch to avoid more hazard phazing.

Actual choices: p1 Drill Peck; p2 stayed asleep.

Grade: p1 miss, p2 unscored.

Reusable lesson: Skarmory did not have to phaze every turn; direct chip into a
sleeping Snorlax was the simpler progress move.

## Error Classes

- Support-action overcorrection: no Explosion overcall this run, but I treated
  "do not boom" as "Spin first" and missed Forretress using Spikes first.
- Handoff underpricing: turns 4, 8, 13, 15, and 17 missed or misnamed the
  recurring teammate that entered next.
- Revealed-role underuse: turns 10 and 16 missed p1's ability to convert
  revealed Normal pressure into Misdreavus, then Misdreavus pressure into
  Donphan.
- Phaze-versus-chip sequencing: turns 19 and 20 misread when Skarmory should
  Whirlwind and when it should simply attack.

## Next Study Target

Run a short support-choice drill, not another Explosion-only drill:

```text
Support compression after a support Pokemon enters:
1. What support action changes a route now?
2. What handoff becomes better after that support?
3. Is Rapid Spin urgent, or can Spikes/status/phazing/handoff happen first?
4. Is Explosion actually removing the current route blocker, or only feeling
   decisive?
```
