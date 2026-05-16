# Sleep Clause Four-Choice Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_038` into a compact decision drill. Each
scenario asks for one of four action classes without labeling the intended
heuristic:

- switch the sleeper out and preserve it;
- stay with Sleep Talk or current sleeping utility;
- stay because the sleeping Pokemon is already the active win route;
- spend or cover the sleeping Pokemon because wake/action or self-KO changes
  the route.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/workspace/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_038_sleep_clause_overcorrection_smogtours-gen2ou-934314_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Forums, GSC Sleep Trap:
  `https://www.smogon.com/forums/threads/gsc-sleep-trap.3622522/`
- Smogon Forums, GSC Introduction to Status:
  `https://www.smogon.com/forums/threads/gsc-introduction-to-status-sleep-paralysis-and-poison-gp-2-2.103998/`

Source note: sleep absorption is route material. Sleep Talk users can absorb
sleep and keep functioning; other slept pieces often switch out to preserve
Sleep Clause. `replay_turn_pause_038` adds that a boosted active sleeper may
stay when switching erases the route and the opponent cannot punish quickly.

## Score Summary

Scenarios: 8.

Action-policy hits: 8 / 8.

Route-job hits: 8 / 8.

Exception hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. These prompts were constructed after the
replay lesson, so the score checks policy retention rather than unseen skill.

## Scenario 1 - Jynx Into Revealed RestTalk Raikou

Public state:

```text
Vanilla GSC. Opponent Jynx just used Lovely Kiss into our Raikou. Raikou is
asleep at 86% and has revealed Thunderbolt / Rest / Sleep Talk. Jynx is 74%
and has Lovely Kiss / Ice Beam / Psychic revealed. Our Snorlax is healthy but
is the only long-term special sponge. No Spikes are up.
```

Frozen answer: stay and use Sleep Talk. Confidence: high.

Route reason: Raikou is not dead material; it absorbed sleep and still
threatens Jynx while preserving Snorlax.

Worst branch: Sleep Talk calls Rest or the wrong attack while Jynx pivots to a
Ground or Snorlax answer.

Policy key: Sleep Talk can make the absorber the immediate answer, not only a
bench shield.

Score: pass.

## Scenario 2 - Sleeping Cloyster With Unique Support Jobs

Public state:

```text
Vanilla GSC. Our Cloyster absorbed Exeggutor Sleep Powder at 90%. It has
Spikes / Rapid Spin / Surf / Explosion revealed. Opponent Exeggutor is 96% and
has Sleep Powder / Psychic revealed. Opponent has Spikes up and a healthy
Snorlax in reserve. Our Tyranitar can enter Psychic safely enough.
```

Frozen answer: switch Cloyster out to Tyranitar or another safe-enough answer.
Confidence: high.

Route reason: Cloyster is Sleep Clause material, the spinner, the setter, and a
future Explosion user. Burning turns in front of Exeggutor risks losing too
many future jobs.

Worst branch: Exeggutor Stun Spores or doubles into the Tyranitar answer, but
that is priced against preserving Cloyster's unique support compression.

Policy key: switch the sleeper when its future jobs are worth more than the
current turn.

Score: pass.

## Scenario 3 - Boosted Sleeper Already Converts

Public state:

```text
Vanilla GSC. Our Snorlax is asleep from Gengar Hypnosis at 84%, with Curse /
Double-Edge / Rest revealed and boosts atk+3 / def+3. Opponent Gengar has
Thunderbolt and Hypnosis revealed, no Explosion revealed, and has only done
slow chip. Switching Snorlax would drop the boosts. No Ghost-immune teammate is
needed this turn.
```

Frozen answer: stay in. If Snorlax wakes, use Rest or the route-preserving
move; if it stays asleep, accept the chip.

Route reason: switching preserves Sleep Clause but throws away the active win
route. The opponent's public punishment is too slow to justify that.

Worst branch: Gengar reveals Explosion or another route-ending move exactly as
Snorlax stays.

Policy key: the preserve-default yields to an already-built active route.

Score: pass.

## Scenario 4 - Boosted Sleeper Under Real Cash-Out Threat

Public state:

```text
Vanilla GSC. Our Snorlax is asleep from Gengar Hypnosis at 52%, boosts
atk+3 / def+3. Opponent Gengar has revealed Thunderbolt and Explosion earlier.
Our own Gengar is healthy and can enter on Explosion. Switching drops boosts,
but losing Snorlax means Zapdos beats the rest of our team.
```

Frozen answer: switch to Gengar or another lower-value Explosion absorber.
Confidence: medium-high.

Route reason: boosted sleep value is real, but a revealed self-KO changes the
worst branch. Preserving Snorlax matters more than staying for wake/Rest.

Worst branch: opponent Thunderbolts or doubles as Gengar enters and the boost
route is reset.

Policy key: the overcorrection goes both ways; stay only if the cash-out
punish is not real or not worth covering.

Score: pass.

## Scenario 5 - Sleeping Non-Talk Phaze Bait

Public state:

```text
Vanilla GSC. Our Snorlax is asleep at 100% after absorbing Lovely Kiss. It has
Curse and Double-Edge revealed but no Sleep Talk. Opponent Skarmory is active,
100%, and has Whirlwind revealed. Spikes are on our side. Our Zapdos is healthy
and can force Skarmory out.
```

Frozen answer: switch Zapdos.

Route reason: staying does not use Sleep Clause material productively; it gives
Skarmory a Whirlwind turn and extra Spikes damage. Preserve Snorlax for later.

Worst branch: Skarmory doubles to Raikou or uses Toxic/Drill Peck into the
switch.

Policy key: asleep plus no Sleep Talk can make a piece phaze bait.

Score: pass.

## Scenario 6 - Sleeper Has No Remaining Job

Public state:

```text
Vanilla GSC. Our Exeggutor is asleep at 12%, has already used Explosion, and
has only Psychic/Giga Drain left. Opponent Raikou is active at 73%. Our
Snorlax is healthy and can take the next hit. Sleep Clause is active, but the
opponent's sleep user is fainted.
```

Frozen answer: do not preserve Exeggutor merely because it is asleep. Sack for
clean Snorlax entry, or switch directly if the entry is safe.

Route reason: Sleep Clause material has value only if it blocks a future sleep
or retains a concrete job.

Worst branch: sacking gives Raikou an extra Leftovers turn or crit chance, but
over-preserving loses more tempo.

Policy key: "sleeping" is not itself a resource; the remaining job is.

Score: pass.

## Scenario 7 - Sleeping Self-KO Target Must Be Covered

Public state:

```text
Vanilla GSC. Opponent Cloyster is asleep at 45%, has Explosion revealed, and
is in range of our Marowak Earthquake if it stays asleep. Our Marowak is the
only route through the opponent's last Tyranitar. Our Jolteon is 24% and no
longer needed except as a sack.
```

Frozen answer: switch Jolteon into the wake-Explosion branch unless the KO is
guaranteed before Cloyster can wake.

Route reason: the sleeping target can still be a route-ending self-KO piece.
Cover the worst branch with a lower-value absorber.

Worst branch: Cloyster stays asleep and Jolteon is sacrificed for no immediate
gain.

Policy key: sleeping targets still have wake/action and wake/self-KO value.

Score: pass.

## Scenario 8 - Rest Sleep Is Not The Same Clause Object

Public state:

```text
Vanilla GSC. Earlier, our Gengar put opposing Snorlax to sleep with Hypnosis.
Snorlax just woke and used Rest, returning to 100% and becoming asleep from
Rest. Gengar is still active, but the opponent also has Gengar and Exeggutor
healthy in the back.
```

Frozen answer: stop treating Snorlax as the same preserved Sleep Clause object.
Use the Rest turns to improve the route: chip with Gengar, pivot to a stronger
attacker if safe, or prepare to sleep a different target once it is legal and
useful.

Route reason: the original Hypnosis sleep has been converted into Rest sleep.
The route question shifts from "preserve or spend Sleep Clause material" to
"how do we punish the Rest window without exposing the wrong piece?"

Worst branch: switching to a stronger attacker eats Spikes and then loses to a
wake or a double.

Policy key: re-solve after wake and Rest; do not carry the old sleep-clause
label forward.

Score: pass.

## Resulting Checklist

For a sleeping Pokemon, rank these before choosing:

1. Is it asleep from opponent sleep or from Rest?
2. Is Sleep Clause still blocking a meaningful future sleep?
3. Does the sleeper have Sleep Talk or another live current job?
4. Would switching erase boosts, board position, or wake/Rest conversion?
5. Is there a revealed cash-out, phaze, setup, or coverage punish that makes
   staying unacceptable?
6. If we spend or preserve the sleeper, which teammate inherits the lost job?

## Next Study Target

Fresh replay transfer with the same four-choice classification, ideally from a
segment where the active sleeper has boosts or RestTalk and an opposing
Explosion, phaze, or stronger-special-attacker branch is live.
