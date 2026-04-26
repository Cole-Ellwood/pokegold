# Codex Curiosity Note: Boss AI's Public Imagination

This was not a requested feature, bug fix, or productivity pass. I followed the
part of the repo that interested me: how the custom boss AI tries to become
strong without becoming omniscient.

## What Caught Me

The interesting shape is not "the AI knows things." The interesting shape is
that the AI has a model of what kind of ignorance it is allowed to have.

`engine/battle/ai/boss.asm` splits player-threat knowledge into two masks:

- `wBossAIPlausibleTypeMaskCache`: this damaging type is legal enough to respect.
- `wBossAILikelyTypeMaskCache`: this damaging type is higher-confidence.

That distinction matters. STAB, revealed damaging move types, and current
species level-up moves at or below the active level go into both buckets. TM/HM
coverage, egg moves, and pre-evolution-only moves go into possible only.
Hidden Power becomes a special risk bit instead of an exact private type read.

I first expected the Dragon package to dominate the AI's public imagination,
especially after the recent "Dragons should feel godly" work. That was the
wrong expectation. Dragonite and Kingdra are scary, but the public-risk model is
more fascinated by broad TM/HM coverage than by theme. The code is less
mythological than I was for a minute.

## Disposable Probe Result

I ran a read-only Python probe over:

- `engine/battle/ai/boss.asm`
- `constants/battle_constants.asm`
- `constants/move_constants.asm`
- `constants/type_constants.asm`
- `data/moves/moves.asm`
- `data/pokemon/base_stats/*.asm`
- `data/pokemon/evos_attacks.asm`
- `data/pokemon/egg_moves.asm`

The probe approximated a fresh public-threat view with no revealed player moves:
STAB plus legal damaging TM/HM, level-up, egg, and pre-evolution-chain moves,
using `BOSS_AI_PLAUSIBLE_MIN_POWER EQU 45`.

At level 50, the largest possible-minus-likely gaps were:

```text
MEW          possible=16 likely= 3 gap=13
SNORLAX      possible=11 likely= 1 gap=10
NIDOQUEEN    possible=12 likely= 3 gap= 9
LUGIA        possible=12 likely= 3 gap= 9
SLOWKING     possible=11 likely= 2 gap= 9
LICKITUNG    possible=11 likely= 2 gap= 9
KANGASKHAN   possible=11 likely= 2 gap= 9
HO_OH        possible=11 likely= 2 gap= 9
BLISSEY      possible=10 likely= 1 gap= 9
```

Some texture at level 50:

```text
DRAGONITE    possible=10 likely=3
GYARADOS     possible= 8 likely=4
AMPHAROS     possible= 7 likely=2
KINGDRA      possible= 5 likely=2
BLISSEY      possible=10 likely=1
QUAGSIRE     possible= 9 likely=3
WOBBUFFET    possible= 1 likely=1
UNOWN        possible= 2 likely=2
SMEARGLE     possible= 1 likely=1
DITTO        possible= 1 likely=1
```

The Smeargle and Ditto result is the funniest edge of the model. A human sees
Smeargle and thinks, "This could be anything." The non-cheating public model
mostly sees Normal unless a move has actually been revealed. That is probably
right for this code's moral universe: representing Sketch's entire possibility
space without hidden knowledge would be either uselessly huge or quietly unfair.

## The Sentence I Ended On

Good non-cheating AI is not an AI that refuses to think. It is an AI that knows
which kind of uncertainty it is allowed to spend.

No behavior changed. I did not run a ROM build because this was a read-only
curiosity pass, not an implementation pass.
