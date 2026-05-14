# Boss AI Re-Solve Trigger Audit - 2026-05-14

Purpose: check whether `STP-058` has a cheap, public-information-only ROM boss
AI implementation path, or whether it should remain a benchmark/audit target
for now.

## Conclusion

Do not implement a broad "subgame re-solver" in ROM right now. That would be
too large, hard to audit, and too easy to turn into hidden-information policy.

There is one cheap, source-grounded candidate worth promoting: hazard-retention
scoring when the active player Pokemon has publicly revealed Rapid Spin and
the boss has already invested Spikes layers. The benchmark layer already knows
this case. The ROM move policy does not appear to encode the same route-level
answer yet.

## Information Model

Ordinary boss AI may use:

- public active battle state;
- public field state;
- boss's own authored team and moves;
- seen player species and revealed player moves;
- approved exact speed comparison exceptions.

Ordinary boss AI must not use:

- unrevealed player party slots;
- unrevealed player moves, PP, items, or private stats;
- current-turn player input outside quarantined Haki Oracle behavior.

Source anchors:

- `docs/boss_ai_spec.md` defines the target as "absurdly strong but
  non-cheating" and quarantines Haki as the only intentional exception.
- `tools/audit/check_boss_ai_no_cheat.py` scans boss AI policy files for
  hidden player party/move/item/input reads and only approves the narrow direct
  exact-helper exception already listed there.

## Current ROM Evidence

The ROM already re-scores moves and switches each turn from current public
state:

- `engine/battle/ai/boss_policy_move.asm:172` `BossAI_ApplyMoveModel` resets
  turn caches, selects a plan if needed, computes public plausible type masks,
  and scores each live enemy move.
- `engine/battle/ai/boss_policy_move.asm:1944` `BossAI_SelectMove` recomputes
  the move choice from current scores, with weighted best-vs-second randomness.
- `engine/battle/ai/boss_policy_switch.asm:17` `BossAI_SwitchOrTryItem`
  separately resets caches, selects a plan, computes public plausible type
  masks, and checks whether a switch should be attempted.
- `engine/battle/ai/boss_policy_move.asm:883` `.PlayerHasRevealedEffectA`
  checks only `wPlayerUsedMoves`, described in-code as the active player's
  public used-move list. This is a legal source for revealed-move reactions.

That is good plumbing, but it is not the same as route re-solving. The current
ROM has individual revealed-move and plausible-risk patches, not a general
branch-bundle evaluator.

## Existing Cheap Wins That Are Real

These are implemented in source and are correctly scoped to public state:

- Revealed Protect punishes boss Explosion/Hyper Beam commitment:
  `engine/battle/ai/boss_policy_move.asm:1248`.
- Revealed recovery encourages Toxic, Leech Seed, or phazing denial:
  `engine/battle/ai/boss_policy_move.asm:1266`.
- Revealed faster Encore discourages punishable setup/commitment:
  `engine/battle/ai/boss_policy_move.asm:1323`.
- Revealed sleep move can encourage preemptive Substitute/Safeguard only if
  the boss is publicly faster: `engine/battle/ai/boss_policy_move.asm:1436`.
- Public speed comparison is centralized in
  `engine/battle/ai/boss_policy_move.asm:2783`, matching the approved exception.
- Switch confidence considers public threat/revenge pressure:
  `engine/battle/ai/boss_policy_switch.asm:356`.

These should stay. They are small, auditable, and do not need Team Preview.

## Gap: Public Spinner After Hazard Investment

The benchmark policy already states the desired answer:

- `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json:468`
  has `romhack_spikes_public_spinner_holdout_001`: Janine Qwilfish has two
  Spikes layers up and the active Starmie has revealed Rapid Spin.
- `tools/boss_ai_preference/benchmarks/state_transition_oracles.json:384`
  labels Explosion best, Sludge Bomb acceptable, and Spikes catastrophic.
- `tools/boss_ai_preference/benchmark_positions.py:199` defines
  `mut_spinner_public_lowers_spikes_001`: public Rapid Spin flips the expected
  policy from `move_spikes` to `move_explosion`.
- `tools/boss_ai_preference/tests/test_benchmark_positions.py` verifies the
  mutation report covers this flip.

The ROM move policy has only the narrower pieces:

- `engine/battle/ai/boss_policy_move.asm:1598` `.ApplySpikesLayerBias` is
  layer-aware. At two layers, it encourages the third layer if the boss is not
  under pressure and a switch looks plausible.
- That Spikes bias does not check whether the active player has publicly
  revealed `EFFECT_RAPID_SPIN`.
- `engine/battle/ai/boss_policy_move.asm:804` `.ApplyRapidSpinBias` encourages
  the boss's own Rapid Spin when the boss has hazards on its side. It does not
  help the boss punish the player's spinner.
- `engine/battle/ai/boss_policy_move.asm:315` only applies a revealed
  Selfdestruct/Explosion response for Protect; there is no boss-specific
  Explosion route-trade override for removing a public spinner.
- Vanilla `engine/battle/ai/scoring.asm:551` `AI_Smart_Selfdestruct`
  discourages Selfdestruct/Explosion when the enemy is above half HP, so an
  82% Qwilfish in the benchmark-like state would likely be pushed away from
  the route-trade answer unless another local rule overcomes it.

This is the clearest cheap-win mismatch I see right now: the benchmark/oracle
has the correct public-information hazard-retention policy, but the ROM
scorer does not appear to express it directly.

## Suggested Cheap Fix Shape

Do not add a general solver. Add a small public spinner policy around the
existing revealed-effect helper:

1. While scoring Spikes, if the target side already has one or two layers and
   the active player Pokemon has publicly revealed `EFFECT_RAPID_SPIN`, reduce
   the layer-completion bonus or discourage Spikes.
2. While scoring Explosion/Selfdestruct, if the active player Pokemon has
   revealed `EFFECT_RAPID_SPIN`, the player side has Spikes layers, and the
   player has not revealed Protect or an active Ghost-like block, add a route
   trade bonus.
3. Keep the condition active-only and revealed-only. Do not infer hidden
   spinners from the player party. Do not use Team Preview.
4. Trace it behind existing boss trace machinery so the top-move trace can
   show "public spinner hazard-retention" as the reason.

This is a small policy because the code already has:

- public revealed-effect scanning;
- Spikes layer counting;
- move-effect dispatch;
- top-move tracing;
- benchmark cards and mutations that define the target ordering.

## Fixture Gate Before ASM Edit

Before changing assembly, add or run a ROM-facing preference fixture that
expects this ordering from the actual boss scorer:

```text
State:
- boss active Qwilfish, Spikes / Sludge Bomb / Surf / Explosion, healthy enough
  that vanilla Explosion would normally be discouraged;
- player active Starmie, Rapid Spin / Recover / Surf publicly revealed;
- player side has two Spikes layers;
- no public Protect/Ghost block.

Expected top three:
1. Explosion or strong spinner-removal action.
2. Sludge Bomb or other live spinner pressure.
3. Spikes should be below the removal/pressure line.
```

The existing public benchmark is good policy evidence, but it is not proof that
the ROM scorer produces the same ordering. This should be tested against
assembly traces before claiming the cheap win is implemented.

## Rejected Broad Fix

"Re-solve after every reveal" is a good advisor discipline and a good benchmark
organizing principle. It is not a good direct ROM implementation target today.
It would require representing routes, opponent continuation bundles, and
resource conversion in a memory-constrained assembly policy. That belongs in
offline benchmarks, traces, and a few surgical scoring patches, not in a
generic ROM solver.
