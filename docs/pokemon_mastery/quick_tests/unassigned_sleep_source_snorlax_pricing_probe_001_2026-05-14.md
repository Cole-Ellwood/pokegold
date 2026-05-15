# Unassigned Sleep Source Snorlax Pricing Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_052` into forced choices around
team-level sleep source assignment, Sleep Clause preservation, and
damage/recoil pricing against Lovely Kiss Snorlax.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_052_lovely_kiss_snorlax_sleep_pivot_smogtours-gen2ou-923076_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, SPL XVII GSC Discussion:
  `https://www.smogon.com/forums/threads/spl-xvii-gsc-discussion.3775984/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer
before treating this as stable.

## Scenario 1 - Do Not Assign Sleep By Species Alone

Public state:

```text
Vanilla GSC. Turn 1 lead Exeggutor faces Cloyster. No moves are revealed.
Your team may be using Lovely Kiss Snorlax as the sleep source, freeing
Exeggutor from Sleep Powder. Cloyster is faster and can set Spikes before
Exeggutor moves. Psychic puts Cloyster into immediate Explosion-cash-out
range.
```

Tempting move: Sleep Powder because Exeggutor commonly carries it.

Frozen answer: prefer Psychic if the team plan assigns sleep to Snorlax or if
Psychic creates the cleaner Cloyster support-cash-out map. Confidence: medium.

Classification: unassigned sleep source. The advice must not rely on a species
default when the move is unrevealed and a teammate can plausibly own the sleep
job.

Score: pass.

## Scenario 2 - Snorlax May Be The Sleep Source

Public state:

```text
Vanilla GSC. Gengar just absorbed Cloyster Explosion and now faces unrevealed
Snorlax. Your Exeggutor is healthy and expendable as a Sleep Clause absorber.
Gengar has not revealed Hypnosis. Snorlax may be Lovely Kiss / Double-Edge /
Earthquake / Explosion.
```

Tempting move: stay in with Gengar and use Hypnosis.

Frozen answer: switch Exeggutor if it is the intended sleep absorber and
Gengar's route job is more valuable awake. Confidence: medium.

Classification: team-level sleep assignment. The line should ask which side's
sleep source is live, not just which active Pokemon commonly has a sleep move.

Score: pass.

## Scenario 3 - Preserve The Sleeper After Sleep Lands

Public state:

```text
Vanilla GSC. Snorlax used Lovely Kiss and put Exeggutor to sleep. Exeggutor is
at 94%, has shown Psychic, and has no revealed Sleep Talk. Sleep Clause now
blocks further opponent sleep. Cloyster can enter and set Spikes.
```

Tempting move: stay in to burn sleep turns.

Frozen answer: switch Exeggutor out and preserve it as Sleep Clause material
unless Exeggutor has an active route that is worth more. Confidence: high.

Classification: sleep-clause preservation. The sleeping Pokemon is a resource,
not a wake-up project.

Score: pass.

## Scenario 4 - Price Damage Plus Recoil Before Pivoting

Public state:

```text
Vanilla GSC. Raikou is at 79% against Snorlax at 83%. Spikes are on both
sides. Sleep Clause is already active because Exeggutor is asleep. Raikou has
revealed Hidden Power Ice. Snorlax has revealed Lovely Kiss and may have
Double-Edge, Earthquake, and Explosion.
```

Tempting move: switch immediately because Snorlax is in front of Raikou.

Frozen answer: stay with Hidden Power Ice if Raikou survives Double-Edge and
the chip plus recoil puts Snorlax into a better range. Confidence: medium.
Re-solve next turn; once Raikou is in KO range, switch to the absorber that
covers Earthquake if that branch is likely.

Classification: priced damage trade into coverage-aware absorber. The first
turn can be a survivable chip trade; the next turn cannot repeat it.

Score: pass.

## Resulting Checklist

When an early GSC offense position involves sleep:

1. Is the sleep source actually revealed, or am I assigning it by species?
2. If Snorlax can own the sleep job, what does that free Exeggutor or Gengar
   to do?
3. Once sleep lands, should the sleeper leave immediately as Sleep Clause
   material?
4. If Snorlax starts attacking after Sleep Clause is active, can the active
   Pokemon survive one hit and make recoil matter?
5. After a priced damage trade, which absorber covers the most likely coverage
   branch?

## Next Study Target

Fresh replay transfer focused on unassigned sleep source, post-sleep doubles,
and damage/recoil pricing into Snorlax.
