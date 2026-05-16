# Replay Turn-Pause 006 Spinner Poison Pivot - smogtours-gen2ou-907668 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-907668`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 2`.

Mode: spectator public.

Purpose: fresh turn-pause rep for the active 1500-Elo learning goal, focused on
hazard removal, spinner punishment, and plan revision after support progress.

Local docs read:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/study_roadmap_2026-05-14.md`

Web sources checked:

- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-2.3777598/`
- `https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/`

Contamination control:

- Local docs were searched for `907668`; no prior local reference was found.
- The raw log was downloaded to `.local/pokemon_mastery/replay_logs/`.
- The first file-header check exposed turns 1-6, so turns 1-6 were excluded.
- Turns 7-11 were answered before each reveal using
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Turn 8 p2 was not scored because full paralysis hid the selected move.

## Score Summary

Turns: 7-11.

Decisions scored: 9 side-decisions.

Top-match: 4 / 9.

Acceptable-match: 5 / 9.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 9.

Targeted improvement: after correctly identifying the immediate spin sequence,
I underweighted the opponent's next support conversion. I treated the poisoned
spinner as a reason to continue the hazard loop, but the players immediately
reclassified: p2 used Toxic to tax Starmie, then pivoted to Raikou; p1
anticipated that pivot and moved Snorlax in before Starmie became a liability.

## Turn 7

Public state: p1 +1 Skarmory at 100% vs p2 paralyzed Cloyster at 94%; no
Spikes currently; p1 has revealed Starmie with Rapid Spin.

My answer: p1 switch Starmie to contest the obvious Spikes turn; p2 use Spikes.

Actual choices: p1 switched Starmie; p2 used Spikes.

Grade: both top-match.

Reusable lesson: when a paralyzed Cloyster gets a clean support turn into
Skarmory, the spinner entry is the route-preserving response even if the layer
is still likely to appear.

## Turn 8

Public state: p1 Starmie 100% vs p2 Cloyster 99% paralyzed; p1 side has
Spikes.

My answer: p1 Rapid Spin; p2 stay and try to re-lay Spikes after the faster
spin.

Actual choices: p1 Rapid Spin; p2 was fully paralyzed.

Grade: p1 top-match; p2 unscored because the selected move was hidden.

Reusable lesson: the move-order branch matters. If the slower Cloyster can act
after Rapid Spin, it can potentially erase the spin turn by setting Spikes
again.

## Turn 9

Public state: p1 Starmie 100% vs p2 Cloyster 100% paralyzed; no Spikes on the
field; Starmie has Rapid Spin revealed.

My answer: p1 attack Cloyster with the best damaging move, with Psychic if
available; p2 set Spikes.

Actual choices: p1 Psychic; p2 Toxic.

Grade: p1 acceptable; p2 miss. The important miss was p2's support priority:
poisoning the spinner made the future hazard war easier than immediately
setting the layer.

Reusable lesson: when the spinner is active and the field is clean, status on
the spinner can be better long-term progress than another hazard click.

## Turn 10

Public state: p1 toxic Starmie 100% with Psychic/Rapid Spin revealed vs p2
paralyzed Cloyster at 53%; no Spikes.

My answer: p1 continue Psychic pressure; p2 switch Snorlax to preserve
Cloyster after Toxic landed.

Actual choices: p1 switched Snorlax; p2 switched Raikou.

Grade: both miss. I saw that Cloyster should probably leave but chose the wrong
handoff and missed p1's proactive answer. Once Starmie was poisoned, p2's
Electric pivot was the cleaner route; p1 correctly moved Snorlax into that
branch before Starmie had to absorb it.

Reusable lesson: after a spinner is poisoned, re-score the whole board. The
next route is often not "set Spikes again"; it may be "force the spinner out
with the special attacker that the spinner no longer wants to trade into."

## Turn 11

Public state: p1 Snorlax 100% with Body Slam revealed vs p2 Raikou 100%; no
Spikes. p2 has revealed Cloyster, Exeggutor, Raikou, and Snorlax.

My answer: p1 Body Slam; p2 switch Cloyster to keep cycling support.

Actual choices: p1 Body Slam; p2 switched Golem.

Grade: p1 top-match; p2 miss. I underpriced the unseen normal-resist branch in
spectator-public no-preview play. Golem was not knowable, but a normal resist
or Ground/Rock pivot was a live class once p1 Snorlax met p2 Raikou.

Reusable lesson: when Snorlax enters on Raikou in no-preview GSC, do not limit
the opponent's branch map to revealed support pieces. Price unrevealed normal
resists and Ground/Rock pivots before assuming the visible Cloyster is the
handoff.

## Error Classes

- Route reconstruction error: missed Toxic as the spinner-punishment move on
  turn 9.
- Plan-revision error: after Toxic landed, I continued thinking in the old
  Spikes/Rapid Spin loop instead of re-solving around p2's Raikou pressure and
  p1's Snorlax answer.
- Hidden-branch pricing error: missed the unrevealed Golem/normal-resist class
  on turn 11.

## Next Study Target

Run the next short replay rep around poisoned-spinner or Raikou-vs-Snorlax
positions. Before choosing a support move, explicitly ask:

```text
If the spinner or support piece is now statused, what route does the opponent
hand off to next?

If Snorlax enters on an Electric, what unrevealed normal resist or Ground/Rock
branch must be priced before choosing the opponent's switch?
```
