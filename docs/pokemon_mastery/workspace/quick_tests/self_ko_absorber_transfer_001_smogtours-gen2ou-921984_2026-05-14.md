# Self-KO Absorber Transfer 001 - smogtours-gen2ou-921984 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-921984`.

Context source: Smogon GSC OU Winter Seasonal #8 Round 9 replay post.

Mode: focused fresh replay transfer. This is a sealed turn-pause segment that
advanced from the public opener until the first route-relevant self-KO threat.
It is not a 30-decision primary gate.

Contamination control:

- Local docs were searched for `921984`; no prior local use was found.
- Web search confirmed the replay link in the Smogon Winter Seasonal Round 9
  thread.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Turns were revealed sequentially from the public opener until the first
  low-Cloyster trade threat into Snorlax appeared.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/explosion_absorber_resource_probe_001_2026-05-14.md`

## Score Summary

Target decisions: 1.

Top-match: 1 / 1.

Acceptable-match: 1 / 1.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Measurement status: focused fresh transfer only. This shows the replay 070
severe miss can be restated under pressure, but it does not replace a 30-50
decision fresh replay packet.

## Lead-Up

Public sequence before the target:

- p1 Zapdos used Thunder into lead Jynx, paralyzing it; Jynx used Thief and
  stole Zapdos's Leftovers.
- p1 Snorlax entered, then p1 Cloyster absorbed Lovely Kiss from Jynx.
- p2 Cloyster entered against sleeping p1 Cloyster, set Spikes, then switched
  out to Zapdos.
- p1 Snorlax entered through Spikes into Zapdos Thunderbolt.
- p2 Cloyster re-entered on Snorlax and took a critical Double-Edge, leaving it
  at 40% before Leftovers.

## Target Turn - Turn 9

Public state:

```text
Vanilla GSC spectator-public state. p1 Snorlax is active at 67% against p2
Cloyster at 40%. Spikes are on p1's side. p1 has Zapdos at 91% with no
Leftovers and sleeping Cloyster at 100%; other p1 slots are unrevealed. p2 has
paralyzed Jynx at 70% with Thief and Lovely Kiss revealed, Zapdos at 100% with
Thunderbolt revealed, and Cloyster with Spikes revealed.
```

Frozen answer:

- p1: switch sleeping Cloyster or another lowest-value absorber into the
  Explosion/Self-Destruct branch. Snorlax is a route piece for Zapdos, Jynx, and
  unknown special pressure; leaving it in is only correct if survival is
  clearly route-positive.
- p2: Explosion is the self-KO branch, but Toxic or Surf are serious
  alternatives because Cloyster may punish the absorber or preserve itself.

Actual choices: p1 switched sleeping Cloyster through Spikes. p2 used Toxic,
which failed because Cloyster was already asleep.

Grade: p1 top-match. The absorber line beat both the named self-KO branch and
the actual Toxic alternative.

## Error Classes

- No severe miss. The replay 070 failure was corrected in this focused spot:
  after naming the cash-out branch, the answer chose the absorber instead of
  leaving the route piece in.
- Remaining risk: this was a single target turn. The next proof still needs a
  fresh longer packet where the same checklist is applied without an obvious
  low-Cloyster setup.

## Policy Extraction

Trigger:
  A low Cloyster or other self-KO user has already done its support job and
  faces a route piece such as Snorlax.

Default:
  Switch the lowest-value absorber when that line also covers the non-boom
  punish, such as Toxic into an already-statused sleeper.

Exceptions:
  Stay with the route piece only when it survives the trade with a remaining job
  or when switching loses to the ordinary attack more than staying loses to
  Explosion.

Worst branch:
  You correctly name the boom, leave the route piece in anyway, and discover
  that the opponent's non-boom support option would also have been covered by
  the absorber.

Local status:
  Vanilla GSC replay evidence. Local romhack Explosion, Toxic, sleep, type,
  item, and AI behavior need local verification when decision-relevant.

Drill:
  In the next fresh full replay packet, require the answer to name both the
  self-KO absorber and the non-boom punish before choosing the move.
