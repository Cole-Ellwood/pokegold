## Decision

**The architecture is ready for the restricted offline prototype, with two narrow contract clarifications required before the bridge code is written:** explicit far-call argument/result marshaling, and explicit restoration of the legacy fields read after fallback.

I found **no defect in the generalized factoring identity, no intrinsic overflow in the proposed widths, and no unavoidable record-size conflict for the first slice**. I would not require another oracle-freezing exercise, completed native operation bounds, prototype timing, or a production interrupt audit before starting.

I read the readiness record, contract, roadmap, review, and manifest before checking the relevant source and inherited recommendations. I also reproduced the supplied arithmetic-script results, independently extracted the simple catalog counts, and verified all **48 complete embedded section hashes**, reversing the package’s newline conversion. The three labeled excerpts cannot verify their complete source-artifact hashes. I did **not** rerun the ROM fixtures: the attachment expressly excludes the ROM binaries and full linker map. 

The distinction matters: the algebra can be established now; implementation equivalence, actual live ranges, and native timing must be established by the prototype.

## 1. Factoring correctness: the formulation is sound

For one resolved order, the normalized formulation is:

$$
N_o=65536\cdot1024+256(\mu_a+\mu_r)+z_a z_r\,\kappa_o,
$$

where the active maps include the reference’s **start-of-action interruption checks**, and

$$
\kappa_o=V(S_o(s))-V(s)-\Delta_a-\Delta_r.
$$

The proof depends on the inactive transitions being identities—not on the active transitions being ordinary damage, one-sided, linear, or commutative. That permits recovery, drain, recoil, and supported item effects within the stated framework. The contract correctly separates this numerical normalization from original-event uncertainty. 

### Recovery, drain, recoil, and interruption

Recovery and recognized boosts execute before the accuracy branch, so their scoring mass is 256. Full-HP recovery remains a transition that can become useful after the other action; its initial zero delta does not make it globally inactive. The source’s dispatch order supports that treatment. 

Drain, recoil, and the modeled after-hit items belong inside the active transition. In particular, the source performs damage, then the item effect, then recoil/drain. It refreshes the attacker’s current HP between those operations. An intermediate zero caused by Life Orb therefore does not end an action that subsequently drains. 

Interruption must be tested at the next action’s boundary. Both `.OwnMove` and `.Reply` require the relevant actors to remain alive before entering their programs. Their gates can be included in the deterministic maps without invalidating the identity.  

### Selfdestruct

The special treatment is necessary and correctly specified. Selfdestruct’s miss is not identity: projected self-faint occurs before the miss/zero-accuracy return, while damage uses the pre-faint attack facts. It must not acquire `z=0` merely because its original hit mass is zero. Keeping it on complete pair fallback initially is sufficient.  

### Identity and reuse certificates

The local certificates are strong enough **as specifications**. They require continuation-wide identity and equality of the remaining program’s read set, rather than equal standalone utility or equal capped damage. I would preserve them, not demand a stronger general formalism before coding.  

Their implementation must distinguish four different claims:

| Certificate                                    | What it permits                                                         |
| ---------------------------------------------- | ----------------------------------------------------------------------- |
| Numerical identity over relevant continuations | Skip numerical interaction, not flags                                   |
| Reusable raw amount                            | Reuse the amount, while recapping at execution-time HP                  |
| Equal continuation                             | Merge only after matching the remaining program and everything it reads |
| Equal terminal utility                         | Merge terminal scoring work, not unfinished actions                     |

No additional pre-coding proof is needed here. The opcode/read-set assertions and differential tests are the implementation evidence.

## 2. Exact arithmetic: the equations and widths work

### Normalization and fallback cancellation

The initialization and final shared-moment addition assign each pair this baseline:

$$
w_r\left[2\cdot65536\cdot1024+512(\mu_a+\mu_r)\right].
$$

Consequently, adding `w_r * (N − baseline)` replaces that pair exactly. The later `512*B` addition is already accounted for in that cancellation; it must not trigger another incoming-moment subtraction. The contract gets this right. Combining the two tie corrections before multiplication also preserves the full numerator without intermediate rounding. 

For switches, the incoming moment is relative to **post-entry HP**, not the original defender state. Entry KO removes execution, not denominator mass. Replacement’s absent reply and mass 2 are correctly separate from the ordinary reply sweep. 

When implementing switch fallback, make its replacement baseline match that switch baseline. Do not mechanically substitute the active-action formula using an incoming moment measured before entry.

### Width closure

The following bounds follow from the contract’s potential range and constructed reply-weight limit; they do not require prototype measurements:

| Quantity           |                          Bound / consequence |
| ------------------ | -------------------------------------------: |
| Total reply weight |                                \(W_R\le282\) |
| Mass               |                                  \(M\le564\) |
| `M << 8`           | Up to **144,384**: requires 18 unsigned bits |
| Shared moment `B`  |        Absolute value at most **69,304,320** |
| `512 * B`          |    Absolute value at most **35,483,811,840** |
| Grouped correction |    Absolute value at most **70,967,623,680** |
| Final numerator    |                   At most **73,333,211,136** |

The last bound uses \(U\le1984\) and \(D=564\cdot65536\). A conservative absolute sum of the initialization, corrections, and shared term is **179,784,646,656**, still comfortably within signed 40-bit storage. The proposed 40-bit accumulation therefore has adequate room; the important risk is narrowing **before** a shift or multiply. The individual correction bound of 2,013,265,920 also fits signed 32 bits as stated. 

**First-batch verification:** exercise the accumulator directly with maximum masses, both signs, `256*256`, and values of `M` crossing 255/256. Check `(M<<8)*mu` and `512*B` independently before testing complete selectors. These are tests of the planned implementation, not missing preparation deliverables.

### Grouped recovery needs the deterministic mass

**Affected section:** contract “Numerical contract,” grouped-mass paragraph; inherited review “Grouped masses.”

The inherited review contains an important qualification that the local contract compresses into “where applicable”: `z[a]*H*K` is for identity-on-miss groups. For deterministic recovery/boost groups, replace `H` with `256*W_g`. 

**Failure scenario:** an owned hit removes 40 HP from a full-HP opponent, followed by recovery that restores it. With 128-weight, 100-max-HP valuation, the owned standalone gain is 52 and the recovery standalone delta is zero. If recovery’s original hit mass is zero, using original `H=0` omits the correction and yields 1076 instead of 1024. Recovery still executes in the reference.

**Required correction:** before grouping is implemented, make the local contract explicit:

$$
Z_g=\sum_r w_r z_r,\qquad \text{correction}=z_a Z_g K.
$$

Thus `Z_g=H` for identity-on-miss groups and `Z_g=256*W_g` for deterministic groups. Original `H,Q` remain available for event semantics and special handling.

**Smallest verification:** grouped versus ungrouped recovery with original masses 0, an intermediate value, and 256.

This is **not a blocker to the initial ungrouped prototype**.

### Full numerators and integer ties

The proposed output and selection rules are correct. Preserve all five numerator bytes, then compute `floor((T >> 16)/M)`. Equal integer scores must choose the lowest original index even when the numerators differ. No losing-candidate shortcut is compatible with the complete-vector contract.  

## 3. Required contract clarification: far-call marshaling must cover entry as well as return

**Affected sections/symbols:** contract “Entry, results, and banking” and “Producer bridge and fallback”; `farcall`, `BossAI_ValuePublicExchangeFromContext`, `BossAI_EnumeratePublicActions`.

The return correction is valid, but the macro also replaces **A and HL before entering the callee**. `FarCall_hl` then preserves the callee’s flags and BC while clobbering A during its return sequence.  

Two concrete failures follow from an otherwise plausible implementation:

* `farcall BossAI_ValuePublicExchange` cannot deliver its advertised slot in A and reply/branch in H/L. The macro substitutes the bank and target address.
* A plain cross-bank call to `BossAI_EnumeratePublicActions` cannot deliver replacement kind 2 in A. That routine distinguishes replacement from ordinary enumeration using A.  

**Required correction before bridge coding:** add a short bridge-ABI paragraph stating that every cross-bank service must marshal any A/HL inputs and A outputs explicitly. In particular:

* Use the existing `BossAI_ValuePublicExchangeFromContext` entry for cross-bank direct fallback.
* Give candidate enumeration a same-bank shim or another explicitly marshaled entry.
* Do not assume that a future public wrapper solves the decision-kind input merely by reloading the selected index on return.

The existing FromContext entry was written for exactly this purpose. No new fallback architecture is necessary. 

**Smallest useful verification, during the first batch:** compare direct invocation with invocation through the actual macro/shim for ordinary and replacement enumeration, plus a fallback exchange with nonzero reply and branch values. Check results, DE, SP, BC/carry where declared, and return ROM bank. The current harness sets the target bank and PC directly, so direct harness success cannot establish this bridge ABI. 

The eventual selected-index reload must also preserve carry while computing the result address. That wrapper remains a later integration deliverable; it need not be completed before the private prototype starts.

### SRAM contract

Closed entry, explicit bank 0, and closed exit are appropriate. The supplied helpers do not preserve an unknown previous enable/bank state, and the package correctly stops promising that. `CloseSRAM` preserves AF, which is useful for a shared return epilogue. 

The first implementation should route **every return after acquiring SRAM ownership**, including rejected/incomplete returns, through cleanup. Test an early exit after opening SRAM—not only successful decisions. This enforces the existing closed-exit intent; it does not require production integration.

## 4. Memory fits, but fallback must invalidate read dependencies—not just restore selectors

The address arithmetic is consistent: WRAM totals 472 bytes and SRAM totals 1,536 bytes. The inherited records contain the first slice’s required persistent numerical information: both standalone deltas and moments, original accuracy, HP successors, defense overrides, actor valuation modes, and separate control storage for weather/time/link state. I found no necessary extra persistent field for this slice. The 64 uncommitted bytes are inside the allocation, not additional capacity.  

The legacy HP-table prohibition is essential. The existing two 704-byte tables physically overlap the proposed records; closing and reopening SRAM would not protect them. 

### Required clarification: distinguish restored inputs from a restored prepared epoch

**Affected section:** contract “Producer bridge and fallback,” particularly “Restore bridge slot/kind/move/reply/branch inputs after fallback.”

**Failure scenario:** direct fallback clears prepared/speed-mode branch bits and overwrites the AV prefix. A later call to `BossAI_PreparedActionHasSpeedTie` depends on those speed-mode bits, cached speed words, and candidate-specific prepared facts. Restoring only the public event bits and five logical selectors does not establish those dependencies. With numerically equal speeds and copied-speed uncertainty, a stale restored context can manufacture a modeled tie.  

**Required correction before bridge coding:** state that restoration covers the **complete read set of the next legacy helper**, not merely the named selector inputs. The compact records should remain authoritative for new order/accuracy work. A bridge that invokes a prepared service must reconstruct or revalidate the required prefix and preparation epoch first.

This does not require preserving all 324 bytes around every call. That would defeat the design. It requires knowing which producer-owned state remains valid and rebuilding the rest.

**Smallest useful verification:** run fallback immediately before another producer/record construction, using copied-speed uncertainty and differing active moves. Compare with a clean reconstruction. Poison dead prefix fields between operations as well as checking boundary canaries: canaries do not detect an incorrect read from an address that is legitimately inside the workspace.

### Two lifetime rules for the first batch

**Defender-local sums must be consumed before reuse.** Add the active defender’s shared `512*B` contribution to its plans before repurposing common sums or actor views for a bench defender. For switches, consume the post-entry unary sum before moving to the next bench slot. A minimal adversary uses different max HP and win-condition weighting across defenders, then reverses traversal.

**Continuation mass must have a declared unit.** Its two-byte first-event field is sufficient for an unweighted original-event mass of 0–256. It is not sufficient for a grouped mass of 72,192. Keep grouped masses in the reserved three-byte group fields; before grouping, document that they are not folded into the two-byte continuation field. Otherwise 72,192 can silently become 6,656. The record sizes need not change.  

Actual assembly assertions, stack high-water checks, and producer/fallback canaries belong in the first batch, exactly where the readiness record puts them.

## 5. Two source-specific traps worth adding to the first batch

These are implementation hazards within the chosen design, not reasons to expand its scope.

### Recovery helper output is a capped gain, not a reusable quota

**Affected symbols:** `BossAI_ContextRecovery`; recovery fields in the compact records.

**Failure scenario:** call the helper at full initial HP, receive BC=0, and store that as the recovery quota. Later, after incoming damage, the native executor incorrectly heals zero. Calling the helper with synthetic HP=0 does not obtain the quota either: the helper explicitly returns zero at fainted HP. 

**Required correction:** construct the reusable quota from max HP, effect, weather, TimeOfDay, and LinkMode, or use an explicitly justified adapter. Apply the missing-HP cap at execution time. Do not export the helper’s current-state capped gain under the quota field’s name.

**Smallest verification:** the already specified full-HP Rest/recovery followed by nonlethal damage, observed at the record and primitive seams. Include one nontrivial time/weather denominator. No new test framework is needed.

### Do not add a Substitute drain gate that the frozen exchange does not execute

**Affected symbols:** `.OwnMove`, `.Reply`, `BossAI_ContextDrain`, `.ReplyAfterHitItem`.

The drain helper’s comment assigns Substitute eligibility to its caller, but the supplied single-hit exchange applies its selected damage and drain without inserting a new Substitute rejection at that point. Substitute contributes uncertainty; Helmet has its own explicit Substitute gate. Those are different behaviors in this conditional model.    

**Failure scenario:** a cleaner-looking generic after-hit dispatcher suppresses single-hit drain or Life Orb because Substitute is present, changing the reference result.

**Required correction:** translate the actual exchange control flow, not a stronger interpretation of helper comments or gameplay mechanics.

**Smallest verification:** a supported single-hit Life-Orb/drain pair with Substitute toggled, checking full numerator and flags. Keep Helmet’s distinct rule covered by fallback until its native family is implemented.

## 6. Uncertainty: the bounded reachability program is sufficient

The proposed program can preserve the reference’s positive-mass flags without reproducing exhaustive scoring. For each actual order, there are at most two original first-action outcomes to consider. Equal continuations may merge; for each remaining positive-mass state, the second action needs its reached check/dispatch/range metadata—not a fresh terminal utility calculation for every latent event combination. The inherited program correctly distinguishes check reachability from execution permission. 

The critical boundaries are already captured: confusion/paralysis before later denial, recovery/boost before damage-prefix flags, Rest uncertainty only for positive recovery, raw range inequality despite equal capped loss, and genuine ties versus conservative uncertain order. 

One implementation rule should be explicit at the pair seam:

**Do not commit speculative pair flags before deciding whether native execution or fallback owns the pair.** Numerical baseline replacement is reversible; an OR into the action’s accumulated uncertainty is not. Select fallback before committing flags, or hold tentative pair flags locally.

**Failure scenario:** provisional native processing contributes a range or transition flag, then discovers an unsupported variant and replaces the numerical pair. The fallback correctly finds that the flagged action was interrupted, but cannot remove the already-ORed bit.

**Smallest verification:** force fallback for an early-KO/interrupted pair and compare both the complete pair numerator and flag byte. This is an implementation test, not another pre-coding gate.

The performance risk remains real: a reachability program can still be expensive if it repeatedly rebuilds contexts or recomputes ranges. Measure its calls and phase cost. Bounded state count alone is not a timing proof.

## 7. Scope, domain, and performance

### The initial slice is sufficient

Ordinary damage establishes the inexpensive path. Recovery exposes continuation-sensitive zero standalone values. Life Orb followed by drain exposes action-completion boundaries and two-sided HP changes. Switch/replacement/wait expose the orchestration and mass conventions. That is a useful structural experiment, not an artificially easy demonstration.

Keep Selfdestruct, defensive overrides, multihit, and other unimplemented combinations on exact pair fallback. They need to be exercised through that path, but need not become native before the first structural measurements. The readiness sequence already makes that distinction correctly. 

### The HP domain is adequate for this prototype

For max HP ≤999, the largest rank representation occupies:

$$
2(\lfloor999/8\rfloor+1)=250\text{ bytes},
$$

so it fits either reservation. The `M>=W` eligibility condition is necessary; small maxima need direct bytes because a single HP increment can change the valuation by more than one. Wider threshold valuation does not certify wider HP-regime execution: the reference’s doubling/tripling predicates are finite-width operations.  

Do not turn the HP/stat cap rationale into a claim that **post-screen/item damage operands** never exceed 999. For example, a defense word of 512 doubled by Reflect becomes 1024. The reference then jointly quarters both stats once, extracts low bytes, and applies its defense-zero guard. That behavior is not equivalent to clamping defense back to 999 or repeatedly shifting until it fits a byte.  

**Before the native arithmetic backend:** distinguish imported/raw/staged limits from post-modifier operand limits, and pin a 1024 low-byte case alongside the 255/256 tests. This does not block the producer-backed slice.

### Catalog and grouped bases

My extraction agrees with 254 moves, 157 damaging moves, 134 potentially supported damaging moves, 129 formula moves, 11 multihit moves, seven recoveries, five recognized boosts, 242 base-priority replies, and 85 numerical zero-power no-ops. The 21/19/2 power groups and five-power lattice also reproduce. These remain catalog facts, not runtime support certificates. 

The 1,324 count is reproducible: of the 85 numerical no-ops, 80 have base priority and five do not. Removing their numerical interaction units from 1,984 leaves 1,324. Their classification and flag work remain.

The incoming five-power recurrence is algebraically valid after the exact normalization, including joint truncation, Selfdestruct defense adjustment, and zero guards. It does not establish outgoing item simplifications or finishing equivalence.

The **1,228 finishing configuration and 3,010 multihit-step envelopes remain unverified**. The package now says so honestly. Their dependency rules and compatible maxima must be generated before timing acceptance, not before coding begins. 

### Phase targets

The 7.35M native allocation plus 750,000 integration allowance sums correctly to 8.10M, leaving 288,608 cycles. None is a measurement. The fresh reference and two approximately 458M-cycle adversaries establish workloads and old-architecture costs—not native feasibility or infeasibility.  

Use the existing stop conditions. Also retain this asymmetry: excessive unavoidable native work can reject the budget early; low measured work from a slice that still sends difficult families to fallback cannot certify the final budget.

## 8. Evidence quality and remaining gates

The evidence description is substantially honest. The important shared dependencies are:

| Evidence                                       | Establishes                                                                | Does not independently establish                            |
| ---------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Prepared/direct actor and accuracy comparisons | Preparation/cache parity                                                   | Correctness of every shared loader or arithmetic helper     |
| Cached/direct first-action successors          | Cache replay and invalidation parity                                       | Independent action semantics                                |
| Python arithmetic script                       | Tested constructions and algebraic identities                              | Real opcode certificates, flags, assembly widths, or timing |
| Host exhaustive exchange aggregation           | Independent weighting/order/selection aggregation over reference exchanges | An independent battle simulator                             |

The local review expressly acknowledges the shared bulk loader. The joint harness itself obtains candidates, replies, and exchange outcomes from ROM services, then independently aggregates event weights. That is useful structural evidence without being independent evidence for every shared semantic component.   

The full-numerator adapter remains essential. Retain the host’s already-computed integer `total` and full event mass per original index; compare them with exported T and `M*65536`. Matching a captured numerator’s divided score is weaker than matching the numerator itself, and the package correctly admits that limitation. 

One later integration point deserves an explicit note: the old selector’s final score vector does not retain every candidate’s numerator. An out-of-domain restart adapter cannot reconstruct those numerators from scores after the call. It must capture or collect complete per-candidate totals before they are reused, or obtain them by exact aggregation. That belongs with implementation of the restart adapter, not before this prototype.

### Required edits and first-batch changes

| When                                         | Required work                                                                                                                                                                                                                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Before bridge coding**                     | Amend the contract to specify A/HL input and A-output marshaling; name `ValuePublicExchangeFromContext`; clarify that post-fallback restoration covers the next helper’s complete read set.                                                                                                                  |
| **First implementation batch**               | Build those bridges; add wrapped-call and prefix-poisoning tests; verify recovery quota extraction and the Substitute case; keep tentative pair flags local; consume defender-local sums before reuse; implement the already-planned full-numerator adapter, actual HP lookup, canaries, and phase counters. |
| **Before grouping/native timing acceptance** | Make deterministic group mass and continuation-mass units explicit; certify descriptor eligibility and complex counts; complete native in-domain families and measure disjoint costs.                                                                                                                        |
| **Before production promotion**              | Complete the public wrapper, restart-result adapter where applicable, reachable-domain audit, ownership/interrupt/DMA audit, and measured integration timing.                                                                                                                                                |

**No architectural blocker remains after the two bridge-contract clarifications. No additional broad preparation pass is warranted.** Start with the restricted slice and let implementation settle the remaining layout, equivalence, and timing questions.

**READY WITH REQUIRED CHANGES**
