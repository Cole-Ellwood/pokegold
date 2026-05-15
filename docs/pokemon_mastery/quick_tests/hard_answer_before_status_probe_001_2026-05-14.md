# Hard Answer Before Status Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_048` into three forced choices around the
clean-answer exception to the status-before-hazard rule.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_048_hard_answer_before_status_smogtours-gen2ou-924922_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

## Score Summary

Scenarios: 3.

Action-policy hits: 3 / 3.

Classification hits: 3 / 3.

Route-job hits: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. This should be followed by a fresh replay
transfer before treating the exception as learned.

## Scenario 1 - Hard Answer Before More Support

Public state:

```text
Vanilla GSC. Our Cloyster has already set Spikes. Opposing Snorlax is at +1
Attack / +1 Defense and has revealed Curse and Double-Edge only. Our Skarmory
is healthy in reserve and can enter Double-Edge. Cloyster has Toxic available.
```

Tempting move: Toxic because Curselax wants a status clock.

Frozen answer: switch Skarmory. Confidence: medium-high.

Classification: recurring hard answer before status. The support action that
matters most, Spikes, is already delivered, and Skarmory enters cleanly.

Score: pass.

## Scenario 2 - Counter-Setup Before Phaze

Public state:

```text
Vanilla GSC. Our Skarmory has entered against +1 Snorlax. Snorlax has revealed
Curse and Double-Edge only. Skarmory is healthy enough to keep answering and
has Curse, Toxic, and Whirlwind available.
```

Tempting move: Whirlwind immediately because Snorlax is boosted.

Frozen answer: Curse. Confidence: medium.

Classification: counter-setup. If Snorlax has only shown resisted physical
damage, Skarmory can improve its own position before phazing becomes urgent.

Score: pass.

## Scenario 3 - Coverage Reveal Ends Counter-Setup

Public state:

```text
Vanilla GSC. Our Skarmory is in against +1 Snorlax. Snorlax has just revealed
Thunder or Fire Blast into Skarmory, proving it is not a pure resisted
Double-Edge route. Skarmory is still alive but no longer a clean long-term
hard answer.
```

Tempting move: Curse again because counter-setup worked before.

Frozen answer: abandon counter-setup; Whirlwind, switch, or use the appropriate
emergency route depending on HP. Confidence: high.

Classification: re-solve after coverage reveal. The clean-answer exception
only applies before coverage changes the matchup.

Score: pass.

## Resulting Checklist

Before adding status after hazards are up:

1. Is the key support already delivered?
2. Is there a clean recurring answer that enters the current attack?
3. Has the attacker revealed coverage that invalidates that answer?
4. If the answer is still clean, can counter-setup improve the answer before
   phazing?

## Next Study Target

Fresh replay transfer with this clean-answer exception; stop after the first
two misses again.
