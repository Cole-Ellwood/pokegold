# Support-Set Hidden Role Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the support-set hidden-role misses from `920961` before another
fresh transfer.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`

Web/current sources checked:

- Smogon, `Playing with Spikes in GSC`.
- Smogon, `Introduction to Status in GSC`.
- Smogon Forums, `Forretress (OU Revamp) Done`.

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Support-role route hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - RestTalk Setup Still Needs A Handoff Check

Public state:

```text
Vanilla GSC spectator-public style. Your Jolteon has revealed Rest, Sleep Talk,
Thunderbolt, and Growth. It is asleep at high HP after Sleep Talk selected
Growth. Opposing Snorlax is active and has revealed Curse and Earthquake. Your
Forretress is known and healthy enough to take Earthquake and change the route.
```

Tempting move: stay with Jolteon because Growth makes Sleep Talk look active.

Frozen answer: switch to Forretress unless the Electric boost immediately
changes the Snorlax board. Revealed RestTalk plus setup is not proof to stay
when a known teammate owns the physical branch better. Confidence: medium.

Classification: RestTalk setup handoff.

Score: pass.

## Scenario 2 - Toxic Before Spikes When Snorlax Is The Clock

Public state:

```text
Vanilla GSC spectator-public style. Your Forretress faces Snorlax before your
Spikes are down. Snorlax has shown Curse and Earthquake and can become the
route converter if left unclocked. Forretress has Toxic, Spikes, Rapid Spin,
and a hidden fourth move.
```

Tempting move: always set Spikes first because Forretress is the Spiker.

Frozen answer: use Toxic first when poisoning Snorlax forces Rest, makes later
Spikes/phaze damage meaningful, or denies a free Curse route. Set Spikes first
only when the layer changes more than the poison clock or Snorlax cannot
convert now. Confidence: medium.

Classification: support move before default role move.

Score: pass.

## Scenario 3 - Curse Skarmory Is A Route Role, Not Just A Phazer

Public state:

```text
Vanilla GSC spectator-public style. Your Skarmory has entered on a poisoned
Snorlax after Snorlax revealed Curse, Earthquake, Double-Edge, and Rest.
Skarmory has not revealed a move yet. You need to stop Snorlax from converting
while keeping the poison and Spikes route live.
```

Tempting move: assume Skarmory's only support job is immediate phazing.

Frozen answer: price Curse as a live support role before defaulting to
Whirlwind. Curse is correct when matching boosts keeps Skarmory from being
overwhelmed and improves the next Snorlax board; Whirlwind is correct when the
hazard loop is already converting or Snorlax cannot be allowed another turn.
Confidence: medium.

Classification: hidden setup support on a standard phazer species.

Score: pass.

## Scenario 4 - Phaze To Break Trap

Public state:

```text
Vanilla GSC spectator-public style. Opposing Misdreavus has trapped your Zapdos
with Mean Look. Misdreavus has revealed Mean Look, Perish Song, and Destiny
Bond. Your Zapdos has revealed Thunderbolt and has not yet revealed its support
move.
```

Tempting move: attack with Zapdos because the Electric matchup looks active.

Frozen answer: use Whirlwind if available to break the trap route immediately.
Direct Electric pressure is only better if it prevents Perish Song or Destiny
Bond from mattering more reliably than phazing. Confidence: medium-high.

Classification: support move beats the named route, not just the active
Pokemon.

Score: pass.

## Resulting Checklist

Before choosing in this boundary:

1. Did a revealed RestTalk setup piece still need a better branch owner?
2. Is the support piece's best move the species-default job, or a clock-setting
   move such as Toxic first?
3. Does a standard phazer have setup support that changes the active route?
4. Is the opponent's real route trap, setup, hazard conversion, or forced
   switch, and does a support move beat that route better than damage?

## Next Transfer Check

Run a fresh no-keyword-screen replay transfer and score support-set hidden
roles separately from coverage lures: RestTalk setup handoff, Toxic or status
before default utility, Curse or setup on a standard support piece, and phaze
or forced-switch support that breaks a trap or setup route.
