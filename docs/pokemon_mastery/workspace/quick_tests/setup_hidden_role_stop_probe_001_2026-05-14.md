# Setup Hidden Role Stop Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the `921389` misses where setup or support reveals changed whether
the active Pokemon should keep pressure, leave, or treat phazing as the real
counter-handoff.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/workspace/quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`

Web/current sources checked:

- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, `Tyranitar (OU Revamp) [Done]`:
  `https://www.smogon.com/forums/threads/tyranitar-ou-revamp-done.3658517/`
- Smogon Forums, `GSC OU Snorlax`:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, `GSC OU Threatlist`:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Setup/support stop-condition hits: 4 / 4.

State-explicitness hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - Substitute Makes The Counter-Answer Temporary

Public state:

```text
Vanilla GSC spectator-public style. Your Rhydon has revealed Substitute,
Curse, and Earthquake. It is behind a Substitute at high HP and has just drawn
Starmie, which has not yet revealed Surf. Spikes are on your side.
```

Tempting move: switch immediately because Starmie is the obvious Rhydon answer.

Frozen answer: keep Earthquake or Curse-plus-Earthquake pressure live until the
Substitute, Starmie's attack, and the recovery clock prove Rhydon is forced
out. Confidence: medium.

Classification: setup changes the apparent counter-handoff.

Score: pass.

## Scenario 2 - Broken Substitute Restores The Forced-Switch Check

Public state:

```text
Vanilla GSC spectator-public style. Your Rhydon had a Substitute, but Starmie
has now revealed Surf and broken it. Rhydon is boosted, Starmie is low, and
Starmie has Recover. Rhydon can Earthquake again or leave for a special owner.
```

Tempting move: keep attacking because the previous Earthquake nearly converted.

Frozen answer: explicitly re-score HP, Substitute state, Surf damage, Recover,
and speed before declaring either stay or switch. If Earthquake still forces
Recover without dying, attack is live; if Surf now removes Rhydon before it
acts, hand off. Confidence: medium.

Classification: state-explicit stop condition after setup is removed.

Score: pass.

## Scenario 3 - RestTalk Is An Active Job, Not Just Sleep

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax has revealed Rest and Sleep
Talk after using Double-Edge earlier. It is asleep against Tyranitar, which has
shown Rock Slide but not yet Roar. Snorlax may roll Earthquake, Double-Edge, or
Rest from Sleep Talk.
```

Tempting move: always switch the sleeping Snorlax out to preserve Sleep Clause
value.

Frozen answer: Sleep Talk can be the active job if its rolls punish Tyranitar
or preserve the route better than a handoff. Stay is correct only if the roll
map and worst branch are named; switch if Tyranitar's support move or setup
beats the sleeping active. Confidence: medium.

Classification: revealed RestTalk stay versus handoff.

Score: pass.

## Scenario 4 - Phaze Support Is The Counter-Handoff

Public state:

```text
Vanilla GSC spectator-public style. Opposing Snorlax or Rhydon is trying to
keep a setup route active. Your Tyranitar is in, has Rock Slide, and may have
Roar. Spikes are up or the opponent has a vulnerable forced-in teammate.
```

Tempting move: treat the counter-handoff as only a switch to a species answer.

Frozen answer: price Roar as the counter-handoff if it breaks the setup route,
drags a worse board, or converts Spikes. Attack first when Rock Slide damage is
the concrete route and phazing only resets without progress. Confidence:
medium.

Classification: phaze support as counter-handoff.

Score: pass.

## Resulting Checklist

Before choosing in this boundary:

1. Is the active protected by Substitute, RestTalk, boosts, or a phaze threat?
2. Has the protection actually been removed, or am I assuming the counter works
   from species alone?
3. If the active stays, what exact damage, recovery, Sleep Talk roll, or phaze
   branch makes progress?
4. If the active leaves, which teammate owns the current punish and what is
   lost by giving up the active route now?
5. Is plain damage still the best line after all handoff branches are named?

## Next Transfer Check

Run a fresh no-keyword-screen replay transfer and score setup-hidden-role stop
conditions separately: Substitute state, RestTalk stay or handoff, phaze as a
counter-handoff, and active damage over speculative loops.
