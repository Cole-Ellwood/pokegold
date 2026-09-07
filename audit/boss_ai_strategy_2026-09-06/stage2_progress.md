# Stage 2 work in progress



The full roadmap remains active. Stage 1 is approved; its frozen manifest and

fixtures are historical evidence. The following groundwork does **not** constitute

joint action valuation, switch-policy promotion, or completion of stage 2.

This is an incremental work log. Earlier context sizes and profiles describe
their recorded revisions. The current defensive-boost section supersedes the
earlier layouts: direct exchange 89 bytes, prepared exchange 141, matrix 273.


## Implemented facts



- The public damage adapter accepts an explicitly owned party slot. Bench stats

  begin at neutral stages and apply entry status modifiers once. Active volatiles

  and active items cannot contaminate another owned party member's estimate.

- Caller contexts contain both actors' HP and max HP. Threshold flags can be

  refreshed after projected HP changes. Raw damage is retained separately from

  capped HP loss, because recoil and drain use raw damage even on overkill.

- Entry damage uses the hack's Spikes fractions (eighth, sixth, quarter), minimum

  one, Flying immunity and current-HP cap. Air Balloon does not prevent Spikes.

  Entry precedes Imposter; bench Ditto remains uncertain when its copied state is

  not represented, including fixed-damage immunity changes.

- Recovery amounts use projected HP, missing-HP caps, the Rest/full versus

  Recover/half distinction, and this hack's time/weather/link rules. Status

  transitions and whether the command can execute belong to action evaluation.

- Executing recoil uses quarter raw damage, minimum one, then Steel's mono zero

  or dual half modifier. Drain uses half raw damage with minimum one and a

  missing-HP cap. Drain command arithmetic can add HP at zero; action denial must

  be checked by its caller. The helper does not silently impose a different rule.

- Speed facts apply known active Speed or neutral bench Speed, Electric then

  paralysis modifiers, and known own Choice Scarf. Public player Speed uses DV8,

  public stages/status/types and no unknown item. Carry marks ordinary modeled

  ordering usable; player Transform and bench Ditto explicitly clear it.

- Known per-hit item interactions requiring two-sided HP transitions remain

  unsupported, including outgoing multi-hit Life Orb/Shell Bell and incoming

  contact multi-hit into Rocky Helmet. Unsupported means uncertainty, not zero

  incoming risk or a reliable outgoing KO.



No persistent WRAM or save-format changes were added for these contexts.



## Validation and bounded review



Gold built with the 51-byte context and all helpers. The 67 party damage cases,

215 active damage cases, 90 entry/recovery cases, 42 recoil/drain cases, and

46 speed cases passed targeted runs. Speed cases include stage extremes,

level-one rounding and explicit transformed/Imposter uncertainty. Public-state

preservation is checked independently of arithmetic. No-cheat audit passed.



The recoil/drain reference executes actual combat command HP mutation and stops

before UI animation. Entry/recovery references execute actual combat fraction

routines; those tests do not claim complete command/turn validation.



Astra approved the bounded entry/recovery implementation at action_facts.asm

SHA256 `3a62044ed79d8b237e829bbe49537619544ec9777cd3e8dd9b125e6d1efe9012`,

then recoil/drain and ordinary speed at

`75d66d02b3fea712900247850a412cc96ef7ee549b6477245be91b7b431668e4`.

The explicit speed-uncertainty flag and added boundary corpus were then approved

at SHA256 `3fb388c545883c2e70225f9cda926412aa02c2491dd239a1a4527d74e2161193`.

None of these approvals covers the pending joint valuer.



The initial full Gold run passed 637 cases before the speed-uncertainty follow-up.

The last full Gold run before the candidate/reply additions below, including all 45 draft exchange cases, passed all 696 cases and is recorded in

`pokegold_stage2_fixtures.json`. All 12 applicable audits passed in

`stage2_checks.json`.

Do not rebuild a ROM while its fixtures run: the harness opens it per case.



## Required next implementation



Complete and integrate the draft move/switch/replacement evaluator below. It must

enumerate all legal living bench candidates, preserve actual

switch restrictions and authored Haki/tier behavior, account for forfeited switch

tempo and retained material, and distinguish reliable interruption from uncertain

hit/order/survival premises. Remove legacy nomination/low-HP/type/sack vetoes only

with joint-policy validation. Then complete the public successor search, outcome

learning and strategic corpus/ablations required by the remaining roadmap.



## Draft exchange evaluator



`action_value.asm` now implements `BossAI_ValuePublicExchange` over an 81-byte

caller-owned context. It takes one legal owned action and one explicit public

reply. Kind 0 is a move, 1 a voluntary switch, and 2 a faint replacement. Branch

bits distinguish own/reply misses, explicit same-priority order, and each

side's damage endpoint. Explicit order cannot override move priority and keeps

the order-uncertainty flag; callers must enumerate only feasible orders.

No candidate nomination, RNG consumption or

live battle-state mutation occurs inside the evaluator.



Its shared scale is 256 material units plus 128 HP units per ordinary mon; the

authored owned win condition has 1.5 times that weight. It scores the change in

material and HP, with a 1024 return-value bias. HP fractions are rounded per

state so successive deltas telescope. A switch retains the outgoing mon's

existing material rather than granting the incoming mon's starting value again.

These weights are model choices awaiting strategic validation, not combat rules.



The draft handles action order, interruption by a finish, entry hazards, lost

switch tempo, recovery timing, Selfdestruct on misses, successful-hit recoil and

drain on both sides, and certain sleep/recharge/freeze/flinch denial. It uses

noncritical outgoing minimum and incoming maximum damage by default; callers

can request outgoing maximum and incoming minimum with their matching raw

side-effect amounts. Endpoint branches do not constitute a roll distribution

or prove bounds for arbitrary successors. Hit, order, amount

range and unmodeled transition flags prevent a conditional estimate from being

advertised as a deterministic exchange. Damage-roll variation is flagged even

when overkill caps HP loss but leaves raw side-effect damage variable.



The input contract requires caller-validated slot/kind and move legality,

including PP, Disable, Encore and Choice. Missing replies must never be encoded

as a harmless zero move: zero specifically means no reply. Pursuit against a

voluntary switch remains unsupported because it targets the outgoing active

before entry; the draft flags it instead of damaging the bench candidate.



Known Life Orb, Shell Bell and Rocky Helmet HP effects run after direct damage

and before the move's recoil/drain, matching combat. Shell Bell cannot revive

an already fainted user. Helmet still triggers when its holder faints. The

following drain command can restore HP after item damage reaches zero; the

evaluator preserves that command ordering rather than assuming an early faint.

Known Quick Claw, Air Balloon/King's Rock transitions, existing Protect/Endure/Attract/

Destiny Bond, secondary-effect families and Poison contact retaliation remain

explicit uncertainties. Critical branches, full status/stage/volatile successors,

end-of-turn effects, branch probabilities, future offense, plausible-reply

enumeration and production selector integration remain unfinished. The current

HP result is not a complete battle successor in those cases.



All 45 exchange fixtures passed on the current Gold build. They cover fixed-damage trades and finishes,

recovery order, switch/replacement tempo, entry fainting, large HP fractions,

win-condition weights, miss/immunity script order, action denial, explicit hit/

miss branches, amount uncertainty, and unresolved-transition flags. Normal damage

cases obtain their reference amount from the actual combat pipeline. The driver

also checks no RNG consumption, caller state preservation, and hidden-player-

state invariance. Additional combat-reference cases execute the actual held-item

dispatcher followed by drain/recoil, bypassing presentation only. They check

Life Orb and Helmet reaching zero before drain, and Shell Bell before recoil.

Their raw damage is seeded from the evaluator, so these cases prove HP-command

sequencing; separate outgoing/incoming combat comparisons verify endpoints.



Astra approved only this bounded conditional, noncritical HP scope at

`action_value.asm` SHA256

`7d6e753ae87cfc20ea4b1ab64f2c0d02ac18516ad6a1b10abb2c16a92f4f15e3`.

This is not approval of stage 2 or the pending selector integration.



Astra subsequently approved the known-item additions at SHA256

`1ba1a36a5299b73ace51f58e9e24352d82e73a113dc88fb39ab7c1ced1e29958`.

The explicit endpoint/order extension is a separate bounded review; none of

these approvals promotes the evaluator into production candidate selection.



Astra approved the endpoint/order extension, then the priority-effect

classification correction, with all prior bounded item/core retention decisions,

at final `action_value.asm` SHA256

`744d0dbe91dc713eddc01af198141a709837a11e063b271391b5979d2bae83e4`.

`EFFECT_PRIORITY_HIT` uses the combat `NormalHit` script; its modeled priority

does not require an additional unknown-transition flag. Endpoint cases compare

both incoming endpoints and outgoing maximum against combat; the priority case

confirms an explicit same-priority order branch cannot reverse move priority.

Approval remains confined to the conditional HP exchange and these branches.



## Candidate and public-reply groundwork



`action_candidates.asm` enumerates exact usable owned moveslots, forced actions,

recharge waits, and every legal living bench slot. It preserves combat's Encore,

Choice, Assault Vest, PP, Disable, trapping and locked-turn precedence without

legacy preference or low-HP candidate vetoes. All 32 targeted Gold cases passed;

forced-action references call the actual parser. Astra approved the source at

`f7ba190181861f584469c1b16c4d5bb142624c5b664207928883a4effb5a5cb6`.

Testing also exposed and fixed Assault Vest fallback clobbering its move/slot

and scan pointer during Encore normalization; the reviewer approved that bounded

combat fix at `late_gen_held_items.asm` SHA256

`f82f2d558cc0fc0b118fd56d0af01cd4858251716cc8ee45fc0e0363ba17b0c3`.



`public_replies.asm` builds possible and revealed move sets from public species,

level, evolution ancestry, TM/HM compatibility, egg moves and observations.

The earliest ancestor admits all its level-up moves because breeding's shared-

parent path ignores hatch level. This conservatively overapproximates breeding

eligibility; possible does not mean owned. Four trusted revealed moves close the

prior; transformed and unrevealed Smeargle sets remain broad. Struggle remains

possible because player PP is private. The builder preserves battle/party and

BaseData state and consumes no RNG.



The updated Gold ROM built successfully and all 17 targeted reply cases passed,

including level-5 Pidgey inheriting Quick Attack and Pidgeotto retaining inherited

Agility. Tests compare complete sets with an independent ROM ancestry graph,

check metadata/state preservation and vary hidden moves, PP, item and input.

Astra approved changes and retention decisions at source SHA256

`f3562c5a73386c4c29b2272f8958ae4261ba4c28227ebc4eaee24cf98ba9b967`.



`joint_action.asm` is an unpromoted conditional matrix draft. It compares legal

actions with weighted public replies and aggregates once before choosing a stable

best index. All 13 matrix fixtures pass: exhaustive independent aggregation,

all four action/reply traversal orders, stable ties, fast finishes, replacement

hazards, an empty replacement set, recharge waits, forced Struggle, and Encore

PP/Disable failures. Disable expiry uses combat's low-nibble counter rule;

counter zero with a nonzero disabled move still denies the action. A forced

failure can encounter confusion first, so WAIT retains transition uncertainty.

Known unresolved charging/continuous effects remain conditional. The context-

based far-call wrapper and WAIT routing are exercised through the matrix, with

direct calls to the original exchange entry serving as the aggregation reference.

Tests also check stack/context preservation, no live-state writes, no RNG and

hidden-player-state invariance. None of this verifies production integration.



The broad Smeargle case compares nine legal actions against all 254 replies,

with one revealed move and a total reply weight of 261. It passes but exposes

unacceptable runtime. ROM-cycle profiling measured 1,375,126,376 cycles before

neutral scaling shortcuts and 1,041,562,376 after (about 24% less). The remaining

cost is roughly four minutes of emulated time, so promotion is still blocked by

performance. Profiles include less than two frames of return-trap padding;

inclusive child timings overlap and must not be added to parent timings.

`profile_joint.py` reproduces the measurement; `joint_profile_before_identity.json`

and `joint_profile.json` retain the comparison. No replies or actions were removed.



Neutral scaling now avoids redundant Multiply/Divide calls. The quotient shortcut

preserves Multiply's low-24-bit input rule and Divide's zero remainder. All 60

direct comparisons against the original ROM arithmetic passed, including a

nonzero discarded high byte; see `check_identity_math.py` and `identity_math.json`.

All 758 Gold fixtures passed in `pokegold_joint_fixtures.json`, including the

previous damage/combat corpus and WAIT with confusion. All 12 applicable audits

passed in `joint_checks.json`. The no-cheat scan now includes the three new policy

files. The farcall HL audit recognizes `ad_address` as the full HL reconstruction

its macro definition supplies; four positive/negative boundary checks passed.

The Gold dev index was regenerated and documentation navigation checks passed.



No production selector has been switched to this matrix. Probability branches,

complete successors/future offense, production integration and practical runtime

remain required for stage 2/search work; stages 3–5 and the full goal are unfinished.





## Prepared context and damage reuse follow-up



The matrix now prepares the owned action and speed facts once per candidate.

Its optional 133-byte exchange context preserves the original 81-byte entry

contract. Single-hit raw damage endpoints are reused only when the refreshed

HP-dependent flags match; Super Fang, False Swipe and multihit moves are excluded.

Final damage is capped against current target HP. Priority uses the shared move

priority helper, including Vital Throw. Unchanged HP skips cancelling fraction

calculations while retaining material checks. All replies and weights remain.



The final broad-case profile is 623,729,576 cycles: 40.1% less than the

1,041,562,376-cycle start of this follow-up, and 54.6% less than the original

1,375,126,376. This is still about 149 seconds of emulated time and is unsuitable

for production. The earlier four-minute profile is preserved in

`joint_profile_before_prepare.json`; `joint_profile.json` now contains the latest

measurement. Historical manifests bind their original states.



Normal Gold and Silver builds passed; each passed all 773 fixtures in

`pokegold_prepared_fixtures.json` and `pokesilver_prepared_fixtures.json`.

This includes all 14 matrix fixtures, cache invalidation/reinitialization,

original-context canaries, priority, heal/recoil caps and comparison across 32

order/endpoint/hit branches. All 12 audits in `prepared_checks.json` passed;

documentation navigation and `git diff --check` passed. Debug/trace binaries were

not rebuilt in this follow-up, so their existing memory audit evidence is

historical. The current bounded state is recorded in `prepared_manifest.json`;

review disposition is in `prepared_review.md`.



Production integration, practical runtime, complete probabilistic successors,

future offense/search and stages 3–5 remain unfinished. This optimization does

not complete stage 2 or the roadmap.





## Single-hit reuse and local chart follow-ups



Single-hit endpoint reuse is approved in `single_hit_review.md` and reduced the

broad-case profile from 623,729,576 to 464,461,544 cycles. Both ROMs passed all

773 fixtures, including 298 adapter comparisons with the general two-kernel

range path; see `single_hit_progress.md` and its manifest.



The subsequent chart increment emits the existing authoritative TypeMatchups

rows under a second label beside the damage kernel. Three direct byte reads

replace repeated banked reads. Both ROMs contain 332 identical chart bytes and

the parser still returns the same 110 entries (`chart_mirror_check.json`).

The data, Foresight sentinels, Majesty handling, per-row rounding, Struggle and

early-immunity behavior are retained. This adds ROM bytes and no persistent RAM.



The broad nine-action/254-reply profile now measures 359,827,768 cycles versus

464,461,544 before the chart change (22.5% reduction), with the same exhaustive

score comparison passing. This remains about 86 seconds of emulated time and

prevents production promotion. Baseline: `joint_profile_before_chart.json`;

current: `joint_profile.json`. All 12 `chart_checks.json` audits and documentation

navigation pass. The independent final disposition and complete fixture evidence

are recorded in `chart_review.md` and `chart_manifest.json`. Gold and Silver

each passed all 773 fixtures with zero errors.

Normal Gold/Silver builds pass; debug/trace evidence remains historical.



A concrete next semantic gap is equal-priority speed ties: the current matrix

uses a single opponent-first conditional branch. Weighting both feasible orders

without changing total reply mass or rounding early is proposed, not implemented.

Unknown order mechanisms must remain explicit uncertainty. Accuracy/survival,

full successors, retained future offense, practical runtime and stages 3–5 remain

unfinished; these optimizations do not complete the roadmap.





## Modeled speed-tie valuation



The matrix now averages both orders for equal-priority ties in prepared public

speed estimates. This does not establish the player's private true Speed.

Quick Claw and copied-speed uncertainty do not receive an invented 50/50 model.

Switches, replacements, forced waits, unequal priorities and unequal full-word

speeds retain a single conditional exchange. All existing uncertainty flags

remain: an expectation is not a deterministic guarantee.



Each tied order receives the reply's original weight; a non-tied exchange

receives twice that weight. This preserves total prior mass for each reply.

The matrix accumulates before dividing once, without rounding individual reply

means. Even assigning revealed weight to every possible reply, total event mass

is at most 4064 and utility below 2048 fits the existing 24-bit accumulator.

No context expansion, persistent RAM or RNG is introduced. Traversal flag bit2

reverses tie-order traversal for invariance checks.



All 19 matrix fixtures pass. Five new cases cover mixed priorities and prior

weights, lethal ties, Quick Claw, Transform, a high-byte speed difference and

premature-rounding sensitivity. The rounding case gives 1049 when accumulated

correctly versus 1048 if each reply is rounded first. Focused cases compare all

eight action/reply/event traversal combinations and directly check classifier

purity. The exhaustive reference independently derives admission from legacy

exchange speed facts, combat priority, public copy state and known own items;

it invokes the original explicit order branches and never uses the new

classifier to define expected scores.



The broad profile is 361,232,248 cycles (about 86 seconds, 0.39% over the previous

359,827,768). The focused four-action/five-reply tie case is 4,494,340 cycles

(about 1.07 seconds). These are bounded ROM measurements with return-trap padding,

not production turn-time guarantees. `profile_joint.py` now accepts `--case` and

`--output` to reproduce both measurements (`joint_profile.json`, `tie_profile.json`).

All 12 `tie_checks.json` audits and documentation navigation pass; normal Gold

and Silver builds pass. Complete ROM results and final independent review are

recorded in `tie_manifest.json` and `tie_review.md`. Gold and Silver each passed

all 778 fixtures with zero errors. Debug/trace verification remains historical.



Accuracy, negation/survival events, complete projected successors, retained

future offense, practical worst-case runtime and stages 3–5 remain required.

The new matrix is still unpromoted and the full roadmap remains incomplete.





## Exact accuracy event weights



Both actors' public accuracy now contributes exact hit/miss event weights.

Byte 255 means 256/256; other values use their /256 threshold. Zero-mass events

are skipped before evaluation and uncertainty aggregation. Each reply retains

its original prior through total event mass `2 * reply_weight * 65536`, including

latent outcomes when a knockout prevents the later action. Switch/wait/replacement

owned actions and absent replies have certain latent hits to avoid duplicates.



The numerator is five bytes; reply/order mass remains two bytes. After every

reply has accumulated, the existing division uses the numerator's top three

bytes. This is exact because `floor(T / (65536*M)) = floor((T >> 16) / M)` for

positive integer M. There is no per-event or per-reply rounding. Context size

increases from 260 to 265 caller-owned bytes; no persistent memory is added.

Traversal bit3 reverses hit-event order in invariance tests.



The incoming accuracy lookup initializes only the fields consumed by the shared

accuracy routine and avoids damage-stat estimation. Its contract does not

promise a complete damage context. Incoming adapter fixtures poison all 51

scratch bytes before comparing its answer with the complete public builder.

Stages, identification, Fly/Dig, known own items, weather and Flying accuracy

remain governed by the same source routine. The prepared outgoing template and

AV fields survive accuracy capture.



Six new matrix cases cover mixed accuracy/tie/prior weights, healing/recoil/drain,

missed Selfdestruct on either side, a reply interrupted by a knockout, impossible

hits and retained Focus Band uncertainty. Focused cases compare all 16 traversal

orders, explicit branch values, exact full event mass, state preservation and

hidden-state invariance. `check_probability_math.py` passes 142 direct ROM

checks of threshold/complement decoding, four-byte products and global division

boundaries, including nonzero fractional bytes and high numerator bytes.

Unmodeled crash, status, negation/survival and secondary effects stay uncertain;

accuracy weighting does not resolve those effects.



The final broad profile is 438,057,308 cycles (about 104 seconds), versus

361,232,248 before accuracy weighting. Avoiding complete damage-context creation

for accuracy capture reduced the first implementation's 528,505,824 cycles.

The focused mixed case is 11,938,088 cycles (about 2.85 seconds). These measurements

cover the expanded conditional model and still prevent production promotion.

Artifacts: `joint_profile_before_accuracy.json`,

`joint_profile_accuracy_full_capture.json`, `joint_profile.json`, and

`accuracy_profile.json`. All 12 `accuracy_checks.json` audits, normal Gold/Silver

builds and documentation navigation pass. Complete fixture results and final

independent review are recorded in `accuracy_manifest.json` and

`accuracy_review.md`. Gold and Silver each passed all 784 fixtures with zero

errors; debug/trace evidence remains historical.



Full successor state, retained future offense, practical runtime, production

integration and stages 3–5 remain unfinished. The roadmap is not complete.





## Projected defensive boosts



The shared direct/prepared exchange now executes Harden, Withdraw, Barrier,

Acid Armor and Amnesia after the actor can act. A faster defensive boost changes

the later attack's damage; a slower boost records its resulting defense without

retroactively reducing damage. A knockout still interrupts the later action.

Defense Curl and effects with secondary boosts remain outside this transition

scope and retain explicit uncertainty.



The eight-byte sparse successor extension has one four-byte record per actor,

with each record containing axis (zero unchanged, one Defense, four Special Defense),

stage and effective stat before screens/items. One selected move per actor can

change only one of these axes in this model. Both records reset on every exchange,

including prepared event reuse. Direct context size is 89 bytes, prepared size

141 and matrix size 273; existing fields through branch byte 80 stay in place.

All callers migrate together. No persistent WRAM or save layout changes.

Future multiple-command or multi-action successors must expand this contract.



Stat arithmetic follows combat's raw-stat recalculation, integer rounding and

999 cap, including the unusual one-stage rollback after a failed two-stage

raise when the effective stat was already 999. Unchanged axes remain implicit:

turn order is already selected and the booster has no second action here.

Projected defense replaces the adapter value before the existing screen and

known defender-item multipliers are reapplied once. A matching player defense

override bypasses prepared raw endpoints; a different category can reuse them.



Validation includes 364 paired stat-command checks, 54 paired exchange cases

covering both sides, orders, categories, screens, Eviolite, Metal Powder, caps

and ties, and an exhaustive matrix case with all event traversal orders.

Direct/prepared comparisons include the sparse records and repeated event reset.

Reference workspaces now use the separate 360-byte attribute map; context bounds

and reserved branch-bit canaries remain checked. Shared Python layout constants

also keep the 142 probability arithmetic checks aligned with the larger matrix.

The focused matrix profile is 8,848,220 cycles (about 2.11 seconds), with no

production promotion implied. Full successors, retained future offense, practical

runtime, production integration and roadmap stages 3–5 remain unfinished.

Current regression/audit totals and the final independent disposition are recorded

in `defense_manifest.json` and `defense_review.md`.

