# CurseBoom Phaze Timing Probe 001 - 2026-05-15

Status: constructed/nonblind regression drill. This does not count as fresh
progress proof.

Parent packet:
`workspace/quick_tests/post_triage_curseboom_transfer_001_smogtours-gen2ou-931588_2026-05-15.md`

Source check:
- Smogon GSC move priority article: Roar and Whirlwind are `-1` priority, so
  the phazer takes normal attacks or Self-Destruct before the phaze resolves.

Rule being drilled:

```text
Before phazing a boosted boom user, check whether the phazer survives the hit
that moves first. If not, rank Curse, switch to a resist, sack, or direct KO
before generic phaze.
```

## Score

Policy hits: 4/4.

Severe blunders: 0.

Mechanics errors: 0.

## Prompts And Expected Answers

### 1. Full Skarmory Into +2 Snorlax

Public state: Skarmory is full. Snorlax is +2 Attack/+2 Defense, has revealed
Curse, and Self-Destruct is a strong-prior branch but not revealed.

Expected answer: do not autopilot Whirlwind. First ask whether unboosted
Skarmory survives +2 Self-Destruct before negative-priority phaze. If not,
Curse or switch to the planned resist/sack is the top branch-punish; Whirlwind
is top only when the boom branch is covered or survival is confirmed.

### 2. Low Skarmory Into Known Self-Destruct Lax

Public state: Skarmory is low. Snorlax has revealed Self-Destruct and Curse.

Expected answer: switch to a resist, Ghost, or deliberate sack if available.
Whirlwind is not a reset because the explosion moves first. Staying is correct
only if Skarmory is the chosen sack or survives the damage range.

### 3. Phazer Has Sleep Talk Whirlwind

Public state: a sleeping phazer has revealed Sleep Talk and Whirlwind. The
opponent may attack or set up.

Expected answer: separate normal Whirlwind from Sleep Talk-called Whirlwind.
Sleep Talk can call Whirlwind at normal priority, but the branch is random and
must be priced against the attack, Rest, or setup branch.

### 4. Golem Versus Snorlax With Explosion Threat

Public state: Golem is in versus Snorlax. Golem has Earthquake and strong-prior
Explosion. Snorlax has revealed Earthquake and is central to the route.

Expected answer: if Explosion would trade into central Snorlax, switch to the
chosen resist/sack or Ghost when available. Staying to attack is top only when
side-known coverage, damage, or lack of absorber makes the trade acceptable.

## Next Fresh Check

The next fresh replay should fail fast if either pattern repeats twice:

```text
voluntary entry -> hidden coverage top
boosted boom user -> generic phaze without survival check
```
