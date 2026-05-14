# Replay Turn-Pause 003 Re-Solve Canary - smogtours-gen2ou-917193 - 2026-05-14

Source: Smogon GSC OU Winter Seasonal #8 Round 6 post linking
`https://replay.pokemonshowdown.com/smogtours-gen2ou-917193`.

Mode: spectator public.

Purpose: test `STP-058` / `PTA-055`, the poker-AI transfer rule that after a
route-changing reveal I should re-solve the local subgame by naming three
branches before choosing:

- obvious punish;
- route-preserving switch;
- greed/support continuation.

Contamination control:

- Local docs were searched for `917193`; no prior reference was found.
- The raw log was downloaded to `tmp/` and accessed only through
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Each prediction was frozen in chat before reveal.
- This is a replay turn-pause score, not a sealed final exam.

## Score Summary

Turns: 1-6.

Decisions scored: 12 side-decisions.

Branch-bundle compliance: 6 / 6 turns.

Top-match: 2 / 12.

Acceptable-match: 6 / 12.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Main result: the transfer rule improved process but not accuracy yet. I did
name the three branches every turn, which prevented pure single-line thinking.
However, I over-weighted the obvious punish branch, especially Explosion, and
under-weighted the strong-player support/pivot branches.

## Turn 1

Public state: p1 Snorlax vs p2 Zapdos, no moves revealed.

Branch bundle:

- obvious punish: Zapdos attacks Snorlax with Thunder;
- route-preserving switch: p1 goes to an Electric answer if known;
- greed/support: p1 uses Lovely Kiss or Curse.

My answer: p1 Lovely Kiss if available, otherwise switch; p2 Thunder.

Actual choices: p2 switched Cloyster; p1 Curse.

Grade: p1 acceptable because Curse was listed as the greed branch, but not
top-match. p2 miss. Cloyster was the route-preserving anti-Lax support pivot.

Reusable lesson: in Snorlax vs Electric lead positions, the Electric user may
not attack. If Snorlax is likely to start a route, immediate support pivot can
matter more than lead damage.

## Turn 2

Public state: p1 +1 Snorlax vs p2 Cloyster.

Branch bundle:

- obvious punish: Cloyster Explosion into boosted Snorlax;
- route-preserving switch: p1 leaves to a less valuable Explosion absorber;
- greed/support: Cloyster sets Spikes while Snorlax continues.

My answer: p1 switch; p2 Spikes.

Actual choices: p2 Toxic; p1 Curse.

Grade: both miss. Cloyster chose a fourth branch I underpriced: status the
setup anchor first, then set hazards or pivot later.

Reusable lesson: when a setup route is still young, status can be the best
route-stopper before Explosion or Spikes. The branch bundle should include
"disable the route" when status is plausible.

## Turn 3

Public state: p1 +2 poisoned Snorlax vs p2 Cloyster.

Branch bundle:

- obvious punish: Cloyster Explosion;
- route-preserving switch: p1 exits before poison plus Explosion spends Lax;
- greed/support: Cloyster sets Spikes while Snorlax attacks.

My answer: p1 switch; p2 Spikes.

Actual choices: p2 Spikes; p1 Body Slam, paralyzing Cloyster.

Grade: p1 miss; p2 top-match. p1 chose to cash Snorlax's setup by damaging and
paralyzing Cloyster despite the poison clock.

Reusable lesson: after Toxic lands, the setup anchor may become a temporary
breaker rather than a piece to preserve forever. "Poisoned" does not
automatically mean "switch now."

## Turn 4

Public state: p1 +2 poisoned Snorlax 94% vs p2 paralyzed Cloyster 62%.

Branch bundle:

- obvious punish: Cloyster Explosion;
- route-preserving switch: p1 goes to an Explosion absorber;
- greed/support: p1 attacks while p2 preserves Cloyster.

My answer: p1 Body Slam if Snorlax is expendable; p2 Explosion.

Actual choices: p2 switched Steelix; p1 Earthquake.

Grade: p1 acceptable because attacking was right but move was wrong. p2 miss.
The strong line was to move the route-stopper into the expected Normal move
while p1 used the Ground coverage.

Reusable lesson: do not tunnel on Explosion after naming it. A paralyzed
Cloyster may be more useful preserved if another physical wall or phazer can
enter the current boosted threat.

## Turn 5

Public state: p1 +2 poisoned Snorlax 82% vs p2 Steelix 50%.

Branch bundle:

- obvious punish: Steelix Roar or Explosion ends the Snorlax route;
- route-preserving switch: p1 exits before poison plus phaze/trade spends Lax;
- greed/support: Snorlax Earthquake again to remove Steelix.

My answer: p1 Earthquake; p2 Roar.

Actual choices: p1 switched Forretress; p2 switched Machamp.

Grade: both miss. Both players re-solved away from the visible Snorlax-Steelix
exchange: p1 preserved poisoned Snorlax, p2 brought in a Fighting threat.

Reusable lesson: if both active Pokemon have already shown the central damage
interaction, the next high-level line may be a double re-solve to the piece
that controls the next subgame, not the move that wins the visible matchup.

## Turn 6

Public state: p1 Forretress 94% with Spikes on own side vs p2 Machamp 100%.

Branch bundle:

- obvious punish: Machamp Cross Chop into Forretress;
- route-preserving switch: p1 goes to a Fighting answer;
- greed/support: Forretress spins, sets support, or trades.

My answer: p1 switch; p2 Cross Chop.

Actual choices: both players switched Zapdos.

Grade: p1 acceptable; p2 miss. p2 rejected immediate damage and reset into a
Zapdos mirror or pressure position.

Reusable lesson: a threat advantage can be used to force the opponent's answer
and then pivot, not only to attack. Branch bundles should include "use threat
to choose the next matchup" when the active threat is obvious.

## Next Study Target

Improve branch-bundle quality, not just compliance:

- include status-as-route-stopper when a support Pokemon can disable setup;
- include preservation of the punisher after it becomes statused or chipped;
- include double re-solve after both sides have seen the active damage
  interaction;
- distinguish "obvious punish exists" from "obvious punish is best now."
