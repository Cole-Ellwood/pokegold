# Sleep Clause Absorber Probe 001 - 2026-05-14

Mode: constructed policy regression. This is not a fresh replay score, not a
holdout, and not final-exam evidence. It exists to harden the rule exposed by
`replay_turn_pause_017`: in GSC, a Pokemon put to sleep is often switched out
immediately and preserved as Sleep Clause material instead of burning wake
turns in front of the sleep user.

Purpose: test six branches after a sleep absorber is put to sleep:

- preserve the sleeper as Sleep Clause material;
- burn sleep turns because the sleeper still functions while asleep;
- burn sleep turns because all switches lose faster;
- attack the sleeper to stop wake value;
- sack into a possible wake Explosion;
- stop preserving once the sleeper has no real future job.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_017_sleep_route_marowak_continuation_smogtours-gen2ou-934428_2026-05-14.md`

Web sources checked:

- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon GSC OU primer:
  `https://www.smogon.com/resources/competitive/gs/gs_ou_primer`
- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon GSC Cloyster discussion:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

Source note: Smogon status material highlights that GSC sleep must be aimed at
the right target and must respect Sleep Talk. The GSC primer states the Sleep
Clause rule in simulator play. Explosion material reinforces why a slept
Cloyster or Exeggutor can still be a saved route piece rather than spent
material.

## Score Summary

Scenarios: 6.

Correct branch class: 6 / 6.

Route job named: 6 / 6.

Sleep Clause material priced: 6 / 6.

Exception handling: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0. Each prompt either supplies the relevant moves or
marks the branch as an inference rather than known team information.

Measurement status: guided regression only. Count this as policy coverage, not
as unseen replay improvement.

## Scenario 1 - Default Preserve After Absorbing Sleep

Public state:

```text
GSC OU. Our Cloyster just absorbed Snorlax's Lovely Kiss and is asleep at 94%.
Sleep Clause is now active against Snorlax's side. Cloyster has revealed Spikes
and Explosion. Our Machamp is unrevealed but healthy in the back. Opposing
Snorlax is 100% and has revealed Lovely Kiss and Double-Edge.
```

Recommendation: switch Cloyster out to the Snorlax punish, with high
confidence if Machamp or another credible answer can enter.

Route reason: Cloyster has already done the sleep-absorption job; preserving it
keeps Sleep Clause active and saves Explosion or later Spikes pressure.

Worst branch: Snorlax uses Curse or attacks on the switch and the incoming
answer takes too much damage, but this is still usually better than donating
sleep turns while Snorlax controls the board.

Score: pass.

## Scenario 2 - Stay Because The Sleeper Functions While Asleep

Public state:

```text
Our Zapdos absorbed Exeggutor Sleep Powder and is asleep at 82%. Zapdos has
revealed Sleep Talk, Thunder, and Hidden Power. Exeggutor has revealed Psychic
and Sleep Powder. The opponent has no Ground revealed, and Zapdos is the best
current Exeggutor answer.
```

Recommendation: stay and Sleep Talk unless the opponent has a clearly better
punish switch.

Route reason: Sleep Clause material still matters, but this absorber keeps its
current job while asleep. Burning turns is not waste when Sleep Talk is the
route.

Worst branch: Sleep Talk selects the wrong move while Exeggutor pivots to a
receiver or Explodes, so preserve alternatives still need to be ranked.

Score: pass.

## Scenario 3 - Sack Into Wake Explosion To Preserve The Only Win Route

Public state:

```text
Our Agility-passed Marowak is 100% and is the only Pokemon that can beat the
opponent's last Tyranitar. We also have Jolteon at 31%. Opponent Cloyster is
asleep at 50%, has revealed Explosion, and is in Earthquake range. If Cloyster
wakes and Explodes into Marowak, Jolteon loses to Tyranitar.
```

Recommendation: strongly consider switching Jolteon into the wake-Explosion
branch if Marowak is the only remaining converter; attack only if the route
requires accepting the wake risk.

Route reason: the slept absorber is not harmless. It is preserved Sleep Clause
material with a one-time trade that can remove the only win condition.

Worst branch: Cloyster stays asleep while Jolteon is sacrificed, giving the
opponent a switch or extra Leftovers turn. The branch is acceptable only if
Marowak preservation is more important than the tempo loss.

Score: pass.

## Scenario 4 - Stay Because Every Switch Loses Faster

Public state:

```text
Our sleeping Suicune is 74% against a boosted Marowak. Sleep Clause is active.
Suicune has revealed Surf and Sleep Talk. The rest of our team is Zapdos at 28%
and Tyranitar at 40%; both are KOed by the public Marowak coverage. Suicune can
survive one hit and has a Sleep Talk Surf route.
```

Recommendation: stay and use Sleep Talk.

Route reason: switching out to preserve Sleep Clause material is the default
branch, but here preservation gives Marowak the game. The sleeper's current job
is better than the abstract value of keeping it asleep in reserve.

Worst branch: Sleep Talk fails to select Surf, but the switch branches lose
even more directly.

Score: pass.

## Scenario 5 - Stop Preserving A Sleeper With No Job

Public state:

```text
Our Exeggutor is asleep at 18%, has already used Explosion, and has only
Psychic/Giga Drain utility left. Sleep Clause is active. Opponent Raikou is 64%
and can force progress with Thunder. Our healthy Snorlax can enter and is the
actual long-game anchor.
```

Recommendation: do not preserve Exeggutor merely because it is asleep. Either
sack it for clean Snorlax entry or switch directly if the entry is safe.

Route reason: Sleep Clause material is valuable only when the sleeping Pokemon
has a remaining job or when keeping it asleep prevents a meaningful second
sleep. A spent 18% Exeggutor is not worth warping the route around.

Worst branch: over-preserving the sleeper gives Raikou free damage or setup and
spends the anchor's entry path.

Score: pass.

## Scenario 6 - Preserve A Sleeping Spinner / Exploder

Public state:

```text
Our Cloyster is asleep at 76% after absorbing Jynx Lovely Kiss. It has revealed
Spikes, Rapid Spin, Surf, and Explosion. Opponent has Spikes up, a low Zapdos,
and a Snorlax in the back. Our Golem can enter Jynx safely enough this turn.
```

Recommendation: switch Cloyster out and preserve it.

Route reason: Cloyster is not just a sleeping body. It is Sleep Clause
material, the spinner, and a future Explosion trade into Snorlax or Zapdos.
Burning turns risks losing the exact support piece that makes the endgame
playable.

Worst branch: Golem entry gives the opponent a switch to a Water or Grass, but
that branch is priced against preserving Cloyster's unique support jobs.

Score: pass.

## Extracted Checklist

After a Pokemon is put to sleep in GSC:

1. Is Sleep Clause now active, and against which side's sleep moves?
2. Does the sleeping Pokemon still have a future job if preserved?
3. Can it perform its current job while asleep through Sleep Talk or bulk?
4. Does burning turns invite the sleep user or a teammate to punish for free?
5. Does switching the sleeper out preserve a later Explosion, Spin, Spikes,
   phaze, sack, or wake attack?
6. Is the sleeper actually spent, making preservation a fake priority?
7. If the sleeping Pokemon can wake and Explode, which piece are we willing to
   lose to that branch?

## Next Rep

Run a fresh unseen replay segment and stop at the first sleep absorption. Score
whether the answer names the immediate switch-out branch, the Sleep Talk
exception, and any later Explosion or support job.
