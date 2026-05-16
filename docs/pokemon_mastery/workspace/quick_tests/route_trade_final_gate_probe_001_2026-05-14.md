# Route Trade Final-Gate Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_025` turn-25 miss into six compact
prompts that force the final choice after support has been delivered:
Explosion, preservation, or double-switch when an absorber branch exists.

This is not final-exam evidence. The prompts were built after studying the
policy and prior replay, so the score is a regression/checklist result, not a
fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_025_route_trade_timing_transfer_smogtours-gen2ou-934874_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/route_trade_timing_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`

Source note: Spikes and Toxic make the eventual trade better, but the
Explosion guide's anti-Explosion advice and the Forretress source both keep the
final gate honest: the opponent can use a low-value or immune absorber, and a
low Forretress can still have route value through typing, Spikes, Toxic, Spin,
or later Explosion pressure.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 2 and 4 need fresh replay transfer
because they are the closest to the `replay_turn_pause_025` miss: the exploder
has completed Toxic/Spikes, is low, and Explosion feels natural, but the
absorber or double-switch branch may make preservation better.

## Scenario 1 - Exact Target Stays

Public state: vanilla GSC, player-side known set. Our Forretress is 32% with
Spikes / Toxic / Rapid Spin / Explosion. Opposing Snorlax is active at 68%,
badly poisoned, at `atk+2 def+2 spe-2`, and has Curse / Double-Edge / Rest
revealed. Spikes are up on both sides. The opponent's only revealed bench
members are Zapdos at 38% and Starmie at 44%, both in range after Spikes and
Explosion aftermath. Our Raikou converts if Snorlax is gone.

Frozen answer: use Explosion. Confidence: high. The route is exact-target
cash-out: Snorlax is staying or must risk losing the game, Forretress has
delivered Toxic and Spikes, and delay gives Rest or another attack. Serious
alternatives: Toxic/Spikes are already complete; preserving Forretress is only
better if a Ghost or low-value absorber is likely. Worst branch: Snorlax
switches to a sack and Forretress loses its one-time trade.

Policy key: support completion plus exact active target can meet the final
gate.

Grade: complete.

## Scenario 2 - Absorber Branch Makes Preservation Better

Public state: vanilla GSC, spectator-public style. Our Forretress is 23% with
Toxic and Spikes revealed. Opposing Snorlax is active at 94%, badly poisoned,
and at `atk+1 def+1 spe-1`. The opponent has not revealed all six Pokemon.
Their Skarmory is asleep but has Sleep Talk revealed, and a Normal-resistant
absorber such as Golem, Steelix, or Ghost is plausible from team structure.
Forretress still resists Snorlax, can reset Spikes later, and can threaten
Explosion again.

Frozen answer: preserve Forretress or pivot, not automatic Explosion.
Confidence: medium-high. The route is to keep the final trade threat while
letting poison, Spikes, and a safer absorber advance the Snorlax clock.
Serious alternative: Explosion only if Snorlax staying is strongly forced or
Forretress has no future route utility. Worst branch: Snorlax stays and
attacks while preservation gives up a clean removal chance.

Policy key: low HP plus completed support is not enough; price the absorber
and future-utility branches before cashing out.

Grade: complete.

## Scenario 3 - Double-Switch Catches The Absorber

Public state: vanilla GSC, player-side known team. Our Cloyster is 41% with
Spikes / Toxic / Surf / Explosion. Opposing Snorlax is active at 62%, badly
poisoned, and has repeatedly switched out of Explosion pressure. The opponent
has revealed Gengar at 82% as the Explosion absorber and Starmie at 70% as the
spinner. Our Tyranitar is healthy and traps or pressures Gengar.

Frozen answer: double-switch Tyranitar into the likely Gengar, not Explosion.
Confidence: medium. The route is to punish the absorber that would make
Explosion fail while preserving Cloyster's Spikes/Explosion threat for later.
Serious alternatives: Surf if Snorlax staying is likely; Explosion only if the
Gengar branch no longer preserves the opponent's route. Worst branch: Snorlax
stays in and Cloyster misses the immediate trade window.

Policy key: when the absorber is known and likely, the route action can be the
double-switch that punishes it.

Grade: complete.

## Scenario 4 - Preserve Because The Exploder Still Has A Job

Public state: vanilla GSC, player-side known set. Our Forretress is 28% with
Spikes / Rapid Spin / Toxic / Explosion. Opposing Snorlax is poisoned and at
55%, but the opponent's Starmie is healthy and has Rapid Spin / Recover
revealed. Spikes are currently up on our side and absent from theirs. Our
Forretress is the only spinner and the only way to re-set Spikes after Starmie
removes them.

Frozen answer: preserve Forretress and either Rapid Spin or pivot depending on
the immediate board; do not Explosion into Snorlax yet. Confidence: high. The
route is hazard control: spending Forretress may remove or dent Snorlax but
loses the entire Spikes-removal subgame. Serious alternative: Explosion only
if Snorlax wins immediately and no other answer exists. Worst branch: Snorlax
Rests or attacks while Forretress preserves too cautiously.

Policy key: final-gate accounting includes the user's remaining job, not only
the target's value.

Grade: complete.

## Scenario 5 - Attack Before Trade

Public state: vanilla GSC, player-side known set. Our Cloyster is 54% with
Surf / Toxic / Spikes / Explosion. Opposing Snorlax is at 29%, badly poisoned,
and has no Rest revealed. The opponent has Golem at 100% revealed and likely
to absorb Explosion. Surf plus poison puts Snorlax in forced range even if it
stays, and it punishes Golem enough for Zapdos later.

Frozen answer: use Surf. Confidence: medium-high. The route is to cover both
branches: hit Snorlax if it stays and avoid donating Explosion to Golem.
Serious alternative: Explosion only if Surf fails to stop a route-ending Rest
or attack. Worst branch: Snorlax survives Surf and uses Self-Destruct or Rest.

Policy key: if ordinary damage covers stay and absorber branches better than
Explosion, use ordinary damage.

Grade: complete.

## Scenario 6 - Explosion As Anti-Reset

Public state: vanilla GSC, player-side known set. Our Cloyster is 36% with
Toxic / Spikes / Surf / Explosion. Opposing Snorlax is at 64%, not poisoned,
and has Curse / Rest / Double-Edge revealed. Spikes are up. The opponent's
only revealed absorber is Skarmory at 21%, which dies to Surf or Spikes later.
If Snorlax gets Rest this turn, the route resets and Cloyster is unlikely to
get another chance.

Frozen answer: use Explosion. Confidence: high. The route is anti-reset:
ordinary support has already been delivered and the cost of delay is Rest
undoing the clock. Serious alternatives: Toxic only if it lands before Rest
and still traps Snorlax in a losing cycle; Surf is too weak unless it creates
guaranteed range. Worst branch: Skarmory catches Explosion or Snorlax survives
and rests later anyway.

Policy key: when delay gives a reset that invalidates the whole route,
Explosion can be correct even with a possible low-value absorber.

Grade: complete.

## Resulting Rule

Final-gate questions after support is delivered:

1. Is the exact target forced to stay or strongly likely to stay?
2. What absorber, Ghost, Normal resist, or low-value sack is plausible?
3. Does the exploder still own a future job: Spin, Spikes, Toxic, walling, or
   later trade pressure?
4. Does ordinary damage or a double-switch cover both stay and absorber
   branches better than Explosion?
5. Does delay give Rest, setup, recovery, Spin, or escape that invalidates the
   route?

## Next Study Target

Run a fresh replay or paused-turn segment where a low exploder has already
delivered support, and score whether the final-gate questions prevent another
automatic Explosion overcall.
