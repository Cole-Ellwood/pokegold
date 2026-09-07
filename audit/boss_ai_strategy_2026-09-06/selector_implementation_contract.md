# Exact selector prototype implementation contract

Prepared 2026-09-06. This is a design contract, not implemented assembly.
Amended after [Pro's final review](selector_preflight/pro_final_review.md):
explicit bridge marshaling/read-set restoration and narrow first-batch checks.
Use with [the roadmap](two_second_roadmap.md) and
[preflight readiness/evidence](selector_readiness.md).

## Scope and reference

Implement a private BOSS_AI_REFERENCE-only hybrid selector. Preserve the current
conditional public battle model, original candidate identities, all twelve output
slots, exact totals/mass/scores/uncertainty, and no RNG consumption. The complete
gameplay policy and exhaustive evaluator remain unchanged. The frozen preflight
ROM is the offline regression oracle; the direct unprepared exchange remains the
pair-level semantic oracle during development.

The first slice supports identity transitions, ordinary/fixed/level damage,
native incoming conservative KO after its gates, recovery, owned Life Orb then
drain, and switch/replacement/wait orchestration. Other families initially use
whole-pair fallback. No helper or descriptor may implement additional combat
behavior simply because the compact executor could support it.

## Entry, results, and banking

Private proposed symbol: `BossAI_ComparePublicActionsFastPrototype`.

Inputs: DE points to the owned 472-byte workspace (initial harness location
$c900); A is ordinary decision 0 or replacement decision 2; B bits 0..3 reverse
actions/replies/order/events for tests. Higher traversal bits are reserved and
must not silently enable legacy table modes. Inputs remain stable for the call.

The harness directly selects the entry bank and masks IE/clears IF before
invocation. Require exclusive animation scratch, closed SRAM, no callbacks,
graphics transfers, decompression, or RTC work during live scratch. The selector
does not itself disable interrupts for a production decision.

Return: DE and SP preserved; BC is best integer score (0 if none); carry means
at least one legal candidate. AF other than carry and HL are scratch. **A is not
an authoritative return value across FarCall.** Obtain the selected index from
the exported result block. The eventual public ROM0 wrapper must reload A from
that block after FarCall and preserve the declared BC/carry result. Test the real
wrapper separately when it exists; direct harness calls do not test its ABI.

Cross-bank input marshaling is also mandatory: the farcall macro replaces A and
HL with the destination bank/address before entry. Every cross-bank service must
explicitly marshal any A/HL inputs and A outputs through memory or a same-bank
shim. Use BossAI_ValuePublicExchangeFromContext for direct pair fallback. Give
BossAI_EnumeratePublicActions a shim that reloads decision kind before its local
call; a plain farcall cannot pass replacement kind in A. The future public
wrapper must marshal its decision-kind input as well as reload the returned
index, preserving carry during result-address calculation.

SRAM contract: OpenSRAM with bank 0, then CloseSRAM on every return after ownership
is acquired, including rejected/incomplete early exits.
OpenSRAM/CloseSRAM do not track the prior bank/enable state. Do not promise to
restore an unknown prior SRAM bank. FarCall restores hROMBank but uses A,
wTempBank, and wFarCallBC; FarCopyBytes also uses banking scratch. Ordinary
math HRAM and these bank globals are allowed scratch, not retained state.

Result records are big-endian, original-index ordered:

| Record offset | Bytes | Meaning |
| --- | ---: | --- |
| 0 | 5 | Complete numerator T, before fractional-byte removal |
| 5 | 2 | Mass M, with implicit denominator factor 65,536 |
| 7 | 2 | Integer score floor((T >> 16) / M) |
| 9 | 1 | Uncertainty |

Indices 0..3 are exact active PP slots; 4..9 are party slots; 10 is forced
selected action, including its sentinel-to-wait conversion; 11 is forced wait.
Invalid records use numerator/mass 0, score $ffff, uncertainty $ff. Never infer
legality from a subtotal. Candidate modes are alternatives: at most four live
active plans and five bench plans, nine candidates, despite twelve index slots.

After the final producer/fallback call, copy the 120 result bytes to WRAM
offsets 0..119, then export summary at offsets 120..127:

    120 best index ($ff if none), 121 best uncertainty ($ff if none)
    122..123 best score (0 if none), 124..125 legal-index mask
    126 completion/backend status, 127 contract version (initial version 1)

Status values: 0=completed native-only, 1=completed with pair fallback,
2=completed external reference restart, $ff=rejected/incomplete. An empty legal
set can be a completed status with carry clear. A rejected or incomplete attempt
must not expose a partial vector as a completed result. Exact out-of-domain
whole-selector restart occurs only after
discarding all new live SRAM state; copy/export the reference result through an
explicit compatibility adapter when that path is implemented.

That restart adapter must collect per-candidate totals before the old selector
reuses them, or obtain them by exact aggregation. Its final score vector alone
cannot reconstruct the complete numerators required by this contract.

## Memory ownership and lifetimes

| WRAM offsets | Bytes | Owner while evaluation is live |
| --- | ---: | --- |
| 0..323 | 324 | Existing prepared producers; fallback uses only first 89 |
| 324..331 | 8 | Candidate enumeration |
| 332..398 | 67 | Reply set |
| 399..446 | 48 | Current reply record |
| 447..471 | 25 | Control |

Control fields, in order: decision kind, traversal flags, defender slot,
candidate kind, live-plan count, action cursor, reply cursor, reply ID, reply
weight, phase, order descriptor, event descriptor, weather, TimeOfDay, LinkMode,
two bank bookkeeping bytes, two reserved bank/lifetime bytes, lifetime flags,
two-byte legality mask, two-byte total reply weight, backend flags. Reserved
bytes do not imply readable hardware SRAM-bank state.

| SRAM range | Bytes | Owner |
| --- | ---: | --- |
| $a000..$a17f | 384 | Owned HP valuation |
| $a180..$a27f | 256 | Player HP valuation |
| $a280..$a2f7 | 120 | Results |
| $a2f8..$a3f7 | 256 | Four active plans, 64 bytes each |
| $a3f8..$a447 | 80 | Two actor views, 40 bytes each |
| $a448..$a477 | 48 | Two continuations, 24 bytes each |
| $a478..$a4f7 | 128 | Producer bridge/variant staging |
| $a4f8..$a5ff | 264 | Working storage |

The last 264 bytes reserve 24 for group masses/flags, 32 for wide arithmetic,
48 executor working bytes, 24 for eight outgoing defensive variants, 24 for
common sums, 48 for three 16-byte base states, and 64 uncommitted bytes.
Do not assign those 64 bytes without updating the live-range inventory.

Adopt Pro's explicit field maps for the 64-byte active plan, 48-byte reply,
24-byte continuation and 40-byte actor view from
[the preserved review, section 3](selector_preflight/pro_second_review.md).
Amounts occupy tagged payloads, never untagged unions. Producer exports copy
values, not pointers into AD. Descriptor pointers are same-bank only and cannot
outlive or assume a bank selection. A bridge call may overwrite all first 324
bytes; no persistent plan, sum, or continuation may rely on their contents.

The continuation's two-byte first-event mass is an unweighted original-event
mass in 0..256. Grouped masses remain in the reserved three-byte group fields;
never copy a grouped mass such as 72,192 into that continuation field.

Implemented allocation (2026-09-07, ordinary orchestration; supersedes the
provisional control-field list above where they differ):

- WRAM control 447..471: 447 decision kind, 448 traversal flags, 449 defender
  slot / bench cursor, 450 bench count, 452 plan cursor, 453 reply cursor,
  454 replies left, 455 reply weight, 456 unary record index ($ff none),
  457 unary kind, 458 move-plan flags, 459 unary flags, 461..464 plan index map
  (original result index per plan slot, $ff unused), 467..468 legal mask,
  469..470 total reply weight, 471 backend status. Bytes 451, 460, 465..466 are
  unused. No saved-bank bytes exist: the selector never reads hardware bank
  state.
- Common sums $a578..$a58f: $a578 pair total (5), $a57d shared incoming sum
  (signed 32), $a581 mass M, $a583 entry delta (signed 16), $a585 unary
  baseline `2*65536*(1024+entry delta)` (5), $a58a accumulation temporary
  (5), $a58f spare.
- Actor view extras: own/player speed at actor 14..15, item class at own 32
  (1 = Quick Claw), setup flags at own 35, speed mode at own 36 (bit0 unknown
  public order). Bench defenders overwrite own start HP/Phi with the
  post-entry values after the entry delta is recorded.
- Producer bridge: $a48f Quick Claw class exported by
  `BossAI_FastPrepareActiveFacts`; $a490 regime mask compiled for the current
  reply; $a491 family opcode, $a492 producer-input patch kind, $a493 delta
  store flag (compile-time only).
- Later 2026-09-07 additions: control byte 460 reply regime mask, 465 reply
  identity, 466 order descriptor of the pair being evaluated; $a58f incoming
  regime fault latch; $a53f executor opcode; $a530..$a53c family scratch
  aliasing the damage-script inputs (consumed before the script runs);
  $a5c0..$a5d7 scalar pair gate caches; $a5d8..$a5df native compile
  temporaries (bytes 5..7: family opcode, delta flag, halved defense);
  $a5e0..$a5ff per-defender reply facts; $a590..$a5bf and $a4f8..$a50f
  physical formula-base cache; special base cache in the dead outgoing
  template bytes at context 89..190. Reply record bytes 7, 8, 23 and 26 hold
  per-regime maximum-minus-minimum deltas for multihit and False Swipe
  replies. Later on 2026-09-07: `$a4f8..$a50f` holds the eight defensive
  variants (two 3-byte slots per plan: raw minimum at the start regime, then
  range / supported / special-axis / valid bits), `$a4b4..$a4b7` the amount
  override the boost pair hands the owned executor (flag exactly 1 while
  live), and the fallback evaluators live in a separate bank behind far
  entries. The group-mass area and the base-state area remain unassigned.

Lifetime sequence:

1. Enumerate candidates/replies before live SRAM records where possible.
2. Establish bank 0 and initialize all records/control explicitly.
3. Prepare actor/owned plans through the legacy bridge; copy outputs immediately.
4. Stream replies and variants; consume each temporary correction before reuse.
5. Perform normalization and selection; no later producer call is permitted.
6. Export records over dead producer scratch; close SRAM and return.

Consume the active defender's shared 512*B into its plans before reusing common
sums or actor views for a bench defender. Consume each switch's post-entry unary
sum before advancing the bench slot. Traversal reversal must preserve this scope.

Never call PrepareHPValues or set AV_PREPARED_HP_F under this allocation. Legacy
HP tables overlap the new records. Do not call the old full joint selector while
new control is live. A helper with physical sScratch writes is forbidden in the
live interval even if SRAM is temporarily closed/reopened.

Fresh reference map establishes wBattleAnimTileDict=$c900, wBattle=$cad8,
sScratch=$a000, and sPartyMail=$a600. New entry/table/code placement still needs
assembly assertions and fresh maps after implementation. A floating ROMX section
has space in the current reference; no new fixed bank number is prescribed.

## Numerical contract

At action boundaries for valid non-reviving initial states:

    Phi(W,M,h) = 0 if h == 0 else 2*W + floor(W*h/M)
    V = Phi_own - Phi_player
    utility = 1024 + V(final) - V(initial)

Own weight is 128, or 192 for the designated win condition; player weight 128.
Same-action transient zero followed by drain is allowed. No irreversible faint
latch may be introduced. Stop another action only after the first action finishes.

Decode accuracy byte 255 as 256; other bytes retain their numeric value. Original
hit/miss masses remain the authority for uncertainty and fallback. For scoring,
identity-on-miss families use effective mass z=decoded accuracy, recovery/boost
z=256, and a certified globally identity transition z=0. Selfdestruct is special.

An identity certificate must hold over every relevant continuation. Recovery at
full initial HP, zero standalone utility, current overkill, or current immunity
alone does not establish that certificate. Execution predicates and effective
probabilities must retain their reference dependency scope.

For an active transition define delta=V(active(initial))-V(initial). For the
general two-event representation, mu=p*delta_hit+(256-p)*delta_miss, without any
division. Let W_R=sum reply weights, M=2*W_R, D=M<<16. Initialize each active plan:

    T[a] = 1024*D + (M<<8)*mu[a]
    B = 0
    for each reply r:
        B += weight[r]*mu[r]
        for each active plan a:
            resolve actual reference order descriptor
            # one order with k=2; genuine modeled tie has two with k=1
            if both transitions normalize:
                K = sum(k*(V(active_active_final)-V(initial)-delta[a]-delta[r]))
                T[a] += weight[r]*z[a]*z[r]*K
            else:
                N = complete unweighted special/fallback pair numerator
                baseline = 2*(65536*1024 + 256*(mu[a]+mu[r]))
                T[a] += weight[r]*(N-baseline)
            F[a] |= reachable_flags_for_actual_positive_mass_paths
    T[a] += 512*B

Combine tie corrections before multiplying. Zero effective mass skips numerical
interaction, not flag processing. For grouped replies use three-byte hit/miss
masses H=sum(w*p), Q=sum(w*(256-p)); shared moment H*delta_hit+Q*delta_miss.
Use effective group mass Zg=sum(w*z) for correction z[a]*Zg*K: Zg=H for
identity-on-miss groups, but Zg=256*Wg for deterministic recovery/boost groups.
Keep original H,Q for event semantics and special handling. The group key must guarantee the same
continuation function and order behavior; preserve gated flag unions separately.

Switches: T=D*(1024+entry_delta)+512*sum(w*mu_postentry). Entry KO skips execution,
not reply mass. Wait has no entry damage and retains its action-check flags.
Replacement uses one absent reply, weight 1, M=2, T=2*65536*(1024+entry_delta),
and no open-prior flag.

Switch fallback replaces the switch baseline using post-entry reply moments;
never apply the active-action replacement formula with a pre-entry reply moment.

| Quantity | Conservative bound | Required width |
| --- | ---: | --- |
| Standalone delta | absolute <=960 | signed 16-bit |
| Standalone moment | absolute <=245,760 | signed 24-bit |
| One order correction | absolute <=1,920 | signed 16-bit |
| Combined order correction K | absolute <=3,840 | signed 16-bit |
| z[a]*z[r] | <=65,536 | unsigned 17-bit or wider |
| Weight<=8 individual correction | absolute <=2,013,265,920 | signed 32-bit |
| Shared incoming moment | absolute <=69,304,320 when W_R<=282 | signed 32-bit |
| Group H or Q | <=72,192 | unsigned 24-bit |
| Group products / T | prove within 40-bit ring/final output bound | 40 |

Widen before shifting or multiplying: M<<8 can reach 144,384 (18 unsigned bits),
512*B has absolute bound 35,483,811,840, grouped corrections 70,967,623,680, and
the final T is at most 73,333,211,136 under the stated domain. A conservative
absolute sum of initialization/corrections/shared terms is 179,784,646,656, within
signed 40 bits. These bounds do not justify narrowing intermediate factors to 16 bits.

Reveal storage has four slots; unique revealed replies receive weight 8, other
possible replies weight 1, so W_R<=254+7*4=282 and M<=564 for valid construction.
If caller-supplied sets bypass construction, these tighter bounds must be checked
or replaced with the broader reference bounds. Sign-extend negative products;
never zero-extend signed 32-bit into 40-bit. Compare only finalized integer scores.

Keep complete T, then score=floor((T>>16)/M); no intermediate probability
division, expected-HP substitution, numerator-based winner choice, or winner-only
early exit when the output contract requires all twelve records.

## Uncertainty and executor obligations

Uncertainty follows decision/setup, action-check reached, allowed dispatch,
damage-prefix reached, positive-mass hit/range reached, and order resolution.
Confusion/paralysis flags can arise before a later denial. Recovery/boost dispatch
precedes damage-prefix flags. Rest adds transition uncertainty only for positive
modeled recovery. Raw endpoints can differ even when both capped losses match.

Process at most two first-action successor classes per order. Merge equal
continuations only when the next program and every field it reads agree, summing
mass and retaining reached flag unions. A terminal utility match permits terminal
merging; it does not establish continuation equality. Quick Claw/copied-speed
uncertainty is not a new random tie order.

Keep tentative pair flags local until native execution or fallback owns the
complete pair. Numerical baseline replacement cannot undo a prematurely ORed
uncertainty bit. On fallback, discard speculative native flags and commit only
the exact fallback pair's reached flags.

Primitive order comes from action_value.asm/action_facts.asm:

- Denial/check prefix, boost/recovery/switch-Pursuit dispatch, then damage prefix.
- Selfdestruct self-faint precedes miss/failure return; its amount uses pre-faint
  attack facts and the same action completes before interruption.
- Successful selected damage, known after-hit item, then recoil/drain. Use raw
  amount operands and the actual current HP at each primitive.
- Life Orb/helmet zero followed by drain is legal within the modeled action.
  Dual-Steel recoil can round to zero; mono-Steel cancels recoil.
- Unsupported incoming damage removes remaining own HP only after earlier gates;
  no normal after-effects are appended. Unsupported own damage remains its own
  reference transition. Preserve unsupported multihit/item combinations.
- Multihit advances HP per hit, stops at KO and reevaluates Ice regimes; preserve
  both raw range paths where needed, without assuming raw endpoint ordering.
- Preserve strictly 3*HP<max and 2*HP>max predicates and reference finite-width
  behavior outside the ordinary HP domain.

Recovery records store the uncapped quota derived from max HP/effect/weather/
TimeOfDay/LinkMode, then cap by missing HP at execution. ContextRecovery returns
current-state capped gain, not that quota; full HP and zero HP both return zero.
Do not use either state to infer a reusable quota from its output.

Translate actual exchange control flow: do not add a Substitute gate to the
single-hit drain or Life Orb path because a helper comment mentions eligibility.
The frozen exchange does not apply that extra gate. Helmet has its own explicit
Substitute rule, which remains distinct.

## Producer bridge and fallback

Legacy bridge may use PreparePublicAction, PrepareIncomingActor,
BuildPreparedIncoming/PreparePublicReply, PublicDamageRange, and scalar helpers.
PreparePublicAction invalidates its actor/accuracy/outgoing epoch. Incoming
construction overwrites AD; PublicDamageRange returns maximum through DE.
Save the context pointer. Never use the last prepared action's priority/accuracy
as the facts for a different active plan.

The direct fallback uses BossAI_ValuePublicExchangeFromContext across banks,
with its 89-byte prefix and prepared bits disabled. Populate the context selectors
before the call; FromContext loads A/B/C/H/L inside the destination bank.
Enumerate only original positive-mass hit/miss and actual orders;
produce the complete pair numerator and union of flags. Replace the pair baseline
exactly as above, with no extra shared-moment subtraction later. Restore
the complete read set of the next legacy helper after fallback, not only
slot/kind/move/reply/branch. Compact records remain authoritative for new order
and accuracy work. Before invoking a prepared service, reconstruct or revalidate
its required prefix, speed-mode bits, cached speed words, outgoing facts, and
preparation epoch. Do not preserve all 324 bytes blindly around every fallback;
track valid producer state and rebuild what the next call actually reads.
Numerical baseline replacement does not recover flags; retain fallback flags
under their actual reachability.

The first implementation must prove this limited footprint with canaries.
The old complete selector is allowed only as an external restart/oracle after
the new live allocation is discarded, never as an inner-loop service.

## HP and damage backend decisions

HP representation mode is explicit per actor. Direct bytes fit when M+1 is no
larger than that actor's reservation; use them for M<W. Rank8 requires M>=W and
2*(floor(M/8)+1) bytes. It fits owned M<=1535 and player M<=1023. Store block base
and a seven-increment mask; lookup uses same-bank popcount of masked increments.
Construct from threshold events. Wider domains use W 16-bit thresholds, including
duplicate thresholds, and measured search costs. Handle h=0/full/unchanged without
unnecessary lookups. No arithmetic code is implemented by this document.

For incoming ordinary bases, schedule defender -> runtime category/Selfdestruct
-> increasing power group -> reply -> active plan. Preserve joint stat truncation,
byte extraction, Selfdestruct defense adjustment, zero guards, and item identity
assumptions. Up to three 16-byte recurrence states support base/Def+1/Def+2; special
needs base/SpDef+2. Stage outgoing defensive variants separately, at most eight
for four move plans under the current recognized boosts.

Current catalog counts reproduce 21/19/2 power groups, all multiples of 5. For
eligible normalized incoming configuration, compute divmod(5*K*A,50*D) once and
advance quotient/remainder in five-power steps, emitting only requested bases.
Assert generator eligibility and use direct-base calculation for other inputs.
Do not apply incoming item simplifications to outgoing arithmetic without proof.

Raw/imported stat limits are not post-modifier operand limits. Reflect can turn
defense 512 into 1024: preserve the reference's single joint quartering, low-byte
extraction, and defense-zero guard. Do not clamp back to 999 or repeatedly shift
until a byte fits. Pin this case before replacing amount producers.

Specialize finishing in original order, with zero/minimum-one/cap behavior,
Foresight, duplicate types, Struggle and Dragon substitution preserved. Selected
raw amount plus exact range-difference metadata may replace unused endpoints only
for proven families. The ordinary d>=2 variation shortcut is not a general rule
through saturation, False Swipe, postroll changes, or multihit.

## Disjoint development allocations and stop conditions

These are targets from Pro's second review, not measured native performance:

| Phase | T-cycle target |
| --- | ---: |
| Entry/public facts/actors/legality/replies/accuracy | 650,000 |
| Base arithmetic | 650,000 |
| Finishing arithmetic | 1,360,000 |
| HP representation construction | 400,000 |
| Standalone transitions/valuation | 800,000 |
| Classification/order/reachability | 600,000 |
| Scalar interactions | 1,460,000 |
| Probability/wide accumulation | 900,000 |
| Multihit progression | 430,000 |
| Normalization/selection/export/banking | 100,000 |
| Native target | 7,350,000 |
| Integration allowance | 750,000 |
| Combined target / remaining to two seconds | 8,100,000 / 288,608 |

Count each cycle once. Use bank-qualified host hooks, not a new in-ROM logging
system. Measure the actual intended HP lookup and scalar executor in the first
prototype. Separate old producer and whole-pair fallback costs. A fall in total
cycles caused by skipping required semantics is a correctness failure.

The simple order bound is 2,032; current base-priority catalog tightens to 1,984 and
certified no-op skipping suggests 1,324 nontrivial order units. Local extraction
supports the simple catalog counts. Pro's 1,228 finishing configurations and 3,010
multihit-step envelopes remain unverified hypotheses until generated dependency
and compatibility checks reproduce them. Roughly 1,100 cycles per scalar unit or
finishing configuration and 140 per multihit step are early targets under those
counts, not measured ceilings for individual paths.

If native non-producer work exceeds 7,638,608 on an in-domain adversary, revise the
design before optimizing amounts; if above 8,388,608, free preparation cannot
rescue the target. Persistent phase overruns trigger transfer-function or shared
successor factoring for the expensive family. No unbudgeted in-domain fallback
is permitted at performance acceptance. Interrupt-enabled production requires its
own ownership, latency and ABI gates; harness masking is not an integration fix.
