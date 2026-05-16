# Replay Turn-Pause 009 PTA-057 Follow-Up - smogtours-gen2ou-928699 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-928699`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 12 [REPLAYS Required]`.

Mode: spectator public.

Purpose: fresh Round 12 replay rep for the active 1500-Elo learning proxy,
targeted at `PTA-057: Cash-Out Or Handoff Before Explosion`. The test was
whether the previous lesson changed live predictions around a support Pokemon
with Explosion available.

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
- `docs/pokemon_mastery/paused_turn_atlas.md`

Web sources checked:

- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-12-replays-required.3781144/latest`
- `https://replay.pokemonshowdown.com/smogtours-gen2ou-928699`
- `https://www.smogon.com/forums/forums/gsc/`
- `https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/`
- `https://pokemonshowdown.com/pages/ladderhelp`

Source note: the web check confirmed this was a current standard Gen 2 OU
tournament replay source, while Pokemon Showdown's ladder help keeps the
1500-Elo target framed as a proxy rather than proof of universal skill.

Contamination control:

- Local docs were searched for `928699`, `928703`, and `928706`; no prior
  local reference was found.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-13 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Turn 8 p1 was excluded from scoring because Cloyster fainted before the
  chosen move was logged.

## Score Summary

Turns: 1-13.

Decisions scored: 25 side-decisions.

Top-match: 3 / 25.

Acceptable-match: 12 / 25.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Targeted improvement: partial. On turn 10, Forretress entered against Espeon
with Explosion plausible, and I correctly predicted Spikes before cash-out.
The improvement did not hold on turn 11: after Spikes landed, I jumped to
Explosion into boosted Espeon, while the actual player preserved Forretress and
handed off to Jynx.

## Turn 1

Public state: p1 Zapdos 100% vs p2 Jynx 100%; no moves revealed.

My answer: p1 Thunder; p2 Lovely Kiss, with Ice Beam or Thief as alternatives.

Actual choices: p1 Thunder; p2 switched Rhydon, blocking Thunder.

Grade: p1 top-match, p2 miss.

Reusable lesson: when facing lead Zapdos, the Jynx side can make immediate
progress by handing to a Ground immunity if it has one, not only by clicking
sleep.

## Turn 2

Public state: p1 Zapdos 100% with Thunder revealed vs p2 Rhydon 100%.

My answer: p1 switch to a Water, Grass, or physical answer; p2 Rock Slide.

Actual choices: p1 switched Cloyster; p2 switched Jynx.

Grade: p1 acceptable, p2 miss.

Reusable lesson: after forcing Zapdos out, the Rhydon side may double back to
the sleep/status lead to catch the obvious Water handoff.

## Turn 3

Public state: p1 Cloyster 100% vs p2 Jynx 100%; Jynx has no revealed moves.

My answer: p1 switch to a sleep absorber or RestTalk tank; p2 Lovely Kiss.

Actual choices: p1 switched Snorlax; p2 used Lovely Kiss.

Grade: p1 acceptable, p2 top-match.

Reusable lesson: sleep absorption was the correct route before trying to force
Spikes through a faster Jynx.

## Turn 4

Public state: p1 Snorlax 100% asleep vs p2 Jynx 100% with Lovely Kiss revealed.

My answer: p1 stay and burn sleep or use Sleep Talk if available; p2 Thief,
with Ice Beam or Psychic as alternatives.

Actual choices: p1 switched Zapdos; p2 used Ice Beam, taking Zapdos to 41%.

Grade: p1 miss, p2 acceptable.

Reusable lesson: I undervalued a direct Zapdos pressure line and overvalued
sleep-turn burning before checking what Jynx could punish.

## Turn 5

Public state: p1 Zapdos 41% vs p2 Jynx 100%; Jynx has Ice Beam and Lovely Kiss.

My answer: p1 switch Cloyster to cover Ice Beam and a possible Rhydon pivot;
p2 switch Rhydon to block Thunder.

Actual choices: p1 switched Snorlax; p2 used Ice Beam.

Grade: both acceptable. Snorlax was the sleep-absorber variant of my preserve
line, and Ice Beam was the main stay-in alternative.

Reusable lesson: once sleep clause is active, Jynx can keep using direct Ice
Beam pressure instead of immediately yielding to the Ground handoff.

## Turn 6

Public state: p1 Snorlax 86% asleep vs p2 Jynx 100% with Ice Beam, Lovely Kiss.

My answer: p1 stay and burn sleep; p2 Ice Beam or Thief if known.

Actual choices: p1 switched Espeon; p2 used Thief.

Grade: p1 miss, p2 acceptable.

Reusable lesson: the p1 side had a proactive Espeon route; I kept treating the
sleep absorber as the default local subgame.

## Turn 7

Public state: p1 Espeon 77% vs p2 Jynx 100% with Ice Beam, Lovely Kiss, Thief.

My answer: p1 Growth; p2 switch to a special sponge or continue Ice Beam if no
switch is available.

Actual choices: p1 switched Cloyster; p2 used Ice Beam.

Grade: p1 miss, p2 acceptable.

Reusable lesson: I overvalued early setup from Espeon before proving that the
current Jynx board was the right place to start boosting.

## Turn 8

Public state: p1 Cloyster 92% vs p2 Jynx 100%; sleep clause active.

My answer: p1 Spikes; p2 switch to a Cloyster answer.

Actual choices: p2 used Psychic and crit-KOed Cloyster before p1's move was
logged.

Grade: p1 unscored, p2 miss.

Reusable lesson: Psychic was a real route-stopper into Cloyster, not just a
low-value chip move. The crit decided the turn, but the move choice still
showed that Jynx could attack the support route directly.

## Turn 9

Public state: p1 Snorlax 92% asleep vs p2 Jynx 100%; p1 Cloyster fainted.

My answer: p1 stay and try to wake or Sleep Talk; p2 switch to a normal resist
or special support answer.

Actual choices: p1 switched Espeon; p2 switched Forretress.

Grade: p1 miss, p2 acceptable.

Reusable lesson: after a support piece dies, immediately re-solve both route
maps. p1 still had an Espeon converter, and p2 had Forretress as the support
answer.

## Turn 10

Public state: p1 Espeon 77% vs p2 Forretress 100%; p1 side has no Spikes yet.

My answer: p1 Hidden Power Fire if available or a pressure handoff; p2 Spikes.

Actual choices: p1 Growth; p2 Spikes.

Grade: p1 miss, p2 top-match.

Reusable lesson: this was the successful PTA-057 moment. Forretress had
Explosion pressure, but Spikes changed the route first and preserved the
one-time trade.

## Turn 11

Public state: p1 +1 Espeon 77% vs p2 Forretress 100%; p1 side has Spikes.

My answer: p1 switch Snorlax to cover Explosion; p2 Explosion.

Actual choices: p1 Growth; p2 switched Jynx.

Grade: both miss.

Reusable lesson: after support lands, cash-out is still not automatic.
Forretress preserved itself and handed to Jynx rather than spending Explosion
into a target that had not yet forced the trade.

## Turn 12

Public state: p1 +2 Espeon 77% vs p2 Jynx 100%.

My answer: p1 Psychic; p2 switch Forretress, with Ice Beam as the stay-in
alternative.

Actual choices: p1 Growth; p2 Ice Beam.

Grade: p1 miss, p2 acceptable.

Reusable lesson: the actual p1 route was greedier than I expected. My p2 line
still over-favored immediate Forretress re-entry after missing the Jynx handoff
purpose.

## Turn 13

Public state: p1 +3 Espeon 39% vs p2 Jynx 100%.

My answer: p1 Psychic; p2 switch Forretress.

Actual choices: p1 Morning Sun; p2 Ice Beam, critting Espeon to 11%.

Grade: both miss.

Reusable lesson: at low HP, the setup route needed recovery before conversion.
I kept pricing only attack versus switch and missed Morning Sun as the route
preserver.

## Error Classes

- Second-stage Explosion overcall: turn 10 improved, but turn 11 repeated the
  cash-out mistake after the support move landed.
- Route-preserving switch misses: turns 1, 2, 9, and 11 missed handoffs to
  Rhydon, Jynx, Forretress, or Jynx again.
- Setup/recovery sequencing error: turns 7, 12, and 13 misread when Espeon
  should set up, attack, or heal.
- Support route pricing error: turn 8 underpriced Jynx Psychic as a direct
  way to stop Cloyster before Spikes.

## Next Study Target

Run one PTA-057 regression drill with this narrower prompt:

```text
A support Pokemon has already delivered its first support action and still has
Explosion. Before cashing out, re-rank: preserve support, hand off to a
recurring teammate, status/phaze, attack, then explode. Cash out only if the
current target is now the route blocker or no preserved route improves the
board.
```
