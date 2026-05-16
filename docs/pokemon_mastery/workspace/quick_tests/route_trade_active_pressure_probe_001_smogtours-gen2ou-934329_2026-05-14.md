# Route Trade Active Pressure Probe 001 - smogtours-gen2ou-934329 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934329`.

Mode: post-oracle regression from exposed replay turns.

Purpose: convert the `934329` exposure into six compact prompts that force the
question: "Is this one-time trade removing an active route, and is the lost
role already covered?"

This is not final-exam evidence. Turns 1-21 of the replay were already exposed
while searching for a different phaze drill, so this is a policy regression
and calibration artifact only.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_exposure_note_smogtours-gen2ou-934329_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the Explosion guide explicitly supports Self-Destruct Snorlax as
a way to stop opposing CurseLax, while the current sample-team material
describes Exeggutor baiting and exploding on Zapdos or Raikou to improve a
sweeper's route. The Zapdos source keeps the target value honest: RestTalk
Zapdos is a major active pressure piece and status sponge, not passive sleep
material.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Original exposed miss: turn 2. I undercalled Snorlax Self-Destruct after the
opponent's Snorlax started a Curse route.

Weakest remaining pressure: scenario 1 needs a fresh replay transfer check,
because the hardest live skill is recognizing an early Self-Destruct threshold
before hindsight proves that the opponent's Snorlax was a route threat.

## Scenario 1 - Self-Destruct Into Started CurseLax

Public state: vanilla GSC, player-side known team. Our Snorlax is 98% after
using Double-Edge. Opposing Snorlax is 72% at `atk+1 def+1 spe-1` after
revealing Curse. No Ghost or Protect user has been revealed. Our team has
Raikou and Vaporeon healthy, so Snorlax is not our only special sponge.

Frozen answer: use Self-Destruct. Confidence: high. The route is defensive
trade-down: remove or cripple the Curselax before it can Rest, stack more
Curses, or force the rest of the team to answer it through Spikes. Serious
alternatives: Double-Edge only if Self-Destruct is not in the known set or if
Snorlax is still the only piece covering multiple special attackers; switch
only if an immune target is strongly expected. Worst branch: a Ghost or
low-value Normal resist catches the move, or losing Snorlax exposes a special
route we failed to cover.

Policy key: a one-time trade can be correct very early if the target has
already started the route that will otherwise own the game and the lost role
has a successor.

Grade: complete.

## Scenario 2 - Do Not Cash Out Before The Route Exists

Public state: vanilla GSC, player-side known team. Lead Snorlax mirror at
100% each. Our Snorlax has Double-Edge / Earthquake / Fire Blast /
Self-Destruct. The opponent's Snorlax has revealed no move yet. We have no
public evidence of Curse, Rest, Lovely Kiss, or Self-Destruct. Our Raikou is
not yet revealed and may need Snorlax's special bulk later.

Frozen answer: use Double-Edge or another ordinary scout/pressure move, not
Self-Destruct. Confidence: high. The route is to get information and chip
before spending the team's strongest special sponge. Serious alternative:
switch only if the matchup is bad by team plan; Self-Destruct is reserved for
when the target's removal opens a named route or stops a named threat. Worst
branch: the opponent gets the first Curse, but that creates the threshold for
the next turn rather than justifying a blind turn-1 trade.

Policy key: do not overcorrect from the turn-2 lesson into booming before the
opponent's route is public.

Grade: complete.

## Scenario 3 - Explosion Into Active RestTalk Zapdos

Public state: vanilla GSC, player-side known team. Our Exeggutor is 61% and
has Psychic / Stun Spore / Explosion revealed. Opposing Zapdos is 67%,
paralyzed, and has Rest / Sleep Talk / Thunder / Hidden Power revealed. Spikes
are on both sides. Opposing Snorlax is gone. Our Vaporeon is healthy, Raikou
is asleep but preserved, and Exeggutor has already spread paralysis.

Frozen answer: use Explosion. Confidence: medium-high. The route is to remove
the active RestTalk Electric that is still pressuring through sleep and
paralysis, opening Vaporeon/Raikou endgame material while Exeggutor's support
job is mostly complete. Serious alternatives: Psychic only if Explosion is
needed for a more exact blocker or if Zapdos is already forced into range;
switch only if preserving Exeggutor covers a larger route. Worst branch:
Explosion is caught by a Normal resist/Ghost or Zapdos is not the true blocker.

Policy key: sleeping or statused RestTalk Zapdos can still be the active route
piece worth trading for.

Grade: complete.

## Scenario 4 - Preserve The Exploder When The Target Is Replaceable

Public state: vanilla GSC, player-side known team. Our Exeggutor is 80% with
Sleep Powder / Psychic / Giga Drain / Explosion. Opposing Zapdos is asleep at
90% from Rest and has not revealed Sleep Talk. The opponent still has healthy
Snorlax and Vaporeon unrevealed to our Machamp route. Our Exeggutor is the
only current Water/Ground check and still has sleep or paralysis support to
deliver.

Frozen answer: use Psychic or switch; do not Explosion yet. Confidence:
medium-high. The route is to preserve Exeggutor until the target is the actual
route blocker or the sleeping Zapdos proves active through Sleep Talk/wake
timing. Serious alternative: Explosion only if Zapdos waking now would end the
route and no lower-cost answer exists. Worst branch: Zapdos wakes and attacks,
but spending Exeggutor into a replaceable or inactive target can lose more.

Policy key: "Electric is valuable" is not enough. The trade target must be
active or route-defining.

Grade: complete.

## Scenario 5 - Execution Gate Before The Trade

Public state: vanilla GSC, player-side known team. Our Exeggutor is 18%
against Zapdos at 76%. Zapdos is awake, faster, and has Thunder and Hidden
Power revealed. Exeggutor has Explosion, but no paralysis support is on the
field and no Substitute is present. If Exeggutor faints before acting, the
trade does not resolve.

Frozen answer: do not assume Explosion is available; switch or sacrifice only
if that creates the better entry. Confidence: medium. The route calculation
starts with execution: if Zapdos can KO first, the proposed Explosion is not a
real route trade. Serious alternative: Explosion only if damage evidence shows
Exeggutor survives the likely hit or if Zapdos chooses Rest/Sleep Talk. Worst
branch: we plan around removing Zapdos and simply lose Exeggutor before the
trade begins.

Policy key: price Speed, current HP, likely damage, and status before scoring
the one-time trade's route value.

Grade: complete.

## Scenario 6 - Trade Target Is The Remaining Material Blocker

Public state: vanilla GSC, simplified endgame. Our Gengar is 73% with
Explosion / Thunderbolt / Ice Punch / Hypnosis. Opponent has Snorlax at 62%
and Vaporeon at 40%. Our last teammate is healthy Raikou, which beats Vaporeon
but cannot make progress through Snorlax. Spikes are on the opponent's side.
No Ghost or Normal resist remains.

Frozen answer: use Explosion into Snorlax if it is active or force the line
that catches Snorlax on entry. Confidence: high. The route is final-material
proof: after Snorlax is gone, Raikou handles Vaporeon; after Vaporeon is gone,
Raikou still cannot beat Snorlax. Serious alternatives: Hypnosis only if sleep
accuracy is the safer route to the same Snorlax removal; Thunderbolt into
Vaporeon is the wrong target unless Snorlax is already dead or trapped. Worst
branch: Explosion misses the Snorlax target via switch or Gengar was still
needed as the only emergency answer.

Policy key: choose the trade target by the remaining converter's blockers, not
by which visible target is easiest to damage.

Grade: complete.

## Resulting Rule

Before spending Explosion or Self-Destruct, answer four questions:

1. What route is the target actively starting, preserving, or blocking?
2. Who inherits the user's lost job after the self-KO?
3. Can the trade execute under current Speed, HP, status, and switch branches?
4. What final material remains after the trade, and who converts it?

## Next Study Target

Run a fresh unseen replay segment with early Snorlax Self-Destruct or
Exeggutor/Cloyster Explosion pressure and score whether the active-route trade
threshold transfers without overcalling blind Explosion.
