# Branch Coverage Spin Phaze Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_040` into a compact six-scenario drill.
The target is branch coverage: after naming the worst branch, choose an action
that actually covers it, improves it, or deliberately accepts it as a priced
trade.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, GSC OU Golem:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

Source note: the Spikes article supports treating Rapid Spin, spinblocking,
phazing, and pressure as a single subgame. The Golem analysis is especially
relevant because Golem compresses Normal resistance, Roar, Rapid Spin, and
Explosion. The Explosion source supports treating a one-time trade as a route
decision rather than a panic button.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-coverage hits: 6 / 6.

Route-job hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. These prompts were constructed after the
replay lesson, so the score checks retention and gives a next-transfer
checklist rather than estimating unseen skill.

## Scenario 1 - Clean Spin On A Forced Switch

Public state:

```text
Vanilla GSC. Our Golem is 93% against opposing Raikou at 93%. Spikes are on
both sides. Opponent has a poisoned Cloyster at 82% revealed with Spikes /
Toxic and no Ghost revealed. Our Golem has Earthquake / Rapid Spin / Roar
revealed. Zapdos and Snorlax in back want repeated entries.
```

Named worst branch: clicking Earthquake while Raikou switches lets our side
keep taking Spikes and turns Golem into only an Electric answer instead of a
support compressor.

Frozen answer: use Rapid Spin. Confidence: high.

Branch coverage: Rapid Spin covers the likely Raikou switch and improves every
future Zapdos/Snorlax entry. Earthquake is correct only if Raikou is likely to
stay or if removing Raikou now is the route.

Score: pass.

## Scenario 2 - Reset Spikes Before The Support Piece Is Spent

Public state:

```text
Vanilla GSC. Our poisoned Cloyster is 71% facing opposing Zapdos. Our Spikes
were just removed by Golem. Opponent still has Golem in reserve, but no Ghost
has been revealed. Zapdos threatens Thunder. Our Cloyster has Spikes / Toxic /
Surf and can survive one non-critical resisted or neutral sequence only
briefly.
```

Named worst branch: trying to win the active matchup with Surf while the hazard
route disappears gives Zapdos and Snorlax cheaper future entries.

Frozen answer: use Spikes if Cloyster survives the immediate turn; otherwise
switch only if a teammate preserves a stronger route. Confidence: medium-high.

Branch coverage: Spikes covers the lost-layer branch before Cloyster becomes
too low to support. Surf is better only if it removes Golem or another hazard
piece before a reset can matter.

Score: pass.

## Scenario 3 - Roar Into The Spinblocker

Public state:

```text
Vanilla GSC. Our Golem is 99% against poisoned opposing Cloyster at 43%.
Spikes are on both sides. Cloyster is likely to reset Spikes or switch to a
Ghost if it fears Rapid Spin. Our Golem has Rapid Spin / Roar / Earthquake
revealed. Opponent has not yet revealed Gengar, Misdreavus, or another Ghost.
```

Named worst branch: clicking Rapid Spin into a Ghost fails, while switching
Golem out lets Cloyster reset Spikes and preserve the removal subgame.

Frozen answer: use Roar. Confidence: medium-high.

Branch coverage: Roar covers both Cloyster staying for Spikes and a hidden
spinblocker entering; it forces Spikes damage and can expose the Ghost for the
next direct punish. Rapid Spin is clean only if the Ghost branch has already
been priced away.

Score: pass.

## Scenario 4 - Punish The Spinblocker Directly

Public state:

```text
Vanilla GSC. Roar has dragged in opposing Gengar at 93% through Spikes. Our
Golem is 100%, with Rapid Spin / Roar / Earthquake revealed. Spikes are on our
side. Gengar has no moves revealed yet, but it blocks Rapid Spin and may have
coverage.
```

Named worst branch: clicking Rapid Spin now wastes the turn into Ghost
immunity and lets Gengar attack or force Golem out.

Frozen answer: use Earthquake. Confidence: high.

Branch coverage: Earthquake covers the spinblock branch by removing or heavily
damaging the blocker. If Gengar has Hidden Power coverage, accepting that hit
is still better than letting the Ghost invalidate Spin for free.

Score: pass.

## Scenario 5 - Low-Resource Sack For Clean Entry

Public state:

```text
Vanilla GSC. Our Golem is 14% against opposing Espeon at 93%. Spikes are on
our side. Golem has Earthquake / Rapid Spin / Roar revealed, but if it switches
out, it re-enters through Spikes at about 1% and cannot reliably act. Our
Snorlax can enter after Golem faints and threatens Double-Edge. Espeon has
Psychic revealed.
```

Named worst branch: preserving Golem forces Snorlax to take both Spikes and
Psychic immediately, while Golem's future entry is fake.

Frozen answer: stay in and let Golem faint, unless Earthquake or Roar creates a
specific final route before it dies. Confidence: high.

Branch coverage: the sack covers the clean-entry branch. Switching preserves
the name "Golem" but not a usable resource.

Score: pass.

## Scenario 6 - Priced Explosion Trade, Not Covered Branch

Public state:

```text
Vanilla GSC. Our Zapdos is 79% facing opposing Exeggutor at 70%. Exeggutor has
Leech Seed / Protect / Psychic revealed and likely has Explosion or Sleep
Powder as the final move. Our Snorlax is 65% and still needed for the opposing
Snorlax. Spikes are on both sides. Zapdos has Hidden Power that is likely Ice
and Thunder revealed.
```

Named worst branch: Hidden Power into Explosion loses Zapdos, so the move does
not "cover" Explosion. It accepts the trade if Exeggutor is the support loop
piece that must be removed.

Frozen answer: use Hidden Power if removing Exeggutor opens the route and
Snorlax can handle the post-trade board; otherwise switch to an Explosion
absorber. Confidence: medium.

Branch coverage: this answer is explicit about the distinction. Hidden Power
covers the Leech Seed / Protect loop and Exeggutor staying, but it accepts
Explosion as a priced trade. If Zapdos is irreplaceable, the correct action
becomes absorber switch, not Hidden Power.

Score: pass.

## Resulting Checklist

Before finalizing a serious move in a branch-heavy turn:

1. Name the worst plausible branch.
2. Mark the chosen action as one of: covers, improves, accepts, or fails to
   address that branch.
3. If the action only accepts the branch, name the post-trade material that
   makes the acceptance worthwhile.
4. Discount "preserved" low-HP pieces that cannot re-enter through hazards and
   still act.
5. Check whether a support move, phaze, Spin, or sack covers more branches than
   direct damage.

## Next Study Target

Fresh replay transfer with branch-coverage scoring added to the turn table.
Stop early if the same error recurs twice: naming a punish while choosing a
line that still loses to that punish.
