# Battle AI strategic optimization audit — 2026-09-06

**Verdict: the AI is not strategically optimized, and there is no basis for calling it perfect.** It has broad tactical coverage, public battle memory, difficulty tiers, and explicit resource limits. Its main weakness is that many independently authored rules judge the same position in different ways. More rules or a larger nominal planning horizon would not reliably make it stronger.

The highest-value direction is a shared tactical evaluation for every feasible action, informed by public observations, with deeper reasoning reserved for consequential uncertainty. Keep the public-information foundation and constrained implementation. Establish that a replacement improves actual decisions before expanding it.

This is a findings-only audit. No game source was changed. The user clarified that optimization means careful, big-picture decision quality; runtime correctness is supporting evidence, not the definition of success. No speedup, win-rate gain, or numerical intelligence rating is claimed.

## What the current decision system actually does

1. Selects some bosses' opening Pokémon through a blind weighted choice among the first three living options.
2. Records seen species, revealed moves, switches, and coarse recent observations.
3. Builds plausible and likely attacking-type masks from visible typing, revealed moves, and public learnability.
4. Scores moves using legality checks, damage pressure, numerous tactical adjustments, plan bias, and repetition/scouting rules. Lower scores are preferred.
5. Applies a bounded extra heuristic evaluation to some move candidates. Its “four/five-turn horizon” is a multiplier for current-state bonuses and penalties, **not a simulated sequence of four/five turns**.
6. Usually chooses the first strict minimum. It may mix in a damaging coverage hedge against a seen, living bench species.
7. Separately considers switching through candidate-risk ranking, vetoes, confidence thresholds, and a probability roll. Faint replacements use another ranking system.
8. Routes eligible ace actions through the authored, once-per-battle Haki exception. Trainers use no bag items.

Evidence: `engine/battle/ai/boss_policy_move.asm` labels `MaybePickAdaptiveEnemyLead`, `BossAI_ApplyMoveModel`, `BossAI_SelectMove`, `BossAI_ApplyMultiTurnProjection`; `boss_policy_switch.asm` labels `BossAI_TrySwitch`, `BossAI_PickFaintReplacement`; `items.asm` label `DontSwitch`.

## Strategic findings, in priority order

### 1. Attacking, switching, and replacing a fainted Pokémon need a common tactical basis

**Confirmed architecture limitation; likely highest-value improvement.** Move scoring uses additive preference points. Switching minimizes a type-risk score and compares a separate confidence value with a threshold. Faint replacement uses categorical filters such as raw move power at least 60, super-effective coverage, base offense at least 60, and a quarter-HP gate. These systems do not answer the same question: which action leaves the best position after the opponent responds?

Switching also finalizes a candidate before applying several rejection rules. If that candidate is rejected for low HP or another veto, the routine stays rather than evaluating the next viable candidate. The four-candidate scan cap can omit a fifth living bench option unless it was the initially nominated candidate. These are sources of roster-order sensitivity, not evidence-based pruning.

**Improve:** generate feasible moves and switches first; compare survival, damage/status progress, entry hazards, initiative, and the value of preserving each team member through the same tactical model. Keep switching-specific costs, but express them in that shared evaluation. Filter unsafe candidates before ranking or retain a runner-up. Cheaply screen all five possible bench members before spending expensive evaluation on a shortlist. Handle forced loss and immediate victory explicitly: an urgent Perish escape should not depend on an ordinary type-flee gate, but a battle-winning action should still take precedence over unnecessary escape.

This does not require a complete battle simulator or an immediate rewrite. First use common legal-action and damage/survival helpers inside the existing entrypoints, then compare decisions against the current implementation.

Evidence: `boss_policy_switch.asm:17`, `BossAI_RefineSwitchCandidateForPlausibleRisk`, `BossAI_FaintRepl_HPGateAndPct`, `BossAI_FaintRepl_CandidateHasRealCoverage`; `constants/battle_constants.asm:96`.

### 2. Improve the information used to judge tactics before increasing search depth

**Confirmed model limitation.** Offensive pressure compresses stat-scaled move power, typing, STAB, items, and passives into a small pressure bucket. The KO oracle adds a coverage-confirmation bonus; it does not produce a damage distribution or a KO probability. Damage dominance uses saturated eight-bit ranks. It approximates every resistance as one half, and applies type/STAB approximations to fixed-damage equivalents. Accuracy is mainly a threshold penalty, not the probability-weighted value of damage and secondary effects.

The ordinary public speed predicate compares species base Speed and the enemy's Choice Scarf. It does not use public Speed stages, paralysis, relative levels, or observed same-priority move order. A fresh ROM helper probe returned “enemy faster” both for normal Gengar and for Gengar at -6 Speed with paralysis against the same Rattata. The separate exact-speed setup exception does not correct other consumers.

This can make nominal KO pressure, safe setup, revenge risk, and defensive timing disagree about the same position. Adding deeper reasoning around those estimates amplifies their error.

**Improve:** use the boss's known stats, moves, PP, and items exactly; use bounded opponent stats and uncertainty from public species/level information. Include observed stages/status and this hack's actual mechanics. Produce compact damage/survival intervals or a few meaningful outcome bands, with distinct fixed-damage, immunity, priority, and accuracy handling. Preserve observed same-priority speed evidence only while relevant conditions remain unchanged. Use conservative estimates for catastrophic loss and expected value for ordinary trades. Never solve uncertainty by reading private opponent stats or items.

Evidence: `boss_policy_move.asm:3278`, `:3312`, `:3449`, `:3980`, `:4035`; `ko_band_oracle.asm:16`, `.ScalePowerByMatchup`, `.ApplySTABToRank`. ROM evidence: `probe_results.json`, `public_speed`.

### 3. Replace duplicated bonus stacking with explicit tradeoffs; use genuine shallow replies selectively

**Confirmed architecture limitation.** Setup is considered in the initial model, setup discipline, plan bias, the lookahead body, and multi-turn projection. Threat and KO predicates recur across those layers. The final lookahead delta is capped at four points, so different combinations of evidence can collapse to the same adjustment. A larger horizon constant mostly strengthens overlapping judgments of the present state.

Some judgments also refer to the whole moveset when evaluating one candidate. For example, lookahead skips a reply-risk branch when *any* KO move exists, even if the candidate being considered is a utility move. That is not the same as establishing that the chosen action prevents retaliation.

**Improve:** give each important fact one clear contribution: immediate outcome, reply risk, future team value, or uncertainty. Inspect contribution traces and remove a duplicate only when an ablation shows that decisions improve or remain equivalent. On ambiguous, high-impact turns, evaluate a small set of public opponent hypotheses—attack, defensive action, plausible switch—using a projected successor state for each candidate. Branches need their own HP, status, stages, field effects, and cache validity. Quiet obvious turns should use the cheap evaluator.

Search breadth and depth must be earned by decision improvement per emulated cycle. A shallow model with dependable survival estimates is a better first experiment than a nominally deeper model with unchanged heuristic inputs. The existing roadmap already recognizes that branch-local state and legality must precede reply search.

Evidence: `boss_policy_move.asm:239` onward, `:5541`, `:5849`, `:5963`, `:6004`; `constants/battle_constants.asm:94`, `:107`; `docs/boss_ai_future_roadmap_2026-05-26.md`, deferred branch-context work.

### 4. Opponent adaptation should learn from outcomes and opportunities

**Confirmed limitation.** The observation log's “damage band” is calculated from a revealed move's type severity against the current enemy. It does not measure HP lost. Its calibration therefore reuses a model estimate rather than checking that estimate against reality. Move order is stored without separating priority from Speed. The switch tendency table assigns positive switch-prediction points to attacks, status, setup, and recovery as well as switches; there is no corresponding opportunity denominator.

The threat masks are useful conservative priors, but a set of learnable types is not a probability distribution over plausible four-move sets. Species-level role packages can contain several mutually competing roles. After four ordinary moves are revealed, speculative learnability is suppressed, but STAB types have already been inserted. That can retain an attacking type the known set does not contain. Memory keyed by species also merges duplicate Pokémon; temporary/copied-move guards reduce some inference errors but do not establish individual identity.

**Improve:** record actual observed damage with its context, distinguish direct damage from residual/healing effects, and invalidate calibration after relevant changes. Estimate switching conditional on comparable opportunities, with smoothing and decay. Maintain a few coherent public hypotheses rather than treating all learnable attacks as simultaneous threats. Let revealing four stable moves narrow those hypotheses. Preserve ambiguity for duplicates and transformations instead of asserting hidden identity.

Scouting should be valued by whether information could change a future decision, plus the cost of obtaining it. The current scorer makes repeated independent scout rolls and marks a species scouted when a scout move is selected, without checking that useful information was obtained. Compute strategic scouting value once for the turn and apply variety at final action selection.

Evidence: `observation_log.asm`, especially `BossAI_CurrentObservationDamageBand`, `BossAI_ConsultKOBandCalibration`; `data/boss_ai/tendency_counter_weights.asm`; `boss_policy_move.asm:4110`, `:5122`, `:6623`, `:6692`; `boss_platform.asm`, `BossAI_GetActiveSpeciesSeenIndex`; `data/boss_ai/role_package_classifier.asm`.

### 5. Plans and personality should adapt to the board, not override it

**Confirmed policy tradeoff, not proof that every such decision is bad.** Setup affordability is tied to time on the field: turn zero passes, turn one requires full HP, and turn two onward fails. That can discourage a valuable setup opportunity created later by sleep, a forced recovery, or a switch. Conversely, generic plan/projection bonuses can still reward setup after the affordability check declines it. Plan roles are broad, and the two authored coach templates mostly track phases and stop conditions rather than alternate routes to winning.

The selector's hedge requires a seen living bench wall, which is a useful public-information restriction. But the presence of that wall does not establish that switching is likely this turn or that losing immediate damage is affordable. Exact ties normally favor the earlier move slot. Both behaviors make storage order and fixed probability bands stand in for tactical uncertainty.

**Improve:** evaluate whether another setup turn changes the race or survival outcome, accounting for enemy replies, rather than using turns present as the primary affordability rule. Treat plans as preferences with explicit invalidation conditions and maintain the value of particular teammates against revealed threats. Make hedge probability depend on plausible opponent actions and the cost of being wrong. Apply leader personality and tier variety among defensible actions; retain intentional early-game simplicity and authored roster identity.

Evidence: `boss_policy_move.asm:4328`, `:4905`, `:5061`, `:5541`, `:2756`, `:2934`; `data/boss_ai/coach_plan_templates.asm`; `data/trainers/ai_tiers.asm`.

## Concrete interactions that must be resolved before weight tuning

These matter because they corrupt the values being optimized. They are not a substitute for the strategic recommendations above.

| Finding | Evidence and practical implication | Recommended treatment |
|---|---|---|
| **Switch-risk weights are overwritten by mask helpers.** | `boss_policy_switch.asm`, `.mask_risk` / `.likely_mask_loop` / `.possible_mask_loop`, keeps weight in `d`; `boss_platform.asm` bit-test helpers replace it with a bit mask. Fresh ROM probes of a Pidgeot candidate against one likely 2x type yield ICE=2, ELECTRIC=99, ROCK=32 at every tier, instead of intended tier weights 4/7/10. | Preserve the weight and use non-wrapping accumulation. Add type-renaming/weight-progression tests before tuning switch confidence. |
| **Lookahead accumulators are clobbered.** | `boss_policy_move.asm`, `BossAI_EvaluateActionLookahead` initializes `b/c` as upside/downside, then calls the pressure scorer and player HP helpers without preserving them. `scoring.asm:2665` and `:2742` onward show those HP helpers overwrite `bc`; the thunks preserve `hl`, not `bc`. | Repair the accumulator contract across all affected calls. Synthetic helper outputs are recorded, but no specific ideal gameplay delta is asserted. |
| **Unavailable attacks influence strategic alternatives.** | `BossAI_HasAnyKOMove`, damage-dominance scanning, and `.HasStrongMatchupDamagingMove` do not consistently filter PP/Disable/Choice legality. Fresh ROM probe: the KO predicate stays true after its only damaging move reaches zero PP and receives score 80. | Share an action-availability predicate across all scans. Distinguish “in moveset” from “can be chosen now.” |
| **A later bonus reopens a publicly failing move.** | The status-failure path sets score 80 but continues. `BossAI_ApplyPlanMoveBias` and `BossAI_EncourageScoreHL` can lower it. Fresh ROM probe: Toxic against an already poisoned target becomes 78 under STATUS_CHOKE and is selected. This isolates sentinel reopening; it is not claimed as a realistic four-move battle preference example. | Separate availability/failure flags from preference scores or make blocking terminal and irreversible throughout scoring. |
| **Perish urgency does not reach a viable escape.** | `BossAI_TrySwitch` initially recognizes urgency but `BossAI_CheckAbleToSwitchSafe` still requires ordinary threat/low-HP conditions. Fresh ROM probe: healthy Pidgeot, neutral opponent, count 1, living bench; urgency=true, switch parameter=0, no switch. | Evaluate legal escape as an emergency action, with explicit terminal-win, trapping, and entry-survival considerations. |
| **Futility bound is not a valid incumbent bound for signed deltas.** | Running best starts at the raw minimum and only decreases even if that candidate is penalized. With CAP=4, raw scores `[10,15]` and allowed deltas `[+4,-4]`, pruning yields `[14,15]` while full evaluation gives `[14,11]`. This is an algebraic counterexample, not a reproduced natural battle. It also leaves skipped hedge scores on a different evaluation basis. | Use an evaluated incumbent and valid bounds; preserve scoring needed by the stochastic hedge. Compare against an exhaustive four-move reference on identical states. |
| **Known dead species remain in Choice-lock regret.** | `.SeenSpeciesChoiceLockRisk` scans seen species without the alive mask, unlike the hedge scan. It can penalize a lock because of a counter the player has already lost. | Use consistent alive/public-memory filters. |
| **Baseline quarter-HP fallback has incorrect arithmetic.** | `switch.asm:604` onward says it computes HP times four, but `:626` and `:628` shift the low byte right. The boss faint-replacement path can fall back into baseline switching. Source finding, not a fresh gameplay replay. | Correct and test the boundary helper; keep fallback candidates consistent with the common feasible-action model. |

Additional inspection target: `BossAI_CoachExpectedMoveResistedByPlayer` reads global `wBaseType1` instead of explicitly loading the current defender's types. Its callers' base-data context needs a dedicated trace. This remains unresolved; no gameplay failure or approved retention is claimed for it.

The suspicion that Protect should work behind Substitute was **rejected**: this hack explicitly fails Protect with an existing Substitute in `engine/battle/move_effects/protect.asm`. Auditing against standard Pokémon assumptions would have produced a false finding.

## What to keep

These are specific retention decisions about architecture and authored policy, not a blanket approval of all unchanged code.

| ID | Retain | Reason and qualification |
|---|---|---|
| R1 | Public-information boundary and isolated Haki contract | Fair inference is a design requirement. Haki is explicitly an exception; the whole AI must not be described as universally non-cheating. Preserve its gates and tell while assessing tactical quality separately. |
| R2 | Compact bitsets, generated public tables, and caching of stable inputs | Appropriate for Game Boy limits. Improve their semantics and invalidation instead of discarding the representation. Current switch-weight and identity issues are excluded from approval. |
| R3 | Bounded computation and cheap-first candidate screening | Resource limits are useful. Current pruning correctness and roster-order exclusions are not endorsed. Extra depth needs measurable benefit. |
| R4 | Readable policy tables, plans, tiers, and blind opener variety | These make difficulty and identity authorable. Keep them subordinate to feasible actions and tactical evaluation. No claim that present weights/templates are optimal. |
| R5 | Cross-bank access thunks and separation of trace output from policy | These are necessary implementation boundaries and useful diagnostics. The lookahead caller's register-preservation defect remains a change recommendation. |
| R6 | No trainer bag items; ordinary-trainer baseline as a separate difficulty policy | Both are intentional scope choices. No reason to add item search or give every ordinary trainer late-boss reasoning. Shared safety helpers and known fallback defects still require work. |

## How to prove an optimization is worthwhile

1. **Stabilize the decision inputs.** Address the confirmed weighting, accumulator, legality, sentinel, and emergency-path errors. Preserve each as a small ROM regression, including both sides of its branch. Refresh matching ROM/symbol/capture evidence.
2. **Introduce shared tactical estimates incrementally.** Apply availability, damage/survival, and public speed estimates to move choice, voluntary switches, and replacement choice. Keep an old-policy comparison so each change's consequences remain reviewable.
3. **Evaluate strategic quality on complete turns and continuations.** Use actual boss rosters across early/mid/late tiers, hidden and fully revealed sets, PP exhaustion, priority, hazards, forced losses, setup windows, recovery loops, and sacrifice/endgame positions. Compare against simple reference policies and an offline, deeper public-information evaluator on a bounded corpus. Offline reference analysis may use more compute, but must not gain hidden opponent information.
4. **Measure decision regret and avoidable losses, not just label agreement.** Record dominated-action rate, missed forced wins, preventable KOs, switch loops, wasted setup/recovery, and outcomes across varied player policies and matched random seeds. Report uncertainty and worst-case regressions. Win rate alone can reward predictability or overfit roster matchups.
5. **Run ablations.** Disable one heuristic group at a time in a controlled experiment. Keep the group only if its benefit survives unseen scenarios, or if it serves an explicit personality/difficulty goal. Test move/bench permutations, dead-threat removal, exhausted moves, and irrelevant hidden-state changes. An optimization should not manufacture new private information.
6. **Spend cycles where decisions are unstable.** Add shallow reply branches only after the shared estimates work. Measure actual emulated cycles, bank usage, and branch-state storage together with quality. Precompute/reuse per-turn action facts where valid; avoid blindly increasing search. The current trace reserve is full, so additional state needs a deliberate layout decision.

The first milestone should be **coherent action comparison with dependable inputs**, not “more intelligence features.” Only a measured comparison can establish whether consolidation reduces cost or improves play.

## Coverage and verification record

This covers the full decision architecture and its functional units, with targeted source/ROM examination of consequential interactions. It is not exhaustive verification of every move effect, every party composition, or all reachable battle states.

| Unit | Source and inspection coverage | Disposition |
|---|---|---|
| Entrypoints, tiers, opener, baseline dispatch | `move.asm`, `items.asm`, `boss_policy_move.asm` opener; `read_trainer_attributes.asm`; tier maps; relevant `core.asm` callsites | R1/R4/R6 retained; shared feasibility changes recommended |
| Move tactical policy and score writes | `boss_policy_move.asm` scoring, effect matrix, setup/status/recovery/hazard/trade rules; platform score helpers | Findings 2/3/5 and concrete interaction table; no blanket weight approval |
| Selector, hedge, scouting, projection | All corresponding policy labels and cap constants | Findings 3/4/5; pruning and accumulators require changes |
| Public memory, masks, threat/speed estimates | `boss_platform.asm`, mask/threat helpers, generated role classifier, `observation_log.asm` and weights | R2 retained conditionally; model and identity limitations identified |
| Plan/template lifecycle and team roles | Plan/role helpers and both coach-template rows | R4; tactical adaptation recommended; base-data context unresolved |
| Voluntary switches, sacrifices, replacements | Complete `boss_policy_switch.asm`; baseline `switch.asm` | Finding 1; confirmed defects identified; no optimized-policy approval |
| Haki and action ordering | Switch-policy Oracle helpers, eligibility, queue/flush and core dispatch, taunt queue | R1; existing contract retained, no claim of tactically optimal Haki |
| Damage model, item/passive interactions | `ko_band_oracle.asm`, pressure/dominance helpers, relevant move-effect implementation | Finding 2; not an independent full combat-engine audit |
| Banking, trace, budgets | `boss_thunks.asm`, `boss_trace_topmoves.asm`, platform tracing; budget/gating/invariant checks | R3/R5, with named register and evidence gaps |
| Ordinary-trainer scoring and redundancy | Scoring layer dispatch, shared HP/speed helpers, redundant-effect table and baseline switch; selected tactical handlers | R6 at architecture level; exhaustive per-effect gameplay correctness remains outside demonstrated coverage |
| Verification system | ROM fixture harness/cases, static audits, preference regression and its Python scorer distinction; archived capture ledger | Useful infrastructure retained; current checks do not establish optimal play |

Fresh results:

- All **18 existing ROM decision-path fixtures passed**. Covered paths: Haki after-player/boss-first/eligibility/gates, ordinary boss move choice, and Destiny Bond scoring. This is the result of that specific suite, not a count of every ROM test in the repository.
- **45/45 strict preference pairs agreed**, with nine non-strict labels skipped. This compares labels with the Python fixture scorer, not actual ROM decisions or complete battles.
- Policy contract, no-cheat audit, tier gating, memory budget, trace invariants, index lines, and futility source-pattern audit passed. Several assert source structure; their passing does not invalidate the behavioral/algebraic findings above.
- Live-capture ledger **skipped**: local trace ROM fingerprint differs from the manifest-pinned capture basis. Archived captures cannot certify the current build.
- Memory audit reports normal Boss AI reserve **112/140 bytes** and trace reserve **140/140 bytes**. These are existing map/report results; no fresh build was performed.
- `probe.py` records 21 fresh ROM helper scenarios across the documented targeted probes, plus one algebraic pruning example. Each scenario uses a fresh emulator. They establish local routine behavior under seeded conditions, not natural battle reachability or a strength benchmark.

Reviewed baseline: git HEAD `4d322950b49e89fe0f1fb086fcd92ed862c444fe`, with pre-existing unrelated dirty work. Game AI source was clean and unchanged during this audit. The local ROM was not rebuilt; its evidence is pinned in `probe_results.json`:

- `pokegold.gbc` SHA256 `7733800325651929bc24d47d1a6e2dcded3075aaadd45fa3673ada798f983fb7`
- `pokegold.sym` SHA256 `0f27b7b440d50699842f58d0fe2cf524c8eb00438b8ae640594092fe1f865267`

See `source_manifest.json` for the inspected source basis. Independent Astra reviewer approval of the final findings and retention decisions is recorded separately in `review.md` when received. Approval concerns this audit's judgments, not certification that the existing AI or the proposed future design is optimal.
