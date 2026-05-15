# Counter-Handoff Loop Probe 001 - 2026-05-14

Source parent:
`quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the loop error from `921372`: missing the counter-handoff after a
support handoff was revealed, then overcalling that loop once active pressure
was still good enough.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`

Web/current sources checked:

- Smogon Forums, `GSC OU Snorlax`:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, `GSC Zapdos`:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, `GSC OU Skarmory`:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Counter-handoff boundary hits: 4 / 4.

Stop-condition hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - First Counter-Handoff After Support Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Skarmory revealed Toxic into an
opposing Zapdos switch last cycle. Your known Raikou entered to meet Zapdos.
The opponent then showed Snorlax as the counter-handoff into Raikou. The same
Skarmory versus Snorlax board has now reappeared.
```

Tempting move: treat Zapdos as the whole branch and switch Raikou again.

Frozen answer: name both layers before moving: Skarmory can Toxic or otherwise
cover the Zapdos handoff, but if Zapdos is likely to answer by pivoting Snorlax
into Raikou, the next action must account for Snorlax too. Confidence: medium.

Classification: counter-handoff after revealed support handoff.

Score: pass.

## Scenario 2 - Obey The Counter-Handoff When The Active Has No Progress

Public state:

```text
Vanilla GSC spectator-public style. Your Raikou faces opposing Snorlax after
the opponent counter-handed Zapdos to Snorlax on the previous Raikou entry.
Raikou has revealed Thunder only. Snorlax has revealed Body Slam and Curse.
Your Skarmory is healthy and already shown as the Snorlax answer.
```

Tempting move: stay and attack because the opponent might double back to Zapdos.

Frozen answer: switch to the Snorlax owner unless Raikou has a revealed route
move that changes this board. Once Snorlax is active and Raikou has no public
progress beyond shaky damage, obey the handoff. Confidence: medium-high.

Classification: counter-handoff obeyed.

Score: pass.

## Scenario 3 - Stop Overcalling When Active Pressure Still Converts

Public state:

```text
Vanilla GSC spectator-public style. Your Raikou faces opposing Snorlax at high
HP. Earlier, Snorlax counter-handed into Raikou, but this turn Snorlax stayed
and took Thunder pressure while threatening Body Slam. No new Zapdos switch is
forced, and Body Slam chip or paralysis is still useful for the Snorlax side.
```

Tempting move: predict a second-order double every time the loop appears.

Frozen answer: keep the active-pressure branch live. A revealed loop raises the
counter-handoff prior, but it is not a script; when both actives still make
concrete progress, choose or at least rank the active move before a speculative
double. Confidence: medium.

Classification: stop condition for overcalling the loop.

Score: pass.

## Scenario 4 - Third Owner Beats The Named Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Raikou has stayed in once against
Snorlax and is now in range where another Body Slam plus Spikes matters. Your
Skarmory is known, but the opponent has shown a willingness to use Snorlax
instead of Zapdos. You also have an unrevealed Ghost that can enter Body Slam
and preserve Raikou.
```

Tempting move: assume the answer must be the previously revealed Skarmory.

Frozen answer: choose the branch owner that beats the current punish, not the
last revealed owner by habit. If a Ghost enters Body Slam cleanly and preserves
Raikou, it can be better than repeating Skarmory. Use possible language until
the Ghost is public in spectator mode. Confidence: medium.

Classification: third-owner handoff after loop re-score.

Score: pass.

## Resulting Checklist

Before choosing in a support-handoff loop:

1. What was the first handoff?
2. What was the counter-handoff that answered it?
3. Does my current active still make concrete progress if both sides stay?
4. Which known or plausible owner beats the current punish, not just the last
   branch I named?
5. Is this a forced handoff, a counter-handoff, active pressure, or a
   speculative double?

## Next Transfer Check

Run a fresh no-keyword-screen replay transfer and score loop turns separately:
first handoff found, counter-handoff found, counter-handoff obeyed, active
pressure stop condition, and third-owner re-score.
