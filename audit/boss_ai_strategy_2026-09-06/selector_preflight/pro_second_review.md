## 1. Implement the hybrid—but broaden the factored kernel

**Choose option 3: algebraic corrections backed by a compact sequential executor. The important revision is that factoring applies to substantially more than ordinary damage.**

The ordinary kernel should handle one-sided damage algebraically. The complex executor should handle the remaining *deterministic interaction*, not enumerate the whole hit/miss exchange again.

### The stronger identity

For any action whose miss leaves the modeled state unchanged, write its transition as:

$$
A(s)=
\begin{cases}
s & \text{inactive event}\\
A_H(s) & \text{active event}.
\end{cases}
$$

Let its active probability mass be \(p\), out of 256. For two such actions, define their standalone changes:

$$
a=V(A_H(s))-V(s),\qquad r=V(R_H(s))-V(s).
$$

For order \(o\), define:

$$
c_o=V(S_o(s))-V(s)-a-r,
$$

where \(S_o\) executes both active transitions in that order, including interruption checks.

Then the exact numerator for that order is:

$$
N_o=65536\cdot1024+256(pa+qr)+pq\,c_o.
$$

**Proof:** the inactive–inactive, active–inactive, and inactive–active outcomes are already represented by the standalone terms. Only active–active differs from their sum.

That proof does not require one-sided HP writes. It covers recoil, drain, Life Orb, Shell Bell, Helmet, False Swipe, Super Fang, and supported multihit—provided their inactive transition is identity. In the supplied code, damage-path miss checks precede damage and its after-effects. Selfdestruct explicitly violates that condition.  

Recovery and recognized defensive boosts can use the same framework with **effective active mass 256**, because their transitions occur before the accuracy branch. Retain the original accuracy separately; do not use this scoring normalization to rewrite uncertainty semantics. 

This produces the following boundary:

| Class                                                   | Scoring implementation                                                   |
| ------------------------------------------------------- | ------------------------------------------------------------------------ |
| Identity transition, including certainly denied actions | Standalone zero; no numerical correction                                 |
| Ordinary one-sided damage                               | Algebraic zero, KO, or HP-regime correction                              |
| Other identity-on-miss damage families                  | One compact active–active execution per required order                   |
| Recovery and defensive boosts                           | Deterministic active transition; same correction identity                |
| Selfdestruct                                            | Explicit two-event exception, heavily reduced by guaranteed interruption |
| Switch, replacement, wait                               | Separate unary/action-kind handling                                      |

I would **not** implement an all-pairs sequential interpreter first. It would test a more expensive architecture than the one you need. Nor would I write separate algebraic formulas for every recoil/item/recovery combination. The compact executor is the semantic backstop for those combinations.

The main revisions to my previous proposal are:

* Generalize factoring beyond ordinary damage.
* Combine both order corrections **before probability multiplication**.
* Replace the old memory layout.
* Stop committing to full power rows.
* Use a faster, compact HP representation rather than assuming binary threshold searches throughout the hot path.

I did not execute a ROM for this review. The current-source bundle explicitly contains pending changes and lacks fresh build/link-map verification; the timings below are therefore targets or conditional estimates, not measurements of that source revision. 

## 2. The first prototype

### Entry point and output contract

Add a private experimental entry such as:

```text
BossAI_ComparePublicActionsFastPrototype

Inputs:
    DE = the existing 472-byte decision scratch window
    A  = decision kind, using the existing ordinary/replacement convention
    B  = traversal-test flags
    SRAM closed
    public/owned decision inputs stable throughout the call

Outputs:
    DE preserved
    BC = best integer score
    A  = lowest original index attaining that score, or $ff
    carry = at least one legal candidate

    scratch[0..119]:
        12 result records, indexed by original action index

    scratch[120..127]:
        best index, best uncertainty, best score,
        legal mask, status/version bytes

    SRAM closed; required bank/caller state restored
```

Each result record should contain the **five numerator bytes, two mass bytes, two score bytes, and one uncertainty byte**. For invalid entries, retain the reference’s invalid score/flag convention and explicitly define unused numerator/mass fields as zero.

Do not require callers to reopen SRAM to obtain results. Copy the result block into the producer workspace only after the last producer call, then close SRAM.

### Smallest useful native slice

The first prototype needs both an inexpensive path and one genuinely difficult path. Otherwise it can establish ordinary-damage timing while telling you nothing about the compact executor.

Implement these initial native families:

1. Identity/no-modeled-state-change transitions, with their complete flag behavior.
2. Supported single-hit, HP-regime-independent one-sided damage, including fixed and level damage.
3. The incoming conservative KO transition, **after all preceding gates**.
4. Recovery, with a precomputed recovery quota.
5. Damage followed by drain, including the owned Life Orb-before-drain sequence.
6. Switch entry, replacement, and wait orchestration.

Initially route Selfdestruct, multihit, defensive overrides, and unimplemented item/recoil combinations through the exact pair fallback. Route a pair through fallback when a relevant HP-dependent amount variant is not yet represented.

The Life Orb/drain case is worth including immediately: it tests whether the executor distinguishes **an intermediate zero HP value from completion of an action**. A prototype that gets that boundary wrong is not a viable foundation.

### Producer and fallback boundaries

Keep verified amount producers temporarily:

* `BossAI_PreparePublicAction`, once while constructing each owned plan or defender epoch.
* `BossAI_PrepareIncomingActor`, at defender scope.
* `BossAI_BuildPreparedIncoming` / `BossAI_PreparePublicReply`, at reply scope.
* `BossAI_PublicDamageRange`, inside the producer bridge.
* Existing scalar recovery/entry helpers during preparation.

Add thin adapters that export standalone HP successors, selected raw amounts, range behavior, and gated flag metadata. Do not cache pointers into the mutable `AD` prefix.

For an unimplemented pair, call the **direct, unprepared exchange evaluator using its 89-byte prefix**, enumerate the original positive-mass events/orders, and obtain a complete pair numerator and flag byte. Subtract the baseline already assigned to that pair and add its exact replacement contribution.

Do **not** invoke the complete old joint selector in the middle of the new selector. Its metadata overlaps the proposed current-reply/control storage.

The direct evaluator masks out prepared-mode bits, whereas prepared execution depends on the candidate-specific outgoing template and cached state. That makes the direct prefix the cleaner fallback boundary. 

### Mutation hazards

These are concrete:

* `PreparePublicAction` resets the accuracy cache and replaces the prepared actor/outgoing epoch.
* Incoming construction overwrites `AD`.
* `PublicDamageRange` changes amount/output scratch and returns its maximum through `DE`; preserve the context pointer explicitly.
* Prepared accuracy/order helpers may read the **last prepared owned action**, not whichever active plan the new inner loop currently considers.
* Direct fallback changes `AV` fields. Restore the bridge’s slot/kind/reply/branch inputs before the next producer invocation.
* `PrepareHPValues` writes fixed SRAM addresses. It must not run under the new allocation.   

### Measurement and acceptance

Use bank-qualified PC hooks and the emulator’s emulated cycle counter. Place boundaries around preparation, standalone construction, classification/reachability, scalar corrections, multihit steps, probability arithmetic, fallback, and finalization. Charge nested work to exactly one category.

Do not allocate a large in-ROM profiling subsystem. Host-side counters can count records, order units, variant constructions, and fallback calls without consuming decision scratch.

Acceptance requires exact full outputs across the existing traversal variants, memory/caller preservation, and meaningful timing of both the ordinary and Life Orb/drain paths. A 45–50M total with legacy producers is neither required nor sufficient.

For structural timing, use the proposed record layout and an actual fast HP lookup. Subtracting a guessed future HP-lookup cost from an old-divider measurement is not validation.

## 3. A layout that can coexist with current producers

### Current source-defined sizes

The current definitions evaluate to:

```text
AD_CONTEXT_SIZE             51
AV_CONTEXT_SIZE             89
AV_PREPARED_CONTEXT_SIZE    324
AC_CONTEXT_SIZE               8
PR_CONTEXT_SIZE              67
JC_CONTEXT_SIZE             457
```

Thus the complete current joint context leaves **15 bytes**, not 88. The prepared producer workspace itself is 324 bytes; the remaining joint-selector metadata is not needed by the new traversal. These are arithmetic evaluations of the source definitions, pending linker assertions.    

### WRAM: exactly 472 bytes

Offsets are relative to `DE`.

| Offsets | Bytes | Lifetime                           |
| ------- | ----: | ---------------------------------- |
| 0–323   |   324 | Legacy prepared-producer workspace |
| 324–331 |     8 | Candidate enumeration              |
| 332–398 |    67 | Public reply set                   |
| 399–446 |    48 | Current compact reply              |
| 447–471 |    25 | Selector control                   |

The 25 control bytes can hold:

```text
0 decision kind       1 traversal flags
2 defender slot       3 candidate kind
4 active-plan count   5 action cursor
6 reply cursor        7 reply ID
8 reply weight        9 phase
10 order descriptor  11 event descriptor
12 weather           13 TimeOfDay
14 LinkMode
15..16 saved ROM-bank state
17..18 saved SRAM-bank state
19 lifetime flags
20..21 legal-index mask
22..23 total reply weight
24 backend flags
```

The actual banking interface must determine what those saved bank fields mean; reserving bytes does not establish that a hardware register is readable.

### SRAM: exactly 1,536 bytes

| Range         | Bytes | Purpose                                       |
| ------------- | ----: | --------------------------------------------- |
| `$a000–$a17f` |   384 | Owned HP-value representation                 |
| `$a180–$a27f` |   256 | Opponent HP-value representation              |
| `$a280–$a2f7` |   120 | Twelve result records                         |
| `$a2f8–$a3f7` |   256 | Four 64-byte active plans                     |
| `$a3f8–$a447` |    80 | Two 40-byte actor views                       |
| `$a448–$a477` |    48 | Two 24-byte continuations                     |
| `$a478–$a4f7` |   128 | Producer bridge / next-record staging         |
| `$a4f8–$a5ff` |   264 | Arithmetic, grouping, variants, working state |

**There is no power row in this layout.**

### Record definitions

Use big-endian words/totals to match the reference, with two’s-complement signed moments.

**Active plan, 64 bytes:**

```text
 0 original index         1 action kind
 2 owned slot             3 move ID
 4 transition opcode      5 original accuracy byte
 6 priority               7 can-act verdict
 8 check-prefix flags     9 damage-prefix flags
10 hit-path flags        11 setup flags
12 HP dependency mask    13 amount-valid mask
14 range-difference mask 15 support mask

16..31 amount payload, tagged by opcode:
       single-hit: selected raw amounts for up to four HP regimes
       multihit: per-hit min/max amounts for relevant regimes
       recovery/boost: opcode-specific parameters

32..35 standalone original-hit successor: owned HP, opponent HP
36..39 standalone original-miss successor: owned HP, opponent HP
40..41 signed hit delta
42..43 signed miss delta
44..46 signed standalone moment, denominator 256
47 standalone hit flags
48 standalone miss flags
49 defense axis
50 projected defense stage
51..52 projected effective defense
53..54 recovery quota
55..56 known item quota
57 recoil/Steel class
58 minimum hits
59 maximum hits
60..61 same-bank descriptor pointer
62 minimum postroll modifier
63 maximum postroll modifier
```

For deterministic recovery/boosts, original hit and miss successors are identical. For identity-on-miss damage, the miss successor is the initial state. Selfdestruct uses both.

**Current reply, 48 bytes:**

```text
 0 move ID                1 opcode
 2 original accuracy      3 priority
 4 can-act verdict        5 check-prefix flags
 6 damage-prefix flags    7 hit-path flags
 8 HP dependency mask     9 amount-valid mask
10 range-difference mask 11 support mask
12..27 tagged amount/semantic payload
28..31 standalone hit HP pair
32..35 standalone miss HP pair
36..37 signed hit delta
38..39 signed miss delta
40..42 signed standalone moment
43 minimum hits
44 maximum hits
45 recoil class
46..47 descriptor pointer
```

**Continuation, 24 bytes:**

```text
 0..1 owned HP             2..3 opponent HP
 4..7 owned defense override
 8..11 opponent defense override
12..13 selected raw amount
14..15 actual HP loss
16 flags
17 remaining-program/order tag
18..19 first-event mass
20 event identity
21 within-action phase
22..23 working regime/temporary
```

Only two first-action continuations are needed. Process orders serially and consume terminal contributions immediately. Do not retain four or eight terminal records.

**Actor view, 40 bytes:**

```text
 0..1 start HP       2..3 max HP
 4..5 start Phi      6..7 entry HP
 8..9 entry Phi
10..11 third-HP cut 12..13 half-HP cut
14..15 speed
16..19 physical/special attack
20..23 effective Defense/Sp. Defense
24..27 raw Defense/Sp. Defense
28..29 defensive stages
30..31 types
32 item class       33 status
34 value weight     35 setup flags
36 speed mode       37 HP-table mode
38 recoil class     39 item flags
```

A concrete allocation of the last 264 bytes is:

```text
24 current-group masses/flags
32 probability and wide-arithmetic temporaries
48 current terminal / executor working state
24 eight outgoing defensive variants, 3 bytes each
24 common sums
48 up to three simultaneous base-calculation states
64 spare, explicitly uncommitted
```

Grouped hit and miss masses occupy **three bytes each**. The shared incoming moment occupies four signed bytes. The 32-byte arithmetic area must provide five-byte operands/results for grouped products.

### Candidate count and physical ownership

Four plans are sufficient for legal candidate construction: ordinary moves, forced move, and forced wait are alternative modes, not six simultaneous active actions. With a valid current party index, at most five other party entries are considered. Thus nine is the maximum simultaneous legal candidate count, although twelve original-index output slots remain necessary.   

**Keeping the legacy HP tables does not fit this prototype.** They reserve 704 bytes each, overlapping the same decompression scratch. Replace that use, disable its prepared-table flag, and leave amount producers otherwise intact. 

SRAM safety remains unresolved until the repository audit covers bank helpers, interrupt handlers, callbacks, and math scratch. Run candidate/reply-set discovery before establishing live SRAM records when possible. A helper that can overwrite `sScratch` cannot be made safe merely by closing and reopening SRAM around it.

## 4. Exact accumulation and widths

Define:

$$
\Phi_{W,M}(h)=
\begin{cases}
0 & h=0\\
2W+\lfloor Wh/M\rfloor & h>0
\end{cases}
,\qquad V=\Phi_{\rm own}-\Phi_{\rm opponent}.
$$

This matches the reference at action boundaries for valid states without revival of an initially fainted actor. **Transient zero HP followed by same-action drain is allowed**; do not create an irreversible faint latch. The reference scores final HP/material, not intermediate faint events. 

Let:

```text
decode(255) = 256
decode(x)   = x otherwise
```

Retain original event masses for reference fallback and flags. Define an effective scoring mass `z`:

```text
identity-on-miss damage: z = decoded accuracy
recovery / recognized boost: z = 256
globally identity transition: z = 0
Selfdestruct: special two-event representation
```

For every action/reply, compute the standalone moment without division:

$$
\mu=p\Delta_H+(256-p)\Delta_M.
$$

For non-Selfdestruct normalized transitions, this is simply \(z\Delta_{\rm active}\).

### Active-move accumulation

```text
W = sum(reply_weight[r])
M = 2 * W
D = M << 16

for each legal active action a:
    T[a] = 1024 * D + (M << 8) * mu[a]
    F[a] = applicable decision/setup flags

B = 0                           # signed shared incoming moment

for each streamed reply r:
    build its standalone record
    B += weight[r] * mu[r]

    for each active action a:
        orders = exact_reference_order_descriptor(a, r)
        # One order with k=2, or two orders with k=1.

        if a and r have normalized identity-inactive transitions:
            K = 0
            for (order, k) in orders:
                c = exact_interaction_delta(a, r, order)
                K += k * c

            T[a] += weight[r] * z[a] * z[r] * K

        else:
            N = exact_special_or_reference_pair_numerator(a, r, orders)
            base_pair = 2 * (
                65536 * 1024 + 256 * (mu[a] + mu[r])
            )
            T[a] += weight[r] * (N - base_pair)

        F[a] |= exact_reachable_flags(a, r, orders)

for each active action a:
    T[a] += 512 * B
```

When either effective mass is zero, skip numerical interaction execution, but not applicable uncertainty processing.

For a tie, compute `c_own_first + c_reply_first` and multiply once. Do not perform two separate wide probability products.

### Switches, wait, replacement

For a switch, compute entry change \(e\), then evaluate reply moments relative to the **post-entry** state:

$$
T=D(1024+e)+512\sum_r w_r\mu_r^{\rm postentry}.
$$

Entry KO eliminates reply execution, but **does not eliminate reply mass**.

Wait has no entry change and no owned numerical action. Preserve its explicit `OwnCanAct` uncertainty invocation.

Replacement is different: the reference evaluates one absent reply with weight one. Therefore:

$$
M=2,\qquad T=2\cdot65536\,(1024+e),
$$

with no open-prior flag. Do not assign the full ordinary reply denominator to replacements.  

### Grouped masses

For transition-equivalent replies:

$$
H=\sum_r w_rp_r,\qquad Q=\sum_r w_r(256-p_r).
$$

Then:

$$
B_g=H\Delta_H+Q\Delta_M.
$$

For an identity-on-miss group, its correction is:

$$
z_a H K.
$$

For a deterministic group, replace \(H\) by \(256W_g\). For Selfdestruct groups, retain both \(H\) and \(Q\).

### Width proof

The opponent’s potential lies in \([0,384]\); the owned potential lies in \([0,576]\). Consequently \(V\) spans at most 960 units.

| Quantity                       | Bound                                     | Storage                  |                         |           |
| ------------------------------ | ----------------------------------------- | ------------------------ | ----------------------- | --------- |
| Standalone delta               | (                                         | \Delta                   | \le960)                 | signed 16 |
| Standalone moment              | (                                         | \mu                      | \le256\cdot960=245,760) | signed 24 |
| One-order correction           | (                                         | c                        | \le1,920)               | signed 16 |
| Combined order correction      | (                                         | K                        | \le3,840)               | signed 16 |
| Two active masses multiplied   | \(z_a z_r\le65,536\)                      | unsigned 17, normally 24 |                         |           |
| Individual weighted correction | \(\le8\cdot65536\cdot3840=2,013,265,920\) | signed 32                |                         |           |
| Shared incoming moment         | \(\le W\cdot256\cdot960\)                 | signed 32                |                         |           |
| Grouped correction             | Can exceed signed 32                      | signed/modular 40        |                         |           |
| Final total                    | Fits existing 40-bit contract             | unsigned 40              |                         |           |

The correction bound follows from:

$$
c=V_{\rm final}-V_a-V_r+V_{\rm initial}.
$$

There are two positive and two negative terms from an interval of width 960, giving \(|c|\le1920\).

The revealed set is populated from four observed slots. Therefore \(W\le254+7\cdot4=282\), and \(M\le564\). Grouped hit mass can reach the conservative bound \(282\cdot256=72,192\), requiring more than sixteen bits.  

The shared incoming moment can exceed 69 million in magnitude under that bound. **It is not a 24-bit value.**

Implement signed contributions either by signed-magnitude multiplication followed by conditional negation, or by correctly sign-extending into the 40-bit ring. Modular accumulation is valid because the final exact total lies within the unsigned output range. It does not authorize signed comparisons of unfinished totals.

Silent failures to guard against include:

* `256 × 256` truncated to sixteen bits.
* Grouped masses passed through byte-weight APIs.
* A negative 32-bit correction zero-extended into forty bits.
* Truncating the shared incoming moment to twenty-four bits.
* Multiplying a grouped correction in thirty-two bits.
* Dividing standalone moments or per-reply contributions early.

Finally:

```text
score[a] = unsigned_divide(T[a] >> 16, M[a])

choose a when:
    score[a] > best_score
    or (score[a] == best_score and original_index[a] < best_index)
```

Keep the original five numerator bytes intact. The reference explicitly removes fractional bytes only after complete accumulation. 

## 5. Uncertainty must follow a separate reachability program

Factoring scores does not justify unioning all standalone flags.

Use these stages:

| Stage                           | Contribution                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Decision                        | Open-prior flag, where applicable                                                                             |
| Exchange setup                  | Item/volatile flags; applicable copied-speed uncertainty                                                      |
| Action check reached            | Flags produced while checking confusion, paralysis, wake/thaw, etc., even when a later check denies execution |
| Allowed action dispatch         | Recovery/boost/switch-Pursuit behavior                                                                        |
| Damage prefix reached           | Effect uncertainty and hit uncertainty, even on a miss                                                        |
| Positive-mass hit reaches range | Range variation and unsupported-damage flags                                                                  |
| Order resolution                | Tie/order uncertainty according to the reference’s order logic                                                |

The distinction between **check reached** and **execution allowed** is necessary. For example, confusion can set a flag before sleep subsequently denies the move. Recovery and boosts return before damage-prefix uncertainty. Rest sets transition uncertainty only when its modeled recovery is positive.  

A bounded algorithm is:

```text
for each actual order:
    obtain the first action's positive-mass successor classes
    OR flags reached during that first action

    merge equal continuation states, summing masses and ORing reached flags

    for each remaining positive-mass continuation:
        if the second action's entry gate is not reached:
            continue

        OR its check-prefix flags
        if its can-act verdict denies execution:
            continue

        execute its flag dispatch:
            boost: no damage-prefix flags
            recovery: conditional Rest flag
            switch/Pursuit: transition flag, then stop
            damage:
                OR damage-prefix flags
                if original hit mass is positive:
                    OR supported/unknown/range flags for this state
```

This needs at most two first-action successor classes per order, not four terminal exchange evaluations.

Specific cases:

* **First action prevents second:** no second-action check, prefix, or range flags.
* **Only some branches reach damage:** OR only those reached with positive probability.
* **Hit/miss share HP successor:** merge state masses, but preserve the union of flags from both positive-mass paths.
* **Replies share transitions but differ in uncertainty:** retain flag unions at the corresponding gates, including separate positive-hit information.
* **Both endpoints overkill:** raw endpoint inequality still sets the range flag.
* **Order uncertain:** distinguish a modeled two-order tie from uncertainty that retains one conservative order. Quick Claw and copied-speed uncertainty must not manufacture an extra coin flip.  

Flags may be excluded from continuation equality **after order resolution**, because they no longer affect these action transitions. Before resolution, the order-uncertainty state is not merely an output annotation.

## 6. Executable equivalence and classification rules

Use a classifier with explicit certificates:

```text
if either effective scoring mass is zero:
    NO_NUMERICAL_INTERACTION

elif either transition is identity for every relevant continuation:
    ZERO_CORRECTION

elif both transitions are ordinary opposing one-sided damage:
    if a first action can KO:
        KO_OR_REGIME_CORRECTION
    elif no first action changes a field read by the second amount:
        ZERO_CORRECTION
    else:
        HP_REGIME_CORRECTION

elif either action is Selfdestruct:
    SELFDESTRUCT_SPECIAL

else:
    COMPACT_ACTIVE_ACTIVE_EXECUTION
```

For ordinary damage with unchanged amounts:

```text
own-first correction:
    +incoming standalone loss, if owned hit prevents the reply
    0 otherwise

reply-first correction:
    -owned standalone gain, if reply hit prevents the owned action
    0 otherwise
```

For HP-regime changes:

$$
c_{\rm own-first}=\ell_{\rm initial}-\ell_{\rm after-own},
\qquad
c_{\rm reply-first}=g_{\rm after-reply}-g_{\rm initial}.
$$

A useful narrower finding: for **pure one-sided damage**, the first action changes the second attacker’s HP, not the second target’s HP. Thus Fire’s attacker-low predicate may change; Ice’s defender-high predicate does not change from that first one-sided attack alone. Both predicates can change when the first action also has self-HP effects.

### Never classify from standalone utility alone

Recovery at full HP can have standalone delta zero yet heal after an opposing attack. A defensive boost can have zero material/HP delta yet change the following amount. Neither is a no-op certificate.

Continuation equality requires the same remaining program and equality of every projected field it reads: HP, applicable defensive overrides, and any relevant execution-state inputs. Equal terminal utility permits terminal merging; equal utility before another action does not.

### Reply grouping

The grouping key must establish the same transition functions over relevant continuations:

```text
resolved execution/denial behavior
priority/order class
transition opcode and parameters
selected amount behavior over HP/defense regimes
raw-damage after-effect behavior
support/fallback behavior
remaining state read/write contract
```

Accuracy may differ; aggregate its masses. Uncertainty may differ; aggregate its gated flag metadata.

Do not group by zero power, standalone HP result, capped damage alone, or current overkill alone. Generate simple class runs first; defer a general runtime equivalence hash table.

## 7. Difficult semantics: decisions for each family

| Family                      | Required implementation                                                                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Recovery                    | Deterministic `HEAL` opcode; quota compiled from max HP, effect, weather, TimeOfDay, LinkMode; cap at execution-time missing HP            |
| Life Orb then drain         | Ordered within-action program; zero HP does not terminate that program; interruption is checked after completion                           |
| Selfdestruct                | Explicit opcode with pre-faint amount facts; self-faint on both hit and miss; no next action after it completes                            |
| Defensive boosts            | Four-byte projected override; normalize the complete attack/defense pair after applying the override and applicable screen/item operations |
| Multihit                    | Per-hit amount profiles plus bounded HP/raw-total progression; evaluate both range paths where needed                                      |
| Unsupported incoming damage | Explicit upper-bound opcode only after preceding gates/dispatch; no ordinary after-effects appended                                        |
| Switch/Pursuit              | Dedicated modeled transition-uncertainty result after can-act checking, before damage dispatch                                             |
| Switch entry                | Entry operation before incoming standalone state construction; replacement gets no reply                                                   |

The previously missing recovery/recoil/drain bodies are now present.

Recovery’s time-sensitive denominator is exactly derived from an index initially equal to two, modified by TimeOfDay/LinkMode and weather, indexing `{8,4,2,1}`. The final gain uses the kernel’s positive-input minimum-one scaling and execution-time missing-HP cap. 

Recoil has another easy-to-miss rule:

$$
q=\max(1,\lfloor raw/4\rfloor).
$$

Mono-Steel cancels it; dual-Steel uses \(\lfloor q/2\rfloor\), which **can be zero**. Drain uses \(\max(1,\lfloor raw/2\rfloor)\), capped at missing HP, including when current HP is zero. 

Do not implement currently unsupported multihit/item interactions “more accurately.” Owned multihit with Life Orb/Shell Bell, and incoming contact multihit into Helmet, are deliberately rejected by the adapter. Their reference behavior remains the corresponding unsupported path. 

Likewise, do not apply a newly inferred immunity before an unsupported-damage gate when the reference does not. Preserve the actual adapter/executor ordering.

**Missing evidence is now mainly integration evidence:** `OpenSRAM`/`CloseSRAM`, banking trampolines, interrupt handlers and their transitive calls, external legality helpers, the public saturation helper, actual stat/HP construction limits, and a fresh link map. The supplied helper bodies do not establish those contracts.

## 8. Arithmetic backend: grouped bases, not full power rows

### Source-grounded counts

My parse of the supplied move table and supported-effect classification finds:

```text
254 replies
157 damaging moves
134 potentially supported damaging moves
129 formula-based damaging moves
11 multihit moves
7 recovery moves
5 recognized defensive boosts

Ordinary physical formula powers: 21 distinct
Ordinary special formula powers:  19 distinct
Selfdestruct formula powers:       2 distinct
```

Thus the normal incoming workload needs **42 base calculations per defender**, or 252 for six defenders—not 256 powers for each of eighteen rows. The runtime Outrage category exception does not add a new power: power 100 already exists in both ordinary category groups. These counts are derived from the supplied table and adapter rules, not a linked-ROM trace.   

With both physical defensive raises and the special defensive raise, the conservative additional incoming groups are:

$$
2(21+2)+19=65,
$$

giving **317 incoming base-group calculations**.

At a conditional 2,000–3,000 cycles per grouped direct base, the ordinary six-defender cost would be approximately 0.50–0.76M. My former eighteen-row allocation at 80,000 cycles per row was 1.44M. Neither unit cost is currently measured, but the counts strongly argue against committing to full rows.

### A better partial evaluation: stream a five-power-step recurrence

All formula powers in this catalog are multiples of five.

For an incoming normalized configuration, let:

$$
K=\lfloor2L/5\rfloor+2,\quad n=5Ka,\quad d=50D.
$$

Compute once:

$$
s_q,s_r=\operatorname{divmod}(n,d).
$$

Then advance through powers in steps of five:

```text
q = 0
remainder = 0

advance power by five:
    q += step_quotient
    remainder += step_remainder
    if remainder >= denominator:
        remainder -= denominator
        q += 1
```

Emit `min(q,997)+2` only at powers actually needed. Once the cap is reached, later groups are constant.

This is exact because the only combined divisions are adjacent:

$$
\left\lfloor\frac{\lfloor N/D\rfloor}{50}\right\rfloor
=
\left\lfloor\frac{N}{50D}\right\rfloor.
$$

The catalog requires at most:

```text
36 steps for ordinary physical powers
36 steps for ordinary special powers
50 steps for Selfdestruct powers
```

That is **732 steps across six defenders**, or **940 including the defensive configurations**, plus initial divmods. No 512-byte row is constructed or stored.

Keep a generic direct-base path for non-lattice inputs and assert catalog eligibility at generation time. Do not apply incoming cap/item simplifications to the outgoing item pipeline without a separate proof.

### Processing order and defensive variants

Use:

```text
defender
    runtime category / Selfdestruct class
        power group
            reply
                active action
```

Hold up to **three small base-calculation states simultaneously**: ordinary, Defense +1, Defense +2. The special group needs ordinary and Sp. Defense +2.

Three 16-byte recurrence states fit the proposed 48-byte base workspace. This avoids both row rebuilding and a second 254-reply cache.

Keep the base reply record in WRAM. Build a needed boosted variant in the bridge staging area, use its correction immediately, and discard it. Outgoing variants against opponent boosts need at most:

$$
2n_{\rm physical}+n_{\rm special}\le8.
$$

An opponent’s recognized boost does not also change HP. Therefore **defensive variants do not require a Cartesian product with changed-HP variants from the same preceding action**.

### Finishing operations

Specialize shifts/adds, ordered chart operations, and frequent fixed ratios. Compile chart operation sequences, not an aggregate multiplier: source order, duplicate-type handling, Foresight, Struggle, and Dragon immunity substitution remain part of the plan.

Use same-bank tables for awkward fixed fractions and probability multiplication only when their actual instruction counts justify them. Keep rare/general cases generic initially.

For endpoint elimination:

* Store selected raw amount plus exact range-difference information.
* For an ordinary variable single hit with postroll one, no False Swipe, and pre-roll amount \(d\), range inequality is exactly \(d\ge2\).
* Do not extend that shortcut through saturation, False Swipe, differing postroll rules, or multihit stopping.
* Multihit raw “minimum” and “maximum” sums must not be assumed ordered: different KO stopping points can change the number of raw hits accumulated.

Addressing is material. For example, a memory-to-memory unrolled five-byte addition costs roughly 152 T-cycles for its byte operations alone, before pointer setup and call/return. An 80-cycle general 40-bit accumulate is not an adequate budget. RGBDS instruction timings also make a same-bank direct byte lookup cheap only when its index and pointer are already available. ([RGBDS][1])

## 9. HP valuation: use compact rank blocks

I would revise the threshold-table recommendation.

Use the same 384-byte owned and 256-byte opponent reservations, but select among:

* Direct bytes for sufficiently small HP domains.
* **Eight-HP rank blocks** for ordinary larger domains.
* Threshold representation for wider domains that do not fit rank blocks.

For \(M\ge W\), consecutive HP fractions differ by zero or one. For block \(b\), store:

```text
base[b] = floor(W * (8b) / M)
mask[b] = which of the next seven HP increments increase the value
```

Then:

$$
v(h)=base[h>>3]
+\operatorname{popcount}\left(
mask[h>>3]\ \&\ ((1<<(h\&7))-1)
\right).
$$

This is exact and uses:

$$
2(\lfloor M/8\rfloor+1)
$$

bytes. A 713-HP domain, for example, needs 180 bytes per actor—not 714.

The lookup requires index construction, two SRAM bytes, a mask, and a same-bank popcount lookup. A straightforward register-clobbering implementation is approximately **144 T-cycles before call/return, input loading, and dispatch**; budget roughly 200–300 rather than calling it free.

Construct blocks from the \(W\) threshold events rather than evaluating every HP fraction. Construction is bounded by the number of blocks plus \(W\). For \(M<W\), a small direct table avoids multi-unit increments.

After factoring, valuation occurs for standalone successors and genuinely changed active–active successors. It is not required afresh for every hit/miss cell. Cache initial potentials, bypass unchanged/full/zero HP, and reuse ordinary regime-specific loss values when their target HP is unchanged.

One unresolved domain issue remains: the old table’s `<704` guard is an optimization-domain check, **not proof that all legal HP fits that domain**. Wider HP must retain exact valuation, and its timing must be counted. The source’s HP-regime arithmetic also uses finite-width doubling/tripling; a larger valuation domain does not automatically justify replacing those predicates with unbounded arithmetic.  

## 10. Adversarial operation counts and budget

A universal two-second bound is **not established**. There is, however, a stronger count model than either previous paper budget.

### Counts that can be reduced by proof

**Candidates:** twelve output slots, at most nine simultaneous legal candidates.

**Order units:** retain 2,032 as the simple upper bound. In this catalog, 242 replies have base priority, so four base-priority tied actions require:

$$
4(254+242)=1984
$$

order-specific units before state-based reductions.

**Hit/miss expansion:** normalized non-Selfdestruct pairs require one active–active interaction per order, not four terminal calculations.

**No-op replies:** 97 zero-power moves minus seven recoveries and five boosts gives 85 replies with no modeled state transition. They still require flags, but no numerical interaction—even against a complex owned action. This leaves at most:

$$
4(169+162)=1324
$$

potentially nontrivial order-specific interactions at base priority.

**Finishing configurations:** a conservative catalog-derived envelope is 1,228 paired-endpoint finishing configurations, including incoming HP regimes, applicable defensive configurations, and outgoing variants. This deliberately combines some incompatible maxima; the generator should reproduce the count against the frozen catalog.

**Multihit:** do not rerun an owned multihit range merely because the reply changed owned HP. These catalog multihit moves do not read attacker-low Fire state. Reuse remains valid when opponent HP and applicable defense are unchanged.

My parse finds at most 77 reply IDs that can change opponent HP before a surviving owned multihit action when Helmet is considered; without Helmet the corresponding set is sixteen. Including standalone ranges, incoming-second ranges, and outgoing defensive variants gives a conservative envelope of:

$$
7(66+4+44+4\cdot77+8)=3010
$$

per-hit progression steps, counting both range paths. This requires the stated invalidation rule; without it, the loose bound is 7,910 steps.

These catalog counts must become generated assertions/report entries, not hand-maintained assumptions.

### Disjoint go/no-go allocation

This is a **proposed acceptance allocation**, not a forecast that the current implementation achieves it.

| Phase                                                               | Count basis / requirement                                                       |       Ceiling |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------: |
| Entry, public facts, actors, legality, reply set, accuracy metadata | All supported candidates/replies; no repeated per-pair actor construction       |       650,000 |
| Base arithmetic                                                     | Up to 317 incoming groups plus outgoing variants; streamed recurrence available |       650,000 |
| Finishing arithmetic                                                | Up to 1,228 paired-endpoint configurations                                      |     1,360,000 |
| HP representations                                                  | All constructions included                                                      |       400,000 |
| Standalone transitions and valuation                                | Shared first-action results; excludes amounts, probability math, multihit steps |       800,000 |
| Classification, order, reachability bookkeeping                     | Full pair set, including no-op replies                                          |       600,000 |
| Scalar interaction execution                                        | Up to 1,324 nontrivial order units; excludes probability and multihit steps     |     1,460,000 |
| Probability arithmetic and wide accumulation                        | Includes moments, grouped-width handling, combined tie corrections              |       900,000 |
| Multihit progression                                                | Up to 3,010 steps                                                               |       430,000 |
| Normalization, selection, export, selector bank handling            | Complete output vector                                                          |       100,000 |
| **Isolated selector ceiling**                                       |                                                                                 | **7,350,000** |
| Development integration allowance                                   | Must ultimately be replaced with measured/bounded evidence                      |   **750,000** |
| **Combined allocation**                                             |                                                                                 | **8,100,000** |
| **Unallocated margin**                                              |                                                                                 |   **288,608** |

The tight implementation requirements are approximately:

* Around 1,100 cycles per paired-endpoint finishing configuration at the conservative count.
* Around 1,100 cycles per nontrivial scalar order unit, with probability work separate.
* Around 140 cycles per multihit progression step.
* No unbudgeted in-domain reference fallback.

Those are demanding but testable. The earlier “roughly 2,000 cycles per ordinary unit” trigger is too permissive and too ambiguous.

### Which maxima coexist?

Four complex draining attacks, both uncertain actors, speed ties, relevant HP regimes, and five switches can coexist in the declared modeled domain.

But:

* Four damaging moves and three distinct owned defensive boosts cannot occupy the same four slots.
* A recognized boost cannot also cause the HP changes needed for a crossed HP/defense variant.
* Owned Life Orb/Shell Bell multihit is unsupported rather than a costly modeled combination.
* Contact multihit into Helmet follows the unsupported path.
* Selfdestruct first always interrupts the second action.
* Always-hit moves and deterministic recovery/boost transitions do not create two scoring events.
* Quick Claw/copied-speed uncertainty does not create the modeled two-order tie.

The final bound should maximize a count-and-cost expression over these compatible configurations, not add every independent maximum and call the result a reachable workload.

Fallback must be charged as:

$$
C_{\rm fallback}=\sum_f n_f
\left(C_{{\rm preparation},f}^{\max}
+C_{{\rm execution},f}^{\max}\right).
$$

The historical approximately 60k per pair is an average, not a fallback maximum. While supported families still fall back, the universal target remains open.

Integration also needs bounded interrupt/DMA costs and safe scratch ownership. Interrupt entry itself has a defined cost; the repository-specific handlers dominate the missing evidence. Disabling interrupts for the entire decision is not a free substitute for that audit. ([GBDev][2])

## 11. Bounded verification

Use the existing fixture infrastructure, with four comparison seams.

| Level            | Compare                                                                                                                          |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Record           | Accuracy, priority, gate verdict/flags, selected raw amount, support/range behavior, standalone HP/defense successors and moment |
| Action primitive | HP after each ordered primitive, especially zero-then-drain; completed-action flags                                              |
| Pair             | Complete unweighted numerator, order mass, uncertainty; special/fallback replacement versus factored result                      |
| Selector         | All twelve numerator/mass/score/flag records, legality, selected original index, caller state                                    |

Do not require native private backends to reproduce unused legacy arithmetic scratch. Compare their declared observable contracts.

Essential adversaries include:

* Accuracy bytes 0, 254, 255; both actors uncertain; both orders.
* Equal integer scores with unequal numerators.
* KO equality, overkill, raw endpoint variation after capped equality.
* Strict half/third-HP boundaries with odd maxima.
* Rest at full HP versus Rest after damage.
* Life Orb to zero followed by drain.
* Steel recoil rounding to zero.
* Selfdestruct miss and Selfdestruct interrupted before execution.
* Joint truncation around 255/256 and low-byte extraction boundaries.
* Multihit Ice crossing and different endpoint stopping counts.
* Unsupported incoming damage after denial, miss, and special dispatch.
* Switch/Pursuit, entry KO, replacement mass, forced/wait flags.
* Known Quick Claw versus actual modeled ties.
* Hidden-opponent-state invariance, repeatability, and fresh-decision cache invalidation.

Metamorphic checks should include reply/action/order/event traversal reversal, grouping versus ungrouping, splitting a weighted group into equivalent members, changing irrelevant HP flags, and changing scratch-fill patterns between calls.

On mismatch, stop at the first differing record or pair and replay **that pair** with action-boundary traces. Do not build a permanent generalized execution-log subsystem.

I ran independent checks of the proposed arithmetic: 4,200,496 HP-valuation comparisons, 100,000 transition/accumulation comparisons, and 520,000 five-power-step base comparisons passed. These prove implementation-independent identities and test the Python constructions; they do not validate opcode classification, assembly carry handling, banking, or ROM timing.

[Arithmetic verification script](sandbox:/mnt/data/verify_selector_redesign.py)

## 12. Final implementation decision

### Required roadmap corrections, ranked

1. **Replace “ordinary-only factoring” with normalized active-transition factoring.** Complex identity-on-miss families need one active–active correction per order, not renewed hit/miss enumeration.
2. **Replace the provisional memory allocation.** Current producer scratch is 324 bytes; the complete joint context is 457. Legacy SRAM HP tables cannot coexist with the proposed records.
3. **Remove mandatory 512-byte power rows.** Grouped bases—and especially the five-power-step recurrence—fit the actual catalog and defensive-variant schedule better.
4. **Strengthen the accumulation contract.** Shared moments require signed 32 bits; grouped correction products require forty bits; combine tie corrections before multiplication.
5. **Make uncertainty a gated reachability program.** Execution denial, recovery dispatch, raw range variation, and order uncertainty cannot be flattened into one standalone flag union.
6. **Replace average-based timing claims with the adversarial count model.** Complete score vectors also remove the previous permission to stop at proven losing candidates.

### Choices to adopt

Adopt the hybrid executor, four 64-byte plans, a 48-byte streamed reply, the phase-separated producer workspace, compact rank-block HP valuation, grouped base-calculation states, explicit Selfdestruct handling, and full indexed result export.

Keep the exhaustive evaluator and gameplay selector separate and unchanged.

### Defer

Defer full power rows, general runtime reply hashing, large multiplication tables, broad arithmetic replacement, and elaborate pruning. Simple generated equivalence classes and a small same-bank multiplication backend can follow actual profile evidence.

### First implementation batch

1. Freeze the oracle and verify scratch/banking/interrupt contracts.
2. Add the private ABI, result records, and linker assertions.
3. Add producer bridges and remove legacy HP-table use from this entry.
4. Implement compact HP lookup, exact wide accumulation, and combined-order weighting.
5. Implement identity, ordinary damage, conservative incoming KO, recovery, and the Life Orb/drain executor slice.
6. Add whole-pair direct-reference fallback with explicit baseline replacement.
7. Differential-test and profile ordinary and adversarial complex paths before replacing damage producers.

### The abandonment trigger

**If measured non-producer work exceeds 7,638,608 cycles on an in-domain adversary, the design has failed the development allocation even with free damage preparation. If it exceeds 8,388,608, no damage-backend optimization can rescue it.**

A softer but earlier stop is sustained failure of the scalar-interaction or finishing phase ceilings after using the intended records and HP lookup. At that point, replace the expensive family’s executor with an action-specific HP transfer function or further shared-successor partial evaluation; do not continue polishing context builders and assume the remaining factor will appear.

The roadmap is implementable after these corrections. **Its universal two-second claim is still conditional on the native phase measurements, a certified legal input domain, and the transitive SRAM/interrupt audit.**

[1]: https://rgbds.gbdev.io/docs/v0.9.4/gbz80.7 "https://rgbds.gbdev.io/docs/v0.9.4/gbz80.7"
[2]: https://gbdev.io/pandocs/Interrupts.html "https://gbdev.io/pandocs/Interrupts.html"
