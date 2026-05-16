# Replay Turn-Pause 007 Electric Handoff Overcorrection - smogtours-gen2ou-907668 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-907668`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 2`.

Mode: spectator public.

Purpose: follow-on rep from
`replay_turn_pause_006_spinner_poison_pivot_smogtours-gen2ou-907668_2026-05-14.md`,
focused on the exact miss from that run: Snorlax-vs-Electric handoffs,
unrevealed normal-resist branches, and avoiding overcorrection into Explosion
fear.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_006_spinner_poison_pivot_smogtours-gen2ou-907668_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- `https://www.smogon.com/gs/articles/gsc_threats`
- `https://www.smogon.com/forums/threads/gsc-ou-viability-rankings-mk-4.3633233/page-8`
- `https://www.smogon.com/forums/threads/gsc-teambuilding-compendium.3547538/`

Source note: the web check reinforced the branch classes being tested here:
Raikou is a defining GSC threat that forces switches; the January 2026 VR keeps
Snorlax, Raikou, Steelix, and Golem in relevant modern GSC context; and the
teambuilding compendium discussion explicitly treats Golem as a real modern GSC
piece and part of the broader Electric-check map.

Contamination control:

- This is not a fully fresh replay after turn 11 because turns 7-11 were
  already scored in the previous artifact.
- Future turns were still hidden: turns 12-18 were answered before each reveal
  using `tools/pokemon_mastery/replay_turn_pause.py`.
- Turn 14 p2 was not scored because full paralysis hid the selected move.

## Score Summary

Turns: 12-18.

Decisions scored: 13 side-decisions.

Top-match: 4 / 13.

Acceptable-match: 7 / 13.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 13.

Targeted improvement: I corrected the immediate turn-12 Golem branch from the
previous run: Snorlax should preserve into Skarmory, and Golem's straightforward
Earthquake branch must be priced. The new weakness was overcorrection. I
started seeing Explosion everywhere and missed quieter handoffs: Cloyster back
into Skarmory, Exeggutor into Starmie, and Snorlax into Raikou.

## Turn 12

Public state: p1 Snorlax 100% with Body Slam revealed vs p2 Golem 95%;
Golem entered on Snorlax after p2 Raikou was met by p1 Snorlax.

My answer: p1 switch Skarmory to preserve Snorlax and cover Earthquake; p2
Earthquake.

Actual choices: p1 switched Skarmory; p2 Earthquake, immune.

Grade: both top-match.

Reusable lesson: after the unrevealed normal-resist/Ground branch appears,
respect the simple move first. The first job is not to outguess Explosion; it
is to preserve Snorlax from Earthquake while keeping the Electric-answer map
live.

## Turn 13

Public state: p1 Skarmory 100% vs p2 Golem 100%; Golem has Earthquake
revealed.

My answer: p1 Curse on the expected switch; p2 switch Raikou to restart special
pressure.

Actual choices: p1 Drill Peck; p2 switched Cloyster.

Grade: both miss. I saw that Golem should leave, but I picked the wrong support
handoff and got too greedy with Skarmory's turn. Drill Peck immediately prices
the low Cloyster re-entry.

Reusable lesson: when a blocked Ground invites a switch, do not assume the next
route is always Electric pressure. Low support pieces can re-enter if their
job, here Spikes or spinner pressure, still matters.

## Turn 14

Public state: p1 Skarmory 100% vs p2 Cloyster 42% paralyzed; no hazards.

My answer: p1 Drill Peck, with Starmie switch as the main alternative; p2 set
Spikes.

Actual choices: p1 switched Starmie; p2 was fully paralyzed.

Grade: p1 acceptable; p2 unscored because the selected move was hidden.

Reusable lesson: even a low paralyzed Cloyster can still force the spinner
entry if the field is clean and the opponent cannot let the layer stick.

## Turn 15

Public state: p1 poisoned Starmie 94% with Psychic/Rapid Spin revealed vs p2
Cloyster 48% paralyzed; no hazards.

My answer: p1 Psychic; p2 switch Raikou to preserve Cloyster and pressure the
poisoned spinner.

Actual choices: p1 Psychic; p2 switched Exeggutor.

Grade: p1 top-match; p2 acceptable. I got the preserve-Cloyster handoff class,
but missed the exact target. Exeggutor absorbs Psychic, threatens useful
special pressure, and keeps Raikou unrevealed for later.

Reusable lesson: once the spinner is poisoned, the handoff can be any piece
that forces Starmie to stop acting freely. Do not collapse the whole class into
Electric by default.

## Turn 16

Public state: p1 poisoned Starmie 88% vs p2 Exeggutor 76%; Exeggutor has
Stun Spore and Psychic revealed.

My answer: p1 switch Skarmory to cover Explosion; p2 Explosion to remove the
spinner.

Actual choices: p1 switched Raikou; p2 Psychic.

Grade: both miss. I overcorrected into Explosion fear and missed that paralyzed
Raikou was still a useful special sponge and pressure piece.

Reusable lesson: Explosion is a route trade, not the default explanation for
every Exeggutor turn. Before preserving against boom, ask whether a special
sponge can enter and improve the next board without spending the Steel.

## Turn 17

Public state: p1 paralyzed Raikou 74% vs p2 Exeggutor 76%; Exeggutor has
Psychic/Stun Spore revealed.

My answer: p1 switch Skarmory to keep Raikou away from Explosion; p2 Explosion.

Actual choices: p1 Hidden Power; p2 switched Snorlax.

Grade: both miss. The p1 attack kept pressure instead of surrendering tempo to
a feared Explosion, and p2 used Snorlax as the special sponge rather than
cashing Exeggutor.

Reusable lesson: when the opponent still has a healthy Snorlax, Raikou pressure
often hands off into Snorlax before the boomer cashes out. Price the recurring
special sponge route before assuming the one-time trade.

## Turn 18

Public state: p1 paralyzed Raikou 80% with Hidden Power revealed vs p2 Snorlax
96%; no hazards.

My answer: p1 switch Skarmory to preserve Raikou; p2 Curse on the expected
switch.

Actual choices: p1 switched Skarmory; p2 Body Slam.

Grade: p1 top-match; p2 acceptable. The p2 move was not the setup move I chose,
but it was the same broad route: use Snorlax's free turn to pressure the
incoming answer.

Reusable lesson: after Snorlax catches Raikou, the defender's first job is
preservation. The attacker may take immediate Body Slam damage/paralysis odds
instead of starting with Curse.

## Error Classes

- Support-handoff error: after Golem was blanked, I assumed Raikou instead of
  checking whether Cloyster still had a support job.
- Explosion overcorrection: after naming the boom branch, I over-preserved and
  missed Psychic, Hidden Power pressure, and Snorlax handoffs.
- Handoff-class narrowing: I treated "poisoned spinner gets forced out" as
  "Electric enters" instead of the broader class of Psychic absorber, special
  sponge, or support-preserving pivot.

## Next Study Target

Run a drill or replay segment where Exeggutor, Golem, or Cloyster can either
cash out or hand off. The required question before predicting Explosion:

```text
If this support piece does not spend the one-time trade now, which recurring
teammate gets a better board by entering instead?
```
