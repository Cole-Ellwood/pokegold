# Voluntary Entry Triad Probe 001 - 2026-05-15

Status: constructed/nonblind regression drill. This does not count as fresh
progress proof.

Parent review:
`reviews/role_package_plateau_loop_review_002_2026-05-15.md`

Rule being drilled:

```text
When a Pokemon voluntarily enters a threat, classify it as:
direct coverage owner / absorber / bait-handoff.
Hidden coverage cannot outrank the public route unless revealed, side-known,
or explicitly a high-risk read with fallback.
```

## Score

Policy hits: 6/6.

Severe blunders: 0.

Hidden-info errors: 0.

## Prompts And Expected Answers

### 1. Zapdos Enters Nidoking Before Sleep Lands

Public state: Nidoking has revealed Lovely Kiss. Zapdos voluntarily enters and
has not revealed Hidden Power or Sleep Talk.

Expected classification: absorber transaction.

Expected answer: top line is to let Zapdos take or threaten to take sleep, then
handoff after Sleep Clause is active. Hidden Power is only side-known or a
high-risk read with fallback.

### 2. Zapdos Is Now Asleep Versus Nidoking

Public state: Zapdos is asleep after Lovely Kiss. Sleep Talk is not revealed.
Nidoking may carry mixed coverage.

Expected classification: post-clause handoff.

Expected answer: preserve sleeping Zapdos if it still has future absorber or
sack value; hand off to the Nidoking owner such as Snorlax/Cloyster/Steel by
class. Do not burn sleep turns as generic progress.

### 3. Dragonite Enters Toxic Golem

Public state: Golem has Earthquake and Toxic status. Dragonite voluntarily
entered Earthquake. Dragonite has no revealed moves.

Expected classification: absorber or bait-handoff first, direct coverage only
if side-known.

Expected answer: Dragonite publicly blocked Earthquake and forced a new owner
decision. Do not make hidden Surf/Thunder the main line unless side-known.
Name the likely Golem exit and our handoff into that exit.

### 4. Dragonite Faces Cloyster

Public state: Dragonite has no revealed moves. Cloyster can set Spikes, Spin,
Ice Beam, or Explode. Raikou is unrevealed but later proved to be the actual
handoff.

Expected classification: possible bait-handoff.

Expected answer: if Dragonite's Electric coverage is side-known, attack. In
spectator-public mode, rank the public route first: Cloyster's package is
hazard/reset/Explosion, so switch or hand off to the Electric/Water owner class
unless Dragonite coverage is revealed or explicitly read-based.

### 5. Gengar Enters Snorlax Double-Edge

Public state: Snorlax revealed Double-Edge. Gengar voluntarily enters and
blanks it.

Expected classification: absorber/reset of the Normal route.

Expected answer: Snorlax must not repeat Normal pressure. Switch to the Gengar
owner, use revealed coverage if it exists, or price a high-risk self-destruct
read. For Gengar's side, the next branch is often a double to the Gengar
owner's counter, not just staying in.

### 6. Sleeping Umbreon Returns Into Gengar

Public state: Umbreon is asleep but has revealed Pursuit. Gengar revealed
Thunderbolt. Sleep Clause is already active.

Expected classification: absorber with a later job.

Expected answer: sleeping Umbreon can still be the public Gengar owner. Staying
to burn sleep or switching depends on whether Gengar exits, but the sleeper is
not dead weight and should not be abandoned without naming the new Gengar
owner.

## Next Fresh Check

The next fresh replay should fail fast if it repeats the same mistake twice:

```text
voluntary entry -> hidden coverage top
```

The acceptable correction is:

```text
voluntary entry -> direct coverage / absorber / bait-handoff -> public owner
```
