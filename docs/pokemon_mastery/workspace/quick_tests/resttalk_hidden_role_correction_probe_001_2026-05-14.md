# RestTalk Hidden Role Correction Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the RestTalk overcorrection and hidden-role voluntary-entry misses
from the `920928` transfer before another fresh replay.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/workspace/quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

RestTalk boundary hits: 2 / 2.

Hidden-role pricing hits: 2 / 2.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - Revealed RestTalk, No Better Owner

Public state:

```text
Vanilla GSC spectator-public style. Your Zapdos has revealed Rest, Sleep Talk,
and Thunder. It is asleep in a mirror-like or neutral board. No teammate with a
clear public job has been revealed yet.
```

Tempting move: switch because a sleeping Pokemon is often saved.

Frozen answer: stay and use Sleep Talk unless the opponent's next branch has a
known better owner. Confidence: medium.

Classification: revealed RestTalk can stay.

Score: pass.

## Scenario 2 - Revealed RestTalk, Known Branch Owner

Public state:

```text
Vanilla GSC spectator-public style. Your RestTalk Zapdos is asleep, but the
opponent has moved into Snorlax pressure. Your Skarmory is known and healthy
enough to own the Snorlax board.
```

Tempting move: Sleep Talk because RestTalk was just revealed.

Frozen answer: switch to the known branch owner. RestTalk is not a reason to
leave the wrong Pokemon active once the better owner is public. Confidence:
medium.

Classification: RestTalk handoff.

Score: pass.

## Scenario 3 - Odd Voluntary Entry As Lure Evidence

Public state:

```text
Vanilla GSC spectator-public style. Your Miltank voluntarily enters Cloyster.
The ordinary role would suggest Heal Bell or passive support, but the entry
looks bad unless Miltank has a lure move or a specific job.
```

Tempting move: assign the standard cleric role and click Heal Bell.

Frozen answer: raise the prior on a lure or off-standard move before assigning
the standard role. If Thunder or another direct punish is plausible, price it
as the route action without claiming it as fact. Confidence: low-medium.

Classification: voluntary entry signals hidden-role possibility.

Score: pass.

## Scenario 4 - Active Pressure Into A Named Receiver

Public state:

```text
Vanilla GSC spectator-public style. Your Miltank faces a very low Cloyster.
The opponent may preserve Cloyster by handing to Gengar. Thunder or another
active attack still damages both the active target and the Ghost receiver.
```

Tempting move: count active pressure as correct without naming the receiver.

Frozen answer: active pressure is clean only if the receiver is named first and
the damage changes that receiver board. Confidence: medium.

Classification: active pressure into receiver with branch named.

Score: pass.

## Resulting Checklist

Before choosing in this boundary:

1. Is RestTalk actually revealed, or am I assigning it from species?
2. If revealed, does the sleeping Pokemon own this board better than any known
   teammate?
3. Did an odd voluntary entry imply a lure or off-standard role?
4. If I keep active pressure, did I name the likely receiver and why the move
   still improves that board?

## Next Transfer Check

Run one fresh no-keyword-screen replay transfer and score:

- RestTalk revealed-stay;
- RestTalk handoff to known branch owner;
- hidden-role voluntary-entry pricing;
- active pressure into named receiver.
