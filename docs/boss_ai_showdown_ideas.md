# Boss AI ideas mined from public Showdown bots

Research notes from reading public Pokemon Showdown AI bots (foul-play,
Percymon, showdownbot, AverageAI). The goal is a punch list of *concrete*
heuristics that translate to Z80 assembly and the 4 MHz Game Boy CPU. This
doc is a backlog of ideas to discuss before implementing — it is not a
roadmap or a commitment. Each entry includes where it would hook into the
existing boss AI, a rough cost (S/M/L), and the regression risk.

Sources read:
- [pmariglia/foul-play](https://github.com/pmariglia/foul-play) — uses MCTS via Rust `poke-engine`; the rule logic lives outside Python and isn't directly extractable. Skipped beyond architecture.
- [Percymon (Stanford CS221)](https://varunramesh.net/content/documents/cs221-final-report.pdf) — Minimax depth-2, hand-tuned eval. The paper explicitly cites the "use a boosting move once" insight that motivated our recent setup affordability gate.
- [rameshvarun/showdownbot weights.js](https://raw.githubusercontent.com/rameshvarun/showdownbot/master/weights.js) — Percymon's actual feature weights.
- [rameshvarun/showdownbot greedybot.js](https://raw.githubusercontent.com/rameshvarun/showdownbot/master/bots/greedybot.js) — clean priority table for moves and switches.
- [EnrcDamn/PokemonShowdownBot AverageAI.py](https://github.com/EnrcDamn/PokemonShowdownBot) — readable rule-based decision tree with switch and attack scoring.

## Capabilities already in place

(Mirrored from the parent's brief so this doc is self-contained.)

- Move scoring with lookahead (MID/LATE tiers).
- Switch confidence + per-candidate risk weighting (`BossAI_ComputeSwitchCandidateRisk`).
- Wincon / role-mon detection (`BOSS_ROLE_SETUP/STATUS/DENIAL`).
- Plan system (`TEMPO_PRESSURE`, `SETUP_SWEEP`, `STATUS_CHOKE`, `ANTI_SETUP_DENIAL`, `WALLBREAK_THEN_CLEAN`).
- Player-revealed move tracking (`wPlayerUsedMoves`).
- Player-mon "scouted" memory across switches.
- Adaptive lead pick (LATE-tier bosses).
- Setup move affordability gate (turn-0 / turn-1-at-full-HP / hard cap), Speed-as-binary handling, KO-move gate.
- Sack-vs-switch logic.
- Anti-setup-revealed avoidance (Roar/Whirlwind/Haze tracking).

## Ideas, ranked by impact-per-cost

### 1. OHKO short-circuit

**Source:** AverageAI ([`AverageAI.py`](https://github.com/EnrcDamn/PokemonShowdownBot/blob/main/AverageAI.py)) lines 33-37: `kill_if_ohko(battle)` runs *before* `should_i_switch` and *before* `attack`. If the AI is faster than the opponent and has a guaranteed OHKO move, it picks that move and does no further scoring.

**Rule:** before any switch evaluation or fancy scoring, ask: am I faster *and* do I have a move that will guaranteed-KO the active opponent? If yes, pick that move. End of decision.

**Why it works:** the most common AI mistake is "thinking too hard" with a clean kill on the board. Short-circuiting eliminates a class of bugs where lookahead picks Setup or Switch when Wing Attack ends the turn.

**Gen 2 applicability:** clean transfer. Speed comparison and damage estimate are both already implemented (`AICompareSpeed`, `BossAI_HasAnyKOMove`). Note: `BossAI_HasAnyKOMove` uses "KO pressure" which is a heuristic, not a guaranteed OHKO. Strengthen by also requiring (a) the move's accuracy is ≥ 95 *or* the move is sure-hit, and (b) the opponent has no priority-move counter-threat (Quick Attack / Mach Punch / etc.).

**Implementation sketch:** new top-level entry point `BossAI_TryClosingMove` called at the very start of `BossAI_SelectMove`, before any plan or lookahead work. Costs **S** (~30 lines including the priority-counter check).

**Risk:** very low. The existing setup gate already deprioritizes setup when HasAnyKOMove returns yes, so this is the same logic moved earlier and elevated to "just do it" rather than "encourage it." Worst case: AI uses a damaging move when it could have used a status move that also wins; that's a draw, not a regression.

### 2. Revenge-killer pick on forced switch

**Source:** AverageAI `find_best_switch`, `revenge_value = 15` when `is_forced` and the candidate `is_revenge_killer`. Big positive nudge.

**Rule:** when forced to switch (current mon fainted), strongly prefer a mon that can OHKO the player's active mon. Outweighs almost all other considerations.

**Why it works:** after a faint, the player's active just earned tempo. Sending in someone who can immediately punch back stops their snowball. Sending in a passive defensive switch concedes the next turn for free.

**Gen 2 applicability:** clean. The math: for each alive bench mon, run `BossAI_HasAnyKOMove`-style check vs the active player mon, with a +Speed bonus if the candidate outspeeds. Top-rank a candidate that *outspeeds and OHKOs*; second-rank just OHKOs.

**Implementation sketch:** extend `BossAI_FindFirstAliveSwitchCandidate` (or a parallel "best-after-faint" picker invoked only on forced switches) to score candidates. Hook at the `BossAI_OnSwitchExecuted` predecessor — wherever the forced-switch path picks the next mon. Costs **M** (40-60 lines, needs a per-candidate KO-or-not loop, but reuses HasAnyKOMove).

**Risk:** medium. The existing forced-switch picker is "first alive"; replacing it with a scored picker changes which mon comes in. Could break setpieces where the trainer was specifically expected to send mons in order (e.g., scripted boss progression). Verify boss tier-gating: probably want this LATE-only.

### 3. Type-disadvantage penalty multiplier for proactive (non-forced) switches

**Source:** AverageAI line 95: `if not is_forced: if type_value < 0: type_value *= 4`. Penalizes proactive switches *into* a bad matchup four times harder than mid-turn switches that simply maintain a status quo.

**Rule:** the AI should be much more reluctant to switch from a neutral matchup *into* a type-disadvantageous one than to stay in a slightly-bad current matchup. "Don't make it worse" beats "find the perfect counter."

**Why it works:** proactive switches forfeit a turn for the player to free-attack the new mon. Switching into a 2× weakness compounds the loss. The bot literature converges on "stay in unless the change is clearly better."

**Gen 2 applicability:** clean. We already have `BossAI_ComputeSwitchCandidateRisk` which factors in plausible threat types. Adding a multiplier when the candidate has 2× weakness to the player's active is one more comparison.

**Implementation sketch:** in `BossAI_ComputeSwitchCandidateRisk` (or right before it's combined into switch confidence), check the candidate's typing vs the player's known damaging types. If 2× weak, multiply risk by 2. If 4× weak, multiply by 4. Cost **S** (~15 lines, type chart already accessible).

**Risk:** low. Increases switch-staying bias, which is the dominant correct behavior. Could miss occasional "switch-and-revenge" plays where the new mon eats a hit but wins the next turn — but those are exactly what idea #2 is for, gated by `is_forced`.

### 4. Don't re-cast active screens / stat-up effects already in play

**Source:** greedybot.js priority 12: `if(helpfulSideEffects.indexOf(move.id) >= 0 && !p1.getSideCondition(move.id))`. The "if not already up" guard.

**Rule:** if Light Screen / Reflect / Mist / Safeguard / Tailwind is already active on the AI's side, do not encourage casting it again.

**Why it works:** a re-cast is a wasted turn. Vanilla AI already has some screen handling but the boss layer can over-encourage on plan grounds.

**Gen 2 applicability:** Gen 2 has Reflect, Light Screen, Mist, Safeguard. No Tailwind (Gen 4+). Each has a side-condition flag we can read.

**Implementation sketch:** in the move-scoring layer (probably `engine/battle/ai/scoring.asm`'s effect-specific handlers), gate on the corresponding `wPlayerScreens`/`wEnemyScreens` bit. Cost **S** (~5-10 lines per effect, four effects). Probably already partially implemented; audit needed.

**Risk:** very low. Worst case is no behavior change because vanilla already does this for Reflect.

### 5. Don't re-Spike at max layers (3)

**Source:** greedybot.js entry-hazard gate. Adapted to this hack's 3-layer Spikes.

**Rule:** discourage Spikes when the player's side already has 3 Spike layers. The move would fail.

**Why it works:** identical to #4 — failed move = wasted turn.

**Gen 2 applicability:** this hack added 3-layer Spikes (`docs/mechanics_changes_from_base.md` §1.4). Vanilla Gen 2 had only 1 layer.

**Implementation sketch:** find the existing Spikes scoring path (probably `EFFECT_SPIKES` in scoring.asm). Read the per-side layer count and `AIDiscourageMove` if at max. Cost **S** (~10 lines).

**Risk:** trivial.

### 6. Speed as multiplicative bonus on attack value

**Source:** AverageAI: `if faster: atk_value *= 1.5`. Used in both current-mon evaluation and switch-candidate evaluation.

**Rule:** when the AI is faster than the active player mon, scale up the value of attacking moves. Outspeed converts attacking into "fire before being hit" which is materially different from attacking-while-slower.

**Why it works:** in our current scoring, "I outspeed" is treated as a binary gate for some heuristics (Speed-binary check, AICompareSpeed) but not as a continuous scaling factor on offense. Treating it as a multiplier captures "I'm faster, so my Wing Attack is more valuable than my Reflect this turn."

**Gen 2 applicability:** clean. AICompareSpeed exists and is used.

**Implementation sketch:** in the boss-layer move-scoring lookahead (around `boss.asm:5440-5500`, the `.delta` block), add a Speed multiplier on damaging moves' upside (`b`). Probably +1 to upside if `AICompareSpeed` says faster. Cost **S** (~10 lines).

**Risk:** low. Could make the AI over-prefer damage when status would be better — but our existing scoring already handles status-vs-damage, and a +1 nudge on damage is small relative to the status-encourage values (which are typically +2 to +5).

### 7. Sweep-blocker recognition on forced switch

**Source:** AverageAI lines 79-87: `sweep_block_value = 15` when `is_forced and opponent_is_sweeping` and the candidate is faster *or* has Focus Sash with no hazards on the field.

**Rule:** when forced to switch into a player who is mid-sweep (has +stages stat boosts), prioritize mons that are faster than the sweeper, or that can survive one hit and threaten KO back.

**Why it works:** the worst forced-switch outcome is sending in a mon that gets one-shot, ceding two free turns. Sending in something faster forces the player to respect tempo even if it dies, and the +stage boost the opponent has becomes a liability if you can phase or revenge.

**Gen 2 applicability:** Gen 2 has no Focus Sash (Gen 4+). Replace the Sash heuristic with: "candidate at full HP *and* a known multi-stage attack OR phazing move (Roar/Whirlwind)." Speed comparison transfers cleanly.

**Implementation sketch:** the "is opponent sweeping" check is a sum of `wPlayerStatLevels` deviations from base. If any sums to ≥+2, opponent is sweeping. Then in the forced-switch picker (paired with idea #2), add a +score for candidates that are faster than the player's active *or* know a phazing move. Cost **M** (40-60 lines including the sweep detector).

**Risk:** medium. Same risk class as #2. Want LATE-only initially.

### 8. Recovery-move HP threshold

**Source:** greedybot.js priority 9: `if hp is low enough` (`myPokemon.hp * 2 < myPokemon.maxhp` — i.e. ≤ 50%).

**Rule:** don't encourage recovery moves (Recover, Soft-Boiled, Synthesis, Moonlight, Morning Sun, Milk Drink, Roost) above ~50% HP. Below half, do encourage. Below quarter, encourage hard.

**Why it works:** at 90% HP, a Recover heals 10% — not worth the turn. At 30% HP, a Recover that saves you from 2HKO is game-changing.

**Gen 2 applicability:** clean. Vanilla GSC AI has *some* HP-aware recovery scoring (`AICheckEnemyHalfHP`/`QuarterHP` are used in scoring.asm) but it should be audited; probably already half-correct.

**Implementation sketch:** audit existing `EFFECT_HEAL`/`EFFECT_MORNING_SUN`/etc. handlers in scoring.asm. If not already gated by HP fraction, add the gate. Cost **S** (~5 lines per effect; if already gated, this is just verification).

**Risk:** very low. Worst case: confirms existing behavior.

### 9. Don't double-status

**Source:** greedybot.js priority 10: `if(move.category === "Status" && move.status && !oppPokemon.status)` — only encourage status moves if opponent has *no* status.

**Rule:** discourage Toxic/Thunder Wave/Will-O-Wisp/Glare/Hypnosis/Spore/Sleep Powder when the player's mon already has a major status condition.

**Why it works:** status moves apply at most one status. Casting Toxic on a paralyzed mon does nothing. Wasted turn.

**Gen 2 applicability:** clean. `wBattleMonStatus` is readable.

**Implementation sketch:** audit existing status-move scoring. Add a gate: if `wBattleMonStatus & STATUS_MASK != 0`, `AIDiscourageMove` for status-inflicting effects. Cost **S** (~5 lines + per-effect check).

**Risk:** very low. May already be present; verify and patch holes.

### 10. Phasing encouragement against boosted opponent

**Source:** greedybot doesn't isolate this, but Percymon's eval gives high penalty per opponent boost stage and high reward for hazard removal. The corollary for our AI: if opponent has +stages, lean into Roar/Whirlwind/Haze.

**Rule:** if the player's active mon has any positive stat stage (`wPlayerStatLevels` value > base), the AI should heavily encourage phazing moves (Roar, Whirlwind) and stat-reset moves (Haze).

**Why it works:** every turn an opponent stays boosted is value gained for them. Phasing erases that value at the cost of one turn. Almost always a winning trade.

**Gen 2 applicability:** Gen 2 has Roar, Whirlwind, Haze. No Clear Smog, Defog isn't yet a stat-reset.

**Implementation sketch:** in scoring.asm's `EFFECT_FORCE_SWITCH` and `EFFECT_RESET_STATS` handlers, check `wPlayerStatLevels`. If any positive stage > 1, encourage by 2-3. Cost **S** (~15 lines). Note: existing `BossAI_ApplyRevealedAntiSetupAvoidance` discourages the AI from setting up *against* a phazer; the inverse rule (encourage phazing against a setupper) is the missing half.

**Risk:** low. Could over-phase against a +1 mon that wasn't actually a threat. Tune the threshold (require +2 or higher to trigger encourage).

### 11. Stronger switch-risk damage estimate

**Source:** AverageAI's `find_opponent_best_damage` returns the max damage the opponent's active could deal to a candidate switch-in, which is then negated and weighted (halved if the candidate is faster). Currently `BossAI_ComputeSwitchCandidateRisk` is more abstract — uses a tier-weighted threat-mask intersection rather than a concrete damage estimate.

**Rule:** for each switch candidate, estimate the damage the opponent's best known damaging move would deal on switch-in. Subtract that from the candidate's switch-in score. Halve the penalty if the candidate is faster (because a faster mon may KO before being hit again).

**Why it works:** abstract threat masks miss "Geodude has Earthquake and your switch-in is Magneton" — the threat is binary, but the damage is overwhelming. A concrete damage estimate captures both type and the mon's offensive stat.

**Gen 2 applicability:** the damage formula is already implemented in `engine/battle/effect_commands.asm` for actual move execution. Borrowing the simulation path for AI estimation is the standard pattern but expensive on GB CPU. A cheap proxy: `(opp_attack_or_special × move_BP × type_effectiveness) >> shift` to get a rough integer rank.

**Implementation sketch:** add `BossAI_EstimateOppDamageOnCandidate` helper. Use the cheap proxy formula. Hook into `BossAI_ComputeSwitchCandidateRisk` as an additive risk term. Cost **M** (60-100 lines; needs the proxy formula and unit-test against real damage rolls for sanity).

**Risk:** medium. A bad damage estimate is worse than no damage estimate. Recommend keeping the existing risk function as the primary signal and adding the damage estimate as a secondary tiebreaker, not a replacement.

### 12. Late-game cleanup recognition

**Source:** Percymon's "boosting once" insight in §10 of the paper, and AverageAI's overall "late game = sweep mode" implicit logic. The rule: when the opponent has 1-2 mons left, your wincon mon should sweep, not preserve.

**Rule:** if `wPartyCount`-equivalent for the player shows 1-2 unfainted mons left and the AI has its wincon mon active, override the standard sack-vs-switch hesitation: stay in even at low HP, attack rather than setup, take the trade.

**Why it works:** in the late game, "preserving" a mon is meaningless — you're trying to land the final hits. The bench has nothing to switch *to* that helps. The wincon mon's job in late game is to use HP as ammunition, not as preservation.

**Gen 2 applicability:** clean. Player-faint count is trackable (we already have `BossAI_RecordPlayerFaint`).

**Implementation sketch:** new helper `BossAI_IsLateGameCleanup` returning carry if player_alive_count <= 2 and current mon == wincon. Wire into the switch-confidence path to *reduce* switch tendency, and into the setup-affordability gate to *also* reduce setup encouragement (don't burn turns boosting when you should be killing). Cost **S** (~25 lines).

**Risk:** low. Increases AI aggression at exactly the moment the AI should be aggressive. Could over-stay in losing matchups; mitigated by the existing wincon-risk and damage-rate gates.

### 13. Choice-locked exploit on player

**Source:** Percymon paper §4.2 mentions choice items as a hidden-info challenge. AverageAI doesn't directly exploit them, but the implicit play: if you've seen the player choice-lock, switch into the resist freely.

**Rule:** if the AI tracks that the player is using a Choice Band/Specs/Scarf and the player's last move is known, the player is locked into that move. Switch into a counter freely; the player can't punish.

**Why it works:** Choice locks turn the player into a single-move actor. Free switches are extremely high EV — the player either has to switch out (losing tempo) or use the locked move into a hard counter.

**Gen 2 applicability:** this hack adds Choice items. Boss AI already has *some* Choice handling for the AI's own use (`BossAI_EnemyChoiceLockedMove`). The mirror — recognizing player Choice — is the missing half.

**Implementation sketch:** track `wPlayerChoiceLockedMove` (new WRAM byte) populated when the AI infers Choice item presence (heuristic: player has used the same move 2+ times in a row at locked-in damage). Use it in switch scoring to bias toward resist/immunity to that locked move. Cost **L** (needs WRAM byte + inference logic + scoring hook). Probably defer this until item-tracking is more robust.

**Risk:** medium. Inference is fragile — players sometimes use the same move twice without Choice. False-positive Choice tag could send the AI to a passive switch when the player isn't actually locked.

## Explicitly rejected

- **Monte Carlo Tree Search / minimax > depth 2** — foul-play and Percymon both rely on deep search via fast simulators (Rust `poke-engine`, Showdown's JS engine). Even Percymon at depth 2 has a *5.5 second median* decision time on modern hardware. Game Boy at 4 MHz couldn't simulate one node, let alone a tree.
- **TD-learned / RL feature weights** — Percymon's future-work section specifically notes TD learning failed to converge in a reasonable timeframe. We have neither the training infrastructure nor the simulator to do this offline. Manually tuned weights (which is what we already do) are the only realistic path.
- **Mega Evolution heuristics** — N/A in Gen 2.
- **Z-moves / Tera / Dynamax** — N/A in Gen 2.
- **Bayesian opponent set inference** — too expensive in WRAM. The boss AI's existing per-mon "scouted" memory plus public-moves table is the cheap version of this; expanding to full set inference would require kilobytes of state.
- **Damage roll Monte Carlo (16 rolls per move)** — Showdown bots use the full 16-roll damage range. The Game Boy AI already uses single-roll damage estimation; iterating across rolls would 16× the lookahead cost with negligible accuracy gain.

---

Saved to `docs/boss_ai_showdown_ideas.md` — 13 ideas, ranked.
