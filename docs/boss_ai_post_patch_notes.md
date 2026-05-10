# Boss AI Post-Patch Notes

## Boss AI Cognition Mode

Read these notes as safety rails, not a creativity brake. The next scary idea
should preserve the no-cheat gates, memory limits, and public-information
discipline listed here while still trying to make the boss feel uncannily
prepared.

Date: 2026-04-26
Scope: boss AI release-safety patch and trace/tuning follow-up

## Implemented Patch Summary

The release-safety patch is now split across `engine/battle/ai/boss_platform.asm`,
`engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_policy_switch.asm`,
and `engine/battle/ai/boss_thunks.asm` with no new boss WRAM fields, SRAM
fields, HRAM fields, or Battle Core bank `0f` hooks.

Implemented behavior:

- Revealed player move knowledge is no longer one global exact-move bitmap.
  `wBossAIRevealedMovesBitmap` is reused as six 4-byte per-seen-species
  revealed type masks. The old spare reserve now also holds
  `wBossAILikelyTypeMaskCache`, `wBossAISeenPlayerAliveMask`, and 3 remaining
  spare bytes.
- Switch loop prevention now checks the proposed switch target against the last
  mon switched out, so immediate A->B->A reversals can be penalized unless an
  emergency exception applies.
- Boss move scoring now hard-discourages visible status failures: already
  statused target, Safeguard, Poison/Toxic into Poison or Steel, paralysis into
  real type-chart immunities such as Thunder Wave into Ground or Glare into
  Ghost, and Leech Seed into Grass.
- Boss move scoring now treats an unconsumed full-Dark player status shield as
  a public fail gate for shield-eligible status and utility effects. Half-Dark
  shield odds are not hard-failed because that would model a coin flip as a
  certainty.
- Boss utility scoring now treats visible player Substitute as a public Dream
  Eater fail state, even if the player is asleep. This matches the battle
  engine's `checkhit` / drain-sub behavior and uses only public active-state
  flags.
- Boss utility scoring now treats Nightmare as a public fail state when the
  player is behind Substitute, not asleep, or already having a Nightmare. This
  mirrors `engine/battle/move_effects/nightmare.asm` using only visible
  active-battle state.
- Boss utility scoring now treats Disable and Encore as public fail states when
  their visible lock state is already active or their public last-move basis is
  empty/invalid. It deliberately does not inspect hidden player move slots or PP;
  that exact legality belongs only inside a spent Haki branch.
- Boss utility scoring now treats Mean Look / Spider Web as public fail states
  when the player is already publicly trapped by `SUBSTATUS_CANT_RUN`. It does
  not inspect hidden reserve availability or last-mon legality, and it does not
  collapse damaging partial-trap moves into the same bucket because their damage
  can still matter.
- Boss move scoring now soft-discourages non-KO contact moves into visible
  Poison-passive defenders when the enemy can be poisoned by retaliation. This
  is a risk penalty, not a hard fail, so the boss can still take the contact
  line when it has KO pressure.
- Boss known-item reasoning now asks the item system for the enemy held effect
  instead of comparing raw item ids to `HELD_*` constants. This makes Choice
  Band/Specs/Scarf, Life Orb, Shell Bell, Assault Vest, Eviolite, and Air
  Balloon reasoning fire from the same public/own information the battle engine
  uses.
- Already Choice-locked boss mons now treat non-locked moves as unusable in
  Boss AI scoring, and `BossAI_HasAnyKOMove` evaluates only the locked move.
  The boss no longer stays in or traces a decision because an illegal coverage
  move would have looked good before the battle core forced the lock.
- Unlocked Choice boss mons now apply a small first-lock regret penalty when a
  damaging non-KO move would hand already-seen player species an immune or
  resisted future switch-in. This uses only public seen species, own held
  effect, current candidate type, and existing switch-pressure heuristics; it
  does not read hidden party data.
- Mid and late bosses now use already-seen bench species as a public revenge
  warning in `BossAI_ShouldRespectPotentialPlayerRevenge`. If public STAB from
  a seen species other than the current active threatens the current boss, the
  boss may consider switching instead of taking an obvious KO, especially when
  wounded. Public fainted seen species are filtered out with
  `wBossAISeenPlayerAliveMask`; this uses send-out/faint events only, not hidden
  reserves or party HP scans.
- Bosses now respect exact revealed player priority as speed-breaking pressure.
  If the active player has already shown a priority damaging move, the boss
  treats it as a public tempo threat when its coarse HP band and matchup make
  the move credible. This is active revealed-move memory only, not hidden move
  slot inference. Switch candidate risk also gives a small penalty to
  half-HP-or-lower boss pivots that would enter into a neutral-or-better exact
  revealed priority move.
- Bosses now apply a small public Protect/Detect commitment penalty. If the
  active player has already revealed Protect or Detect, Selfdestruct is heavily
  discouraged and Hyper Beam is modestly discouraged. This prevents the boss
  from blindly spending catastrophic commitment moves into a known shield
  option without reading the player's current turn.
- Mid and late bosses now apply a small public recovery-loop denial bias. If
  the active player has already revealed a recovery effect and is not at full
  HP, Toxic, Leech Seed, and force-switch moves get a small encouragement when
  the boss lacks a KO line and the move is not publicly blocked.
- Mid and late bosses now apply a public last-move Encore trap bias. If the
  player's last visible move was Protect/Detect or recovery, and public base
  speed says the boss should move first, Encore gets a stronger trap
  encouragement after public fail gates pass. This does not read the player's
  current-turn choice, hidden move list, hidden PP, or hidden party.
- Mid and late bosses now have a public Destiny Bond trade-window bias. If a
  Destiny Bond user is visibly at quarter HP or lower, has no KO line, is
  publicly faster, and the active player has a public threat, Destiny Bond gets
  a real trade encouragement without reading the player's selected move.
- Mid and late bosses now avoid obvious revealed Destiny Bond trades in the
  opposite direction. If the active player has exactly shown Destiny Bond, is
  visibly at quarter HP or lower, and public speed says the boss does not move
  first, boss KO-pressure moves get a strong penalty rather than blindly handing
  over a one-for-one.
- Boss switching now treats the boss's own public Perish Song clock as an
  emergency. When `wEnemyPerishCount` is `1` or `2`, the boss may bypass the
  normal KO-stay gate, avoid the A->B->A loop penalty, and add a strong switch
  confidence bonus. This reads only `wEnemySubStatus1` and `wEnemyPerishCount`,
  not hidden player state or current-turn intent.
- Mid and late bosses now have a public Counter/Mirror Coat trade-window bias.
  If the active player has already revealed a damaging move of the matching
  public type category, the boss is not publicly faster, has no KO line, and the
  reflected move can hit the player's visible typing, Counter or Mirror Coat can
  receive a trade encouragement without reading the player's selected move.
- Mid and late bosses now avoid feeding revealed Counter/Mirror Coat traps. If
  the active player has exactly shown Counter or Mirror Coat, matching non-KO
  damaging moves that can hit the visible active target get a pressure penalty.
  This is a public revealed-move adjustment, not a current-turn prediction.
- Mid and late bosses now avoid boosting into revealed anti-setup denial. If the
  active player has exactly shown Haze, Roar, or Whirlwind, boost-style setup
  gets a pressure penalty unless the candidate already has KO pressure. Rain
  Dance and Sunny Day are not included because Haze does not erase weather.
- Mid and late bosses now respect revealed sacrifice threats with Protect. If
  the active player has exactly shown Selfdestruct or Explosion and is visibly at
  half HP or lower, Protect/Detect gets a scout reward when public fail gates
  pass and the boss has no other KO move. This does not read the player's
  current-turn choice.
- `engine/battle/ai/switch.asm` now shares repeated
  `wEnemySwitchMonParam` store-and-return tails in `CheckAbleToSwitch`. This is
  a size compaction only; it preserves the existing switch behavior while
  keeping the crowded `Effect Commands` bank buildable.
- First-layer Spikes treats `wBossAITurnsElapsed <= 1` as the first scoring
  turn after `BossAI_IncrementTurnsElapsed`, and avoids high hazard greed under
  immediate public pressure.
- Late-tier class role bias is restored, so late bosses keep identity bonuses
  and Lance-style non-KO Hyper Beam discouragement.
- Phase 2 heuristics were added without a simulator: Spikes plus phazing bias,
  +2 setup punishment via denial moves, and a small immunity-pivot tie-break.
- Multi-turn projection now has a public stay-pressure floor before rewarding
  Spikes/setup from predicted switches. If the visible board says the player
  can punish the boss for staying in, the boss no longer gives itself future
  upside for a greedy hazard/setup line just because `BossAI_PredictPlayerSwitch`
  is high.

Important anchors:

- `BossAI_RecordRevealedPlayerMove`
- `BossAI_GetActiveSpeciesRevealedMaskPointer`
- `BossAI_HasRevealedSuperEffectiveMove`
- `BossAI_PlayerHasRevealedPriorityThreat`
- `.ApplyRevealedPrioritySwitchInRisk`
- `.ApplyRevealedProtectCommitmentRisk`
- `.PlayerHasRevealedProtect`
- `.ApplyRevealedRecoveryDenialBias`
- `.PlayerHasRevealedRecovery`
- `.ApplyRevealedFastEncoreAvoidance`
- `.EncorePunishableCommitmentMove`
- `.ApplyLastMoveEncoreTrapBias`
- `.LastPlayerMoveIsEncoreTrap`
- `BossAI_AddRevealedDamagingTypesToMask`
- `.StatusMoveWouldFailPublicly`
- `.DarkShieldBlocksStatusEffect`
- `.DarkShieldBlocksUtilityEffect`
- `.ApplyPoisonContactRiskBias`
- `.HeldItemMoveBlocked`
- `BossAI_GetEnemyHeldEffect`
- `BossAI_EnemyChoiceLockedMove`
- `BossAI_IsChoiceHeldEffect`
- `BossAI_SetScoreHL`
- `.ApplyDestinyBondTradeBias`
- `.ApplyRevealedDestinyBondAvoidance`
- `.ApplyCounterCoatTradeBias`
- `.PlayerHasRevealedCounterCoatCategory`
- `.ApplyRevealedCounterCoatAvoidance`
- `.PlayerHasRevealedCounterCoatTrap`
- `.ApplyRevealedAntiSetupAvoidance`
- `.IsBoostSetupMove`
- `.PlayerHasRevealedAntiSetup`
- `.ApplyRevealedSelfdestructProtectBias`
- `.PlayerHasRevealedSelfdestruct`
- `BossAI_CurrentEnemyMoveScoredPower`
- `BossAI_ShouldRespectPotentialPlayerRevenge`
- `BossAI_EnemyPerishEscapeUrgent`
- `BossAI_SeenBenchThreatScore`
- `BossAI_RecordPlayerFaint`
- `wBossAISeenPlayerAliveMask`
- `.ApplyChoiceFirstLockRegret`
- `.SeenSpeciesChoiceLockRisk`
- `.ApplySetupPunishBias`
- `.ApplyPhazingPlanBias`
- `BossAI_ApplyMultiTurnProjection`
- `.IsUnderPressure`
- `BossAI_ComputeSwitchCandidateRisk`
- `.spikes_layer1`
- `.ApplyLegacyRoleBiasIfNeeded`
- `BossAI_NeedsLoopPenalty`
- `.ApplyPrimaryThreatImmunityTieBreak`

## Memory And Bank Facts

Current generated facts are in `docs/generated/dev_index.md`.

## Public Endgame HP Weapons

Flail/Reversal are intentionally treated as real pressure only when the boss is
visibly wounded. The battle engine stores these moves as 1 power and rewrites
them during execution, so Boss scoring now gives the planner coarse public
HP-band values:

- boss at quarter HP or lower: high-pressure power
- boss at half HP or lower: mid-pressure power
- healthier than half HP: raw stored power

This is legal Boss AI, not Haki. It uses own HP and own move effect only.

Current post-patch memory summary:

- Boss WRAM reserve: normal build still uses 75 bytes and leaves 65 reserved
  bytes.
- Boss WRAM reserve with `BOSS_AI_TRACE`: still uses 94 bytes and leaves 46
  reserved bytes.
- `wBossAIStateEnd` remains before `wEventFlags`.
- `Battle Core` remains in bank `0f`: normal range is `0f:4000-7baa`; trace
  range is `0f:4000-7baa`.
- Boss AI logic lives in the Enemy Trainers section, bank `0e`: normal range is
  `0e:4000-7dd0`; trace range is `0e:4000-7ebf`.
- Plausible player move inference now uses a possible mask plus
  `wBossAILikelyTypeMaskCache`; the likely mask reuses old spare bytes from the
  revealed-move reserve and does not grow the Boss AI WRAM block.
- The single-effect revealed move scans for Protect, anti-setup denial,
  Counter/Mirror Coat avoidance, and Selfdestruct now share one public
  `wPlayerUsedMoves` effect helper. This is behavior-preserving compaction: no
  new WRAM and no new hidden-info reads.
- Mid/late bosses now avoid obvious faster-player Encore traps after Encore has
  been exactly revealed. The penalty applies only to recovery, Protect,
  Substitute, and setup-style commitment moves, and uses no current-turn player
  input.
- Mid/late bosses now avoid obvious faster-player Destiny Bond trades after
  Destiny Bond has been exactly revealed. The penalty applies only to KO-pressure
  moves into a visibly quarter-HP-or-lower active player, and uses no
  current-turn player input.
- Bosses now treat their own public Perish Song countdown at counts `1` or `2`
  as an urgent escape reason. This is switch logic only, costs no WRAM, and reads
  no player hidden information.
- Dream Eater now respects visible player Substitute as a public fail state.
  This is move scoring only, costs no WRAM, and reads no player hidden
  information.
- Nightmare now respects visible player Substitute, non-sleeping targets, and
  already-active Nightmare as public fail states. This is move scoring only,
  costs no WRAM, and reads no player hidden information.
- Disable and Encore now respect public already-active lock state plus public
  invalid last-move state. This is move scoring only, costs no WRAM, and reads
  no player hidden information.
- Mean Look and Spider Web now respect public already-trapped state. This is
  move scoring only, costs no WRAM, and reads no player hidden information.

Do not add persistent chaos or overprediction state to the boss AI block:
`ClearBossAIState` clears it at trainer load.

## Verification Already Performed

`make` was unavailable in the local PowerShell environment, so the ROMs were
built with the bundled RGBDS tools.

Built successfully:

- `pokegold.gbc`
- `pokesilver.gbc`
- `pokegold_trace.gbc`

Audits passed:

```powershell
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
git diff --check -- engine/battle/ai/boss_platform.asm engine/battle/ai/boss_policy_move.asm engine/battle/ai/boss_policy_switch.asm engine/battle/ai/boss_thunks.asm ram/wram.asm docs/generated/dev_index.md
```

## Manual Build Fallback

Prefer the Makefile when `make` is available:

```powershell
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc
make -j4 RGBDS=rgbds-1.0.1/ pokesilver.gbc
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc DEFINES="-D BOSS_AI_TRACE"
```

If `make` is unavailable but the existing non-boss object files are current,
reassemble the touched objects and relink:

```powershell
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -o main_gold.o main.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _SILVER -o main_silver.o main.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -o ram_gold.o ram.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _SILVER -o ram_silver.o ram.asm
```

Relink Gold/Silver using the same object lists from `Makefile`, then run
`rgbfix` and `tools\stadium.exe`. If trace output is needed without overwriting
normal Gold objects, assemble `main_gold_trace.o` and `ram_gold_trace.o` with
`-D BOSS_AI_TRACE` and link them into `pokegold_trace.gbc`.

After any successful relink that changes addresses, regenerate:

```powershell
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
```

## Trace Priorities

Primary trace bosses:

- Morty
- Jasmine
- Clair
- Koga
- Lance

Required behavior checks:

- Alakazam reveals Ice Punch, then another player species enters; the revealed
  Ice threat must not transfer globally.
- Boss switches A->B, then considers B->A; loop penalty should apply unless
  low current HP, public revenge pressure, own Perish Song escape, public
  immunity pivot, or ace timing applies. Generic public type pressure alone
  should not waive it.
- Spikes lead on the actual first scoring turn; hazard bias should be high only
  when public pressure is not immediate.
- Toxic, Thunder Wave, Confuse Ray, sleep, and Leech Seed should be heavily
  discouraged into visible fail states. Thunder Wave/Glare paralysis gating
  follows actual type-chart immunity, not a blanket Electric-target immunity,
  and player Substitute, existing confusion, or existing Leech Seed are treated
  as public fail states.
- Full-Dark active players with an unconsumed Dark shield should make
  shield-eligible status and utility effects look like public fail states.
  Consumed shields and half-Dark odds should not be treated as guaranteed
  failure.
- Non-KO contact moves into visible Poison defenders should receive a small
  risk penalty when the enemy is not already statused, not Poison/Steel, and
  not protected by Safeguard. Full Poison defenders should penalize more than
  half Poison defenders, but KO lines should remain live.
- Already-active Reflect/Light Screen, impossible Substitute, and Protect while
  already behind a Substitute should also be heavily discouraged by the boss
  model, as should Disable/Encore into public invalid lock states, Mean Look or
  Spider Web into public already-trapped state, Dream Eater or Nightmare into
  visible player Substitute, duplicate Nightmare, and healing moves at full HP.
- Late-tier Lance should keep role identity and avoid non-KO Hyper Beam.
- Spikes plus Roar/Whirlwind should gain value after repeated player switching
  or public setup pressure.
- Public +2 Attack, Special Attack, Speed, or Evasion should make Haze, Roar,
  Whirlwind, or Encore more attractive when no immediate KO line exists.
- A public/revealed threat type should make a true immunity pivot slightly
  preferable to a merely neutral pivot.
- Current enemy move pressure should discount non-super-effective hits into
  visible Dragon defenders because Imperial Scales lowers that damage in the
  actual battle engine.

Store excerpts under `audit/boss_ai_trace/`.
