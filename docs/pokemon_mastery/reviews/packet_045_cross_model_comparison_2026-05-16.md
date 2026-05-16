# Packet 045 Cross-Model Comparison - 2026-05-16

## Setup

The intervention shipped in `cf87f141` (Load-Required Triggers in
`live_core.md` + pre-freeze branch-punish audit) was tested by running
packet 045 in parallel with two models. Each was given the same
self-contained spec at `docs/pokemon_mastery/packet_045_codex_task.md`.

The auto-coordination intent (share replay URL + side via
`workspace/packet_045_inputs.md`) **failed** because each runner ran
in a different working tree:

| Runner | Worktree | Replay | Side | Done at (UTC) |
|---|---|---|---|---|
| Codex (GPT-5.5) | main repo (`codex/cleanup-gsc-rebalance-split`) | smogtours-gen2ou-936068 | p1 | 2026-05-16T03:46:44Z |
| Claude (Opus 4.7) | `gallant-goldberg-cb5cc4` | smogtours-gen2ou-781283 | p2 | 2026-05-16T04:27:33Z |

Each runner wrote its own `packet_045_inputs.md` in its own
working-tree path, so neither saw the other before picking. Result:
no per-turn comparison possible (different boards, different teams).

This file documents the **aggregate cross-model finding** under the
constraint that the two runs are different replays.

## Results

| Metric | Target | Codex (936068, p1) | Claude (781283, p2) | Packet 044 baseline |
|---|---|---|---|---|
| **Top-match** | ≥20/30 | 15/30 | 15/30 | 15/30 |
| Acceptable | — | 28/30 | (per writeup, similar) | 29/30 |
| Severe blunders | 0 | **1** (T27 Explosion into Ghost) | **1** (T12 Explosion into Ghost) | 0 |
| Hidden-info | 0 | 0 | **1** (T12 strong-prior label miss) | 0 |
| State | 0 | 0 | 0 | 1 |
| Mechanics | 0 | 0 | 0 | 0 |
| Pre-freeze loaded cards | every turn | ✓ | ✓ | partial (header only) |

## Findings

### 1. H1 (card-not-loaded) intervention works

Both runs report every required card was loaded every turn. The
trigger block did its job. The packet-044 diagnosis's claim that 67%
of misses traced to absent cards is no longer the dominant failure
mode — Claude's writeup explicitly states H1 was "eliminated."

### 2. Top-match still flat at exactly 15/30 across models and replays

This is the strongest evidence available that the order-flip is
required. Two different models on two different replays in the same
format converged on the same numerator. The intervention as shipped
moves the failure from H1 to H2 (card-loaded-but-ignored) without
moving top-match.

### 3. Both models committed the same severe-blunder class

| Run | Turn | Move | Named branch | Outcome |
|---|---|---|---|---|
| Codex | 27 | Explosion (Exeggutor) into revealed Misdreavus | Ghost immunity | 0 damage |
| Claude | 12 | Explosion (Cloyster) into Gengar | Ghost immunity | 0 damage |

Both audits identified the dead-into-Ghost branch in writing.
Both rankings kept the dead candidate at position 1 anyway. This is
the exact rank-then-audit-ordering failure mode predicted at
`top_match_miss_classification_packet_044.md`'s falsification
section. The audit ran AFTER the rank was committed.

### 4. Predicted strict-audit-first rescoring matches observed reality

A hand rescoring of Codex's packet under a strict audit-first rule
(demote any candidate that the audit identifies as dead into a
revealed named branch) predicted **net-zero top-match change**:

- +1 (Turn 7: Explosion-into-Misdreavus demoted, top becomes Zapdos,
  matches actual)
- 0 (Turn 27: Explosion demoted but actual is Stun Spore, not in
  top-3 either way)
- -1 (Turn 30: Explosion demoted but actual IS Explosion — the pro
  read low-probability Ghost switch and clicked the cash-out)

15 + 1 - 1 = 15. The audit-first rule trades severe-blunder
avoidance for cash-out-conviction loss, on this packet. **The
order-flip alone is not sufficient to break the plateau.**

A probabilistic audit-first rule (only demote when the dead branch
is high-probability to switch in) would have netted 16/30 on Codex's
packet — better but still well below the 20/30 falsification gate.

### 5. Failure-mode redistribution

Packet 044 diagnosis (from `top_match_miss_classification_packet_044.md`):
- H1 (card-not-loaded): 67%
- H2 (card-loaded-but-ignored): 13%
- H3 (card-content-vague): 7%
- H4 (oracle-noise): 13%

Packet 045 Claude self-diagnosis after H1 fix:
- H1: ~0% (intervention eliminated)
- H2: ~66%
- H4: oracle-ceiling from 3 off-meta sets in mrsoup's team

H1 has been recycled into H2 by removing the "missing card" excuse.
The misses are now overwhelmingly "loaded card not obeyed" plus
genuine oracle noise.

## Resolution of the packet-044 diagnosis falsification gate

Per `top_match_miss_classification_packet_044.md` § Expected lift
and falsification gate:

> If packet 045 produces exact-top below ~20/30 despite the trigger
> block being honored on every relevant turn, then load-discipline is
> NOT the dominant cause and the diagnosis was wrong. Pivot at that
> point to: 1. H2 mode dominance: cards loaded but not obeyed → audit
> the ranking pass directly, possibly via pairwise contrastive drills.

Outcome: **falsification gate fired exactly as designed.** Both runs
honored the trigger block. Both produced exact-top below 20/30. Both
diagnosed H2 dominance. The pivot is to "audit the ranking pass
directly" — which the rank-then-audit ordering analysis revealed to
be:

1. **Order flip** in the artifact template: audit-first, ranking
   second. This is necessary but not sufficient (kills severe blunders;
   doesn't move top-match by itself per the rescoring analysis).
2. **Probabilistic audit gating**: distinguish dead-branch-high-prob
   (hard demote) from dead-branch-low-prob (soft annotate, keep top).
3. **Pairwise contrastive drills** for the remaining H2 misses that
   are about candidate ranking under conflicting positive moves — the
   inventory's Issue 21 path.

## Recommended next pgoal phase

The original pgoal's manual gate resolves to **ceiling-reached under
THIS intervention** with a specific next intervention named (not an
oracle ceiling — the cards CAN encode the right answer, the order
prevents the encoding from steering the choice).

The next pgoal should be scoped as:
- Phase 1: redesign artifact format with audit-first ordering + a
  `Revised top` slot that the audit can write into.
- Phase 2: add probabilistic gating to the audit (hard vs soft demotion).
- Phase 3: build a small pairwise contrastive drill harness from
  packet-044 and packet-045 misses where the actual was in top-3
  but not top.
- Phase 4: run packet 046 under the new format.
- Falsification gate: same as packet 045 (≥20/30 top with clean gates).

## Coordination fix for next packet

The cross-worktree coordination failure shouldn't repeat. Either:
- (a) Both runners agree to operate from the same working tree (one
  worktree, both prompts pasted there), or
- (b) The inputs file moves to a path that's shared across worktrees
  (e.g., absolute path outside any worktree, or the project's main
  `docs/` which is shared), or
- (c) The user pastes the chosen replay URL + side into both prompts
  manually — defeats the auto-coord but is reliable.

For packet 046, recommend (a): pick one working tree and run both
sessions against it.
