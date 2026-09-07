# Remaining strategic roadmap

For the current exact joint-selector performance work, follow
[the two-second implementation roadmap](two_second_roadmap.md). It incorporates
the Pro/Claude architecture reviews and defines measured correctness, memory,
and runtime gates. The stages below remain the broader strategic roadmap;
completing the performance work does not complete deeper search or learning.

Authorized follow-up to the approved strategic consistency pass. Preserve that
pass and its evidence; each new stage needs an independent Astra review.

1. **Shared damage and survival facts — next major stage.** Use one public-only,
   16-bit damage kernel for owned outgoing and revealed incoming moves. Own
   battle stats are known; player stats are estimated from public species,
   level, stages and status, assuming DV8 and no unknown held-item/badge boost.
   Compare estimated damage with current HP rather than coarse pressure bands.
   Keep supported damage, hit reliability, and action order separate. Handle
   fixed damage, screens, stat truncation, ordinary multi-hit minimums, weather,
   known own items and deterministic type passives explicitly. Unsupported
   conditional effects must not fabricate a reliable KO. Migrate current/any
   KO premises and revealed-priority lethality together.
2. **Joint action valuation.** Extend these facts to the active mon and all
   living bench members; price switch-entry damage, hazards, recovery, sacrifice
   and future retained value on one scale. Preserve authored tiers and variety
   among defensible choices. Validate candidate-order invariance and dominated
   action removal against the previous policy before promotion.
3. **Small public successor search.** Build a bounded two-action continuation
   evaluator over feasible moves, switches and revealed/plausible replies.
   Track HP, status, stages, hazards and forced/locked turns; branch only where
   a reply could change the choice. Prune only with valid bounds. Validate
   against an exhaustive offline reference on the same public information.
4. **Outcome learning.** Record actual observed direct damage with context,
   separate residual/healing effects, and invalidate observations after relevant
   changes. Treat duplicate species and copied/transformed moves as ambiguous.
   Model player switching conditional on opportunities; scout only when new
   information could change a later decision.
5. **Strategic acceptance corpus and ablations.** Use real boss rosters across
   tiers, complete turns and continuations, matched seeds, varied player
   policies and held-out positions. Measure missed finishes, avoidable losses,
   wasted setup/recovery, bad switches and loops alongside win rate. Remove
   heuristic groups only when ablations support the change or an explicit
   authored difficulty goal. Measure cycles, stack and bank/WRAM budgets.

Stage 1 acceptance: paired ROM arithmetic vs actual combat on synthesized public
stats; exact HP, level disparity, screens, fixed/multi-hit and passive boundaries;
state-preservation and hidden-state invariance; end-to-end corrected decisions;
normal/trace regression, Gold/Silver/debug/trace builds and all relevant audits.
No extra persistent memory or save migration is planned. Stage 2–5 are ordered
follow-ups, not features to claim from passing stage-1 helper tests.

## First increment (historical)

The first follow-up corrected fixed-damage KO checks only. Its evidence remains
in `fixed_damage.md`, `fixed_damage_review.md` and `fixed_damage_manifest.json`.
The shared model now supersedes that helper; its exact current/available-moveset
boundary cases remain in the regression suite.

## Stage 1 implementation

The shared public kernel, adapters and paired outgoing/incoming KO migration are
implemented. `stage1.md` records the full scope, supported/unsupported move
inventory, retention decisions and validation. `stage1_review.md` records the
independent final disposition when complete; `stage1_manifest.json` binds it to
source, tests and all four ROM builds. This does not complete stages2-5 or the
full roadmap goal.
