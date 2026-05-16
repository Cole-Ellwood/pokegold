# Low Self-KO Review 001 - smogtours-gen2ou-831843 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-831843`

Parent transfer:
`workspace/quick_tests/low_self_ko_transfer_001_smogtours-gen2ou-831843_2026-05-14.md`

Mode: targeted expert replay review after reveal. This is not a fresh score.

Selected action:
Review turns 2, 6, and 12 to separate route-defining self-KO from merely
possible self-KO. The goal is to prevent both mistakes: staying with a valuable
piece into a live Explosion, and overcovering Explosion before the support
piece has a real reason to cash out.

## Turn 2 - Exeggutor Explosion Was Route-Defining

Public state:
Exeggutor was at 56% against Snorlax at 77%. Exeggutor had revealed Psychic.
Snorlax had revealed Double-Edge. No hazards were up and no absorber was public
for p1; p2's Tyranitar was unrevealed.

Actual:
p2 switched Tyranitar. p1 used Explosion into Tyranitar.

Why self-KO was live:

- Support delivered: partial. Exeggutor had already forced major Snorlax chip.
- Exact target: Snorlax was a central route piece and in range where Explosion
  could remove or heavily cripple it.
- Speed/order: Exeggutor could spend itself before taking another Double-Edge
  turn.
- Survival: Exeggutor did not safely remain a durable long-term route piece at
  56% into repeated Double-Edge.
- Absorber tier: Tyranitar was not revealed, but the defender may still use a
  side-known absorber. Spectator-public advice should at least name
  Rock/Ghost/Steel absorber as the worst branch.
- Active fallback: Psychic chip was useful but did not solve the Snorlax route
  as directly as the one-time trade.

Review conclusion:
For the exploding side, Explosion deserved top-three and likely top action. For
the defending side, the absorber was unknowable in spectator-public mode, but
the correct class was "cover the one-time trade if a lower-value absorber
exists."

## Turn 6 - Forretress Explosion Was Merely Possible

Public state:
p1 Snorlax was at 90%, +1 Attack/+1 Defense/-1 Speed, with Curse revealed.
p2 Forretress entered at 94% through Spikes. Forretress had revealed no moves.
p2 had not yet set Spikes.

Actual:
Forretress used Spikes. Snorlax used Fire Blast and KOed Forretress.

Why self-KO was not primary:

- Support delivered: no. Forretress had not yet placed Spikes.
- Exact target: boosted Snorlax was important, but Forretress had a support job
  that changed the route immediately.
- Speed/order: Forretress could act before slow Snorlax, but speed alone did
  not make cash-out correct.
- Survival: Snorlax could survive the support turn and had a hidden coverage
  route in the actual game.
- Absorber tier: a defender might have an absorber, but the stronger issue was
  that Explosion before Spikes would skip Forretress's main job.
- Active fallback: Fire Blast, if available to the player, was a direct route
  converter that beat both the support and preservation lines.

Review conclusion:
Do not promote "Forretress can Explode" to the main branch before it has
delivered Spikes or before delay clearly lets the boosted target escape. The
first route question was whether Forretress gets support, not whether it booms.

## Turn 12 - Cloyster Explosion Was Covered, Not Chosen

Public state:
p1 Cloyster was at 64% with Spikes and Surf revealed, facing Snorlax at 72%.
p2 had a revealed Misdreavus at 100% with Growl. Spikes were on both sides.

Actual:
p2 switched Misdreavus. p1 used Surf into Misdreavus.

Why self-KO was live but not top for p1:

- Support delivered: yes. Cloyster had already set Spikes.
- Exact target: Snorlax was a valuable target, but p2 had a revealed Ghost
  absorber.
- Speed/order: Cloyster could move, but Explosion into a Ghost would fail.
- Survival: Cloyster still had enough HP and route job to use Surf or preserve
  itself rather than spend into a covered branch.
- Absorber tier: revealed. This is much stronger than possible-only.
- Active fallback: Surf punished the absorber switch while preserving
  Explosion and Cloyster's remaining utility.

Review conclusion:
This is the clean defensive mirror. The defender should cover Explosion with
Misdreavus; the exploding side should not boom into a revealed absorber when
Surf makes progress into that absorber.

## Extracted Gate

Self-KO becomes route-defining when most of these are true:

1. Prior job is delivered or irrelevant.
2. The target is exact and removing it opens a named converter.
3. Delay lets the target Rest, set up, phaze, trap, recover, or escape.
4. The self-KO user has no better future entry or job.
5. The absorber is absent, only possible, or too costly to use.
6. Active pressure does not improve the route enough.

Self-KO is merely possible when most of these are true:

1. The support job is not delivered yet.
2. The target is replaceable or not exact.
3. A revealed or side-known absorber covers the trade.
4. Active pressure, coverage, status, phaze, or support improves the same
   branch without spending the piece.
5. The self-KO user still has future utility or safe entry.

## Transfer Checklist

Before recommending a move around Explosion/Self-Destruct:

1. Is the one-time move `revealed`, `strong prior`, or `possible only`?
2. Has the self-KO user's prior support job been delivered?
3. What exact target does the self-KO remove, and who converts after?
4. What absorber tier exists: revealed, side-known, strong prior, or possible?
5. If we do not cover or cash out now, what route does active pressure,
   coverage, support, or preservation improve?

If the answer cannot name the target, converter, absorber tier, and fallback,
do not treat self-KO as the top branch. If it can name them and delay loses the
route, cover or spend the one-time move before generic active pressure.
