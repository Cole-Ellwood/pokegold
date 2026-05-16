# Replay Turn-Pause 023 Receiver Phaze Counterplay - smogtours-gen2ou-933853 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-933853`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: test whether the receiver-counterplay lesson from
`replay_turn_pause_022` transfers when the defensive side eventually reveals
phazing into an Agility/Baton Pass chain.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move-name presence: Baton Pass,
  Agility, setup, and phazing.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.
- The helper omitted carried Speed boosts after Baton Pass, so manual state
  tracking treated Jolteon and Scizor as Speed-passed until Whirlwind reset the
  chain.
- Post-run note: later raw-log lines were exposed during validation after turn
  14 had already been scored. This does not affect the recorded score, but this
  replay should not be reused for unseen continuation.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_022_receiver_counterplay_transfer_smogtours-gen2ou-935551_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Mean Look / Spider Web + Baton Pass in GSC OU:
  `https://www.smogon.com/forums/threads/mean-look-spider-web-baton-pass-in-gsc-ou.3696148/`
- Smogon Scizor OU Revamp:
  `https://www.smogon.com/forums/threads/scizor-ou-revamp.3510707/`
- Smogon Beginner's Guide to GSC:
  `https://www.smogon.com/forums/threads/beginners-guide-to-gsc.38663/`

Source note: the current GSC discussion and older Scizor material both treat
phazing, Explosion/Self-Destruct, status, and direct damage as central Baton
Pass counterplay. This run tested whether I could price those branches without
assuming unrevealed moves as fact.

## Score Summary

Turns scored: 1-14.

Target phase: turns 10-14, where Scizor boosted, Skarmory revealed Whirlwind,
Marowak was dragged in, and the route had to be rebuilt.

Decisions scored: 28 side-decisions.

Top-match: 17 / 28.

Acceptable-match: 24 / 28.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 3.

Largest route error: turn 12.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Lead Smeargle vs Skarmory | p1 Spore; p2 switch to sleep absorber or phaze/status | p2 Raikou switch; p1 Spore | both top | Correctly identified the sleep-absorber branch. |
| 2 | Smeargle vs sleeping Raikou | p1 Agility; p2 preserve or use Sleep Talk | p2 Sleep Talk Thunder miss; p1 Agility | p1 top, p2 acceptable | Sleeping Pokemon can remain active if Sleep Talk gives it a job. |
| 3 | Speed-boosted Smeargle vs sleeping Raikou | p1 Baton Pass; p2 switch Skarmory | p2 Skarmory; p1 Spikes | p1 acceptable, p2 top | Support before pass can be better than immediate handoff when the counterplay slot is switching in. |
| 4 | Speed-boosted Smeargle vs Skarmory | p1 Baton Pass; p2 phaze/status/attack | p1 Baton Pass to Jolteon; p2 Toxic | p1 top, p2 acceptable | Price Whirlwind, but do not make it public until shown. Toxic was the revealed control. |
| 5 | Jolteon vs Skarmory | p1 Thunder; p2 Snorlax or Raikou pivot | p2 Snorlax; p1 Thunder | both top | Correctly hit the switch-in instead of adding support. |
| 6 | Jolteon vs Snorlax at 66 | p1 Thunder with Baton Pass as alternative; p2 Double-Edge | p1 Baton Pass to Scizor; p2 Double-Edge | p1 acceptable, p2 top | Chain cycling preserved Jolteon while routing Double-Edge into Scizor. |
| 7 | Scizor vs Snorlax | p1 continue chain; p2 Skarmory | p2 Skarmory; p1 Baton Pass to Jolteon | p1 acceptable, p2 top | The chain was not a one-receiver commitment. |
| 8 | Jolteon vs Skarmory | p1 Thunder; p2 Snorlax pivot | p2 Snorlax; p1 Thunder | both top | Correctly repeated the pressure line after Skarmory re-entered. |
| 9 | Jolteon vs low Snorlax | p1 Thunder; p2 Double-Edge | p1 Baton Pass to Scizor; p2 Double-Edge | p1 miss, p2 top | I underpriced the repeated Jolteon-to-Scizor damage sponge cycle. |
| 10 | Scizor vs low Snorlax | p1 Baton Pass, Swords Dance as alternative; p2 Skarmory | p2 Skarmory; p1 Swords Dance | p1 acceptable, p2 top | Boosting on the forced Skarmory switch was the route fork before the phaze reveal. |
| 11 | +2 Scizor vs Skarmory | p1 Baton Pass; p2 Whirlwind if carried | p1 Baton Pass to Jolteon; p2 Whirlwind dragged Marowak | both top | Correctly priced act-last phazing as the answer once the boost was live. |
| 12 | Marowak vs Skarmory after Whirlwind | p1 switch Jolteon; p2 Whirlwind or Toxic | p2 Thief; p1 Fire Blast miss | both miss | Major error: I treated Marowak as walled instead of checking whether the receiver carried coverage for Skarmory. |
| 13 | Marowak with Fire Blast revealed vs Skarmory | p1 Fire Blast; p2 Toxic or pivot | p2 Vaporeon; p1 Fire Blast burned Vaporeon | p1 top, p2 miss | Once coverage was revealed, repeating it was correct; the hidden Water answer was not public. |
| 14 | Marowak vs burned Vaporeon | p1 switch to best Water answer; p2 Surf | p1 Snorlax; p2 Surf | p1 acceptable, p2 top | Preserve Marowak once the Water answer appears; side-known target was hidden, but the switch class was right. |

## Error Classes

- Route coverage miss: on turn 12 I saw "Marowak into Skarmory" and jumped to
  switching, missing that Agility/Baton Pass Marowak teams often need a way to
  punish Skarmory. The correct question was not "does Skarmory wall Marowak by
  species?" but "what coverage or teammate route exists because Skarmory is the
  revealed blocker?"
- Chain-cycling underweight: turns 6 and 9 showed Jolteon and Scizor repeatedly
  trading Baton Pass positions so Scizor absorbed Double-Edge while Jolteon
  preserved Thunder pressure.
- Phaze calibration held: before Whirlwind was revealed, I priced it without
  treating it as fact. After turn 11, I correctly reclassified Skarmory as the
  active chain reset.
- Sleep-clause calibration held but needs repetition: Raikou was preserved as a
  sleep absorber on turn 1, yet turn 2 showed that Sleep Talk can make the
  sleeping piece active instead of automatically switching.

## Policy Update

Add to anti-pass policy: after phazing drags a receiver, immediately rebuild
the blocker map from the dragged Pokemon's likely route job. If the dragged
receiver is normally blocked by the phazer's species, check for route-specific
coverage before auto-switching. Revealed phazing beats an assumed passive
Skarmory, but revealed or strongly implied coverage can still punish the
phazer.

## Next Study Target

Run a short constructed quick probe with six post-phaze receiver states:
coverage punish, auto-switch, re-pass, sacrifice, absorber switch, and
immediate attack. Score whether the blocker map is rebuilt before choosing.
