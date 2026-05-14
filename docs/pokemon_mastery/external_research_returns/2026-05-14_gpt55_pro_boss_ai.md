# GPT-5.5 Pro Boss AI Research Return

_Formatting note: this file preserves the GPT-5.5 Pro response content, with the original 15-column ranked proposal table normalized into per-proposal sections._

Only Prompt 2 was run.

I treated this as a cheap, no-cheat boss-AI pressure test for Gym Leader Lab. The prompt asks for high-value, low-coding-time intelligence wins, explicitly under public-information-only constraints, with 15 proposals, 5 rejected anti-proposals, first implementation picks, and local-source questions. I used the context packet’s rules that boss AI should win by legal inference and public board reading, not hidden player-team reads, and that there is no public Team Preview. I also treated Haki/oracle as quarantined and non-generalizable, and assumed the listed existing boss-AI capabilities are already present.

## Executive summary: 3 best proposals

The three proposals that most clearly clear the “default no” bar are:

1. **Four-Move Saturation Hard Gate**
   Once a player’s active species has publicly revealed all four moves, the AI should stop pricing any unrevealed coverage, recovery, priority, status, or utility from that individual set. This is cheap because revealed-move tracking already exists, and it is very visible because it stops the boss from acting paranoid after the set is fully known.

2. **Opportunity-Weighted Non-Reveal Downgrade**
   Do not treat “has not shown the move” as proof of absence, but do downgrade a likely/possible hidden threat after the player had good public opportunities to use it and repeatedly did not. This is a strong calibration win: bosses look less like they are either cheating or stupidly over-respecting every theoretical TM forever.

3. **Robust Progress Over Possible-Only Counterplay**
   When a possible-only hidden threat would cause the AI to make a narrow counterplay, prefer robust progress if it is close in score: damage, status, hazard pressure, phazing, setup denial, or preserving tempo. This directly targets no-Team-Preview uncertainty and keeps bosses from becoming brittle scripts.

These fit the project’s desired proposal shapes: score bias, small gate, small counter, bitmask reuse, compact table, or trace-only audit. They avoid the bad shapes: broad game-tree search, hidden team reads, exact hidden move/item/PP/stat reads, current-turn input reads, modern Team Preview imports, and untraceable “smartness.”

## Ranked Proposals

_Formatting note: the original wide table has been normalized into one section per proposal. Field text is preserved._

### 1. Four-Move Saturation Hard Gate

- **Intelligence benefit:** Converts revealed-move memory into a clean impossibility rule once four moves are known.
- **Public info used:** Revealed moves by active species; current active species identity; Gen 2 four-move limit.
- **Forbidden info not used:** Hidden moves, hidden party, hidden items, hidden PP, current input.
- **Implementation shape:** Gate / bitmask.
- **Memory:** 0 bytes if move count exists; otherwise 1 byte.
- **Code complexity:** Tiny.
- **Player-visible effect:** Boss stops switching or scouting for impossible coverage after the full set is public.
- **Bosses/roles affected:** All bosses; especially defensive pivots and setup sweepers.
- **Failure mode:** Misfires if romhack has nonstandard move-slot behavior, mid-battle move changes, or transformed/copied moves not modeled.
- **No-cheat risk:** Low, because it only removes impossible threats after public reveal.
- **Trace fields needed:** species_id, revealed_move_count, revealed_move_mask, threat_mask_before, threat_mask_after, gate_reason.
- **Audit test / fixture:** Active player mon has species that can legally carry Ice coverage. It reveals four non-Ice moves. Boss should stop preserving an Ice resist solely for that mon.
- **Better than doing nothing:** Existing memory is weaker if it remembers moves but still prices impossible hidden coverage.
- **Reject if:** Reject if revealed-move storage cannot reliably associate moves with the correct player species/form.

### 2. Opportunity-Weighted Non-Reveal Downgrade

- **Intelligence benefit:** Makes hidden-move priors update from public behavior without declaring absence.
- **Public info used:** Active species, level, legal learnset prior, revealed moves, turns where a hidden move would have been strongly useful, public matchup.
- **Forbidden info not used:** Hidden move slots; hidden PP; player input.
- **Implementation shape:** Small counter / score bias.
- **Memory:** 1 byte per active encounter, or shared 2-bit confidence nibble.
- **Code complexity:** Small.
- **Player-visible effect:** Boss gradually stops over-respecting a theoretical move after the player repeatedly declines obvious use.
- **Bosses/roles affected:** All; especially coverage-sensitive switchers.
- **Failure mode:** Player may be sandbagging a move; downgrade can be exploited if too strong.
- **No-cheat risk:** Medium-low; must only downgrade, never prove absence.
- **Trace fields needed:** candidate_threat, confidence_before, opportunity_seen, opportunity_quality, nonuse_count, confidence_after.
- **Audit test / fixture:** Player’s active species can legally have Thunderbolt and repeatedly faces a Water-type boss answer at safe HP but never uses it. After 2–3 opportunities, AI should lower Thunderbolt from likely to possible-only or possible-only to low.
- **Better than doing nothing:** Avoids static priors that make bosses look like they know every legal move forever.
- **Reject if:** Reject if “good opportunity” cannot be defined from existing score context without lots of new code.

### 3. Robust Progress Over Possible-Only Counterplay

- **Intelligence benefit:** Prevents overfitting to low-confidence threats under no Team Preview.
- **Public info used:** Current score gap, threat confidence bucket, public board, revealed moves, public HP/status/boosts.
- **Forbidden info not used:** Hidden team, hidden moves, hidden exact stats, current input.
- **Implementation shape:** Score bias / gate.
- **Memory:** 0 bytes.
- **Code complexity:** Small.
- **Player-visible effect:** Boss chooses strong neutral progress instead of a weird hard-counter line into a barely plausible move.
- **Bosses/roles affected:** All bosses; especially balanced teams.
- **Failure mode:** Can under-cover rare but devastating hidden coverage.
- **No-cheat risk:** Low if gated to possible-only threats and near-score cases.
- **Trace fields needed:** top_move, top_reason, possible_only_threat, robust_move, score_gap, override_applied.
- **Audit test / fixture:** Two AI choices: switch to resist a possible-only coverage move or click a high-progress STAB/status/hazard. If the hidden threat is only possible and the score gap is small, choose progress.
- **Better than doing nothing:** Does not require new knowledge; it calibrates existing threat masks.
- **Reject if:** Reject if current scoring already has a clear confidence-weighted possible-only cap.

### 4. Observed Speed-Order Memory

- **Intelligence benefit:** Uses actual public turn order instead of private exact speed peeking.
- **Public info used:** Which side moved first last turn at same priority, active species, move priority class, paralysis/status if visible.
- **Forbidden info not used:** Exact private stats, hidden items, hidden speed values.
- **Implementation shape:** 1-byte counter/bitmask.
- **Memory:** 1 byte.
- **Code complexity:** Small.
- **Player-visible effect:** Boss stops making “outspeed” lines after publicly losing speed order; also stops over-fearing speed when it has already moved first.
- **Bosses/roles affected:** Sweepers, revenge killers, frail attackers.
- **Failure mode:** Fails if priority, Quick Claw-like mechanics, paralysis, or move order modifiers are not separated.
- **No-cheat risk:** Low if it only records observed order, not exact stat.
- **Trace fields needed:** last_order_valid, priority_class, boss_moved_first, player_moved_first, speed_confidence, reason.
- **Audit test / fixture:** Same active pair, same priority class. Player moved first twice. Boss should avoid a line requiring it to move first unless priority/KO changes.
- **Better than doing nothing:** The approved exact-speed exception is narrow; this gives a public alternative for ordinary policy.
- **Reject if:** Reject if priority class cannot be cheaply known or if local mechanics scramble move order in untraceable ways.

### 5. Near-Tie Randomization With Guardrails

- **Intelligence benefit:** Makes bosses less deterministic without throwing games.
- **Public info used:** Final move scores, legal moves, existing RNG.
- **Forbidden info not used:** Player input, hidden team, hidden moves.
- **Implementation shape:** Score jitter / tie bucket.
- **Memory:** 0 bytes.
- **Code complexity:** Tiny.
- **Player-visible effect:** Repeated attempts do not produce identical boss scripts when multiple moves are genuinely close.
- **Bosses/roles affected:** All bosses.
- **Failure mode:** Bad jitter could choose visibly inferior moves.
- **No-cheat risk:** Low if only applies within a strict score band.
- **Trace fields needed:** top_score, candidate_scores, tie_band, rng_seed_or_roll, selected_move, excluded_moves.
- **Audit test / fixture:** With three moves within ±N score, repeated seeded runs should distribute choices; moves below the tie band should never be chosen.
- **Better than doing nothing:** Prevents solved deterministic exploitation while staying auditable.
- **Reject if:** Reject if existing move choice already randomizes near-ties safely and traces it.

### 6. Repeated Switch-Route Punisher

- **Intelligence benefit:** Punishes public player habits without reading current input.
- **Public info used:** Observed switch history, same outgoing/incoming species pattern, active matchup pressure, revealed moves.
- **Forbidden info not used:** Current-turn switch input, hidden reserve HP, hidden team slots.
- **Implementation shape:** Small counter / score bias.
- **Memory:** 1 byte.
- **Code complexity:** Small.
- **Player-visible effect:** Boss starts clicking the move that punishes a repeated pivot route, sets progress, or phazes instead of always hitting the current active.
- **Bosses/roles affected:** Bosses with coverage, hazards, phazing, status.
- **Failure mode:** Can be baited by one-time deviation; should only bias near-ties.
- **No-cheat risk:** Medium-low; must not read the current switch command.
- **Trace fields needed:** last_seen_switch_from, last_seen_switch_to, repeat_count, predicted_route_public, punish_score_bonus.
- **Audit test / fixture:** Player switches A→B twice after the same matchup pressure. On the third similar public state, boss biases toward move/status/hazard that punishes B, not because it read the switch, but because the pattern is public.
- **Better than doing nothing:** Existing switch prediction may see pressure; this adds memory for repeated routes.
- **Reject if:** Reject if current switch prediction already tracks route repetition by species pair.

### 7. Sole-Answer Preservation Gate

- **Intelligence benefit:** Keeps the boss from sacrificing its only public answer to a known threat.
- **Public info used:** Boss’s full authored team/moves, seen player species, revealed player moves, public statuses/faints.
- **Forbidden info not used:** Unrevealed player team, hidden moves, hidden items, reserve HP.
- **Implementation shape:** Gate / compact role table.
- **Memory:** 0 bytes if computed; 1 byte if cached.
- **Code complexity:** Medium.
- **Player-visible effect:** Boss stops exploding, trading, or risky-switching with the one piece that checks the player’s revealed sweeper.
- **Bosses/roles affected:** Defensive glue, spinblockers, phazers, ace enablers.
- **Failure mode:** Over-preservation can become passive.
- **No-cheat risk:** Low if based only on seen/revealed threats.
- **Trace fields needed:** boss_mon_role, public_threat_class, alternate_answers_count, preserve_gate, blocked_action.
- **Audit test / fixture:** Boss has one remaining public answer to a revealed setup threat. AI should not use that mon as a low-value sack while another resource can take the hit.
- **Better than doing nothing:** Role bias exists, but “only answer to this seen threat” is sharper and more visible.
- **Reject if:** Reject if own-team role/value map is unavailable or would need a large new table.

### 8. Hazard Retention Against Revealed or Active Spinner

- **Intelligence benefit:** Prices Rapid Spin pressure without assuming a hidden spinner.
- **Public info used:** Current Spikes layers, active species legal Rapid Spin prior, revealed Rapid Spin, seen unfainted spinner species, boss Ghost/spinblock/punish options.
- **Forbidden info not used:** Hidden party spinner, hidden moves beyond public priors, hidden reserve HP.
- **Implementation shape:** Score bias / gate.
- **Memory:** 0–1 byte.
- **Code complexity:** Small.
- **Player-visible effect:** Boss stops mindlessly stacking or protecting Spikes when spin can erase the stack, and instead KOs, blocks, or pressures the spinner.
- **Bosses/roles affected:** Hazard setters, Ghosts, phazers, bulky progress teams.
- **Failure mode:** Over-fears legal-but-unrevealed Spin if species prior is too high.
- **No-cheat risk:** Medium-low; must distinguish revealed Spin from merely legal Spin.
- **Trace fields needed:** spikes_layers, spinner_status: active/revealed/legal_prior/seen, spinblock_available, punish_move, chosen_reason.
- **Audit test / fixture:** At 2–3 layers, active opponent is a legal spinner or has revealed Rapid Spin. Boss should prefer KO/block/punish over passive extra progress unless Spikes click is clearly best.
- **Better than doing nothing:** The romhack’s three-layer Spikes and all-layer Rapid Spin clear make stack retention more important than vanilla one-layer intuition. Locally supplied mechanics need runtime verification.
- **Reject if:** Reject if Rapid Spin timing, Ghost blocking, or local typing cannot be verified.

### 9. No-Progress Counter

- **Intelligence benefit:** Breaks dumb move loops that do not damage, status, set hazards, force switches, reveal info, or improve route.
- **Public info used:** Previous boss action result, public HP/status/hazard/boost changes, fail text if public.
- **Forbidden info not used:** Hidden PP, hidden team, current input.
- **Implementation shape:** Small counter.
- **Memory:** 1 byte.
- **Code complexity:** Small.
- **Player-visible effect:** After two empty turns, boss changes plan toward damage, status, phaze, switch, or setup.
- **Bosses/roles affected:** All bosses; especially utility-heavy bosses.
- **Failure mode:** May abandon a patient but correct PP/endgame route if too aggressive.
- **No-cheat risk:** Low if reset rules are clear.
- **Trace fields needed:** no_progress_count, last_action, public_delta_flags, forced_bias_reason.
- **Audit test / fixture:** Boss uses a utility move twice into immunity/fail/protect loop. Third turn should prefer a progress action unless all progress actions are unsafe.
- **Better than doing nothing:** Existing switch-loop controls may not cover move loops.
- **Reject if:** Reject if current AI already tracks no-progress move loops, not just switch loops.

### 10. Safe Finish Clamp

- **Intelligence benefit:** Avoids stylish but bad plays when a reliable public finish is available.
- **Public info used:** Visible active HP band, own move accuracy/power/category, public speed-order memory if available, priority class.
- **Forbidden info not used:** Exact hidden reserve HP, hidden stats, current input.
- **Implementation shape:** Gate / score bias.
- **Memory:** 0 bytes.
- **Code complexity:** Tiny.
- **Player-visible effect:** Boss chooses the reliable KO or forced-KO line instead of setup/status/low-accuracy greed.
- **Bosses/roles affected:** Attackers, revenge killers, closers.
- **Failure mode:** HP band uncertainty can make a “safe KO” not truly safe.
- **No-cheat risk:** Low if clamp only fires on clear public KO bands or existing KO scoring certainty.
- **Trace fields needed:** finish_candidate, accuracy, hp_band, speed_order_public, clamp_applied.
- **Audit test / fixture:** If a 100% accurate move is in public KO range and a lower-accuracy move is only marginally better, boss picks the reliable move.
- **Better than doing nothing:** Players notice when bosses throw away kills for no reason.
- **Reject if:** Reject if KO scoring already includes accuracy and endgame loss risk strongly enough.

### 11. Public Priority-Risk Guard

- **Intelligence benefit:** Handles priority risk from revealed priority or high-confidence legal priority without private speed stats.
- **Public info used:** Revealed priority moves, active species legal priority prior, HP band, speed-order memory, own priority moves.
- **Forbidden info not used:** Hidden moves as certainty, exact speed/stats, current input.
- **Implementation shape:** Score bias.
- **Memory:** 0 bytes if using masks; 1 byte if cached.
- **Code complexity:** Small.
- **Player-visible effect:** Boss avoids leaving a frail sweeper in range of publicly revealed Quick Attack-style revenge, or uses its own priority to finish.
- **Bosses/roles affected:** Sweepers, low-HP attackers, revenge killers.
- **Failure mode:** Over-prices legal-but-unrevealed priority.
- **No-cheat risk:** Medium-low; strongest only after revealed priority.
- **Trace fields needed:** priority_source: revealed/likely/possible, hp_band, action_risk_before_after.
- **Audit test / fixture:** Player reveals priority. Later, boss at low HP should avoid setup if priority KO is public and choose KO/switch/protective line instead.
- **Better than doing nothing:** Priority mistakes look especially dumb because speed order is otherwise irrelevant.
- **Reject if:** Reject if local priority list is not verified.

### 12. Status Target Floor

- **Intelligence benefit:** Prevents wasting high-value status on obvious sacks or already-low-value targets.
- **Public info used:** Active HP band, current status, revealed Rest/recovery, seen species count/faints, own status move.
- **Forbidden info not used:** Hidden reserve HP/team/items.
- **Implementation shape:** Score bias / gate.
- **Memory:** 0 bytes.
- **Code complexity:** Small.
- **Player-visible effect:** Boss attacks or sets route progress instead of sleeping/paralyzing a 5% mon that is about to die anyway.
- **Bosses/roles affected:** Sleep/status bosses, bulky progress teams.
- **Failure mode:** Sometimes statusing a sack is correct to deny switch or setup.
- **No-cheat risk:** Low if exception handles imminent setup/Explosion/recovery.
- **Trace fields needed:** status_move, target_hp_band, target_status, target_value_bucket, override_reason.
- **Audit test / fixture:** Target is low HP, already statused or likely to die to safe damage. Boss should not choose Thunder Wave/Toxic/Sleep unless status prevents a public immediate threat.
- **Better than doing nothing:** Existing status value may not include “target floor” sharply enough.
- **Reject if:** Reject if current status scoring already accounts for target disposable value.

### 13. Public Rest/Wake Timing Bias

- **Intelligence benefit:** Better timing around Rest cycles without reading hidden sleep counters.
- **Public info used:** Observed turns asleep while active, public Rest use, public wake possibility, own phazing/setup/damage options.
- **Forbidden info not used:** Hidden sleep counter after switch, hidden PP, current input.
- **Implementation shape:** Small counter / score bias.
- **Memory:** 1 byte.
- **Code complexity:** Medium.
- **Player-visible effect:** Boss pressures before likely wake, phazes sleeping boosters, or uses free turns rather than wasting them.
- **Bosses/roles affected:** Bulky bosses, phazers, setup punishers.
- **Failure mode:** Sleep mechanics can be locally changed; exact counter can become hidden if switched.
- **No-cheat risk:** Medium; must track only observed public turns.
- **Trace fields needed:** rest_observed, asleep_turns_observed_active, wake_possible_flag, chosen_policy.
- **Audit test / fixture:** Opponent used Rest and stayed active. On early sleep turns boss may set hazard/boost; near wake window boss should attack/phaze if wake would punish greed.
- **Better than doing nothing:** Rest-cycle intelligence is very visible in Gen 2-style battles.
- **Reject if:** Reject if local sleep/Rest timing is not verified or if public/hidden counter separation is messy.

### 14. Explosion/Selfdestruct Route Budget

- **Intelligence benefit:** Makes sacrificial trades look planned instead of random.
- **Public info used:** Own move list, own team roles, active target public value, seen player species, revealed Ghost/Protect/Destiny Bond/Counter risks, current board.
- **Forbidden info not used:** Hidden team, hidden moves unless revealed/high-confidence public prior, current input.
- **Implementation shape:** Gate / score bias / compact role table.
- **Memory:** 0–1 byte.
- **Code complexity:** Medium.
- **Player-visible effect:** Boss booms to remove a route blocker or unlock closer, not into low-value bait or obvious public immunity/protection.
- **Bosses/roles affected:** Boom users, wallbreakers, route converters.
- **Failure mode:** Too conservative can miss winning trades.
- **No-cheat risk:** Low if based on public target value and revealed counters.
- **Trace fields needed:** boom_candidate, target_value_bucket, route_unlock_flag, public_blocker_risk, gate_result.
- **Audit test / fixture:** Boss has Explosion and faces a low-value statused active while a higher-value revealed wall remains. It should not boom unless it unlocks a clear public route.
- **Better than doing nothing:** Existing risk may know Explosion exists; route budget makes the trade legible.
- **Reject if:** Reject if own-team role labels are not cheap or Explosion mechanics/timing are unverified.

### 15. Emergency Override For Anti-Loop Switching

- **Intelligence benefit:** Keeps anti-loop controls from trapping the boss in a losing position.
- **Public info used:** Public active matchup, visible HP/status/boosts, public KO danger, Perish/Encore/trap/fail state if visible, own switch options.
- **Forbidden info not used:** Hidden moves, current player input, hidden stats.
- **Implementation shape:** Gate.
- **Memory:** 0 bytes.
- **Code complexity:** Small.
- **Player-visible effect:** Boss can still escape a catastrophic public board even if loop controls recently discouraged switching.
- **Bosses/roles affected:** Defensive pivots, Perish/Encore matchups, bulky bosses.
- **Failure mode:** Can reopen switch loops if override is too loose.
- **No-cheat risk:** Low if emergency flags are strict and traced.
- **Trace fields needed:** loop_block_active, emergency_flag, public_loss_reason, switch_allowed_reason.
- **Audit test / fixture:** After two repeated switches loop control would block another switch, but active boss mon faces public guaranteed KO/setup snowball. Emergency override allows switch.
- **Better than doing nothing:** Anti-loop rules are good until they forbid the only sane escape.
- **Reject if:** Reject if current loop control already has strict emergency exceptions.

## Five anti-proposals

1. **Current-turn input reader outside Haki**
   Reject. It would make bosses look smart in the worst way: they would be reading the player’s already-selected action outside the quarantined Haki/oracle exception. The context packet says Haki is one-use, only for named late/major bosses, only on the ace’s first active turn, post-input, traceable, and not ordinary policy.

2. **Hidden party scanner for coverage, spinner, or reserve answer**
   Reject. It would let the boss know unrevealed party slots, hidden moves, hidden items, hidden PP, hidden reserve HP, or private stats. That breaks the information model directly.

3. **Exact private stat / damage-roll oracle for all decisions**
   Reject. The prompt allows only the already-approved exact-speed exception for setup-speed headroom and says not to generalize exact private stat helpers.  A broad exact-stat helper would be a cheat-shaped shortcut.

4. **Broad hidden-information minimax search**
   Reject. It is too expensive, too brittle, memory-heavy, hard to trace, and likely to import assumptions that behave like Team Preview. The prompt explicitly rejects broad game-tree search and large new memory.

5. **Modern Team Preview / Defog / Stealth Rock planner**
   Reject. This romhack is Gen 2 based with no public Team Preview, and later-generation mechanics should not be imported as factual policy. The context packet also warns against assuming Team Preview, importing Defog/Stealth Rock/abilities/modern items, and using vanilla one-layer Spikes math for the romhack.

## Implementation First Picks

The three changes I would inspect or code first are:

1. **Four-Move Saturation Hard Gate**
   It is the cleanest win. It likely reuses revealed-move tracking and threat masks already in memory.

   Exact test idea: create a fixture where the player’s active species can legally carry a dangerous coverage move. The player reveals four different moves, none of which are that coverage. Before the fourth reveal, the boss may price the coverage as possible. After the fourth reveal, trace should show `revealed_move_count = 4`, `hidden_threat_mask_removed`, and the boss should stop switching or preserving resources solely for that impossible move.

2. **Near-Tie Randomization With Guardrails**
   It is probably a tiny scoring-layer change and gives immediate player-visible improvement without new battle knowledge.

   Exact test idea: set up three legal boss moves with final scores within the accepted tie band, plus one clearly inferior move outside it. Run 100 deterministic seeds. The three near-tie moves should appear in the selection distribution; the inferior move should never be selected. Trace should show the score band and RNG roll.

3. **No-Progress Counter**
   It catches a class of embarrassing AI behavior and needs only a compact public delta check.

   Exact test idea: boss uses a utility/status move into a public fail or no-effect state for two consecutive turns. The third turn should apply a progress bias toward damage, hazard, phaze, setup, or switch. The counter should reset after damage, KO, status, successful hazard layer, phaze, boost, forced switch, or meaningful reveal.

I would probably inspect **Observed Speed-Order Memory** immediately after those three. It is slightly more delicate because priority class and local move-order quirks need verification, but it is a strong public-info substitute for private speed peeking.

## Questions For Local Source

Check these before coding:

1. Does revealed-move memory already store per-player-species move count, or only a global/recent move mask?

2. Is there a reliable association between revealed moves and the correct active species across switching, transformation, mimic/copy-like effects, or form/species changes?

3. What is the current score scale and typical near-tie threshold? The robust-progress and randomization proposals need a safe score band.

4. Where are threat masks represented, and can they distinguish **likely**, **possible-only**, and **impossible after four revealed moves**?

5. Can the scoring layer identify a “good opportunity” to use a hidden move using existing damage/risk/status scoring, without adding a new search pass?

6. Does switch history already store species-pair routes, or only a recent switch flag?

7. Are public speed-order observations already available in trace/state, and can they be separated by move priority class?

8. Is local move priority fully verified, including any romhack changes?

9. Are Spikes layer count, Rapid Spin clear timing, Flying immunity, and Ghost spinblocking all runtime-verified? The packet supplies three-layer Spikes, all-layer Rapid Spin clear, Flying-type Spikes immunity, and no Levitate-style ability check, but exact timing and local type/passive changes still need verification.

10. Can the AI identify active or seen species that legally learn Rapid Spin without assuming an unrevealed party spinner?

11. Does the current loop-control code only prevent switch loops, or does it also detect repeated no-progress move loops?

12. Are Rest and sleep counters public enough to track only from observed active turns, without reading hidden switched-out sleep state?

13. Are boss-side role labels available cheaply: ace, wallbreaker, defensive glue, hazard setter, spinblocker, phazer, route converter, sackable support?

14. Can trace logging accept a few new fields per decision without memory or performance issues?

15. Is Haki implemented in a separate enough path that none of these ordinary policy changes can accidentally inherit post-input reads?

My blunt read: start with **four-move saturation**, **near-tie randomization**, and **no-progress counter**. They are cheap, traceable, and hard to argue against. The deeper intelligence wins are **opportunity-weighted non-reveal downgrade** and **robust progress over possible-only counterplay**, but those need more care because a bad confidence rule can make the boss look exploitable rather than smart.
