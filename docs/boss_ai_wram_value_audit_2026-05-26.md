# Boss AI WRAM reserve — value audit, 2026-05-26

Per-field value-per-byte audit of the boss-AI reserve in WRAMX bank 1
(`wBossAITier` $d68e → `wBossAIStateEnd` $d6fe). 112 B used normal /
140 B used trace / 140 B reserved → 28 B free normal / 0 B free trace.

**Read-only deliverable.** The "Keep / cut" column is a recommendation,
not a change. Cole picks from the ranked menu below; no code or symbol
moves on my side.

Source of truth: [ram/wram.asm:2419-2498](../ram/wram.asm) (post P-A
worktree state — includes the new `wBossAILookaheadRunningBest`).

## Reading the value rating

| Rating | Meaning |
| --- | --- |
| **high** | Load-bearing for boss-AI behavior or a hot-path perf optimization; cutting causes a visible regression (worse AI play OR meaningful slowdown OR breaks an authored feature). |
| **medium** | Used and real, but the affected feature is narrow (one Haki gate, two trainers, a single mid-tier decision). Cuttable at a known design cost. |
| **low** | Cheap to recompute or only-marginally-useful cache; cut cost is cycles or doc-keeping, not behavior. |
| **dead** | No readers. None found in this audit. |
| **trace** | Only allocated when `DEF(BOSS_AI_TRACE)`; zero impact on shipping ROM. Cuts only buy headroom in the dev trace build. |

## Ranked cut list (highest value-per-byte savings first)

| # | Symbol(s) | Bytes | Build | Cost if cut |
| ---: | --- | ---: | --- | --- |
| 1 | **whole `BOSS_AI_TRACE` block** (`wBossAITraceTopMoves` … `wBossAITraceLookaheadBonusTop`) | **28** | trace-only | Trace ROM loses all per-decision introspection: `tools/trace/boss_ai_trace_capture.py`, `tools/trace/boss_ai_trace_state_probe.py`, `tools/trace/boss_ai_state_factory.py` all stop returning useful records; `audit/boss_ai_trace/*` captures go silent. Meta-decision: is the trace shape frozen? If yes, the 28 B are dead weight in the trace-build reserve. If we still want to add new trace fields, this block is exactly the headroom. |
| 2 | `wBossAITraceTopMoves` + `wBossAITraceTopScores` | **6** | trace-only | Trace consumers (`boss_ai_trace_capture.py:185-186`, `boss_ai_state_factory.py:459-460`) lose the "top-3 alternatives" summary. Derivable post-hoc from `wBossAITracePreModelScores` + `wBossAITraceChosenMove` if the capture script gets a rewrite. Easiest trace-side win. |
| 3 | `wBossAITracePlanId` + `wBossAITracePlanPhase` + `wBossAITracePlanConfidence` | **3** | trace-only | These snapshot pre-decision Plan state; the non-trace `wBossAIPlanId/Phase/Confidence` are still alive in WRAMX and the trace tool can read them directly — but it would need to sample *before* `BossAI_SelectMove` mutates them, not after. Restructuring cost in `boss_ai_trace_capture.py`. |
| 4 | `wBossAILookaheadDepthCache` | **1** | normal+trace | Cache for `GetProjectionDepth`. Recompute = `ld a, [wBossAITier]` + one `cp`. Comment at `boss_policy_move.asm:5737` notes the input is only `wBossAITier`; cache savings are negligible compared to the `LastMatchupType` cache (~30% of cycles). Cleanest "no real loss" normal-build cut. |
| 5 | `wBossAITierWeightRow` | **1** | normal+trace | **Taste call.** Two trainers (Bugsy/Whitney, see `data/trainers/ai_tiers.asm:63-64` `BossAITierRampMap`) currently use this to ramp their AI-tier weights partway toward MID without flipping their feature-gate tier. Cutting flattens both to the EARLY tier-default row. Whether the bespoke ramp is felt during play is your call. |
| 6 | `wBossAIShouldScoutMatchupValue` | **1** | normal+trace | The field's own comment at `boss_platform.asm:558-562` says: "Defensive: wBossAIShouldScoutMatchupValue is only READ on the hit path… so it doesn't strictly need a sentinel reset today. Resetting anyway keeps the cache-clear story uniform and protects against future refactors that might set prereq cache = 1 without first writing matchup value." Cuttable if you trust the current call structure and accept the refactor-rule. |
| 7 | `wBossAIScoutedMask` | **1** | normal+trace | 6-bit mask "have I successfully scouted this seen species" (boss_platform `BossAI_IsActiveSpeciesScouted` / `SetActiveSpeciesScouted`, ~3 sites). Single Haki feature: cutting removes the gate so scout-tagged behaviors fire every time (or never, depending on how the readers are rewired). |
| 8 | `wBossAIRepeatCount` + `wBossAILastChosenMove` | **2** | normal+trace | Anti-spam repetition counter (`BossAI_UpdateRepeatTracker` at boss_platform:1358). Cutting removes the per-move streak signal — AI won't notice when it's been mashing the same move N turns in a row. Whether this is load-bearing depends on how much late-tier scoring uses it to escape sub-optimal local minima. |
| 9 | `wBossAISwitchCooldown` + `wBossAILastSwitchedOut` | **2** | normal+trace | Switch-cooldown counter + "who was just switched out" pin. `BossAI_DecaySwitchCooldown` ticks down each turn; `BossAI_NeedsLoopPenalty` penalizes back-to-back switches; `LastSwitchedOut` prevents immediate-back. Cutting both flattens switch policy — AI may oscillate (switch out, switch back next turn). Reasonable cost if you'd rather see whether better candidate scoring already prevents oscillation. |
| 10 | `wBossAITraceLookaheadBonusTop` width drift | **1** | trace-only | `ram/wram.asm:2493` allocates 4 B (`sized to BOSS_AI_LOOKAHEAD_N (4)`); `tools/trace/boss_ai_trace_capture.py:33` reads only 3 B. The new audit `tools/audit/check_lookahead_trace_width.py` exists to flag this. Either tighten ASM to 3 B or document why 4 is the design target. Pure consistency fix — not really a "cut" so much as "reconcile." |

**Easy wins (no taste call):** items 4 + 6 = **2 B** added to normal-build free
(28 → 30). Items 2 + 3 = **9 B** added to trace-build free (0 → 9).

**Taste-call wins:** items 5 + 7 + 8 + 9 = **6 B more** of normal-build
free (30 → 36), at the cost of four distinct behavioral features.

**Wholesale trace cut (item 1):** **28 B** of trace-build free (0 → 28),
at the cost of all trace-ROM introspection.

## Per-field table

Symbols are listed in the order they appear in `ram/wram.asm:2421-2495`.
Reader/writer columns cite the first 2-3 representative sites; full
references are in `engine/battle/ai/*.asm` (mapped during this audit
session).

### Always-allocated fields (112 B normal / trace)

| Symbol | Bytes | Purpose (from comment / source) | Readers (path:line) | Writers (path:line) | Value | Keep / cut | Risk if cut |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `wBossAITier` | 1 | Boss-AI tier (0=off, EARLY/MID/LATE); gates every boss-AI feature. | engine/battle/ai/scoring.asm:1731, items.asm:23, boss_platform.asm:25, ~40 more | engine/battle/read_trainer_attributes.asm:72,95 | high | keep | Cutting = no boss AI anywhere. |
| `wBossAIMoveChoiceReady` | 1 | "Boss AI committed a specific move; skip vanilla decrement loop." | engine/battle/ai/move.asm:118 | boss_policy_move.asm:273,2788,2930, boss_policy_switch.asm:492 | high | keep | Cutting = vanilla score-decrement always wins; boss override layer dead. |
| `wBossAISwitchConfidence` | 1 | Switch-confidence accumulator across the switch-policy chain. | boss_policy_switch.asm:110,915,929,935,949,953,1395 | boss_policy_switch.asm:83,912,920,931,941,951,1364 | high | keep | Cutting = lose entire Haki/policy switch reasoning. |
| `wBossAILastSwitchedOut` | 1 | Party slot just switched out — prevents immediate-back switch. | boss_policy_switch.asm:611,617 | boss_policy_switch.asm:506 | medium | menu item 9 | AI may oscillate switch out → switch back next turn. |
| `wBossAISwitchCooldown` | 1 | N-turn cooldown after a switch; decremented every AI tick. | boss_policy_switch.asm:516,604 | boss_policy_switch.asm:508,520 | medium | menu item 9 | Removes "don't switch every turn" pressure. |
| `wBossAIPlayerSwitchCount` | 1 | Committed cross-turn count of player switches. Tier-gated read in policy_move:2109,3757. | boss_platform.asm:41, boss_policy_move.asm:2109,3757 | boss_platform.asm:46 | medium-high | keep | Player-switch-aware scoring goes blind to player switch tempo. |
| `wBossAIPendingPlayerSwitchCount` | 1 | Within-turn pending-switch buffer; flushed to PlayerSwitchCount at top of AI tick. | boss_platform.asm:35, observation_log.asm:102 | boss_platform.asm:40, boss_platform.asm:130 | medium-high | keep | Without the debounce, switch counter double-counts or races. |
| `wBossAITurnsElapsed` | 1 | AI-tick counter; `inc [hl]` each tick. Used by observation log + plan timing. | boss_platform.asm:29, observation_log.asm:44, boss_policy_switch.asm:754,880, boss_policy_move.asm:2105,2144,3753 | boss_platform.asm:30 (inc) | medium-high | keep | Plan progression and observation-log time-stamps both blind. |
| `wBossAIPlanId` | 1 | Plan-tier state machine ID (`PLAN_ENC`, `PLAN_KO`, …). | boss_policy_switch.asm:1594,1604,1619, boss_policy_move.asm:3968,3986,4089,4214,5180,5185,5553 | boss_policy_move.asm:4001,4022,4036,4046,4055,4081,4093,4116,4183,4197 | high | keep | Plan layer central to late-tier AI. |
| `wBossAIPlanPhase` | 1 | Per-plan progression byte (start/mid/end phases). | boss_platform.asm:31, boss_policy_move.asm:3972,3977,3981,4104,4305,4328 | boss_policy_move.asm:4010,4120,4188 | high | keep | Plan-phase guards collapse to "always early." |
| `wBossAIPlanConfidence` | 1 | Plan-commit confidence; gates plan vs reactive scoring. | boss_policy_move.asm:4095,4107 | boss_policy_move.asm:4008,4059,4083,4100,4111,4118,4197 | medium | keep | Plan layer would commit unconditionally or never — feel loss. |
| `wBossAIWinconMonIdx` | 1 | Plan's win-condition mon (which of OUR mons is the closer). | boss_policy_switch.asm:1601,1638,1665,2201,2233, boss_policy_move.asm:4129 | boss_policy_move.asm:4013,4020,4034,4044,4123,4191 | high | keep | Plan layer loses target focus. |
| `wBossAITargetMonIdx` | 1 | Switch-policy candidate target index. | boss_policy_switch.asm:994,1019,1029,1034 | boss_policy_switch.asm:991,1036, boss_policy_move.asm:4015,4061,4125,4194 | medium-high | keep | Switch-policy loses preferred-target carry across helpers. |
| `wBossAIScoutedMask` | 1 | Bit-per-seen-species "have I scouted this active species" mask. | boss_platform.asm:1328,1342 | boss_platform.asm:1344 | medium | menu item 7 | Haki scout-gate fires unconditionally or not at all. |
| `wBossAIRepeatCount` | 1 | Same-move streak count for active enemy. | boss_platform.asm:1364, boss_policy_move.asm:5295 | boss_platform.asm:1366,1373, boss_policy_switch.asm:510 | medium | menu item 8 | Late-tier scoring can't see "I've been mashing this move 5 turns." |
| `wBossAILastChosenMove` | 1 | Move ID last chosen (key for RepeatCount). | boss_platform.asm:1361, boss_policy_move.asm:5300 | boss_platform.asm:1371, boss_policy_switch.asm:511 | medium | menu item 8 | Pairs with RepeatCount — cut together. |
| `wBossAIPlausibleTypeMaskSpecies` | 1 | Cache key (active species) for Plausible/Likely masks. | boss_policy_move.asm:4769 | boss_policy_move.asm:4778, boss_platform.asm:290 | high | keep | Cache recomputes every call (10+ sites/turn); +significant cycles. |
| `wBossAIPlausibleTypeMaskLevel` | 1 | Cache key (active level). | boss_policy_move.asm:4772 | boss_policy_move.asm:4780, boss_platform.asm:291 | high | keep | Same as Species key. |
| `wBossAIPlausibleTypeMaskCache` | 4 | Plausible-type-bitmask for active player species (4 B = 18 types + spare). | boss_platform.asm:1090,1123,1182, boss_policy_move.asm:4792,4847 | as readers (`xor a / ldi`) + boss_platform:1107-1139 set-bit | high | keep | Cut means rebuilding the 18-type mask on every call site that touches it. |
| `wBossAISeenPlayerSpeciesCount` | 1 | Number of distinct player species seen this fight. | boss_platform.asm:148,171,196,425,1047,1063, boss_policy_move.asm:1593,2382,2446,3869 | boss_platform.asm:182 (inc) | high | keep | Foundation of the "public info only" no-cheat rule. |
| `wBossAISeenPlayerSpecies` | 6 | One species slot per seen player mon (PARTY_LENGTH=6). | boss_platform.asm:150,176,201,429,1049,1068, boss_policy_move.asm:1597,2388,2454,3877 | boss_platform.asm:178 (slot write) | high | keep | Without species table, no per-species memo (revealed-moves, alive-mask). |
| `wBossAIRevealedMovesBitmap` | 24 | Per-seen-species revealed-move-type bitmask (4 B × 6 species). | boss_platform.asm:364 (`GetActiveSpeciesRevealedMaskPointer`) → downstream readers in plausibility chain | indirect via PLATFORM helpers | high | keep | Entire revealed-move-aware scoring layer goes blind. |
| `wBossAILikelyTypeMaskCache` | 4 | Tighter "likely" type-mask (revealed moves + public STAB only). | boss_platform.asm:1096,1151,1214, boss_policy_move.asm:4858 | as readers (build path) | high | keep | Likelihood-weighted scoring blind; expensive recompute. |
| `wBossAISeenPlayerAliveMask` | 1 | Bit-per-seen-species "publicly not fainted." | boss_platform.asm:220,231, boss_policy_move.asm:2386,2450,3875 | boss_platform.asm:222,233 | high | keep | Public-alive bookkeeping disappears — no-cheat rule violated or AI can't track outs. |
| `wBossAIRevealedMovesBitmapSpare` | 3 | **Misleading name.** 3 bytes carved off the bitmap, repurposed: byte 0 = tainted-reveal flag bitmask, byte 1 = Haki ace-window flag bits (`BOSSAI_HAKI_ELIGIBLE_F / SPENT_F / ACE_SEEN_F`), byte 2 = pending Haki taunt index. | boss_platform.asm:56,66,332,345, boss_policy_switch.asm:232,307,334, haki_taunt_queue.asm:50 | boss_platform.asm:57,67, boss_policy_switch.asm:334, haki_taunt_queue.asm:37,42,55 | medium | keep (consider rename) | Three independent features lose state. Rename to `wBossAIPlatformFlagsSpare` would document intent without cost. |
| `wBossAIScorePtr` | 2 | Stashed score-byte pointer so deep helpers don't re-derive (push/pop friendly). | boss_platform.asm:1250-1252, boss_policy_move.asm:1898-1900, ko_band_oracle.asm:404-406 | boss_policy_move.asm:266-268 | medium-high | keep | Re-derive at every helper = code-volume cost, possibly bank pressure. |
| `wBossAISavedEnemyMoveStruct` | 7 | `wEnemyMoveStruct` push/pop slot (MOVE_LENGTH=7). `BossAI_SaveEnemyMoveStruct` + `RestoreEnemyMoveStruct`. | boss_platform.asm:1023 (restore) | boss_platform.asm:1010 (save) | high | keep | Scoring helpers that legitimately clobber `wEnemyMoveStruct` would corrupt the active move for everything downstream. |
| `wBossAITemp` | 1 | General scratch (most-used Temp slot). | boss_platform.asm:476,486,492, boss_policy_switch.asm:540,565,797,814, ~40 more sites | many | high | keep | Refactoring all callers to stack/registers is a separate workstream. |
| `wBossAITemp2` | 1 | General scratch. | boss_platform.asm:506, boss_policy_switch.asm:369,410,1048,1401, boss_policy_move.asm:2325 | many | medium-high | keep | Same as Temp. |
| `wBossAITemp3` | 1 | General scratch. | boss_platform.asm:508, boss_policy_switch.asm:427,439,1040,1055,1379-1393, boss_policy_move.asm:1675,1677 | many | medium-high | keep | Same as Temp. |
| `wBossAITemp4` | 1 | Scratch, mostly switch-policy 2x-resist/candidate-type holders. | boss_platform.asm:872, boss_policy_switch.asm:1023,1045,1801,1826,1837,2144,2148,2158 | many | medium | keep | Reducible if switch-policy helpers refactored to stack, but high churn. |
| `wBossAITemp5` | 1 | Scratch, used by `ko_band_oracle` matchup save and switch-policy seen-species loops. | ko_band_oracle.asm:212,246, boss_policy_switch.asm:992,1000,1015, boss_policy_move.asm:2387,2395,2430,2451,2460,2480,3818,3876,3884,3917,3919,4937,4941 | many | medium-high | keep | Heavy concurrent use in two unrelated subsystems — refactor risk is real. |
| `wBossAITierWeightRow` | 1 | Per-trainer weight-row override (default = `wBossAITier - 1`). Used by `BossAITierRampMap` (`data/trainers/ai_tiers.asm:59-65`). | boss_policy_move.asm:2618 | read_trainer_attributes.asm:73,98,126 | medium (taste) | menu item 5 | Bugsy/Whitney lose their bespoke sub-tier difficulty ramp. |
| `wBossAISpeciesUsedMoves` | 24 | Per-seen-species mirror of `wPlayerUsedMoves` (PARTY_LENGTH × NUM_MOVES = 6×4). Preserved across same-fight switches. | boss_policy_move.asm:2408 | boss_platform.asm:447 (`BossAI_GetActiveSpeciesUsedMovesPointer` write path) | high | keep | AI "forgets" revealed moves the moment the player switches — undermines entire revealed-move plausibility chain across switches. |
| `wBossAIHasKOMoveCache` | 1 | Per-tick: "does enemy have any KO move?" $ff=uncomp, 0=no, 1=yes. | boss_platform.asm:900 | boss_platform.asm:550 (reset), 911 (compute) | medium | keep | Per-tick recompute (scans 4 moves + scoring) on every check; perf hit. |
| `wBossAIPublicThreatCache` | 1 | Per-tick: "player has a public threat move vs enemy?" | boss_policy_move.asm:2995 | boss_platform.asm:551, boss_policy_move.asm:3006 | medium | keep | Per-tick recompute reads revealed moves + active typing. |
| `wBossAIRevealedPriorityCache` | 1 | Per-tick: "player has revealed priority move threat?" | boss_policy_move.asm:3070 | boss_platform.asm:552, boss_policy_move.asm:3081 | medium | keep | Per-tick recompute on every check site. |
| `wBossAIPrimaryThreatCache` | 1 | Per-tick: primary-threat type id (or $20=no threat). | boss_policy_move.asm:5837 | boss_platform.asm:553, boss_policy_move.asm:5848,5852 | medium | keep | Per-tick recompute scans player moveset + scoring per call. |
| `wBossAIPublicEnemyFasterCache` | 1 | Per-tick: "enemy publicly known to be faster?" | boss_policy_move.asm:3655 | boss_platform.asm:554, boss_policy_move.asm:3666 | medium | keep | Speed-compare per call. |
| `wBossAILookaheadDepthCache` | 1 | Per-tick projection depth (0 / mid-1 / late-1). | boss_policy_move.asm:5741 | boss_platform.asm:555, boss_policy_move.asm:5757 | low | menu item 4 | Recompute = 1 tier lookup + 1 cp. |
| `wBossAILookaheadRunningBest` | 1 | **P-A new (this week).** Dynamic min non-saturated score for the futility cutoff — tightens monotonically across the per-candidate loop. | boss_policy_move.asm:5387,5410 | boss_policy_move.asm:5364,5413 | high | keep | Loses the dynamic improvement; falls back to static `initial_best + CAP` cutoff. Whole P-A point is the dynamic tightening. |
| `wBossAILastMatchupType` | 1 | **Single hottest cache.** Per-tick key for `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` — "~30% of total cycles, called ~22 times per turn" per source comment. | boss_platform.asm:619 | boss_platform.asm:556, boss_platform.asm:627 | high | keep | Per the comment, this is the single biggest perf cache in the AI. Cutting = noticeable slowdown. |
| `wBossAILastMatchupResult` | 1 | Paired with LastMatchupType — restored to `wTypeMatchup` on cache hit. | boss_platform.asm:622 | boss_platform.asm:631 | high | keep | Pairs with LastMatchupType — useless if either is cut. |
| `wBossAIShouldScoutPrereqCache` | 1 | Per-tick: ShouldScout prereqs satisfied? (0=no, 1=yes, $ff=uncomp) | boss_policy_move.asm:6264 | boss_platform.asm:557, boss_policy_move.asm:6299,6317 | medium | keep | Per-tick recompute of the scout-prereq chain. |
| `wBossAIShouldScoutThresholdCache` | 1 | Cached `GetScoutRollThreshold` result (valid iff prereq=1). | boss_policy_move.asm:6273,6300 | boss_policy_move.asm:6291 | medium | keep (or fold into prereq cache) | Could be folded with prereq cache as a single byte if range allows. |
| `wBossAIShouldScoutMatchupValue` | 1 | `wTypeMatchup` snapshot from prereq chain; restored on cache hit so the side-effect write to `wTypeMatchup` is preserved for downstream readers. | boss_policy_move.asm:6271 | boss_platform.asm:564, boss_policy_move.asm:6297 | medium-high | menu item 6 (defensive, per comment) | If current code structure changes (prereq cache = 1 without writing matchup value), downstream readers see stale `wTypeMatchup`. Today the path is safe per source comment. |

### Trace-only fields (+28 B in `BOSS_AI_TRACE` builds)

| Symbol | Bytes | Purpose | Readers (path:line) | Writers (path:line) | Value | Keep / cut | Risk if cut |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `wBossAITraceTopMoves` | 3 | Top-3 candidate moves snapshot. | tools/trace/boss_ai_trace_capture.py:185, boss_ai_state_factory.py:459, boss_ai_trace_state_probe.py:372 | boss_trace_topmoves.asm:15,30,56,60,64,75,79,90 | trace / medium | menu item 2 | "Top-3 alternatives" summary disappears from trace records. Derivable from PreModelScores + chosen move at capture time. |
| `wBossAITraceTopScores` | 3 | Top-3 candidate scores snapshot. | tools/trace/boss_ai_trace_capture.py:186, boss_ai_state_factory.py:460, boss_ai_trace_state_probe.py:376 | boss_trace_topmoves.asm:20,54,58,62,73,77,88 | trace / medium | menu item 2 | Pairs with TopMoves. |
| `wBossAITracePreModelScores` | 4 | Pre-move-model scores per move (`NUM_MOVES=4`). | boss_ai_trace_capture.py:191, boss_ai_trace_state_probe.py:381 | boss_policy_move.asm:216,235 | trace / medium | keep | Cutting kills the "model delta" line of investigation; you'd only see post-model. |
| `wBossAITracePostModelScores` | 4 | Post-move-model scores per move. | boss_ai_trace_capture.py:192, boss_ai_trace_state_probe.py:387 | boss_policy_move.asm:254 | trace / medium | keep | Pairs with PreModel — losing one halves the trace signal. |
| `wBossAITraceChosenMove` | 1 | Committed chosen move (gate for "did boss AI commit"). | boss_ai_trace_capture.py:187,255,263, boss_ai_state_factory.py:39,657, boss_ai_state_replay.py:58,72 | boss_policy_switch.asm:312, boss_policy_move.asm:2936 | trace / high | keep | Central decision byte; trace stream becomes "did something happen?" with no signal of what. |
| `wBossAITraceSwitchConfidence` | 1 | Switch-confidence snapshot at decision time. | boss_ai_trace_capture.py:213, boss_ai_shared_switch_loop_fixture.py:129 | boss_policy_switch.asm:85 | trace / medium | keep | Switch-decision audits lose confidence signal. |
| `wBossAITracePlanId` | 1 | Plan ID snapshot pre-mutation. | boss_ai_trace_capture.py:214, boss_ai_state_factory.py:40 | boss_policy_move.asm:3987 | trace / low | menu item 3 | Snapshot pre-decision Plan ID; the non-trace `wBossAIPlanId` is the post-decision value. Restructuring trace capture to read non-trace pre-decision is feasible. |
| `wBossAITracePlanPhase` | 1 | Plan phase snapshot. | boss_ai_trace_capture.py:215 | boss_policy_move.asm:3990 | trace / low | menu item 3 | Same as PlanId. |
| `wBossAITracePlanConfidence` | 1 | Plan confidence snapshot. | boss_ai_trace_capture.py:216 | boss_policy_move.asm:3992 | trace / low | menu item 3 | Same as PlanId. |
| `wBossAITracePlausibleMask` | 4 | Plausible-mask 4-byte snapshot. | boss_ai_trace_capture.py:217, boss_ai_trace_state_probe.py:404 | boss_policy_move.asm:4793 | trace / medium | keep | Plausibility-side audits lose the snapshot. |
| `wBossAITraceRiskFlags` | 1 | Per-decision risk/audit flag bits. | boss_ai_trace_capture.py:188,258, boss_ai_trace_state_probe.py:408 | boss_policy_move.asm:2796,5331,6308-6361, boss_policy_switch.asm:313,338 | trace / high | keep | Wide set of writes; load-bearing for many trace-side audit gates. |
| `wBossAITraceLookaheadBonusTop` | 4 | Per-candidate lookahead bonus delta (1 B × `BOSS_AI_LOOKAHEAD_N=4`). | boss_ai_trace_capture.py:219 (reads 3), `tools/audit/check_lookahead_trace_width.py` | boss_policy_move.asm:5332,5425 | trace / high | menu item 10 (reconcile to 3 or 4) | Width drift — Python reads 3, ASM allocates 4. Tighten one to match the other. |

## Honest recoverable-byte totals

Targets are reserve free-bytes (currently 28 normal / 0 trace).

| Scenario | Bytes recovered | Resulting normal free | Resulting trace free |
| --- | ---: | ---: | ---: |
| Cut only "dead" entries | 0 | 28 | 0 |
| Cut only no-taste-call items (4, 6) | 2 normal | 30 | 2 |
| Cut all normal-build menu items (4–9, excl. trace) | 8 normal | 36 | 8 |
| Cut item 1 (wholesale trace block) | 28 trace | 28 | 28 |
| Cut items 2 + 3 + 4 + 10 (trace fine-grained + DepthCache + width fix) | 1 normal + 11 trace | 29 | 11 |

Notes:

- **Trace cuts don't help the shipping ROM.** The 28 B trace block lives
  under `IF DEF(BOSS_AI_TRACE)`. Normal-build reserve is already 28 B
  free; trace cuts only buy headroom for *more* trace-only state later.
- **Dead-only cuts recover 0 B.** Every symbol in the reserve has
  readers in current code — no symbol from a fully removed feature is
  squatting in this region.
- **All non-trace cuts >1 B require feature taste calls.** The largest
  single normal-build savings would come from cutting
  RepeatCount/LastChosenMove (2 B, one feature) or
  SwitchCooldown/LastSwitchedOut (2 B, one feature) — both are
  intentional softening rules that may or may not be load-bearing for
  fight feel.

## Open questions for taste call

1. **Trace block, all-or-nothing or fine-grained?** Is the trace ROM's
   data shape now considered frozen for the foreseeable future (keep
   the 28 B as the trace-side reserve = trace block stays), or do you
   want to add more trace-only state in the next quarter (drop some
   current trace fields to make room)? Or do you want the trace ROM to
   converge toward "doesn't allocate the trace block, captures trace
   data via PyBoy probe-style reads of non-trace WRAM"? That last
   option would let you delete the whole 28 B and reclaim trace
   workflow at the cost of a one-time capture-tool rewrite.

2. **Bugsy/Whitney ramp (TierWeightRow):** Two trainers currently use
   bespoke rows 3 and 4 in `BossAITierWeights` to feel "~25% / ~50%
   toward MID" without taking the full MID tier (which would also turn
   on MID-tier feature gates). Is that ramp something you can feel in
   play, or is it noise? Cutting reclaims 1 B + 5 lines of code in
   `read_trainer_attributes.asm`.

3. **Anti-spam and anti-oscillation softeners (items 8 + 9):** Four
   bytes total (`RepeatCount` + `LastChosenMove` + `SwitchCooldown` +
   `LastSwitchedOut`) implement "don't mash the same move forever" and
   "don't switch every turn." Boss AI's better candidate scoring may
   already prevent the worst of these without the softeners — or the
   softeners may be load-bearing. Worth a play-test if you'd consider
   cutting either pair.

4. **ScoutedMask (Haki gate):** Is the "have I successfully scouted
   this active species" Haki feature live and felt in play, or is it
   instrumentation for a tier that hasn't shipped yet? 1 B reclaim if
   the answer is "stub."

5. **Rename without cut?** `wBossAIRevealedMovesBitmapSpare` (3 B) is
   actually three repurposed bytes (tainted-reveal flag, Haki ace-window
   flag bits, pending Haki taunt index). Cutting any byte = losing one
   of three distinct features. Renaming to e.g.
   `wBossAIPlatformFlagsSpare` would document intent at zero cost —
   worth a separate small PR if you agree.
