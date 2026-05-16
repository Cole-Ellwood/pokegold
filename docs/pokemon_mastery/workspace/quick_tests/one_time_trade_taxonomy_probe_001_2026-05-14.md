# One-Time Trade Taxonomy Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_075_cashout_before_status_transfer_gen2ou-2595963523_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 075's
one-time trade misses can be restated as forced action classes. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_075_cashout_before_status_transfer_gen2ou-2595963523_2026-05-14.md`

## Score Summary

Scenarios: 5.

Action-policy hits: 5 / 5.

Classification hits: 5 / 5.

Route-job hits: 5 / 5.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating this taxonomy as stable.

## Scenario 1 - Explosion Before Another Reset

Public state:

```text
Vanilla GSC spectator-public state. Your Steelix is at 69% with +1 Attack and
+1 Defense, facing Zapdos at 100%. Steelix has revealed Curse, Earthquake, and
Roar. Zapdos has revealed Thunder and Hidden Power that damages Steelix. Roar
can reset the board, but Zapdos can keep taking value if Steelix only phazes.
```

Tempting move: Roar because Steelix has already used it successfully.

Frozen answer: use Explosion when phazing no longer improves the route and the
active Flying target is the converter Steelix can only remove by cashing out.
Roar is correct only if the dragged matchup reliably improves more than the
trade. Confidence: medium.

Classification: Explosion before phaze/reset.

Score: pass.

## Scenario 2 - Destiny Bond Is A Cash-Out

Public state:

```text
Vanilla GSC spectator-public state. Your Gengar is at 80% and faces Exeggutor
at 62%. Gengar has Thunderbolt and may have coverage, but Exeggutor threatens
Psychic. Gengar's ordinary attack may not cleanly remove Exeggutor before
Gengar is KOed.
```

Tempting move: Ice Punch or another direct coverage attack.

Frozen answer: use Destiny Bond when the active target will KO Gengar and the
guaranteed trade is the route. Treat Destiny Bond as the same one-time-trade
family as Explosion, with the same absorber and timing checks. Confidence:
medium.

Classification: Destiny Bond cash-out.

Score: pass.

## Scenario 3 - Preserve Before Bad Explosion

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster is at 50% and has set Spikes
and poisoned opposing Cloyster. Opposing Cloyster is at 66% and has revealed
Hidden Power that heavily damages your Cloyster. You have a healthy Gengar that
can enter through Spikes and take Hidden Power while keeping Cloyster available.
```

Tempting move: Explosion because Cloyster is low and has already set Spikes.

Frozen answer: switch Gengar or otherwise preserve Cloyster when Explosion
does not clearly remove the target and the pivot covers the opponent's best
move. Low support is not spent support until the future job and damage math say
so. Confidence: medium.

Classification: preserve over bad cash-out.

Score: pass.

## Scenario 4 - Absorb The Opposing Boom

Public state:

```text
Vanilla GSC spectator-public state. Your Snorlax is at 93% and faces opposing
poisoned Cloyster at 36%. Your own Cloyster is low but can enter. Opposing
Cloyster has little long-term value and can explode into Snorlax.
```

Tempting move: Double-Edge because Cloyster is low and Snorlax can finish it.

Frozen answer: switch Cloyster into Explosion when preserving Snorlax is the
route and the low Cloyster can act as the absorber. Attack only if Explosion is
not the best-priced opponent branch or if the absorber is still irreplaceable.
Confidence: medium-high.

Classification: absorber switch into one-time trade.

Score: pass.

## Scenario 5 - Endgame Converter Cash-Out

Public state:

```text
Vanilla GSC spectator-public state. Your Snorlax is at 57% against a fresh
Vaporeon that can use Growth. Later, your Exeggutor is low against the
opponent's last Snorlax while your Alakazam remains hidden in the back. Both
your Snorlax and Exeggutor have one-time KO trades available.
```

Tempting move: keep attacking normally to preserve famous species.

Frozen answer: spend the one-time trade when it removes the current endgame
converter and leaves a named follow-up. Snorlax Self-Destruct into Growth
Vaporeon and Exeggutor Explosion into last Snorlax are correct because slow
play lets the converter act. Confidence: high.

Classification: endgame conversion cash-out.

Score: pass.

## Resulting Checklist

Before choosing or rejecting a one-time trade:

1. Is the active target a converter, blocker, or expendable support piece?
2. Is the one-time move Explosion, Self-Destruct, Destiny Bond, sacrifice, or a
   forced absorber switch?
3. Does the trade remove a route problem, or only spend a piece because it is
   low?
4. What absorber, immunity, Protect-like timing, miss, switch, or phaze makes
   the trade fail?
5. If preserving, what pivot covers the opponent's best move and what future
   job remains?

## Next Transfer Check

Run a fresh no-keyword-screen replay with `cashout_boundary.md` and
`branch_action_after_naming.md` loaded. Score one-time trade taxonomy: Explosion
before reset, Destiny Bond as cash-out, absorber switch into boom, preserve
over bad boom, and endgame conversion.
