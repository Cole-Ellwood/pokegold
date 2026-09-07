# Joint evaluator: cycle budget and redesign for 2 s on the DMG (2026-09-06)

Independent algorithm/systems review of the experimental joint action evaluator
(`engine/battle/ai/joint_action.asm`, `action_value.asm`, `public_damage.asm`,
`damage_kernel.asm`, `action_facts.asm`, `public_replies.asm`,
`action_candidates.asm`). Goal: the broad benchmark (9 actions x 254 replies,
case `joint_broad_prior_mass`) under 8,388,608 cycles with integration headroom,
with the exact same score vector, best index, tie-break and uncertainty bytes
as the exhaustive reference. Cycles are DMG T-cycles at 4,194,304 Hz as counted
by the harness (`h.pb._cycles()`), never host time.

## 0. Baseline, measured this session

Build: `pokegold_ai_reference.gbc` (the only ROM that contains the joint
evaluator; `main.asm` gates it behind `BOSS_AI_REFERENCE`), built 21:06 from the
working tree, newer than every source edit. Command, from the repo root:

```
PYTHONPATH="$PWD" python audit/boss_ai_strategy_2026-09-06/profile_joint.py --rom pokegold_ai_reference [--tables]
```

| entry point | cycles | seconds | artifact |
| --- | --- | --- | --- |
| `BossAI_ComparePublicActions` (no SRAM tables) | 157,442,212 | 37.5 | `joint_profile_2026-09-06_2109_notables.json` |
| `BossAI_ComparePublicActionsWithTables` | 149,998,464 | 35.8 | `joint_profile_2026-09-06_2109_tables.json` |

The prompt's 156.6M figure reproduces (the difference is return-trap padding).
Required reduction: 157.4M -> 8.39M is 18.8x; to leave 2M of headroom, 25x.

Per-routine costs from a finer profile (`profile_joint_detail.py`, tables entry,
total 144.4M in that run; inclusive cycles, so rows overlap):

| routine | per call | calls | total | what it is |
| --- | --- | --- | --- | --- |
| `.EvaluateReply` | 61,395 | 2,286 | 140.3M | one (action, reply) pair, everything |
| `.EvaluateBranch` | 24,766 | 2,835 | 70.2M | one hit/miss/order branch incl. weighting |
| `BossAI_PreparePublicReply` | 26,473 | 2,286 | 60.5M | incoming template per pair |
| `BossAI_ValuePreparedPublicExchange` | 20,273 | 2,835 | 57.5M | the exchange itself |
| `BossAI_BuildPreparedIncoming` | 15,490 | 2,286 | 35.4M | clone + 4 far attribute reads + hit facts |
| `BossAI_PublicDamageRange` | 8,991 | 3,297 | 29.6M | avg over real and trivial (power 0) calls |
| `.Reply` (exchange reply half) | 10,239 | 2,835 | 29.0M | |
| `.PreRoll` | 6,162 | 3,810 | 23.5M | about 15k per real damaging call |
| `.Chart` | 3,190 | 3,210 | 10.2M | two calls per damaging range |
| `GetFarByte` | 248 | 39,419 | 9.8M | move/item/table bytes read across banks |
| home `Multiply` | 2,266 | 3,933 | 8.9M | probability weighting only |
| `.LoadPreparedOutgoing` (51-byte copy) | 2,108 | 3,975 | 8.4M | |
| `.Scale` (multiply + divide) | 930 | 8,519 | 7.9M | |
| `BossAI_Divide` | 896 | 8,756 | 7.9M | |
| `.Formula` (incl. `.RawQuotient`) | 4,966 | 1,517 | 7.5M | 3 divides + 2 multiplies |
| `.OwnMove` | 6,035 | 1,240 | 7.5M | |
| `BossAI_Multiply` | 715 | 7,239 | 5.2M | |
| `BossAI_AddTableOffset` | 441 | 10,612 | 4.7M | |
| `BossAI_PublicMovePriority` | 3,485 | 1,260 | 4.4M | far scan of `MoveEffectPriorities` |
| `.variation` | 1,315 | 2,490 | 3.3M | x217/255 roll |
| `.Passives` | 1,837 | 1,508 | 2.8M | |
| `.Mean` | 83,414 | 9 | 0.75M | repeated 16-bit subtraction |
| `BossAI_PrepareHPValues` | 66,792 | 9 | 0.6M | both SRAM tables, per action |
| `BossAI_BuildPublicReplySet` | 93,508 | 1 | 0.09M | |

Benchmark composition (from `cases.py`): boss Snorlax L50 with Tackle (95%),
Recover, Seismic Toss, Rest; bench Steelix, Pidgeot, Gengar, Alakazam, Machamp
(5 switch actions); player Smeargle L50, Tackle revealed, Sketch prior = all 254
moves possible. Move table facts (`data/moves/moves.asm`): 254 moves, 157 with
power > 0, 97 status; of the damaging moves 134 have a kernel-supported effect
and 23 are unsupported (Counter, Fly, OHKO, Reversal, Rollout, ...); 193 moves
have 100% accuracy; 11 are multi-hit; 116 distinct (type, power) pairs.

## 1. Where the cycles go: the avoidable dimensions

Per pair the evaluator spends 61.4k cycles. Only a few hundred of those are
arithmetic that actually depends on the pair. The rest is one of five kinds of
repetition, listed with the cycles they carry in the broad case.

D1. Reply facts recomputed once per action, although they depend only on
(reply, own defender). The four move actions and the forced/wait slots share
the active defender, so 4 x 254 incoming templates are built where 254 would
do. All of `PreparePublicReply` (60.5M) is in this dimension. The floor for
this dimension is one record per (reply, defender): 254 x 6 = 1,524 records,
of which only 134 x 6 = 804 need damage arithmetic (status and unsupported
replies need a class byte, not a kernel run).

D2. Generic multiply/divide for factors that are shifts or constant
divisions. `.Chart` applies 0/5/10/20 as `BC*a/10` through `Multiply` +
`Divide` (10.2M); STAB is `x3/2` (a shift-add); weather `x3/2`, `x1/2`; the
variation `x217/255` (3.3M); the base formula runs three 32-bit restoring
divides and two multiplies (7.5M). Total in this dimension: about 28M.

D3. Decision-time constants re-derived per branch: priority via a far scan
(4.4M), 39k `GetFarByte` reads (9.8M), 51-byte context clones (three per
exchange, 8.4M plus the clone inside `BuildPreparedIncoming`), can-act, item and
volatile checks, `.EffectSupport`/`.HPOnlyEffects` list scans, `AddTableOffset`
(4.7M). Roughly 30M, and it scales with pairs x branches.

D4. Branch multiplicity where successor states coincide. For the 97 status
replies the hit and miss branches produce the same HP state; for status replies
against a status own action both tie orders coincide. The current loop still
runs the full exchange for each. Measured branch factor is 2,835 / 2,286 =
1.24 branches per pair; without merging, a 4-event pair costs four exchanges.

D5. Probability weighting through the home `Multiply` (8.9M for 3,933 calls)
and `.Mean` by repeated subtraction (0.75M). Both are exact integer results
obtainable in a few hundred cycles.

What is NOT avoidable: one base-damage computation per distinct (power,
category, truncation, defender defense) group, one finishing chain per
(reply, defender) damage record, one combine step per (action, reply) pair, and
one 40-bit accumulate per pair. The budget below is built from those counts.

Why pruning did not help and will not be needed: an action's utility bound
spans the whole reply distribution, while the winner's margin in the broad case
is 12 points on a 1,000-point scale. With per-reply records the exact combine
step (about 1k cycles) is cheaper than any sound bound on the same pair, so the
right move is to make the exact evaluation cheap, not to skip it.

## 2. Target architecture

Three phases, one loop order: defender -> reply -> action. The current design
is an interpreter over a 51-byte damage context rebuilt and copied per pair and
per branch. The replacement separates facts by what they depend on and stores
each as a small fixed-layout record.

### 2.1 Phase A: facts (once per decision)

A1. Reply attribute pass. For every possible reply read effect, power, type,
accuracy byte once (one bank switch for the whole pass, or a same-bank copy of
the four columns), plus three build-time ROM tables indexed by move id:
`priority[254]` (from `MoveEffectPriorities` + the Vital Throw special case),
`contact[254]` (exists as `MoveContactFlags`), and `reply_kind[254]` (two or
three bytes per move: damaging-supported, unknown-damaging, status-only,
selfdestruct, recoil, drain, hp-only, heal class, defense-boost class, pursuit,
usable-asleep (Snore/Sleep Talk), thaws (Flame Wheel/Sacred Fire), multi-hit
min/max, fixed-damage type, conditional-postroll type). Generate the kind table
with a Python script from `moves.asm` and the effect lists in
`public_damage.asm` / `action_value.asm`, and audit it against those lists so
the two cannot drift (`tools/audit/`, same pattern as `check_boss_ai_chart_index.py`).

A2. Accuracy. `acc[r]` for the active own defender (evasion stage, Lock-On,
Foresight, Fly/Dig, Bright Powder, X Accuracy, Thunder weather, always-hit) and
`acc_bench_base[r]` once for a neutral bench target, adjusted per bench mon by
its Bright Powder only. The Flying accuracy passive is on the attacker (player),
so it is a per-reply constant shared by all defenders. Negation (Psychic-typed
defender) and Focus Band are per-defender constants that only set the HIT flag.

A3. Damage records, `DR[r][d]` for the 134 supported damaging replies against
each of the up to 6 own defenders. Fast exact kernel (section 2.4). Shared base:
the base damage depends only on (L2, power, attack-after-truncation, defense-
after-truncation), so iterate replies through a build-time permutation sorted by
(category, power) and compute the base once per group per defender, then finish
each member (STAB, chart, passives, roll) individually. Store raw min and raw
max (uncapped, the values `AD_RAW_MIN/MAX` hold today), plus a variant pair when
a threshold bit can change during the exchange (section 3).

A4. Own action records, `AR[a]`: one per action (<= 12), built with the
EXISTING `BossAI_BuildOwnedDamageContext` + `BossAI_PublicDamageRange` (25.8k +
about 20k measured, so about 0.5M for 12 actions). Each holds: kind, executes
(the `OwnCanAct` verdict is a decision constant), accuracy byte, priority,
raw min/max, and per endpoint e in {min, max, miss} the own HP after the own
action in own-first order and the player HP value after it (both constants,
section 2.3), the flag sets `F_reach` and `F_exec`, and the boost/heal/recoil/
drain/selfdestruct class bits. Lazy variants against a boosted player defense
(only Harden/Withdraw, Barrier/Acid Armor, Amnesia going first: at most three
extra ranges per damaging action).

A5. HP value tables: player table once, own table once per defender (the
current `PrepareHPValues` recurrence, 66.8k measured for both tables at L50).

### 2.2 Phase B: combine (per pair)

For the current defender d, for each possible reply r (record `R`), for each
live action a of d (record `A`, at most 6 for the active mon, exactly 1 for a
bench mon):

1. Order: compare `R.priority` with `A.priority`; on equality use the
   per-defender speed relation (own-first / reply-first / tie / unknown).
2. Events: own hit/miss exists per `A.acc` (255 -> only hit, 0 -> only miss),
   reply hit/miss per `R.acc`. Merge rule (section 2.5): if the reply cannot
   change HP on a hit (status-only, or does not execute), evaluate one reply
   event with mass 256; same for the own side.
3. Per remaining branch, walk HP with 16-bit arithmetic on the two HP words,
   using the constants in `A`/`R`: cap damage at the target's current HP, KO
   checks, after-hit item/recoil/drain deltas, then `u = base_a + v_d(ownHP) -
   v_pl(plHP) - [ownHP==0]*2w + [plHP==0]*256` with `v` from the SRAM tables.
   Flags: `A.F_reach | (A executed ? A.F_exec) | (R executed ? R.F_reach |
   (hit ? R.F_hit))` plus the order flag.
4. Weighting per pair (section 2.6), one 40-bit add per pair, mass += 2w.

Pairs with a status reply of the same (kind, priority, executes) can be
grouped into one class with summed weight (the 97 status replies collapse to
roughly ten classes in the broad case). This is optional for the budget and is
listed as a lever in section 4.

### 2.3 Why the per-branch walk is constant-time

In own-first order the own action sees start HP on both sides, so every own
after-effect is a per-(action, endpoint) constant: Life Orb loss
`min(ownHP, floor(max/10))` (only when damage > 0), Shell Bell gain
`min(missing, max(1, raw>>3))`, recoil `ContextRecoil(raw)` capped at own HP,
drain `min(missing, max(1, raw>>1))`, Selfdestruct -> 0, recovery
`min(missing, max>>k)`. So `A.ownHP_after[e]` and `A.vpl_after[e]` are stored
once. If the own hit KOs the player the reply is skipped and the branch utility
is the stored constant `A.u_ko[e]`. The only per-pair work is the reply's damage
capped at own HP, the rare helmet/recoil/drain of the reply, one table lookup,
and the flag OR.

In reply-first order the own action sees own HP after the reply's damage; the
caps above are recomputed at combine time (each is a 16-bit min, about 60
cycles) only for actions whose class bits need them.

### 2.4 Fast exact kernel (Phase A3)

Same integer pipeline as `BossAI_DamageKernel`, same order of floors, faster
primitives. Every step below reproduces the current step bit for bit.

| current step | replacement | status |
| --- | --- | --- |
| `floor(2L/5)` by 32-bit divide per call | per-attacker constant `L2 = floor(2L/5)+2` | trivial |
| `Multiply` x power, `Multiply` x attack | `L2*P` once per (power, category) group, `*A` once per group and truncation variant (8x8 and 16x8 shift-add, about 150/250 cycles) | derived |
| `Divide` by defense, `Divide` by 50 | keep `BossAI_Divide` (896 measured each), or one 22-by-14-bit restoring divide using `floor(floor(x/D)/50) = floor(x/(50*D))` (proven) | measured / proven identity |
| `.Scale` x3/2 (STAB, sun/rain up) | `x + (x>>1)` | proven exhaustively for 16-bit x |
| `.Scale` x1/2 (rain/sun down) | `x>>1` | trivial |
| `.Chart` rows x20/10, x5/10, x0 | `x<<1`, `max(1, x>>1)`, 0 (same min-one rule as `.Scale`) | trivial; keep row order |
| `.Passives` fractions k/n, n in {2,3,5,10,15,20,30,40} | `k*x` by shift-add, then `/2^a` by shifts and `/3`, `/5`, `/15` by two-level tables (`Q[h] + T[R[h]+l]`, exact over 16-bit, about 1.03 KB ROM each), or keep `BossAI_Divide` | table method proven exhaustively; cycle gain estimated |
| roll `x217/255` | `217x = (x<<8) - 39x` (shift-add), then exact `/255` by the recurrence `q += x>>8; x = (x>>8) + (x&255)` until `x < 765`, final `+2/+1/+0` | proven exhaustively for x < 2^22 (2 rounds suffice); the popular 3-term shortcut is WRONG at x = 65535 |
| `.Chart` group scan per call | 17x17 build-time matchup matrix indexed by (attack type, defender type) with the Foresight rows separate | derived from the same data file; audit it |

Estimated per-record finishing cost 600 to 900 cycles; per-group base 1.8k
with `BossAI_Divide`, about 1.2k with the merged divide.

### 2.5 Branch merging, exact

Two branches with identical successor state (ownHP, plHP, faint bits, flags)
have identical utility, so `p*u + (256-p)*u = 256*u` exactly in integers, and
the OR of their flags is the union. Merge when the reply has no HP effect on a
hit (status-only class, or the reply does not execute because the player cannot
act or was KO'd first) and symmetrically for the own side. Flag rule that
preserves the current OR-over-positive-mass semantics: `F_reach` is added
whenever the actor executes in any positive-mass branch; `F_hit` (the flags set
after the miss check: unknown damage, amount range) only when the hit event has
positive mass and the actor executes in it. The zero-mass skip already in
`.EvaluateReply` is the same rule.

### 2.6 Weighting, exact and cheap

Current numerator per reply: sum over orders and events of
`u * w_r * k_order * p_o * p_r` with `k_order = 2` for a single order and 1 per
tie order. Replace by `S_r = sum over orders k * (sum over own events p_o *
(sum over reply events p_r * u))`, then `T += w_r * S_r`. This is the same
integer by distributivity; the bound `S_r < 2^28`, `w*S_r < 2^31`, `T < 2^39`
is unchanged, so the 40-bit numerator and `floor((T>>16)/M)` stay as they are.
Cost: a pair with both actors certain needs no multiply (shifts); one uncertain
actor needs one 16x8 multiply, or none with `256*u_M + p*(u_H - u_M)`; both
uncertain need three. Broad-case average about 0.4 multiplies per pair. Use
`BossAI_Multiply` (715) or a register-only 16x8 routine (about 350), never the
home `Multiply` (2,266). Replace `.Mean` with a 24-by-16-bit restoring divide
(about 1.5k per action instead of 83k).

## 3. Equivalence keys

Each cached value is exact for the key below; anything outside the key forces
a variant or a fallback.

| cached thing | key | notes on HP, order, rounding |
| --- | --- | --- |
| reply damage record | (move, defender identity, defender Def or SpD after screens/known item/boost variant, attacker-low bit, defender-high bit, defender status bit, substitute/balloon/identified bits) | raw endpoints are HP-independent for single-hit supported effects; capping at target HP happens at combine time, which is exactly where `.use_prepared_range` caps today |
| threshold variants | attacker-low only if the player is Fire-typed and the move is Fire; defender-high only if the defender is Ice-typed | these are the only passives that read `AD_ATTACKER_LOW_F`/`AD_DEFENDER_HIGH_F`; select the variant by comparing the HP at execution time against `max/3` and `max/2` |
| multi-hit record vs an Ice defender | (move, defender, per-hit damage above and below half HP, hit count) | walk at most 5 hits at combine time; identical to the kernel's per-hit loop |
| reply accuracy | (move, defender evasion stage, Lock-On on defender, Foresight, Fly/Dig, Bright Powder, player accuracy stage, X Accuracy, weather) | bench mons share everything but Bright Powder |
| own action record | (action, player defense variant, own-low bit if own is Fire and move is Fire, player-high bit if player is Ice) | player-first recoil/drain/helmet changes the cap only, handled at combine time |
| HP value | (defender max HP, weight) -> table; (player max HP, 128) -> table | tables are exact `floor(w*HP/max)`; same values as the non-table path |
| order | (reply priority, action priority, defender speed relation, Quick Claw, speed-unknown) | tie -> both orders, mass 1 each; else one order, mass 2 |
| flags | per record: `F_reach`, `F_exec`/`F_hit`; per pair: order flag; per decision: item/volatile flags | union semantics from section 2.5 |

## 4. Memory layout and cycle budget

WRAM (472 bytes at `wBattleAnimTileDict`, replacing the current 424-byte joint
context):

| block | bytes |
| --- | --- |
| player block (HP, max, thresholds, speed relation, types, stages, status, flags) | 24 |
| current defender block (same shape, plus weight, item bits, Def/SpD used) | 24 |
| live reply record (kind 2, acc, prio, raw min/max, variant min/max, flags 2, hits) | 16 |
| action records, 6 live x 40 (incl. 5-byte total, 2-byte mass, flag byte) | 240 |
| final scores, 12 x 3 | 36 |
| loop state, scan bits, group cursors, status-class masses (<= 16 x 4) | 96 |
| total | 436 |

SRAM bank 0 ($a000-$a5ff): own HP table (<= 705), player HP table (<= 705),
reply bitsets (67) in the remaining 126 bytes. Same open/close contract as the
current tables entry. ROM: kind/priority/attribute arrays (about 1.5 KB),
matchup matrix (289 B), sorted reply permutation (254 B), optional division
tables (about 3 KB). Banks 1 and 11 have 471 and 371 free bytes in the reference
build, so put the fast kernel, the combine loop and all its tables in ONE new
floating ROMX section in an empty bank and reach it with a single `farcall`;
every hot table read must be same-bank (`GetFarByte` is 248 cycles).

Cycle budget, broad case. Unit costs marked M are measured this session, D are
derived from measured primitives, E are estimates from an instruction sketch.

| item | count | unit | cycles | basis |
| --- | --- | --- | --- | --- |
| reply set + candidates | 1 | 98.7k | 0.10M | M |
| reply attribute pass | 254 | 100 | 0.03M | E |
| accuracy, active + bench base, neutral stages | 508 | 300 | 0.15M | D |
| accuracy worst case (non-neutral stages, Flying player) | 508 | 2,200 | 1.1M | D |
| base damage per (power, category) group per defender | 360 | 1,800 | 0.65M | M (2 x `BossAI_Divide`) |
| record finishing | 804 | 800 | 0.64M | E |
| own action records via existing builder | 9 | 45k | 0.4M | M |
| lazy own variants (boost first, thresholds) | <= 6 | 30k | 0.2M | M |
| HP tables, 6 own + 1 player at L50 | 7 | 35k | 0.25M | M |
| HP tables worst case (704 HP) | 7 | 90k | 0.63M | D |
| combine: per pair setup | 2,286 | 150 | 0.34M | E |
| combine: per branch walk + lookup + flags | 2,835 | 500 | 1.42M | E (sketch below) |
| combine: weighting | 2,286 | 250 | 0.57M | D |
| combine: 40-bit accumulate | 2,286 | 80 | 0.18M | E |
| Mean, 9 actions | 9 | 1,500 | 0.01M | E |
| total, typical | | | about 4.0M (0.95 s) | |
| total, worst-case inputs | | | about 5.6M (1.33 s) | |

Per-branch sketch (T-cycles): load player start HP 32; load own raw endpoint 24;
16-bit compare/cap/subtract 50; KO test 12; load own HP after own action 24; KO
test 12; load reply raw endpoint 32; cap/subtract 50; KO test 12; class-bit
tests for helmet/recoil/drain 16; table lookup `v_d(ownHP)` 28; utility
assembly with base constant and material terms 120; flag OR 40; store 30.
Total about 480.

Headroom: the typical estimate leaves 4.4M of the 8.39M budget. The estimate
that decides the outcome is the combine step. If it measures at 2x the sketch
(2.2k per pair), the total becomes about 6.5M and the status-class merging
(pairs 2,286 -> about 1,340) and the register-only multiply become mandatory
rather than optional. If it measures at 3x, the architecture still fits only
with both levers, and the remaining redesign would be to precompute per-action
"reply-independent" utilities for the merged classes; there is no fourth lever
inside this design.

Table construction costs (all in the budget above): HP tables 0.25M typical;
kind/priority/matchup/permutation tables are build-time ROM (0 cycles);
division tables build-time ROM.

## 5. Exceptional cases and exact fallback costs

| case | handling | cost |
| --- | --- | --- |
| status reply (97) | class byte, no kernel; hit/miss merged | about 0 per record |
| unknown damaging reply (23) | class byte; hit branch sets own HP to 0 (current upper bound), miss does nothing | about 0 per record |
| defense-boost reply first (5 moves) | own record variant vs boosted player Def/SpD, lazily via the existing `ProjectedDefense` path | <= 3 x 30k per damaging own action |
| own defense boost first | reply records for the boosted defender are a second defender key; compute only the affected category | 134 x 800 per boost action |
| Fire attacker below 1/3, Ice defender above 1/2 | variant pair in the record; selected by HP compare at combine time | +1 finishing (800) per affected record |
| multi-hit vs Ice defender | piecewise record, <= 5-step walk | +300 per branch |
| False Swipe, Super Fang | formula at combine time (`min(dmg, HP-1)`, `max(1, HP>>1)`) | +60 per branch |
| Pursuit vs switch | flag only (current behaviour) | 0 |
| Substitute, Air Balloon, Foresight, Struggle | bits in the record key; current gates unchanged | 0 |
| Transform / bench Ditto | speed-unknown and unsupported constants as today | 0 |
| Thunder weather, Solarbeam charge, Dream Eater/Snore sleep, Stomp/EQ/Gust conditions | resolved in the attribute pass into accuracy/postroll constants | 0 |
| any (reply, defender) the record cannot express | mark `slow`; run the existing exchange path for that pair | 60k per pair; must stay rare and be counted in the profile |

## 6. First experiment (and the two after it)

Experiment 1, "record and combine": keep every existing fact producer, replace
the pair loop. Loop defender -> reply -> action. Build each reply record with
the EXISTING `BossAI_PreparePublicReply` (so the record's meaning comes from
proven code), each action record with the existing owned builder, tables as
today. Replace `.EvaluateReply`/`.EvaluateOrders`/`.EvaluateBranch`/
`BossAI_ValuePreparedPublicExchange` with the combine step of section 2.2 and
the weighting of section 2.6, keeping the old path selectable as the reference.

Done means: identical score vectors, best index and uncertainty bytes on every
joint/tie/accuracy/defense/prepared fixture in this folder and all 16 traversal
orders; the profiler shows `eval_branch`-equivalent work under 3M and the whole
broad case near 45-50M (prepare drops from 9x254 to 6x254 templates: about 40M;
combine about 3M). This proves the two things the budget rests on, the exact
equivalence of the combine step and its measured per-pair cost, plus the memory
fit, without touching the arithmetic. If the per-pair cost comes out above 2k
cycles, stop and redesign the record layout before building Experiment 2.

Experiment 2, fast kernel: implement section 2.4 as a drop-in behind
`BossAI_PublicDamageRange`'s single-hit path first (the existing paired kernel
fixtures in this folder validate it in isolation), then move reply preparation
to per-(reply, defender) records with base-group sharing. Expected: 40M -> about
1.5M; total about 5M.

Experiment 3, only if the profile demands it: status-class merging, register
multiply, division tables, merged base divide.

Not recommended first: the isolated micro-fixes (priority table, shift-based
Scale, dropping the home Multiply, a real Mean divide). They save about 25M
(16%), would be rewritten by Experiment 2 anyway, and test nothing about the
architecture.

## 7. Proven, plausible, unresolved

Proven (by algebra or exhaustive Python check this session):
`floor(3x/2) = x + (x>>1)` for all 16-bit x; `floor(floor(x/a)/b) = floor(x/(ab))`;
the exact `/255` recurrence for x < 2^22 (and that the 3-term shortcut fails at
65535); two-level table division for n in {3,5,10,15,20,25,30,40,100} over all
16-bit x; distributivity of the weighting rearrangement and the unchanged 40-bit
bound; branch merging with the union flag rule; the own-first per-endpoint
constants of section 2.3 follow line by line from `.OwnMove`, `.OwnAfterHitItem`,
`BossAI_ContextRecoil/Drain/Recovery`.

Plausible (measured primitives times counted operations, or instruction
sketches): every E and D row in the budget table; the 800-cycle finishing
chain; the 480-cycle branch walk; the 2x sensitivity analysis.

Unresolved: whether the combine step's register pressure keeps it near the
sketch on the real SM83 (Experiment 1 answers this); the exact ROM size and bank
placement of the new section; whether any reply in a real (non-Sketch) prior
needs the `slow` fallback; the cost of the accuracy pass when both stages are
non-neutral (bounded above at 1.1M); the status-class grouping key when Encore
or Disable make a status move non-executable (must be part of the key).
