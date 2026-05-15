# Screen Phaze Third Owner Probe 001 - 2026-05-14

Source parent:
`quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the `921412` misses around Reflect+Roar as one package,
Misdreavus as a third route owner in Electric loops, low Snorlax setup without
revealed Rest, and active damage before Rest or pivot scripts.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`

Web/current sources checked:

- Smogon Forums, `GSC OU Sample Teams Breakdown (Updated July 2023)`:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, `Introduction to Competitive GSC`:
  `https://www.smogon.com/smog/issue28/gsc`
- Smogon, `Introduction to Status in GSC`:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon, `GSC OU Threatlist`:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Boundary-condition hits: 4 / 4.

State-explicitness hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - Reflect And Roar Are One Package

Public state:

```text
Vanilla GSC spectator-public style. Your Raikou has just used Reflect against
an opposing Snorlax branch. Spikes are up on the opponent's side, Raikou has
revealed Thunderbolt and Reflect, and Roar is plausible but not confirmed by a
team sheet. Opponent can stay with Snorlax, switch to its Raikou, or use a
physical counter-pivot.
```

Tempting move: treat Reflect as a completed support job and immediately switch
to a generic Snorlax owner.

Frozen answer: if Roar is available or strongly represented by the public line,
score Reflect+Roar as one route package: Reflect softens the physical punish so
Raikou can Roar or attack through the Spikes cycle. Switch only if the named
counter-pivot beats both Thunderbolt and Roar or if Raikou's HP/status makes
the phaze route no longer live. Confidence: medium.

Classification: support action plus next-board handoff.

Score: pass.

## Scenario 2 - Misdreavus Is A Third Route Owner, Not A Generic Electric Answer

Public state:

```text
Vanilla GSC spectator-public style. Your Misdreavus enters during a Forretress
and Raikou loop. Spikes are up, Forretress can Spin or pivot, and opposing
Raikou has been the repeated special owner. Misdreavus has not shown a full set.
```

Tempting move: reject Misdreavus because Raikou threatens it, or keep it in as
though it were a normal special wall.

Frozen answer: first name Misdreavus's actual third job: block Spin, threaten
Perish-trap structure, land Toxic on the Electric owner, or force a Rest clock.
If Raikou enters and Misdreavus can safely Toxic or trap enough to improve the
Spikes route, take that action. If Misdreavus is the irreplaceable spinblocker
and Thunderbolt puts it below its next entry, preserve it. Confidence: medium.

Classification: hidden-role voluntary entry with preservation boundary.

Score: pass.

## Scenario 3 - Low Snorlax Does Not Prove Rest

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax has revealed Curse and
Double-Edge but not Rest. It is low against Raikou after taking electric damage.
Snorlax can Curse again, attack, or hand off; Raikou can attack, Roar, Reflect,
or switch to a physical answer.
```

Tempting move: assume low HP means Snorlax must Rest or switch.

Frozen answer: do not spend a hidden Rest that has not been revealed. Re-score
whether Curse or Double-Edge changes the next board before Raikou removes
Snorlax; switch only if the known HP, speed order, recoil, or phaze branch makes
the boosted route dead. Confidence: medium-low.

Classification: low-HP setup without hidden-set import.

Score: pass.

## Scenario 4 - Active Damage Can Beat Rest Or Pivot

Public state:

```text
Vanilla GSC spectator-public style. Opposing Misdreavus is paralyzed and in
range of strong Electric damage. Your Raikou is poisoned but not yet forced to
Rest. Misdreavus can Toxic, trap, switch, or be preserved for a later spinblock.
```

Tempting move: Rest because Raikou is poisoned, or pivot because Misdreavus is
a Ghost support piece.

Frozen answer: price Thunderbolt or Thunder first. If active damage removes or
cripples the Ghost before it gets another route job, attack. Rest only when the
poison clock or incoming punish flips the route before the damage converts;
pivot only when the opponent's named counter-pivot makes the active hit fail.
Confidence: medium.

Classification: active pressure before defensive script.

Score: pass.

## Resulting Checklist

Before choosing in this boundary:

1. Did a support move create a next action, or only look complete?
2. Is phazing part of the same route package as the screen, hazard, or status?
3. What is the third owner's actual job: block, trap, poison, absorb, scout, or
   preserve?
4. Am I importing Rest, coverage, or a full set that is not public?
5. Does active damage remove the converter before Rest or pivot is needed?

## Next Transfer Check

Run a fresh no-keyword-screen replay transfer and score these separately:
screen-plus-phaze package, third-owner Misdreavus route ownership, low setup
without hidden Rest import, and active damage over defensive scripts.
