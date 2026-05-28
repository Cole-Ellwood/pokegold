# Boss AI Organization Plan — split Boss AI source

> **Status — RESOLVED.** Option C shipped and repartitioned: the former
> monolithic Boss AI source is split into `boss_platform.asm`,
> `boss_policy_move.asm`, `boss_policy_switch.asm`, and
> `boss_thunks.asm`; `boss_data.asm` was folded after the static tables
> moved to their owner files. `main.asm` includes guarded fragments in
> original byte order so `make compare` remains byte-identical. Boss AI rebuild
> (BOSSAI-003) and v2 RL training (BOSSAI-004) remain SHELVED.
>
> Historical planning below is preserved for context; §3 is now an archive of
> the resolved organization decision, not a pending recommendation.
>
> Source frozen at: dev tip `f438afae` (worktree `lucid-bartik-93f5ff`,
> branch `claude/lucid-bartik-93f5ff` tracking
> `origin/codex/cleanup-gsc-rebalance-split`). The shelved rebuild branch
> `claude/thirsty-jackson-893a52` (HEAD `444b2f49`) carries one extra
> commit on `boss.asm` (`08df6f4e` — `BossAI_ScaleMovePowerByBaseStatRatio`
> in `BossAI_CurrentEnemyMovePressureScore`); when/if that branch merges,
> the §5 power-scoring entry needs a re-read. Everything else in this
> plan is unchanged by that commit.

## Why this doc exists

`engine/battle/ai/boss.asm` is 7066 lines, one giant include into the
`Enemy Trainers` ROMX section (`main.asm:171`, bank `0e`,
`0e:4000-708d` = 12430/16384 bytes; ~3954 free per
`docs/generated/dev_index.md`). Fast lookups across the file are slow —
160 top-level labels, 560 local labels, no in-file SECTION banners, no
high-level structural comments. The user's exact ask was *"make a plan on
how to understand and start organizing (so we can find lines quickly),
simplifying, optimizing the boss ai."* This doc covers all five.

`docs/agent_navigation/subsystems/boss_ai_logic.md` already exists as a
hand-maintained Behavior→Source routing table (audited by
`tools/audit/check_boss_ai_index_lines.py`). It's the right artifact for
*"where is X behavior?"* but it does not (a) tell you what regions of the
file cover what concerns, (b) reflect any structural seam between
platform-layer and policy-layer code, or (c) name simplification or
optimization candidates. This plan extends that index, it does not
duplicate it.

## What this doc is NOT

- Not a rebuild plan. The rebuild surface (BOSSAI-003 / 004) is shelved.
  `docs/boss_ai_rebuild_plan.md` and
  `docs/boss_ai_design_conversation_2026-05-05.md` (on
  `claude/thirsty-jackson-893a52`) are the canonical homes for that.
- Not a refactor PR. Every concrete change in §5–§7 is a *proposal*; the
  user picks which to green-light.
- Not a behavior change. Anything that would change
  `audit/boss_ai_trace/*_live.txt` captures byte-for-byte is flagged
  explicitly and parked behind regression-suite refresh.

## File layout today

### Macro view (line ranges)

| Lines | Region (proposed name) | Concern | Approx LOC |
| ---: | --- | --- | ---: |
| 1–143 | **State tracking** | Turn counter, switch counter, seen-species bitmap, alive bitmap | 143 |
| 145–288 | **Adaptive lead** | Pre-battle weighted opener for selected trainers | 144 |
| 290–478 | **Public-info plumbing** | Revealed-moves bitmap, used-moves mirror, move-attribute reads | 189 |
| 480–493 | **Per-tick cache reset** | Sentinel write to 4 cache bytes (`BossAI_ResetTurnCaches`) | 14 |
| 495–2317 | **Move-scoring overlay** (`BossAI_ApplyMoveModel`) | The big one — 30+ `.ApplyXxxBias` heuristics, public-failure gates, role bias, tier weights | 1823 |
| 2318–2329 | **Ghost helper** | `BossAI_EnemyIsGhostType` (used by setup/Curse logic) | 12 |
| 2331–2521 | **Move pick** (`BossAI_SelectMove`) | Two-pass best/second-best, weighted dice, tier dice modifier | 191 |
| 2523–2690 | **Switch dispatch** | `BossAI_TrySwitch`, switch confidence dice, base candidate scan | 168 |
| 2692–2856 | **Threat caches (active)** | Public-threat / revealed-priority caches with $ff-sentinel cache pattern | 165 |
| 2858–3007 | **Type-matchup (no item)** | Four no-item type-matchup wrappers + `Dragon's Majesty` overlay | 150 |
| 3009–3360 | **Pressure scoring** | KO pressure / pressure score / scored power / known-modifier stack | 352 |
| 3361–3463 | **Move category + type contribution** | `BossAI_CurrentEnemyMoveCategory` (callfar TypePassive), accuracy risk, type-contribution helpers | 103 |
| 3465–3527 | **Public-faster (speed)** | Base-speed + Choice-Scarf-aware speed predicate | 63 |
| 3529–3645 | **Switch threshold + loop penalty** | Tier base + per-class delta arms, loop-penalty exception list | 117 |
| 3647–3727 | **Switch reason predicates** | KO-prevention, Perish, revenge respect (`Should*`) | 81 |
| 3729–3835 | **Switch-in classifiers** | Scarf-swing stub, suspicious switch-in, immunity-pivot | 107 |
| 3837–3953 | **Ace-timing + switch confidence** | `BossAI_AceTimingHook`, `BossAI_ComputeSwitchConfidence` | 117 |
| 3955–4068 | **Predict-player-switch + revealed-SE-move** | `BossAI_PredictPlayerSwitch`, `BossAI_HasRevealedSuperEffectiveMove` | 114 |
| 4070–4163 | **Cache misses (passive)** | `TestRevealedSpeciesMaskBit`, `HasAnyKOMove(Uncached)` | 94 |
| 4164–4220 | **Held-item helpers** | `GetEnemyHeldEffect`, Choice-lock probes, `Save/RestoreEnemyMoveStruct` | 57 |
| 4222–4302 | **Bench threat score** | `BossAI_SeenBenchThreatScore` | 81 |
| 4303–4480 | **Plan selection** | `BossAI_SelectPlanIfNeeded` (initial / adapt / decay / wincon-compromised) | 178 |
| 4482–4564 | **Party-by-role** | `BossAI_FindPartyMonByRole` | 83 |
| 4565–4810 | **Setup / status / denial classifiers** | `IsSetupEffect`, `IsCurrentEnemySetupMove`, `SetupBoostHasFurtherValue`, `SetupTurnIsAffordable`, `IsStatusEffect`, `IsDenialEffect` | 246 |
| 4811–4853 | **Seen-species index** | `BossAI_GetActiveSpeciesSeenIndex` | 43 |
| 4855–5354 | **Plausible / likely type-mask construction** | Mask compute, public-STAB seed, revealed-add, Add(Plausible/Likely)Mask twins, level-up/TM/Egg walks, Test(Plausible/Likely) twins | 500 |
| 5356–5410 | **Plan move bias** | `BossAI_ApplyPlanMoveBias` | 55 |
| 5412–5449 | **Scout / repeat biases** | `BossAI_ApplyScoutMoveBias`, `BossAI_ApplyRepeatPenalty` | 38 |
| 5451–5492 | **Score read/write** | `LoadScorePointer`, `SetScoreHL`, `Encourage/DiscourageScoreHL` | 42 |
| 5494–5610 | **Lookahead orchestration** | `ApplyLookaheadToTopMoveCandidates`, `ApplySignedDeltaToScore` | 117 |
| 5612–5905 | **Lookahead body + multi-turn projection** | `EvaluateActionLookahead`, `ApplyMultiTurnProjection`, projection helpers | 294 |
| 5907–5924 | **Signed-delta clamp** | `BossAI_ClampSignedLookaheadDelta` | 18 |
| 5926–6079 | **Primary threat type** | `GetPrimaryThreatType` (cached), `GetPrimaryThreatTypeUncached` (revealed → likely → plausible → HP fallback) | 154 |
| 6081–6216 | **Threat severity + item nullifies** | `GetRevealedMoveThreatTypeAndSeverity`, `GetTypeThreatSeverityVsEnemyMon`, `AdjustThreatSeverityForEnemyKnownDefense`, `EnemyKnownItemNullifiesThreatType`, `EnemySpeciesCanEvolve` | 136 |
| 6218–6248 | **Tier-roll thresholds** | `GetTierPlausibleRiskWeight`, `GetSpeculativePlausibleRiskWeight`, `GetScoutRollThreshold` | 31 |
| 6249–6315 | **Scouted bitmap** | `GetActiveSpeciesSeenBit`, `IsActiveSpeciesScouted`, `SetActiveSpeciesScouted`, `ShouldScout` | 67 |
| 6316–6351 | **Repeat tracker** | `UpdateRepeatTracker`, `MarkScoutedIfScoutMove` | 36 |
| 6353–6724 | **Switch-candidate risk refinement** | `RefineSwitchCandidateForPlausibleRisk`, `ComputeSwitchCandidateRisk` (huge internal `.AddTypeRisk` / `.GetTypeRiskPoints` / `.ApplyPrimaryThreatImmunityTieBreak` / `.ApplyRevealedPrioritySwitchInRisk` / `.CandidateAtHalfHP`) | 372 |
| 6725–6855 | **Switch-confidence finalization** | `ApplyPlausibleRiskToSwitchConfidence`, `ApplyPlanSwitchBias`, `ShouldSackInsteadOfSwitch`, `IsSwitchingIntoWinconRisk` | 131 |
| 6857–6866 | **Mark scout pivot** | `BossAI_MaybeMarkScoutPivot` | 10 |
| 6868–7006 | **Static data tables** | `BossAI_PlausibleThreatTypes`, `HiddenPowerThreatTypes`, `BossAITierWeights`, `BossAIDenyKOEffects`, `BossAIStatusEffects`, 9 per-leader role-effect tables, `BossAIRiskyEffects` | 139 |
| 7008–7066 | **Cross-bank `_HL` thunks** | 7 hl-preserving `farcall` wrappers to `AI Scoring` bank-`0b` helpers | 59 |

Total: 7066 lines. The biggest single block by far is `BossAI_ApplyMoveModel`
at lines 495–2317 (1823 LOC) — this *is* the "policy" surface area in
disguise. Almost every `.ApplyXxxBias` local label below the dispatch is a
mini-function the user will recognize from
`docs/boss_ai_post_patch_notes.md`'s "implemented patch summary."

### Source files at a glance

`boss.asm` is one of three files in the `Enemy Trainers` SECTION
(`main.asm:168-172`):

- `engine/battle/ai/items.asm` (above boss.asm)
- `engine/battle/ai/boss.asm` (this file)
- `engine/battle/read_trainer_attributes.asm` (below boss.asm)

The `Enemy Trainers` bank is bank `0e`. The 7 `*_HL` thunks at the file
tail target `AI Scoring` (bank `0b`, `engine/battle/ai/scoring.asm`); they
exist *because* a plain `call` from boss.asm to a scoring.asm label would
silently land at offset $7xxx in bank `0e` — the May 2026 cross-bank
softlock class. See the file's own comment block at lines 7008–7024,
commit `f2e18554` for the original fix.

## §1 Comprehension pass

### 1.1 Layer seam (platform vs policy)

The shelved rebuild plan
(`docs/boss_ai_rebuild_plan.md` on `claude/thirsty-jackson-893a52`) draws
a ~30 / 70 platform/policy split. After reading the file end-to-end, that
split is approximately right but the seam is not contiguous: platform and
policy code are interleaved, not stacked. Concrete mapping (using the
region table above):

| Layer | Regions (line ranges) | LOC | % |
| --- | --- | ---: | ---: |
| **Platform** — state tracking, no-cheat data plumbing, caches, type-matchup machinery, cross-bank thunks | 1–143, 290–493, 2692–2856 (cache shells only), 2858–3007, 3361–3463 (callfar wrappers), 4070–4163, 4164–4220, 4811–4853, 5006–5354 (mask machinery, structurally), 5451–5492 (score I/O), 6249–6288 (scouted bitmap I/O), 6316–6332 (repeat tracker), 6868–6906 (no-cheat type tables), 7008–7066 (thunks) | ~1850 | ~26% |
| **Policy** — anything that produces a numeric score, picks an action, gates a heuristic | 145–288 (adaptive lead picks an opener), 495–2317 (move-scoring overlay), 2318–2690 (move pick + switch dispatch), 3009–3360 (pressure scoring), 3465–3645 (speed + switch-threshold deltas), 3647–3835 (switch reasons), 3837–3953 (ace + confidence), 3955–4068 (predict + revealed-SE), 4222–4302 (bench threat), 4303–4564 (plan + role), 4565–4810 (effect classifiers — borderline), 4855–5005 (mask construction logic), 5067–5293 (mask source pools — borderline), 5356–5449 (move biases), 5494–5924 (lookahead), 5926–6216 (threat type/severity), 6218–6248 (tier rolls), 6290–6315 (scout decision), 6334–6351 (mark scout if scout move), 6353–6855 (switch-candidate refinement), 6857–6866, 6907–7006 (per-leader effect tables) | ~5050 | ~71% |
| Mixed (data shared by both) | 6868–6906, 6907–7006 | ~140 | ~2% |

The 30/70 prior held up. The actual split is **~26% platform / ~71%
policy / ~3% data** by line count. **Note that the seam is logical, not
spatial** — one of the strongest organization-improvement levers (§3) is
that the two layers can be made spatially contiguous without changing any
function's behavior.

### 1.2 Top-level control flow

Three entry points are called per AI tick from `engine/battle/ai/move.asm`
and `engine/battle/core.asm`. Everything else is reachable from these:

```
move.asm AI tick
    ├── BossAI_ApplyMoveModel               (495)   — score every move
    │   ├── BossAI_ResetTurnCaches          (480)
    │   ├── BossAI_SelectPlanIfNeeded       (4307)
    │   ├── BossAI_ComputePlayerPlausibleTypeMask   (4855)
    │   └── for each move:
    │       └── .ScoreMove                  (527)
    │           ├── .HeldItemMoveBlocked    (662)
    │           ├── KO/tempo/setup/status gates
    │           ├── 30+ .ApplyXxxBias       (1088..1842)
    │           ├── BossAI_ApplyPlanMoveBias       (5356)
    │           ├── BossAI_ApplyScoutMoveBias      (5412)
    │           ├── BossAI_ApplyRepeatPenalty      (5431)
    │           └── .HasKOLine final gate   (2306)
    │
    └── BossAI_SelectMove                   (2331)  — pick from scores
        ├── BossAI_SelectPlanIfNeeded       (4307)  — idempotent
        ├── BossAI_ComputePlayerPlausibleTypeMask
        ├── BossAI_ApplyLookaheadToTopMoveCandidates (5494)
        │   └── BossAI_EvaluateActionLookahead × ≤4 (5612)
        │       ├── BossAI_CurrentEnemyMovePressureScore (3042)
        │       ├── BossAI_IsCurrentEnemySetupMove
        │       ├── BossAI_HasAnyKOMove
        │       ├── BossAI_GetPrimaryThreatType
        │       └── BossAI_ApplyMultiTurnProjection (5761)
        ├── two-pass best/second-best loop  (2354..2427)
        ├── score-gap dice  (2434..2457)
        ├── BossAI_UpdateRepeatTracker     (6316)
        └── BossAI_MarkScoutedIfScoutMove  (6334)

switch.asm AI tick
    └── BossAI_TrySwitch              (2523)  — switch or item
        ├── BossAI_ResetTurnCaches
        ├── BossAI_SelectPlanIfNeeded
        ├── BossAI_ComputePlayerPlausibleTypeMask
        ├── early-out: not in danger?      (2531..2539)
        ├── BossAI_CheckAbleToSwitchSafe   (2636)
        │   └── BossAI_FindFirstAliveSwitchCandidate
        ├── BossAI_RefineSwitchCandidateForPlausibleRisk (6353)
        │   └── BossAI_ComputeSwitchCandidateRisk × N (6435)
        ├── BossAI_ComputeSwitchConfidence (3882)
        ├── BossAI_GetSwitchThreshold      (3529)
        ├── BossAI_NeedsLoopPenalty        (3608)
        ├── BossAI_ShouldSackInsteadOfSwitch (6817)
        ├── BossAI_IsSwitchingIntoWinconRisk (6834)
        ├── confidence-margin dice  (2582..2602)
        └── BossAI_MaybeMarkScoutPivot     (6857)
```

State tracking entries (`Increment*`, `Record*`) are called from
`engine/battle/core.asm` per-turn hooks, not from these three.

### 1.3 Hot path

Per `docs/agent_navigation/subsystems/boss_ai_logic.md:54-89` the hot
path is `BossAI_SelectMove → ApplyLookaheadToTopMoveCandidates →
EvaluateActionLookahead × 4 → ApplyMultiTurnProjection`. The three
"$ff-sentinel" caches (`HasAnyKOMove`, `PlayerHasPublicThreat`,
`PlayerHasRevealedPriority`) plus `GetPrimaryThreatType`'s separate
$20+ encoding exist *because* this fan-out re-asks the same questions.
Reset point is `BossAI_ResetTurnCaches` at the top of `ApplyMoveModel`
and `SwitchOrTryItem`.

### 1.4 Known-broken intuitions for this file

Things a reader meets cold and gets wrong:

1. **The file looks bottom-heavy with utilities, but it isn't.** The
   bottom (lines 6868–7066) is a clean data + thunks tail. The genuine
   policy weight is in 495–2317 (move scoring) and 6353–6855 (switch
   refinement).
2. **`.ApplyRoleBias` (2088) is *not* a top-level function.** It's a
   local label under `BossAI_ApplyMoveModel`. The 11 per-leader branches
   (`.falkner`, `.rival`, `.chuck`, ...) are also local under
   `ApplyMoveModel`. They share the file-scope effect tables at
   6935–7000 only by name (the tables are top-level labels).
3. **"Plausible" and "likely" are different masks, not a typo.** Plausible
   = could exist; likely = high evidence weight. Both are 4-byte type
   bitmasks in WRAM. The mask construction code (4948–5005) and the test
   code (5294–5354) come in twin pairs differing only by which mask
   pointer they target.
4. **`BossAI_IsScarfSwingPossible` (3729) is a deliberate stub.** Body is
   `and a; ret`. Comment: *"Do not infer unrevealed player Choice Scarf
   from private speed values."* It returns no-carry intentionally — this
   is a no-cheat assertion, not dead code.
5. **`BossAITierWeights` has 5 rows for 3 tiers.** Rows 3 and 4 are sub-
   tier "ramp" rows (early +25%, early +50%) used by per-class overrides
   in `BossAITierRampMap` (`data/trainers/ai_tiers.asm:51`). See comment
   at `boss.asm:6900-6903`.
6. **`farcall` from boss.asm to AI Scoring helpers is broken** (clobbers
   `hl`). All such crossings go via the `*_HL` thunks at 7026–7066. Do
   not introduce new direct `call AI*` references — the 39 sites this
   replaced are documented in `f2e18554`.
7. **`BossAI_TraceTopMoves` lives elsewhere.** It was lifted to
   `engine/battle/ai/boss_trace_topmoves.asm` (own SECTION) so the trace
   build doesn't push the `Enemy Trainers` bank past 16 KiB. Caller in
   `BossAI_SelectMove` uses `farcall`. See `boss.asm:6895`.

## §2 Index for fast lookup

The existing `docs/agent_navigation/subsystems/boss_ai_logic.md` is the
"behavior → label / line" index. It's fine. What's *missing* and would
sharpen lookup:

### 2.1 Add a per-region banner comment to boss.asm itself (proposal — non-behavioral)

Insert one comment block per region from §0 above, of the form:

```
; ============================================================
; Region: <name>
; Concern: <one line>
; Layer: PLATFORM | POLICY | DATA | THUNK
; Lines (this region): N
; ============================================================
```

Cost: ~40 banner blocks × ~8 lines each = ~320 lines of comments.
Benefit: end-to-end readability without leaving the file. **No behavioral
change** — comments do not assemble. Trace captures unaffected.

The catch: line numbers in `boss_ai_logic.md` are hand-maintained and
audited by `tools/audit/check_boss_ai_index_lines.py`. Inserting comment
blocks shifts line numbers under every label below the insertion. The
audit will fail until the index is regenerated (or until a generator
script is built that auto-emits the index from `boss.asm` — see §2.3).

### 2.2 Add a layer marker to each top-level function header

Insert a single-line tag at the top of every top-level label:

```
; ai-layer: PLATFORM   ; or POLICY
BossAI_GetMoveAttr:
```

Cost: 160 single-line comments. Benefit: the seam (§1.1) becomes
auditable from the file alone — a future audit
`check_boss_ai_layer_tags.py` could enforce that no platform-tagged
function reads private state, and no policy-tagged function is reachable
without going through the platform API.

This is *the* tag-once, audit-forever artifact for the no-cheat invariant
that today is enforced by symbol blacklist
(`tools/audit/check_boss_ai_no_cheat.py`). The blacklist catches
`wPartyMons` etc. but not "this policy function leaked into platform
territory by reading a not-yet-blacklisted private var." Layer tags
+ a per-function audit close that gap.

Defer behind: explicit user green-light. This is pure policy that
constrains future-Claude / future-Codex work.

### 2.3 Auto-generated index (proposal — new tool)

Replace `boss_ai_logic.md`'s hand-maintained line numbers with a
generator: `scripts/generate_boss_ai_index.py`. Reads `boss.asm`, emits
the existing micro-index format with line numbers re-extracted on every
build. The audit `check_boss_ai_index_lines.py` either deprecates (no
hand-numbers to audit) or becomes the build-time check that the
generator's output is committed.

Cost: ~150 lines of Python, similar shape to
`scripts/generate_dev_index.py`. Benefit: line-number drift class of
audit failures goes to zero; reorganizing boss.asm becomes free of
"index is out of date" round-trips.

Defer behind: §3 organization decision. The generator's output format
depends on whether boss.asm stays one file or gets split.

## §3 Organization proposals — RESOLVED

Option C is the shipped organization. The alternatives below are preserved as
planning history. The linker-visible `BossAI_*` exports remain stable.

### Option A — Banner comments only (lowest cost, recommended first step)

Insert §2.1 region banners and §2.2 layer tags. No code moves. No
function changes. Side effects: line numbers shift; index needs
regenerating once.

Pros:
- Zero behavioral change. Trace captures unaffected.
- Lowest cost (~1 hour of insertion + 1 audit run + index refresh).
- Unblocks every other organization decision: with banners in place,
  *future* code reorgs are reasoned about per-region.

Cons:
- Doesn't actually shorten the file. Lookup is still "scroll till you
  hit the right banner."

Recommended as the **first** change to land. It's a no-regret prerequisite
to either of the next two.

### Option B — Section reorder within boss.asm (medium cost)

Reorder so platform-layer regions are contiguous at the top, policy
layer below, data tail unchanged. Per §1.1 this halves the cognitive
distance — a future reader can stop reading at the policy/platform
boundary if they only care about the no-cheat invariants.

Order proposal:
1. **State tracking** (currently 1–143)
2. **Public-info plumbing** (290–478)
3. **Per-tick cache reset** (480–493)
4. **Caches (passive)** (4070–4163, the `Test*Bit` and uncached
   helpers)
5. **Held-item helpers** (4164–4220)
6. **Type-matchup (no item) machinery** (2858–3007)
7. **Move-category callfar wrappers** (3361–3463)
8. **Seen-species index** (4811–4853)
9. **Mask machinery** (5006–5354) — *structural* parts of plausible/
   likely; the construction (4855–5005, 5067–5293) is policy.
10. **Score I/O** (5451–5492)
11. **Scouted bitmap I/O** (6249–6288, 6316–6332)
12. **Static no-cheat tables** (6868–6906)
13. **Cross-bank `_HL` thunks** (7008–7066)

— PLATFORM/POLICY SEAM —

14. Adaptive lead (145–288)
15. Move-scoring overlay (495–2317)
16. Move pick (2331–2521)
17. Switch dispatch + base candidate scan (2523–2690)
18. Threat caches (active) (2692–2856)
19. Pressure scoring (3009–3360)
20. Public-faster (3465–3527)
21. Switch threshold + loop penalty (3529–3645)
22. Switch reason predicates (3647–3727)
23. Switch-in classifiers (3729–3835)
24. Ace timing + switch confidence (3837–3953)
25. Predict + revealed-SE (3955–4068)
26. Bench threat score (4222–4302)
27. Plan selection (4303–4480)
28. Party-by-role (4482–4564)
29. Setup/status/denial classifiers (4565–4810)
30. Mask construction policy (4855–5005, 5067–5293)
31. Plan/scout/repeat biases (5356–5449)
32. Lookahead orchestration (5494–5610)
33. Lookahead body + projection (5612–5905)
34. Signed-delta clamp (5907–5924)
35. Primary threat type (5926–6079)
36. Threat severity (6081–6216)
37. Tier-roll thresholds (6218–6248)
38. Scout decision (6290–6315)
39. Switch-candidate risk refinement (6353–6724)
40. Switch-confidence finalization (6725–6855)
41. Mark scout pivot (6857–6866)
42. Per-leader effect tables (6907–7006)

Pros:
- Spatially contiguous platform layer ↔ better mental model.
- Future audit / refactor work gets a clean seam to attach to.

Cons:
- Reorders ~7000 lines. Trace captures should still pass (no logic
  changed) but every per-leader trace's first-decision diff must be
  sanity-checked once.
- Index regeneration mandatory.
- `git blame` chains are interrupted — historical diff archaeology gets
  one extra hop.
- Largest-bank-impact change: the linker placement of `Enemy Trainers`
  shifts within bank `0e` (totals unchanged). `roms.sha1` will not match
  unless the resulting ROM is byte-identical, which it should be — `make
  compare` is the verification.

Defer behind: Option A landing first; user explicit approval of the
reorder; trace-capture refresh budget.

### Option C — Split boss.asm into multiple files (SHIPPED + REPARTITIONED)

The shipped split now uses four emitted Boss AI files in the `Enemy Trainers`
SECTION. The repartition folds `boss_data.asm`: no independent static data
remained after no-cheat tables moved to platform code and policy tables moved
to their owner policy code. `main.asm` includes guarded fragments from the
concern-owned files in original byte order for `make compare`. Original
proposal:

- `engine/battle/ai/boss_platform.asm` (~1850 lines): regions in §1.1's
  platform set.
- `engine/battle/ai/boss_policy_move.asm` (~2300 lines): move scoring +
  pick + plan/role.
- `engine/battle/ai/boss_policy_switch.asm` (~2100 lines): switch
  dispatch + candidate refinement + confidence + lookahead.
- `engine/battle/ai/boss_data.asm` (~140 lines): static tables, folded if
  empty.
- `engine/battle/ai/boss_thunks.asm` (~60 lines): cross-bank `_HL`
  thunks. (Kept in `Enemy Trainers` SECTION — must stay in bank `0e`.)

`main.asm:171` becomes guarded INCLUDE fragments instead of 1 monolithic
include. All four emitted files are included in the same `Enemy Trainers`
SECTION so the bank layout and
intra-bank `call` reachability are unchanged. (If a thunk were placed in
a different SECTION it would silently break the cross-bank fix.)

Pros:
- File-scoped lookups become fast: "switch logic lives in ONE file, not
  scattered across 1,800 lines of one giant file."
- Each file is below ~2,500 lines, comprehensible end-to-end in one
  read.
- The platform file becomes the canonical reference for
  `check_boss_ai_no_cheat.py`'s scan surface (currently scans boss.asm,
  move.asm, items.asm — would scan boss_platform.asm + boss_policy_*.asm).

Cons:
- 5× include + 5× SECTION-relative addressing increases the surface for
  link-time mistakes (e.g., a label downgraded `::` → `:` no longer
  visible across files; current single-file convention masks this
  class).
- `tools/audit/check_boss_ai_no_cheat.py` `SCAN_FILES` list expands.
- `tools/audit/check_boss_ai_index_lines.py` per-file line audit gets
  more complex; a generator (§2.3) is essentially mandatory.
- The 4 `tools/audit/check_boss_ai_*.py` audits all hard-code paths to
  `engine/battle/ai/boss.asm`. Need updating.
- Same trace-capture and `make compare` concerns as Option B.

Shipped result after repartition:
- `engine/battle/ai/boss_platform.asm` — platform-owned guarded fragments:
  state/public-info plumbing, passive caches, held-item helpers, type-matchup
  machinery, structural masks, score/scout I/O, and no-cheat tables.
- `engine/battle/ai/boss_policy_move.asm` — move-policy guarded fragments:
  adaptive lead, move scoring, move pick, active threat policy, plan/role,
  lookahead, threat/scout policy, and policy-owned tables.
- `engine/battle/ai/boss_policy_switch.asm` — switch-policy guarded fragments:
  switch dispatch, switch reason/classifier gates, confidence, candidate risk
  refinement, and confidence finalization.
- `engine/battle/ai/boss_thunks.asm` — the HL-preserving cross-bank thunks,
  still in bank `0e`.

### EMIT-guard convention (the trick that makes the seam work)

The shipped repartition uses an unusual pattern that future contributors
need to understand before editing `main.asm` or adding new boss-AI code.

**The decoupling.** In a normal RGBDS layout, the order regions appear in
ROM is identical to the order they appear in source files. That's a
problem here: organizing files by *concern* (platform vs policy) and
preserving the pre-split ROM byte order are two different orderings.
You can have one or the other, not both, with a normal include.

The shipped pattern decouples them. Each region inside a `boss_*.asm`
file is wrapped in a `BOSSAI_EMIT_<region>` guard. Only the region whose
guard is active emits during a given INCLUDE pass. `main.asm` then
INCLUDEs each file *multiple times*, setting one guard per pass, in the
exact ROM order.

**Concrete shape.** `main.asm` around line 167 looks like:

```
DEF BOSSAI_EMIT_PLATFORM_STATE_TRACKING EQU 1
INCLUDE "engine/battle/ai/boss_platform.asm"   ; emits state-tracking only
PURGE BOSSAI_EMIT_PLATFORM_STATE_TRACKING

DEF BOSSAI_EMIT_MOVE_ADAPTIVE_LEAD EQU 1
INCLUDE "engine/battle/ai/boss_policy_move.asm"  ; emits adaptive-lead only
PURGE BOSSAI_EMIT_MOVE_ADAPTIVE_LEAD

DEF BOSSAI_EMIT_PLATFORM_PUBLIC_INFO EQU 1
INCLUDE "engine/battle/ai/boss_platform.asm"   ; back to platform
PURGE BOSSAI_EMIT_PLATFORM_PUBLIC_INFO

... ~30 more INCLUDE+PURGE pairs ...
```

Inside each file:

```
if DEF(BOSSAI_EMIT_PLATFORM_STATE_TRACKING)
; ============================================================
; Region: State tracking
...
BossAI_IncrementTurnsElapsed:
    ...
endc
```

The assembler reads the file every time, but only the region whose
guard is active actually contributes bytes. Every other region is
skipped silently.

**Adding a new region.** If you write a new `BossAI_*` function or new
`.ApplyXxxBias` module:

1. Decide which file it belongs in (platform vs policy_move vs
   policy_switch — use the layer rules from §1.1).
2. Wrap the new region in `if DEF(BOSSAI_EMIT_<name>)` /
   `endc` with a matching guard name.
3. Add an `INCLUDE`/`PURGE` pair to `main.asm` at the slot in ROM
   order where the new region should emit.
4. Build with `make compare` to confirm ROM bytes match expectations
   (or, if you intentionally added bytes, that the new bytes are
   where you expect).

**Common pitfalls.**

- **Adding a region to a file but not main.asm.** The region exists in
  source but never emits to ROM — silently dead code. Always pair file
  edit with main.asm edit.
- **Two regions with the same guard name.** The assembler emits both,
  in source order, the first time the guard is active. Probably not
  what you want. Use unique guard names.
- **Trying to read file size as a measure of code size.** `wc -l
  boss_policy_move.asm` is the sum of all region sizes regardless of
  emission order. Not meaningful. Count regions inside guards
  individually.
- **Assuming order inside a file matters.** It doesn't, except as a
  readability choice. ROM order is set by `main.asm`'s
  INCLUDE/PURGE sequence, not by where a region sits in its file.
- **Touching a thunk's SECTION assignment.** Thunks must stay in bank
  `0e` (`Enemy Trainers` SECTION). The cross-bank fix at
  `commit f2e18554` depends on this; moving a thunk to a different
  SECTION silently breaks the bank `0e` callers' reachability.

**Why this pattern instead of physically reordering files.** A normal
file-partition split would have forced one of these two compromises:
either each file is internally ordered by ROM position (no clean
intra-file organization by concern) or ROM bytes shift (breaks `make
compare` byte-identity, requires trace-capture refresh, surfaces every
audit that depends on bank `0e` byte layout). The EMIT-guard pattern
gives both: each file is internally organized however the author
wants, AND ROM bytes stay byte-identical.

The cost is `main.asm` complexity (~30 INCLUDE+PURGE pairs instead of
1 INCLUDE) and the cognitive load of the convention itself. Both are
acceptable for the seam clarity gained.

### Recommendation

Resolved: Option C is the current source layout. Future simplification and
optimization proposals in §4–§7 remain separate, unshipped work.

## §4 Simplification opportunities

Concrete places where N functions could be 1 (or where a thing exists
twice). All zero-behavior-change.

### 4.1 Twin functions differing only by which mask they target

| Plausible | Likely | Diff |
| --- | --- | --- |
| `BossAI_AddMoveIdToPlausibleMask` (4948) | `BossAI_AddMoveIdToLikelyMask` (4977) | calls `SetPlausibleMaskBit` vs `SetLikelyMaskBit` |
| `BossAI_SetPlausibleMaskBit` (5013) | `BossAI_SetLikelyMaskBit` (5040) | base ptr `wBossAIPlausibleTypeMaskCache` vs `wBossAILikelyTypeMaskCache` |
| `BossAI_TestPlausibleMaskBit` (5294) | `BossAI_TestLikelyMaskBit` (5325) | same — base ptr only |
| `BossAI_AddSpeciesLevelUpMovesToMask` (5159) | `BossAI_AddSpeciesLevelUpMovesToLikelyMask` (5215) | calls `AddMoveIdToPlausibleMask` vs `AddMoveIdToLikelyMask` |

Four twins, ~140 LOC of duplicate body. Three options:

- **Macro**: define `BIT_INDEX_TO_MASK_BYTE base_ptr` macro. Each twin
  becomes a 1-line wrapper. Saves bytes only if the macro inlines
  smartly, but always saves *source* lines and risk of one twin drifting
  from the other.
- **Single function with a base-ptr argument**: one function, callers
  load `hl, base_ptr` first. Saves the most. Slight per-call overhead
  if the load wasn't already in flight; check sites individually.
- **Single function with a flag arg in `b`**: branch internally on the
  flag. Cheapest call site, slightly slower body.

Pick #2. Twin pairs go to one function each; net ~70 LOC saved; no
behavior change. Twin discovery is at risk of one body drifting from the
other, which is exactly the stale-twin class —
`BossAI_AddMoveIdToPlausibleMask` and `…ToLikelyMask` (4948, 4977) are
**already drifting**: both share the `EFFECT_HIDDEN_POWER` early-exit
path, but the early-exit calls a different mask helper (`SetPlausible…`
vs `SetLikely…`), so the bodies are *almost* but not quite mechanical
twins. Fold them.

### 4.2 Twin score-mutators

| `.EncourageScoreByA` (2262, local under `ApplyMoveModel`) | `BossAI_EncourageScoreHL` (5465) |
| `.DiscourageScoreByA` (2275, local under `ApplyMoveModel`) | `BossAI_DiscourageScoreHL` (5479) |

`*_HL` version = `LoadScorePointer` + `…ByA` body. Today `…ByA` is
unreachable from outside `ApplyMoveModel` because it's a local label;
the wrapper exists for callers that don't already have the score
pointer in `hl`. Cleanup: either promote `*ByA` to top-level
`BossAI_EncourageScoreByA` (private to file is fine, just not local) and
have `*_HL` call it, or fold both into one function and cache-load the
pointer based on a flag. Option A is simpler. Saves ~12 LOC and removes
the "two names for the same thing" surprise.

### 4.3 Cache-shaped helpers share a 5-instruction prelude

| `BossAI_HasAnyKOMove` (4104) |
| `BossAI_PlayerHasPublicThreatVsEnemy` (2692) |
| `BossAI_PlayerHasRevealedPriorityThreat` (2781) |

All three start with:

```
ld a, [<cache_ptr>]
inc a
jr z, .miss
dec a
rrca
ret
.miss
call <Uncached>
push af
sbc a, a
and 1
ld [<cache_ptr>], a
pop af
ret
```

— byte-identical except for cache pointer and target label. A macro
`BOSS_AI_CACHED_PREDICATE cache_ptr, uncached_target` saves ~30 LOC
(3 × 10 lines of wrapper) and structurally documents that "this is the
cached form of that uncached predicate." `BossAI_GetPrimaryThreatType`
(5926) also cache-shaped but uses a different sentinel scheme ($ff vs
$20+ vs 0..$1f) — should stay as-is or get a slightly more general macro.

### 4.4 Seven near-identical `_HL` thunks

Lines 7026–7066:
```
AIGetEnemyMove_HL:
    push hl
    farcall AIGetEnemyMove
    pop hl
    ret
```
× 7 different targets. Define a `BOSS_AI_HL_THUNK target` macro. Each
thunk goes from 4 lines to 1. Net ~21 LOC saved. Assembled bytes
identical. The big block comment explaining *why* the thunks exist
(7008–7024) stays.

### 4.5 The 6-arm saturating-add/subtract in `.ApplyClassSwitchThresholdMod`

Lines 3564–3606 are six arms:
```
.minus_10
    ld a, b
    sub 10
    ret nc
    xor a
    ret
```
× 4 (deltas −10, −8, −6, −4) + 2 plus-arms (clamped at 95). Replace
with a small parameterized helper:

```
; saturate b ± delta, clamping at 0 (sub) or 95 (add). Returns clamped a.
SaturateThresholdDelta:
    ; <one body, takes signed delta in c>
```

Each arm becomes: `ld c, -10 :: jr SaturateThresholdDelta`. Saves ~25
LOC. The dispatch above stays as a `cp / jr z` chain; only the
delta-application bodies merge.

### 4.6 The 30+ `.ApplyXxxBias` calls in `BossAI_ApplyMoveModel`

Lines 616–644 are a flat list of ~30 unconditional `call .ApplyXxxBias`
each. The pattern is structural — every bias is a self-contained gate.
Possible simplifications:

- **Table-driven**: a `db ApplyXxxBias` table, walked by a tiny
  dispatcher. Saves only a few bytes per entry; loses the in-source
  documentation value. **Not recommended.**
- **Group by gate type**: many of these gates are
  "if effect == X, encourage/discourage by N." Lift the common shape
  into a helper that takes (effect_id, encourage_amount) and call it
  once per data row. Saves ~80 LOC. Slight readability cost — the
  named bias becomes one row in a table instead of one named
  function. **Worth proposing; user pick.**
- **Leave as-is**: the named functions are easy to grep, easy to
  comment per-bias, and the design intent doc
  (`docs/boss_ai_post_patch_notes.md`) anchors each by name. Status
  quo cost is low. **Recommended.**

This bias chain is also the obvious target for any future structural-
prior table the rebuild brings — but that's the rebuild's problem.

### 4.7 `BossAI_IsScarfSwingPossible` (3729)

Body: `and a; ret`. Comment notes it's an intentional no-cheat assertion.
Today it's a 2-byte function with one caller (only? let me check —
it's referenced once: from `BossAI_NeedsLoopPenalty` indirectly? actually
grep below). If it has no callers in mainline boss.asm, it's a stub-only
no-cheat marker. Either:

- Delete it and document the no-cheat assertion in
  `docs/boss_ai_spec.md` instead.
- Or keep, since the cost is 2 bytes and the symbol's existence is
  itself the no-cheat tripwire (a future PR adding a Scarf-swing inference
  bumps into the named stub and is forced to think about it).

**Recommendation:** keep. Cost is trivially low; the symbol-as-tripwire
is exactly the kind of friction that prevents future-Claude leaking
private state.

### 4.8 The two-pass best/second-best loop in `BossAI_SelectMove`

Lines 2354–2427 walk `wEnemyMonMoves` twice — once for the best
candidate, once for the second-best. Single-pass is possible: track two
running mins simultaneously. Saves ~40 LOC. Slightly harder to read.
**Borderline; defer until the file's structural reorg has settled.**

### 4.9 Uncategorized

- `BossAI_DecPressureB` (3315) and `BossAI_DecThreatSeverityB` (6182)
  are byte-identical: `ld a, b; and a; ret z; dec b; ret`. The semantic
  distinction (pressure vs severity) is documented in their callers but
  the bodies are duplicates. Fold into one
  `BossAI_DecBSaturateAtZero` and rename callers, or leave as a paired-
  comment pattern. Symbolic distinction has near-zero cost (5 bytes ×
  duplicate). **Leave.**
- The "tier-conditional integer" pattern (`GetSwitchThreshold`,
  `GetScoutRollThreshold`, `GetTierPlausibleRiskWeight`,
  `BossAI_AdjustBestMovePickChance` per-tier add) repeats four times
  with the shape *"if tier == LATE return X; if MID return Y; else Z."*
  Could be a small `db` table indexed by tier. Saves ~30 LOC across
  the four. Caller sites become one-liners. **Defer behind organization
  reorg.**

## §5 Optimization opportunities

Bytes/cycles savings. None of these are urgent — the file links
comfortably and the per-tick latency is "audited 2026-05-02" as
acceptable per `boss_ai_logic.md:54`. Listed for completeness.

### 5.1 AG-NN audit-track candidates worth re-running on boss.asm

Per `tech_debt/STATUS.md` and the asm-guide §3.13 / §3.14 (recurrence-
prevention rule), the AG-NN class is "ABI-changing fixes silently break
in-bank callers." `boss.asm` calls scoring.asm helpers via thunks (the
seven `*_HL` wrappers) but the thunks predate the AG-08 c-mirror audit
discipline. Worth a one-shot audit pass:

- Run `tools/audit/check_farcall_a_clobber.py` against the seven
  thunks (or the targets they wrap). This is in the release-smoke floor
  per CLAUDE.md so should already be green; confirm.
- Run `python -m tools.damage_debugger.clobber_smoke` after any change
  that touches these thunks (per asm-guide §3.13/§3.14).
- The thunks themselves preserve `hl` via `push hl/pop hl`. They do
  *not* preserve `bc`. Callers that need `bc` preserved across the
  thunk must save/restore it themselves. **Audit candidate**: scan
  thunk callers for any that consume `c` post-thunk where the thunk
  target may have written to `c`. The `BossAI_*` callers reach
  `AICheckEnemyQuarterHP_HL` etc. which are HP comparison helpers
  that probably leave `bc` alone, but this hasn't been validated.

### 5.2 `BossAI_HasAnyKOMoveUncached` does an unnecessary save+restore on Choice-locked path

Lines 4120–4132: when the enemy is Choice-locked to a move with power
> 0 and KO pressure, the function unconditionally pairs
`BossAI_SaveEnemyMoveStruct` (4121, 5-byte CopyBytes copy) with
`BossAI_RestoreEnemyMoveStruct` (4130). The save can be skipped if the
caller already saved (none do today). More importantly, the save can be
deferred until after the early-exit path: today `MOVE_POWER == 0` falls
through to `.no` which still calls Restore. A no-op restore on top of
no-op save is harmless but wastes ~25 cycles per cache miss. Move the
save inside the path that mutates the struct.

Estimated savings: ~25 cycles per first-call to `HasAnyKOMove` in a turn
where the no-power path triggers. Negligible per turn.

### 5.3 `BossAI_TestRevealedSpeciesMaskBit` (4070), `TestPlausibleMaskBit` (5294), `TestLikelyMaskBit` (5325), and the `Set*` siblings all do an O(N) shift loop

The shift loop:
```
ld a, c
and %00000111
ld e, a
ld d, 1
.loop
    ld a, e
    and a
    jr z, .test
    sla d
    dec e
    jr .loop
.test
```
walks 0..7 to compute `1 << (c & 7)`. Replace with a 8-byte LUT
(`BitMaskByIndex: db 1, 2, 4, 8, 16, 32, 64, 128`), `ld d, [hl]` after
indexing. Saves ~6 cycles per call, fixed 7 cycles in the worst case.
Six call sites → meaningful cycles per turn. ~12 byte ROM cost (LUT
+ ld), saves ~30 byte ROM (one shift loop body removed × 6 sites).

### 5.4 `.GetTierWeight` (2244) walks `BossAITierWeights` row-by-row

```
.GetTierWeight
    ld hl, BossAITierWeights
    ld a, [wBossAITierWeightRow]
    and a
    jr z, .got_tier
.tier_loop
    ld de, 7
    add hl, de
    dec a
    jr nz, .tier_loop
```

Bounded ≤4 iterations (5 rows). Replace with a single `(row * 7)`
multiplication: `ld a, [wBossAITierWeightRow]; ld d, a; sla a; sla a;
sla a; sub d; ld e, a; ld d, 0; add hl, de`. Saves the loop overhead
(~12 cycles per row × up to 4 rows). Frequently called inside
`ApplyMoveModel`'s hot bias chain. Modest improvement.

### 5.5 Tier-conditional integer pattern (~6 sites) could be table-driven

`GetSwitchThreshold`, `GetScoutRollThreshold`,
`GetTierPlausibleRiskWeight`, `GetSpeculativePlausibleRiskWeight`,
the inline `AdjustBestMovePickChance` per-tier add, and
`BossAI_PredictPlayerSwitch`'s tier gate all do
`cp AI_TIER_LATE :: jr z :: cp AI_TIER_MID :: jr z :: <else>`. Replace
with `db` tables indexed by `wBossAITier`. Saves ~30 bytes per site.
Bytes-only optimization; cycles roughly unchanged.

### 5.6 `IF DEF(BOSS_AI_TRACE)` blocks (~12 sites) inflate the bank under trace builds

Trace fields are written inline at: `SelectPlanIfNeeded` exit (4329),
`SelectMove` (2339, 2345, 2479, 2554), `ResetTurnCaches`-adjacent,
`ApplyLookaheadToTopMoveCandidates` (5499), `ComputePlayerPlausibleTypeMask`
(4887), `ShouldScout` (6305), `MarkScoutedIfScoutMove` (6346),
`MaybeMarkScoutPivot` (6861).

The current size budget (`Enemy Trainers` 12430/16384) accommodates
trace fields with ~3954 bytes free. No urgency. *If* trace+future-
heuristics bump pressure, lift the trace writes into a single
`BossAI_TraceWrite` helper called via `IF DEF(BOSS_AI_TRACE)`-gated
`farcall`. Already partially done for `TraceTopMoves` (lifted to its own
SECTION; see the comment at `boss.asm:6895`).

### 5.7 `BossAI_ResetTurnCaches` (480) writes the same byte to four addresses

```
ld a, $ff
ld [wBossAIHasKOMoveCache], a
ld [wBossAIPublicThreatCache], a
ld [wBossAIRevealedPriorityCache], a
ld [wBossAIPrimaryThreatCache], a
ret
```

If the four cache bytes are guaranteed adjacent in WRAM (check
`ram/wram.asm`), replace with a 4-byte loop:
```
ld hl, wBossAIHasKOMoveCache
ld a, $ff
ld b, 4
.loop
    ld [hli], a
    dec b
    jr nz, .loop
ret
```
Saves ~6 bytes; cycles roughly equal. Worth the change *if* the WRAM
fields are already adjacent and audit passes; otherwise leave (cost of
field reordering > benefit).

Verify before action: check `ram/wram.asm` for adjacency.

### 5.8 The mask construction loop in `BossAI_AddBaseTMHMMovesToMask` (5126)

The TM/HM bit walk:
```
inc c
sla b
jr nz, .bit_ok
ld b, 1
inc hl
.bit_ok
```
processes one bit per iteration. The shift through `b` to track the bit
position is a known idiom but somewhat awkward; a LUT-based approach
(see §5.3) would also help here. Bounded by `NUM_TM_HM` (~64), executed
once per mask compute (which is itself cached per `wBattleMon{Species,
Level}`). Modest benefit.

## §6 Constraints when planning execution

Anything in §3–§5 that lands needs to satisfy:

1. **Trace-capture regression suite.** Per-leader `audit/boss_ai_trace/
   *_live.txt` files capture first-decision behavior byte-for-byte.
   Any change that flips even one byte of any capture must be either
   (a) explicitly user-approved (and the capture refreshed), or (b)
   rolled back. Pure simplification (twin folds) and pure reorganization
   should produce zero diffs. Optimization changes (§5.4, §5.7) need a
   per-tier sanity run.
2. **No-cheat audits.** `tools/audit/check_boss_ai_no_cheat.py`,
   `check_boss_ai_gating.py`, and the others in
   `tools/audit/check_boss_ai_*.py` are in the release-smoke floor.
   Reorganizing must not introduce a new private-state read; folding
   twins must not cross the platform/policy seam.
3. **WRAM reserve.** `Boss AI WRAM Reserve` per `dev_index.md`: 104/140
   used (normal), 123/140 used (with `BOSS_AI_TRACE`). Reorganization
   must not grow state. §5.7 (cache adjacency) needs this checked.
4. **Bank `0e` budget.** `Enemy Trainers` is `0e:4000-708d` = 12430
   bytes used / 16384 capacity. ~3954 free. Banner comments (Option A)
   cost zero ROM bytes. Code reorgs (Options B, C) should be byte-
   identical at the linker output. §5 optimizations either save or
   net-zero. None should grow bytes.
5. **Bank `0e` constraint on intra-bank `call`.** The 7 `*_HL` thunks
   exist because boss.asm's policy code uses plain `call` to reach
   them, and they bridge to bank `0b` via `farcall`. **All seven thunks
   must remain in the `Enemy Trainers` SECTION.** A future split (Option
   C) that relocates `boss_thunks.asm` to a different SECTION breaks
   this. Lock this as an invariant for any organization plan.
6. **`make compare` invariant.** Parity ROM SHA1
   (`d8b8a3600a465308c9953dfa04f0081c05bdcb94` for Gold UE) is the gold
   standard for "no behavior changed." Banner comments and pure code
   moves should still match. Any change that breaks SHA1 is by
   definition not parity-preserving.

## §7 Recommended near-term path

1. **Land Option A (banners + layer tags).** No behavioral risk, low
   cost, unlocks the rest. Land as a self-contained PR.
2. **Add an auto-generator for `boss_ai_logic.md`** (§2.3). After the
   banners land, the index becomes a function of the source — generate
   it. Deprecate `check_boss_ai_index_lines.py` in favor of "generator
   output is committed and matches" check.
3. **Pause and check with the user.** §3 (B/C reorg), §4 (twin folds),
   §5 (optimizations) are independent decisions. Don't bundle.
4. **If user green-lights twin folds (§4.1, 4.2, 4.3, 4.4):** land each
   as its own PR with a single-purpose commit. Each is small (<50 lines
   diff) and trivially auditable. Run `make compare` after each.
5. **Defer Option B / C until after twin folds land.** Reordering or
   splitting a file with known duplication is wasted motion.
6. **Optimization (§5) is last.** Latency is acceptable today; bytes
   are not pressing. These are nice-to-haves and should not be on the
   critical path of any other change.

## §8 Out of scope for this plan

- Anything that changes per-leader behavior. That's the rebuild's
  domain; rebuild is shelved.
- Touching `engine/battle/ai/scoring.asm`, `engine/battle/ai/move.asm`,
  or `engine/battle/ai/items.asm`. This plan is `boss.asm`-scoped.
- Adding new heuristics. Same — rebuild's domain.
- The damage debugger workstream (`tools/damage_debugger/`) — separate
  active focus area, not in scope here.
- `engine/battle/ai/POLICY_DESIGN.md` and `engine/battle/ai/PLATFORM_API.md`
  — those are deliverables of the shelved rebuild's Step 1 and Step 2,
  not this plan. (The §1.1 layer seam table here is a partial
  pre-input to PLATFORM_API.md if/when the rebuild resumes, but it is
  not that document.)

## §9 What landing this would change in the doc tree

Option A only:
- Modified: `engine/battle/ai/boss.asm` (banner + tag comments only).
- Modified: `docs/agent_navigation/subsystems/boss_ai_logic.md` (line
  numbers refreshed).
- Modified: `docs/generated/dev_index.md` (regenerated).
- No `roms.sha1` change (comments don't assemble).
- No save-format change.

Options B and C (if user approves later):
- Same set, plus possible new files (Option C) and
  `tools/audit/check_boss_ai_*.py` `SCAN_FILES` updates.

## Appendix A — Region map (machine-readable)

For a future generator (§2.3) — the regions in §0 in TSV form. One row
per region, fields: `start_line`, `end_line`, `name`, `layer`, `loc`.

```
1	143	state_tracking	PLATFORM	143
145	288	adaptive_lead	POLICY	144
290	478	public_info_plumbing	PLATFORM	189
480	493	per_tick_cache_reset	PLATFORM	14
495	2317	move_scoring_overlay	POLICY	1823
2318	2329	ghost_helper	POLICY	12
2331	2521	move_pick	POLICY	191
2523	2690	switch_dispatch	POLICY	168
2692	2856	threat_caches_active	PLATFORM	165
2858	3007	type_matchup_no_item	PLATFORM	150
3009	3360	pressure_scoring	POLICY	352
3361	3463	move_category_and_type_contribution	PLATFORM	103
3465	3527	public_faster	POLICY	63
3529	3645	switch_threshold_loop_penalty	POLICY	117
3647	3727	switch_reason_predicates	POLICY	81
3729	3835	switch_in_classifiers	POLICY	107
3837	3953	ace_timing_switch_confidence	POLICY	117
3955	4068	predict_revealed_se	POLICY	114
4070	4163	caches_passive	PLATFORM	94
4164	4220	held_item_helpers	PLATFORM	57
4222	4302	bench_threat_score	POLICY	81
4303	4480	plan_selection	POLICY	178
4482	4564	party_by_role	POLICY	83
4565	4810	effect_classifiers	POLICY	246
4811	4853	seen_species_index	PLATFORM	43
4855	5354	plausible_likely_type_mask	MIXED	500
5356	5410	plan_move_bias	POLICY	55
5412	5449	scout_repeat_biases	POLICY	38
5451	5492	score_io	PLATFORM	42
5494	5610	lookahead_orchestration	POLICY	117
5612	5905	lookahead_body_projection	POLICY	294
5907	5924	signed_delta_clamp	POLICY	18
5926	6079	primary_threat_type	POLICY	154
6081	6216	threat_severity	POLICY	136
6218	6248	tier_roll_thresholds	POLICY	31
6249	6315	scouted_bitmap	PLATFORM	67
6316	6351	repeat_tracker	PLATFORM	36
6353	6724	switch_candidate_risk	POLICY	372
6725	6855	switch_confidence_finalization	POLICY	131
6857	6866	mark_scout_pivot	POLICY	10
6868	7006	static_data_tables	DATA	139
7008	7066	cross_bank_hl_thunks	THUNK	59
```

## Appendix B — Twin-pair table (machine-readable)

For §4 fold candidates.

```
twin_a	twin_b	diff	loc_a	loc_b
BossAI_AddMoveIdToPlausibleMask:4948	BossAI_AddMoveIdToLikelyMask:4977	calls_SetX	30	30
BossAI_SetPlausibleMaskBit:5013	BossAI_SetLikelyMaskBit:5040	base_ptr	27	27
BossAI_TestPlausibleMaskBit:5294	BossAI_TestLikelyMaskBit:5325	base_ptr	31	30
BossAI_AddSpeciesLevelUpMovesToMask:5159	BossAI_AddSpeciesLevelUpMovesToLikelyMask:5215	calls_AddX	56	56
.EncourageScoreByA:2262	BossAI_EncourageScoreHL:5465	prepended_LoadScorePointer	13	14
.DiscourageScoreByA:2275	BossAI_DiscourageScoreHL:5479	prepended_LoadScorePointer	14	14
BossAI_DecPressureB:3315	BossAI_DecThreatSeverityB:6182	none_(byte_identical)	7	7
HasAnyKOMove_prelude:4104	PlayerHasPublicThreatVsEnemy_prelude:2692	none_(macro_target)	7	7
HasAnyKOMove_prelude:4104	PlayerHasRevealedPriorityThreat_prelude:2781	none_(macro_target)	7	7
```

(`HasAnyKOMove_prelude` is the cache-prologue lines 4104-4118 / 2692-2706 /
2781-2795; the body bodies — `…Uncached` — are not twins, only the
prologues are. This is what §4.3 lifts into a macro.)

## Appendix C — Relationship to the shelved rebuild plan

This plan is **independent of and prerequisite to** the shelved
BOSSAI-003 rebuild:

- The §1.1 layer seam table is a structural input to the rebuild's
  Step 1 (platform/policy audit). If the rebuild resumes, the audit
  refines this table; this plan does not commit to it.
- The §3 organization options leave platform exports stable. Either
  the rebuild (Layer A + Layer B) or the simpler unified architecture
  (one scoring function, eight components per
  `docs/boss_ai_design_conversation_2026-05-05.md`) plug in the same
  way: replace policy regions, keep platform regions.
- The §4 twin folds are zero-behavior-change cleanups that any
  rebuild benefits from (less duplicated surface, smaller diff in
  Step 3 heuristic synthesis).
- The §5 optimizations are bytes/cycles work that the rebuild does
  not block on.

If the rebuild stays shelved indefinitely, this plan still earns its
keep: a navigable boss.asm is the artifact the user actually asked for.
