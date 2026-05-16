# Python Scorer → ROM AI Mapping

Status: living document. The Python scorer at
`tools/boss_ai_debugger/scorer.py` is the REVIEW pipeline's model of
what the ROM AI does or should do. Some Python rules have ROM
equivalents that are already correctly aligned; others don't yet exist
in ROM. This doc tracks the mapping so ROM-side propagation work can
start from a clear list of (rule → status → next action).

## Mapping table

| Python rule (iter) | ROM equivalent | Status | Notes |
| --- | --- | --- | --- |
| `type_resist_pivot` (iter 7) | type-chart consultation in switch scoring | ALIGNED | The ROM uses the hack's type chart for switch evaluation; any resistance is reflected in the type-effectiveness multiplier. Hack-specific changes (e.g. Dragon resists 4 elementals) flow through. |
| `type_wall_pivot` (iter 6) | partially — wall detection via species role | NEEDS REVIEW | The Python rule fires on `"hard wall"` text. ROM has no direct "hard wall" concept; relies on type chart. May behave differently for borderline matchups. |
| `bad_pivot` (iter 4) | switch-target legality + type matchup | ALIGNED | ROM checks switch-target alive, status, type matchup vs revealed player moves. Bad pivots get low scores naturally. |
| `public_notes_chip_qualifier` (iter 13) | nothing | INTENTIONALLY NOT TRANSLATABLE | Fixture `public_notes` are Python-only labeling artefacts. ROM doesn't have fixture concept; it has live game state. The labeler intent ("revealed threat is chip-grade") would translate to ROM as "current active's damage from revealed player moves is < X% per turn AND has counter-pressure." That's a different rule shape; if needed, add as a structural ROM rule under a new name. |
| `type_immunity_pivot` (iter 14) | `BossAI_IsImmunityPivotOpportunity` at `engine/battle/ai/boss_policy_switch.asm:567` | ALIGNED | ROM checks `wLastPlayerCounterMove` type vs switch target's base types via `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem`. The hack's Psychic→Dark = 0× type chart makes Dark switches immune; ROM honors this automatically. iter-14 brought the Python scorer up to par with existing ROM behavior. |
| `healthy_ace_setup_lock_pivot` (iter 15) | nothing direct | GAP | ROM has `BossAI_EnemyBelowOneThirdHP` (one-third HP threshold), but no "above 90% HP + ace + setup-lock potential" check. To translate: combine an HP-percent helper (new), an ace-piece detection (existing trainer attribute or party-slot heuristic), and a switch-confidence dampener. Risk: tight Boss AI WRAM reserve (9 bytes free in trace build) makes new state expensive. Implementation note: the trigger could be derived state, no new WRAM needed. |
| `sleep_clause_free_window` (iter 16) | `AI_Smart_Sleep` at `engine/battle/ai/scoring.asm:394` | PARTIAL | Base AI encourages sleep moves 50% chance regardless of target status. Python rule adds a +4 when target is unstatused and fixture has `sleep` tag without `setup`. ROM-side improvement: in the boss AI overlay, add a deterministic sleep bias when player active status is publicly unstatused AND no player party mon is currently asleep (sleep clause is free, publicly known via switch-out reveals). |

## ROM-side propagation criteria

A Python rule should propagate to ROM when ALL of:

1. The divergence affects actual gameplay (player observable in-game), not just review-tool agreement.
2. The Python scorer is aligned and stable (passes both audit gates).
3. The ROM AI is making the same mistake as the pre-rule Python scorer.
4. The rule can be expressed structurally from ROM-accessible state — no fixture-text matching, no Python tag soup.
5. The rule's gameplay impact is worth the asm-change risk (selector replay, farcall, save format).

## Procedure when propagating

1. Locate the corresponding ROM scoring helper. Most boss AI work lives in
   `engine/battle/ai/boss_policy_move.asm`,
   `engine/battle/ai/boss_policy_switch.asm`, or
   `engine/battle/ai/scoring.asm`.
2. Translate the Python trigger into ROM-state checks:
   - `tags`: usually no direct translation; derive from trainer attributes,
     party shape, fixed move data, or live battle state.
   - `public_notes`: not translatable — the labeler intent must be re-expressed.
   - `active.hp` / `active.status`: read from `wEnemyMonHP`,
     `wEnemyMonStatus`, etc.
   - `revealed_moves`: `wBossAIRevealedMovesBitmap` and friends.
3. Add the new bias function. Public-info-only:
   - No reads of `wBattleMonHP` (player's actual HP) for hidden-info gating —
     only the displayed bucket via the public threat pipeline.
   - No reads of player's full moveset; only revealed-moves bitmap.
   - Mark explicitly which `wBossAI*` reads are involved.
4. Wire into the dispatcher (`BossAI_SelectMove` / `BossAI_SwitchOrTryItem`).
5. Run the full asm audit floor:
   - `python tools/audit/check_release_smoke.py`
   - `python tools/audit/check_boss_ai_selector_replay.py` (must stay at 100% — or update the trace manifest)
   - `python tools/audit/check_farcall_hl_clobber.py`
   - `python tools/audit/check_farcall_a_clobber.py`
   - `python tools/audit/check_cross_bank_call.py`
   - `python tools/audit/check_typepassive_c_mirror.py`
   - `python tools/audit/check_boss_ai_no_cheat.py`
   - `python tools/audit/check_boss_ai_memory_budget.py`
6. Build pokegold.gbc AND pokegold_trace.gbc.
7. Regenerate `docs/generated/dev_index.md`.
8. Commit as `boss-ai: <action>` (drop `-loop` suffix; ROM AI changes are not Python-loop iters).
9. Update this mapping table to mark the rule ALIGNED.

## Risk gating

- Boss AI WRAM is at 104/140 normal and 131/140 trace. Adding any new WRAM byte tips the trace build over budget. Prefer derived state.
- Tight ROMX banks (0x12-0x1f) are pic data; boss AI lives in bank 0x0e which has room.
- HRAM is 0 bytes free. Don't add HRAM.
- Save format is frozen; do not touch `ram/`.

## Out of scope for this doc

- Hidden-info-enabled "Haki" branches (those are separately quarantined; see
  `BossAI_TryMortyHakiOracle`).
- Full rebuild architecture (shelved 2026-05-05; see
  `docs/boss_ai_design_conversation_2026-05-05.md`).
- Per-leader personality weights (separate concern; touched only via the
  existing role-bias tables).
