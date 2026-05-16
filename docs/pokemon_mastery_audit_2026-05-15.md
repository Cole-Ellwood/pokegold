# `docs/pokemon_mastery/` audit, 2026-05-15

Audience: Codex (cross-model review). Author: Claude Opus 4.7. No source files
were modified. Read-only audit. Goal of the audit: characterize whether
`docs/pokemon_mastery/` works as a state-of-the-art reference for an LLM
playing competitive Gen 2 (GSC) OU singles, with awareness of the project's
Pokemon Gold romhack (Gym Leader Lab).

## 0. What Codex should do with this

1. Verify the scope and numeric claims in §1. (Note: this audit ran against
   a worktree snapshot; live state is larger — see §1.)
2. Spot-check the factual Gen 2 claims in §6 against source. Anything where
   Smogon or local engine source disagrees with this document, flag.
3. Argue with the verdicts in §3 / §5 / §8. The hyper-focus calls in §7 are
   the highest-confidence findings.
4. **The user has already reviewed this audit** and agreed with the
   structural diagnosis but rejected the full §9 reorg in favor of a
   smaller staged fix (§9.5). Treat §9 as background; treat §9.5 as the
   active recommendation.
5. If you read a quick_tests / worked_examples / cookbook file I did not
   sample (§12) and it changes a finding, say which and how.

Findings format expected by Codex review: **File / Line / Issue / Why / Fix
/ Confidence**. Where I can give file:line I do.

## 0.1 User feedback on this audit (2026-05-15)

The user reviewed this audit before delivery and noted:

- **Core diagnosis (workspace vs playbook bloat blocking compact heuristics
  at decision time) is correct.** That's the load-bearing finding.
- **Numbers in the first draft were stale.** This worktree's snapshot
  showed 433 files / 3.71M chars / 180 quick_tests / 43 reviews. Live state
  on `codex/cleanup-gsc-rebalance-split` is 638 files / 4.77M chars / 315
  quick_tests / 118 reviews. Numbers below are updated; the diagnosis is
  stronger in live state, not weaker.
- **[active_context.md](docs/pokemon_mastery/active_context.md) is the
  operating entrypoint, not workspace residue.** Earlier draft moved it to
  `workspace/`; that was wrong. It belongs alongside `live_core.md` as
  first-class.
- **ADV OU transfer (§5.3) is off-mission for the current bottleneck.**
  The user's `/pgoal` framing did name Gen 2 *and* Gen 3 — but the active
  wall is GSC unseen move ranking, especially branch-ranking and route
  conversion. Gen 3 is theoretical breadth, not closing-the-gap work.
  Demoted in §5.3 and §10.
- **Per-Pokemon canon pages should be narrower** than the original
  "top-20 mons" plan. The right starter set is the decision-dense few:
  Snorlax (exists), Zapdos, Cloyster, Forretress, Tyranitar, Gengar,
  Jolteon. Plus mechanics-canon for sleep, phazing, crits, Pursuit, Spikes,
  Explosion. 20+ pages up front risks recreating the bloat problem.
- **Fix should be staged and retrieval-focused, not another giant
  reorganization that creates a prettier version of the same overload.**
  See §9.5 for the user's preferred path.

## 1. Scope verified

Audit was performed against a worktree snapshot. User confirmed the live
state on main (`codex/cleanup-gsc-rebalance-split`) is larger; both rows
shown below.

```
                     Snapshot used by audit    Live on main (user verified)
Branch:              claude/cranky-tereshkova-e5565c   codex/cleanup-gsc-rebalance-split
HEAD:                fda90e2b (2026-05-15)             same tip + uncommitted growth
Tracked .md files:   433                               638
Total bytes (md):    3.71 MB                           4.77 MB
Tokens (4 chars/tok): ~925k                            ~1.19M
Subdirectories:      13                                13
```

Per-subdir live counts (main worktree, 2026-05-15):

| Subdir | Files | Delta vs snapshot |
| --- | ---: | ---: |
| quick_tests/ | 315 | +135 |
| reviews/ | 118 | +75 |
| worked_examples/ | 111 | 0 |
| boss_route_maps/ | 25 | 0 |
| heuristic_core/ | 12 | +2 |
| romhack_deltas/ | 9 | 0 |
| policy_cards/ | 9 | 0 |
| pro_notes/ | 6 | 0 |
| external_research_returns/ | 4 | 0 |
| mechanics_fixtures/ | 1 | 0 |
| measurement_reports/ | 1 | 0 |
| battle_captures/ | 1 | 0 |

**The growth since the snapshot is entirely in workspace layers** (quick_tests +135, reviews +75; playbook layers barely moved). This is the diagnosis the audit calls out, observed in motion across the last few days.

Commits on docs/pokemon_mastery/ across all branches at snapshot time:
- `fda90e2b` 2026-05-15 Compress Pokemon mastery live docs
- `6aef5e69` 2026-05-14 docs: checkpoint mastery and presentation artifacts
- `34df885f` 2026-05-13 docs: add pokemon mastery study corpus

If Codex sees a newer commit on another tip, this audit is stale.

## 2. Method

Read in full:
- [docs/pokemon_mastery/README.md](docs/pokemon_mastery/README.md)
- [docs/pokemon_mastery/master_index.md](docs/pokemon_mastery/master_index.md)
- [docs/pokemon_mastery/live_core.md](docs/pokemon_mastery/live_core.md)
- [docs/pokemon_mastery/active_context.md](docs/pokemon_mastery/active_context.md)
- [docs/pokemon_mastery/active_goal.md](docs/pokemon_mastery/active_goal.md)
- [docs/pokemon_mastery/doc_cleanup_audit_2026-05-14.md](docs/pokemon_mastery/doc_cleanup_audit_2026-05-14.md)
- [docs/pokemon_mastery/training_cycle.md](docs/pokemon_mastery/training_cycle.md)
- [docs/pokemon_mastery/study_roadmap_2026-05-14.md](docs/pokemon_mastery/study_roadmap_2026-05-14.md)
- [docs/pokemon_mastery/replay_turn_pause_protocol.md](docs/pokemon_mastery/replay_turn_pause_protocol.md)
- All 8 heuristic_core cards + migration_map + README
- All 9 romhack_deltas files
- [docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md](docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md)
- [docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md](docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md)
- [docs/mechanics_changes_from_base.md](docs/mechanics_changes_from_base.md)

Sampled (not full reads):
- [docs/pokemon_mastery/cookbook.md](docs/pokemon_mastery/cookbook.md) (3,634 lines) — read lines 1-200, 3118-3318, 3618-3635; TOC of 60 recipes via grep.
- [docs/pokemon_mastery/source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md) (2,670 lines) — read lines 1-120 (STP-001, STP-002).

Delegated to parallel breadth agents (4 agents, results synthesized below):
- worked_examples/ (111 files) + reviews/ (43 files) — sampled 17 representative files.
- quick_tests/ (180 files) — sampled 12 representative files.
- boss_route_maps/ (25 files) + pro_notes/ (6 files) — sampled and characterized.
- Smogon GSC OU + ADV OU canon research (web-search heavy) — what a SOTA
  playbook MUST contain.

Plus one spot-check agent on 6 specific Gen 2 mechanics claims (results in §6.1).

Confidence on any subdirectory I delegated breadth-sampling for: medium
(based on 10-15% sample); confidence on files I read in full: high.

## 3. Bloat findings

### 3.1 Top-level token math

`docs/pokemon_mastery/*.md` totals ~1.19M tokens at 4 chars/token on live
state (was ~925k at snapshot). This is **~6× a 200k context window**.
Glob-loading the folder is mathematically impossible. Any "playbook" use
needs an explicit allowlist; the architectural exclusion already exists at
[docs/pokemon_mastery/live_core.md:16-18](docs/pokemon_mastery/live_core.md)
but it is not filesystem-enforced — a naive
`load docs/pokemon_mastery/**` will still pull everything.

The 30% snapshot-to-live growth in <2 days is itself a signal: the
workspace layer is on an active write path that does not pause for
playbook hygiene.

**Confidence: high.** Verifiable by:
`find docs/pokemon_mastery -name "*.md" -exec cat {} + | wc -c`
→ should be ~4.77M chars on main.

### 3.2 quick_tests/ (315 files, ~500k tokens, ~42% of folder)

Breadth agent finding (12-file sample at snapshot): **85-90%
scoring/audit metadata, 10-15% reusable lessons**, and those lessons are
already abstracted into
[docs/pokemon_mastery/policy_cards/](docs/pokemon_mastery/policy_cards/),
[docs/pokemon_mastery/cookbook.md](docs/pokemon_mastery/cookbook.md), and
[docs/pokemon_mastery/source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md).
Every file leads with a `Score Summary:` block plus per-turn frozen-answer-
vs-actual grade tables. Probe files explicitly self-label as
"Mode: constructed nonblind policy regression. This is not a fresh replay
score or final-exam evidence."

This is workspace, not playbook. The architecture knows it
([docs/pokemon_mastery/live_core.md:18](docs/pokemon_mastery/live_core.md)
says "Do not load pre-freeze: ... scored quick tests"). The filesystem
doesn't yet.

The 175% growth (180 → 315) since the snapshot, with no equivalent change
to playbook layers, reinforces this. The write path is generating
measurement provenance, not compact heuristics.

**Confidence: high** that quick_tests/ is not playbook material.
**Confidence: medium** on the 85-90% figure (sample size unchanged).

### 3.3 Four huge aggregator docs

| File | Lines | Tokens | Role | Verdict |
| --- | ---: | ---: | --- | --- |
| [cookbook.md](docs/pokemon_mastery/cookbook.md) | 3,634 | ~55k | 60 source-cited recipes | Keep, split into per-recipe files |
| [worked_examples/live_turn_drills.md](docs/pokemon_mastery/worked_examples/live_turn_drills.md) | 2,713 | ~40k | 33+ "Drill 0NN" entries | Move to workspace (project measurement) |
| [source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md) | 2,670 | ~40k | 58 STP-NN policies | Keep, strip the evidence URLs |
| [pro_notes/03_benchmark_architecture_and_policy_schema.md](docs/pokemon_mastery/pro_notes/03_benchmark_architecture_and_policy_schema.md) | 2,397 | ~36k | JSON benchmark schema | Move to workspace |
| [paused_turn_atlas.md](docs/pokemon_mastery/paused_turn_atlas.md) | 1,749 | ~26k | 60 practice prompts | Move to workspace |

Cookbook is the **single best file** in the folder for competitive-Pokemon
recipes. Sample read (recipes at lines 3118-3318, "GSC Hazard Pressure" /
"Two-Sided Hazard War" / "Sleep Plus Hazard Re-Entry Tax" / "Explosion And
Sacrifice" / "Trade Cascade Ledger") confirms Smogon-grounded content with
clean Trigger / Rule / Check / Failure-signs / Worked-example structure.
At 55k tokens it cannot be loaded alongside anything else. Splittable into
~60 files of ~50 lines each, each topic-tagged.

source_to_policy_ledger has 58 numbered policies (STP-001…STP-058) each
following a clean format. Looking at STP-002 ([source_to_policy_ledger.md:25-120](docs/pokemon_mastery/source_to_policy_ledger.md)):
the rule body is ~3 lines; the remainder is 90+ lines of quick_tests
evidence URLs welded into the body. Strip those URLs to a footer and the
file drops from 40k to ~12k tokens with no playbook information loss.

**Confidence: high** that splitting cookbook + stripping ledger URLs are
size wins. Codex spot-check: read 5 random STP-NN entries and confirm the
"rule body is ~10% of entry" estimate.

### 3.4 Smaller bloat offenders

- 6 `pro_notes/*` files (~80k tokens total) — GPT-5.5 Pro methodology, not
  Pokemon strategy. Breadth agent estimate: ~20% promotable, ~80%
  meta-curriculum.
- 4 `external_research_returns/*` (~40k tokens) — raw Deep Research output,
  intentionally unfiltered per
  [doc_cleanup_audit_2026-05-14.md:47](docs/pokemon_mastery/doc_cleanup_audit_2026-05-14.md).
- 9 date-stamped root `*_2026-05-NN.md` files — process audits and
  handoffs at the same directory level as live decision content.
- [worked_examples/boss_live_turn_practice_run_2026-05-13.md](docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md)
  (54 KB) + [worked_examples/boss_live_turn_prompt_cards.md](docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md)
  (42 KB) — self-scoring runs.

## 4. Organizational findings

### 4.1 What works

| Artifact | Why it works |
| --- | --- |
| [live_core.md](docs/pokemon_mastery/live_core.md) | 66 lines (under its declared 80-line cap); explicitly enumerates what NOT to load pre-freeze; tight single-purpose entrypoint. |
| [heuristic_core/](docs/pokemon_mastery/heuristic_core/) | 8 cards averaging ~20 lines each; uniform Status / Use-when / Rule / Ask / Top-move / Do-not / Archive format. Each card costs ~500 tokens. |
| [master_index.md](docs/pokemon_mastery/master_index.md) "Decision Failure Lookup" table | Indexed by *"what mistake am I trying to stop making?"* — the right shape for a textbook TOC for a player consulting in-game. |
| [romhack_deltas/](docs/pokemon_mastery/romhack_deltas/) | Every doc follows Vanilla baseline → Romhack facts → Strategic translation → "Before advising, ask…". Source-cited with file:line refs into engine asm. |
| [romhack_deltas/mechanics_pending_index.md](docs/pokemon_mastery/romhack_deltas/mechanics_pending_index.md) | Five-tier status taxonomy (`runtime_verified` / `source_verified` / `supplied_unverified` / `unknown` / `not_decision_relevant`) prevents vanilla→romhack mechanics leakage. |

### 4.2 What blocks textbook-style flipping

| Issue | File | Why it matters |
| --- | --- | --- |
| No topic-keyword index. The index is built around mistakes, not topics. | [master_index.md](docs/pokemon_mastery/master_index.md) | A mid-game LLM thinking "should I spin or attack?" can find the right card via failure-lookup, but for "what's Snorlax's expected set", "is +1 Curse Skarmory still phazable?", "does crit ignore the defender's Curse boost?", "is Houndoom Pursuit a real threat?" there is no canonical lookup. |
| Project vocabulary has replaced Smogon-canon vocab in the live layer. | [heuristic_core/*](docs/pokemon_mastery/heuristic_core/), [policy_cards/*](docs/pokemon_mastery/policy_cards/) | "current owner" replaces "lead", "converter" replaces "wincon", "reset loop denial" replaces "phazer chain", "branch punish ranking" replaces "predicting and punishing the pivot". A fresh-context LLM has to learn the project vocab first. |
| `STP-NN` references are opaque at point of use. | [boss_route_maps/brock_turn1_route_sheet.md](docs/pokemon_mastery/boss_route_maps/brock_turn1_route_sheet.md), most worked_examples | Each route sheet cites `STP-001 ... STP-033` without inline definitions. Reader must context-switch to the ledger. |
| Date-stamps in filenames mix recency-search with topic-search. | `quick_tests/replay_turn_pause_036_selfko_absorber_transfer_smogtours-gen2ou-932597_2026-05-14.md` and similar | Fine for an audit trail; poor for "find me the absorber-transfer drill." |
| No "play page" per Pokemon. | Only [romhack_deltas/snorlax_context.md](docs/pokemon_mastery/romhack_deltas/snorlax_context.md) exists. | A SOTA GSC playbook needs one short doc per top-20 OU mon (Snorlax, Zapdos, Raikou, Cloyster, Skarmory, Steelix, Tyranitar, Suicune, Misdreavus, Marowak, Forretress, Starmie, Exeggutor, Jolteon, Machamp, Heracross, Houndoom, Gengar, Nidoking, Umbreon). 19 missing. |

## 5. Topic coverage vs Smogon canon

Cross-referenced against the breadth agent's canonical GSC OU + ADV OU
research (Smogon URLs cited inline). Codex can re-verify the canon list by
fetching [smogon GSC resources](https://www.smogon.com/resources/competitive/gs/).

### 5.1 Covered well

- Hidden-information discipline: [heuristic_core/public_info_tiers.md](docs/pokemon_mastery/heuristic_core/public_info_tiers.md) + [paused_turn_atlas.md](docs/pokemon_mastery/paused_turn_atlas.md) + 40-entry external hidden-info atlas at [external_research_returns/2026-05-14_deep_research_hidden_info_turn_atlas.md](docs/pokemon_mastery/external_research_returns/2026-05-14_deep_research_hidden_info_turn_atlas.md).
- Spikes / Rapid Spin / spinblocker: [romhack_deltas/spikes_and_rapid_spin.md](docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md), [policy_cards/hazard_loop_spin_window.md](docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md), cookbook "GSC Hazard Pressure" / "Two-Sided Hazard War" / "Sleep Plus Hazard Re-Entry Tax".
- Sleep / Sleep Clause / RestTalk: STP-002 alone has 12+ sub-cases; multiple cookbook recipes.
- Explosion / one-time trades: cookbook "Explosion And Sacrifice" / "Trade Cascade Ledger" / "Sacrifice As Active-State Reset" / "Controlled Sack For Clean Entry".
- Snorlax-as-anchor: [romhack_deltas/snorlax_context.md](docs/pokemon_mastery/romhack_deltas/snorlax_context.md) — exemplar.

### 5.2 Covered partially — needs promotion

| Topic | Where it's mentioned | What's missing |
| --- | --- | --- |
| Lead theory | Cookbook "Lead Role Fit Test", "Opening Move As Resource Bid" | The canonical Smogon **lead RPS chart** (Electrics > Cloyster > Snorlax > Electrics; secondary Exeggutor / Nidoking / Jynx / Forretress / Smeargle / Tyranitar). Source: [An Analysis of Leads in GSC OU](https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/). |
| GSC critical hits | Cookbook "Variance Budget Test" + "Risk And Worst Plausible Branch" reference variance | Mechanical nuance: 2× damage, boost-ignore is conditional on stage comparison. See §6.1 below. |
| DV / Hidden Power | [romhack_deltas/speed_order_public_model.md:21](docs/pokemon_mastery/romhack_deltas/speed_order_public_model.md) references DVs and Stat Exp | The shared SpA/SpD DV constraint (a Gen-2 trap for any LLM defaulting to Gen-3+ IV reasoning) is nowhere. HP type/power calc is nowhere. |
| Phazing priority quirk | Alluded to in [romhack_deltas/snorlax_context.md](docs/pokemon_mastery/romhack_deltas/snorlax_context.md) and via Skarmory-Curse setups in route maps | Never stated as a stand-alone rule: priority −1 (not −6, see §6.1), slower mover wins, consequence for Skarmory Curse / Steelix Roar mirrors. |
| Per-Pokemon canonical sets | Snorlax only | Zapdos, Raikou, Cloyster, Skarmory, Steelix, Tyranitar, Misdreavus, Marowak, Forretress, Starmie, Exeggutor, Heracross, Machamp, Houndoom, Gengar, Nidoking, Umbreon, Jynx, Suicune, Miltank — 19 missing. |

### 5.3 Missing entirely

| Topic | Smogon source |
| --- | --- |
| GSC OU Viability Rankings (S+/S/A+/A−/B+/B/B−) | [GSC OU VR mk.4](https://www.smogon.com/forums/threads/gsc-ou-viability-rankings-mk-4.3633233/) |
| Sleep absorber list + Jynx-beats-Zapdos exception | [Lovely Kiss thread](https://www.smogon.com/forums/threads/all-you-millions-embrace-this-lovely-kiss-is-for-the-entire-world.3459278/) |
| Pursuit-trapper / spinblocker / spiker pairings (Mis+Cloy, Gen+Forry, TTar/Doom Pursuit on Starmie/Mis/Gen) | [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats) |
| BoltBeam coverage chart (Rhydon / Steelix / Magneton / Lanturn live it) | [GSC Mechanics](https://www.smogon.com/forums/threads/gsc-mechanics.3542417/) |
| GSC OU archetype catalog (NidoGar / NidoChamp / Jynx-Gengar SO / Triple Thief / Vap Growth / Smeargle BP / DogBoom Stall / Skarm+Lax+Zap balance) | [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/) |
| Sleep Trap Clause + TrapPass Clause | [Mean Look + Spider Web + BP in GSC OU](https://www.smogon.com/forums/threads/mean-look-spider-web-baton-pass-in-gsc-ou.3696148/) |
| GSC critical-hit mechanics primer (2× + conditional boost-ignore) | See §6.1 |
| Endgame PP-counting reference (WW PP=8, Spikes PP=32, Body Slam PP=24) | [Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking) |
| GSC status duration / freeze defrost / Toxic switch-reset / burn quirks | [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status) |
| Item meta primer (Lefties / Berry / Miracle Berry / Thick Club / Light Ball / Thief economy) | [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats) |
| ADV OU transferable lessons | [ADV OU Archetypes](https://www.smogon.com/forums/threads/adv-ou-teambuilding-strategy-archetypes-and-cores-a-data-driven-approach.3654874/), [ADV OU VR](https://www.smogon.com/forums/threads/adv-ou-viability-ranking.3503019/) |

The user's `/pgoal` framing did name Gen 2 *and* Gen 3 transfer. On review,
the user flagged ADV OU as **off-mission for the current bottleneck**: the
active wall is GSC unseen move ranking, especially branch ranking and route
conversion. Gen 3 transfer is theoretical breadth, not closing-the-gap
work. **De-prioritized**; pick up only after GSC fundamentals saturate.

The remaining gaps in this table are real and on-mission. Highest-value
ones to close first (per §0.1 user feedback): GSC critical-hit primer,
phazing-priority primer, sleep absorbers, Pursuit + spinblockers, Spikes
primer, Explosion primer. Lead RPS and viability rankings are next.

## 6. Factual / mechanical concerns

### 6.1 Two GSC nuances worth flagging

Spot-check agent verified 4/6 sampled claims as VERIFIED, 2/6 as NUANCED.

**(a) Phazing priority is −1 in GSC, not −6.** The "slower phazer wins"
mechanic is **correct** and well-modeled in the docs (the Skarmory-Curse
self-slowing strategy appears in route maps). The priority **value** is
−1 in Gen 2 (shared with Counter / Mirror Coat / Vital Throw). The −6
value is Gen 5+. No file I read claims −6 explicitly, but if a future doc
states it that way it will be wrong. **Recommendation:** add the value to
whatever phazing primer is written.
Source: [GSC Move Priority](https://www.smogon.com/gs/articles/move_priority).

**(b) Crits ignore stat boosts conditionally, not unconditionally.** GSC
crits do 2× damage. They ignore attacker offensive and defender defensive
stat modifiers (including burn-Atk halving and Reflect/Light Screen)
**only when the defender's relevant defensive stage ≥ the attacker's
relevant offensive stage**. If the attacker is boosted higher, the crit
uses boosted Atk but the defender's positive boosts still count. Famous
consequence: +0 Machamp crits Reflect Starmie harder than +1 Machamp.
Several cookbook recipes ("Variance Budget Test", "Risk And Worst
Plausible Branch") rely implicitly on crit math. **Recommendation:** state
the rule conditionally in any future crit primer.
Source: [GSC Mechanics thread](https://www.smogon.com/forums/threads/gsc-mechanics.3542417/), [Bulbapedia Critical hit](https://bulbapedia.bulbagarden.net/wiki/Critical_hit).

The other 4 spot-checked claims (SpA/SpD share a DV in GSC; vanilla Spikes
is single-layer 12.5% Flying-immune; Sleep Trap Clause is GSC OU canon;
Houndoom has the strongest Pursuit in GSC OU) are VERIFIED. Codex spot-
check value here: low; these are well-known Smogon canon.

### 6.2 Romhack vs vanilla — no rot detected

I cross-checked sampled romhack claims against
[docs/mechanics_changes_from_base.md](docs/mechanics_changes_from_base.md).
All consistent: Spikes 3-layer 12.5/16.7/25%; Rapid Spin clears all
layers; Dragon's Majesty 0×→0.5× for Dragon attackers; Outrage
category-flip on Dragon users when Atk>SpA; Dark first-status shield
consumption; Psychic 6/256 + 13/256 mind shield; Poison contact
retaliation 10/20%; Air Balloon Ground-immunity then pops; Choice
Band/Specs/Scarf 1.5× + lock; Assault Vest 1.5× SpD + status-move block;
Eviolite 1.5× Def/SpD for evolving species; Quick Claw 60/256 threshold.

The
[romhack_mechanics_firewall.md](docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md)
policy card and
[romhack_deltas/mechanics_pending_index.md](docs/pokemon_mastery/romhack_deltas/mechanics_pending_index.md)
status taxonomy are state-of-the-art for this kind of document.
**Confidence: high.**

### 6.3 Snorlax + Lovely Kiss

[source_to_policy_ledger.md:97-112](docs/pokemon_mastery/source_to_policy_ledger.md)
treats Lovely Kiss Snorlax as a live branch. This is correct: Snorlax can
inherit Lovely Kiss as a Sketch-bred egg move via Smeargle in Gen 2. The
doc handles timing right ("Lovely Kiss Snorlax is a live branch, not a
default"). **No issue.**

## 7. Hyper-focus assessment

Approximate file counts that touch each topic family (grep-based estimate,
not exact):

| Topic family | Files touching | Verdict |
| --- | ---: | --- |
| Hidden-info / public-info discipline | ~70+ | **Over-represented** |
| Boss AI scoring (project-internal) | ~50+ | **Over-represented** (workspace, not playbook) |
| Hazards / Spikes / Rapid Spin | ~50+ | Appropriate |
| Sleep / Sleep Clause / Sleep Talk | ~40+ | Appropriate |
| Snorlax-mirror reasoning | ~20+ | Appropriate |
| Explosion / sacrifice | ~15+ | Appropriate |
| Type effectiveness / passives (romhack) | romhack_deltas + pro_notes/04 | Appropriate for romhack |
| Setup / boost / sweep | ~10 | Light |
| Lead theory / matchup | ~5 cookbook recipes | **Under-represented** |
| Damage calc / breakpoints | Delegated to tools/damage_debugger | **Under-represented** for an LLM playbook |
| Teambuilding archetypes | ~3 cookbook recipes | **Under-represented** |
| Per-Pokemon set sheets | Snorlax only | **Under-represented** |
| ADV OU transfer | None | **Missing** |

Two clearest hyper-foci: (1) hidden-information discipline (the project's
signature problem), (2) boss-AI scoring policy (the project's flagship
implementation). Both are valuable but neither corresponds to "an LLM
picking a move in a competitive GSC game"; both correspond to "an LLM
acting as advisor for the user's romhack project."

**Confidence: high.** Codex spot-check: `grep -l "hidden" docs/pokemon_mastery -r | wc -l` should return ~70+; `grep -l "boss_ai\|boss AI\|BossAI" docs/pokemon_mastery -r | wc -l` should return ~50+.

## 8. Subdirectory verdicts

| Subdir | Files | Tokens | Verdict | Action |
| --- | ---: | ---: | --- | --- |
| `live_core.md` | 1 | <1k | **Keep, exemplar** | Update load-blocklist when subdirs move. |
| `active_context.md` | 1 | ~3k | **Keep, first-class entrypoint** | (User correction: this is the operating routing packet, not workspace residue.) |
| `heuristic_core/` | 12 | ~4k | **Keep, exemplar** | Add 2-3 cards (lead RPS, sleep absorber, Pursuit). Footnote Smogon-canon synonym in each header. |
| `policy_cards/` | 9 | ~6k | Keep | Strip evidence URLs to footer; lead with rule + opposite boundary. |
| `romhack_deltas/` | 9 | ~13k | **Keep, exemplar** | Add stand-alone deltas for Choice items / Assault Vest / Air Balloon / Eviolite / Life Orb / Metronome / Shell Bell / Rocky Helmet / Ditto Imposter / trainer battle rules (all in mechanics_changes_from_base, none have their own delta file). |
| `mechanics_fixtures/` | 1+ | <1k | Keep | Expand per existing fixture plan. |
| `cookbook.md` | 1 | ~55k | Split | Convert to `cookbook/` dir, ~60 files of ~50 lines each, topic-tagged. |
| `source_to_policy_ledger.md` | 1 | ~40k | Trim + keep | Strip quick_tests URLs; should drop to ~12k tokens. |
| `paused_turn_atlas.md` | 1 | ~26k | Move to workspace | Practice material, not playbook. |
| `worked_examples/` | 111 | ~200k | Split | Keep ~15 strong smogtours reviews + pre_battle_route_sheets; move live_turn_drills, drill_scorecard, prompt_cards, *_review_001_* retrospectives to workspace. |
| `reviews/` | 118 | ~200k | Split | Keep long-form Smogon-replay reviews cited from cookbook; move scored *_review_001_*_2026-05-NN.md retros to workspace. |
| `boss_route_maps/` | 25 | ~75k | Keep (romhack layer) | Excellent template + romhack-local content. Not for non-romhack play. |
| `quick_tests/` | 315 | ~500k | **Exclude from playbook** | Move under `workspace/`. Filesystem-enforce the live_core exclusion. |
| `pro_notes/` | 6 | ~80k | **Exclude from playbook** | Move to workspace. ~20% promotable as one consolidated method doc. |
| `external_research_returns/` | 4 | ~40k | **Exclude from playbook** | Move to workspace. Already labeled "raw, filter before integration". |
| `measurement_reports/`, `battle_captures/`, `measurement_progress_ledger.csv` | ~5 | (binary) | **Exclude from playbook** | Workspace. |
| 9 date-stamped root `*_2026-05-NN.md` files | 9 | ~25k | **Exclude from playbook** | Move to workspace. |

## 9. Maximal restructure — preserved for reference, NOT recommended

> User feedback: the §9 blueprint risks becoming "a prettier version of
> the same overload." Treat this as the theoretical end-state, not as the
> active plan. See §9.5 for the recommended staged path.

Token budget after the full restructure (rough): playbook layer ≈ 90k
tokens; workspace layer ≈ 830k tokens. A fresh-context LLM could load the
entire playbook layer with ~110k tokens of context budget remaining for
live game state.

```
docs/pokemon_mastery/
├── README.md                          # playbook-first, <100 lines
├── master_index.md                    # keep, add Topic Lookup
├── live_core.md                       # keep, 80-line cap
│
├── active_context.md                  # operating routing packet (first-class)
├── playbook/
│   ├── heuristic_core/                # 8 cards + 2-3 new ones
│   ├── policy_cards/                  # 8 expanded boundary cards
│   ├── cookbook/                      # ~60 split files, ~50 lines each
│   │   ├── _index.md                  # tagged TOC (hazard/sleep/status/setup/sac/lead/calc)
│   │   ├── gsc_hazard_pressure.md
│   │   ├── explosion_and_sacrifice.md
│   │   └── ... (~58 more)
│   ├── source_to_policy_ledger.md     # trimmed to rules only
│   ├── canon/                         # NEW: Smogon-canon foundation
│   │   ├── gsc_viability_rankings.md
│   │   ├── gsc_top20_mons/
│   │   │   ├── snorlax.md             # already exists (move from romhack_deltas)
│   │   │   ├── zapdos.md
│   │   │   ├── raikou.md
│   │   │   └── ... (17 more)
│   │   ├── lead_rps.md
│   │   ├── sleep_absorbers_and_inducers.md
│   │   ├── pursuit_and_spinblockers.md
│   │   ├── boltbeam_coverage.md
│   │   ├── gsc_archetypes.md
│   │   ├── gsc_crit_mechanics.md      # 2× + conditional boost-ignore
│   │   ├── gsc_dv_and_hp.md
│   │   ├── gsc_phazing_priority.md
│   │   ├── gsc_status_durations.md
│   │   ├── gsc_item_meta.md
│   │   ├── gsc_clauses.md
│   │   └── adv_ou_transfer.md
│   ├── romhack/                       # already exists, expand
│   │   ├── mechanics_pending_index.md
│   │   ├── spikes_and_rapid_spin.md
│   │   ├── type_passive_route_impacts.md
│   │   ├── boss_opening_policy.md
│   │   ├── snorlax_context.md
│   │   ├── speed_order_public_model.md
│   │   ├── present_rollout_function_reclassification.md
│   │   ├── (new) choice_items.md
│   │   ├── (new) assault_vest.md
│   │   ├── (new) air_balloon.md
│   │   ├── (new) eviolite.md
│   │   ├── (new) life_orb_metronome_shell_bell.md
│   │   ├── (new) ditto_imposter.md
│   │   ├── (new) trainer_battle_rules.md
│   │   ├── mechanics_fixtures/
│   │   └── boss_route_maps/
│   └── worked/                        # ~15 strong smogtours replay walkthroughs + pre_battle sheets
│
└── workspace/
    ├── quick_tests/                   # 180 files of scoring metadata
    ├── reviews/                       # *_review_001_*_2026-05-NN.md retrospectives
    ├── live_turn_drills.md
    ├── prompt_cards.md
    ├── practice_run.md
    ├── exact_move_drill_scorecard.md
    ├── pro_notes/
    ├── external_research_returns/
    ├── measurement_reports/
    ├── battle_captures/
    ├── measurement_progress_ledger.csv
    ├── measurement_minigoal_*.md
    ├── training_cycle.md
    ├── study_roadmap_*.md
    ├── doc_cleanup_audit_*.md
    ├── boss_sim_*.md
    ├── boss_ai_re_solve_*.md
    ├── replay_turn_pause_protocol.md
    ├── cross_domain_autonomy_policy.md
    ├── context_management_plan.md
    ├── active_goal.md
    ├── session_handoff_*.md
    ├── goal_*.md
    ├── continue_learning_*.md
    └── paused_turn_atlas.md
```

## 9.5 Recommended staged fix (user-approved 2026-05-15)

The user's preferred approach. Smaller, retrieval-focused, biased toward
fixing the actual bottleneck (GSC unseen move ranking with branch labels
and route conversion) rather than producing a prettier-looking corpus.

### Step 1. Make a smaller default playbook path

Define what the playbook layer actually is. Concretely: the allowlist that
should be loadable in one go before a fresh move-choice decision.

Recommended allowlist:
- [live_core.md](docs/pokemon_mastery/live_core.md)
- [active_context.md](docs/pokemon_mastery/active_context.md)
- [master_index.md](docs/pokemon_mastery/master_index.md)
- [heuristic_core/](docs/pokemon_mastery/heuristic_core/) (all)
- [policy_cards/](docs/pokemon_mastery/policy_cards/) (all)
- [romhack_deltas/](docs/pokemon_mastery/romhack_deltas/) (all)
- [cookbook.md](docs/pokemon_mastery/cookbook.md) (until split — see step 3)
- [source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md) rule bodies only

The exclude rule already exists at [live_core.md:16-18](docs/pokemon_mastery/live_core.md);
this step is to make it a documented allowlist and (optionally) a
filesystem layout.

### Step 2. Move/exclude workspace from default selection

Move out of the default path (preferably into a sibling `workspace/`
subtree or behind a glob filter):
- `quick_tests/` (315 files, ~500k tokens)
- `reviews/*_review_001_*_2026-05-NN.md` retrospectives
- `external_research_returns/`
- `pro_notes/`
- `measurement_*` artifacts
- date-stamped root `*_2026-05-NN.md` audits and handoffs
- [worked_examples/live_turn_drills.md](docs/pokemon_mastery/worked_examples/live_turn_drills.md), [worked_examples/boss_live_turn_practice_run_2026-05-13.md](docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md), [worked_examples/boss_live_turn_prompt_cards.md](docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md), [worked_examples/exact_move_drill_scorecard_2026-05-13.md](docs/pokemon_mastery/worked_examples/exact_move_drill_scorecard_2026-05-13.md)

Do not delete. Move or filter only. The provenance value of these files is
real for the project's measurement loop; the playbook value at decision
time is near zero.

### Step 3. Add a topic lookup/index for precise retrieval

A complement, not a replacement, for the existing Decision Failure Lookup.
Add a Topic Lookup table to [master_index.md](docs/pokemon_mastery/master_index.md)
that lets a decision-time caller pull *only* the entry the position
demands.

Initial topic rows (each points at the existing card / recipe / delta):

- Hazards · Spikes · Rapid Spin · Spinblocker
- Sleep · Sleep Clause · Sleep Talk · Rest · RestTalk
- Status (Toxic / Para / Burn) · clock · absorber
- Setup · Curse · Dragon Dance · Quiver Dance · Belly Drum
- Phazing · Whirlwind · Roar · priority quirk
- Pursuit · trapper · spinblock chain
- Explosion · Self-Destruct · sacrifice · trade
- Lead matchup · opening RPS
- Snorlax route · CurseLax · BellyLax · LK Lax
- BoltBeam coverage · who lives Thunder+IceBeam
- Endgame · PP counting · last-mon forced lines
- Crit math (GSC quirks)
- DV / Stat Exp / Hidden Power (GSC quirks)
- Item meta (Leftovers / Berry / Thick Club / Thief / Choice items in romhack)
- Romhack type passive · contact · Dragon · Dark shield
- Adaptive lead trainer list (romhack)

This table is the single highest-impact item in the staged plan.

### Step 4. Keep training focused on fresh replay turn pauses

The default measurement loop stays: unseen Smogon GSC tournament replay,
turn-pause, top-three ranking with branch labels, score against the actual
choice. Per [replay_turn_pause_protocol.md](docs/pokemon_mastery/replay_turn_pause_protocol.md).

This is the existing rep. The audit changes nothing about it. The goal is
to keep generating signal about what compact heuristics are missing or
miscalibrated — *not* to generate more measurement artifacts that
themselves enter the playbook.

### Step 5. Only promote lessons after repeated misses

Rule: a new heuristic card or policy card is created only when the *same
class of miss* appears across two or more fresh replay-pause runs. One
miss → record in quick_tests/. Two same-class misses → promote into
[heuristic_core/](docs/pokemon_mastery/heuristic_core/) or
[policy_cards/](docs/pokemon_mastery/policy_cards/).

This is the gate that should have been in place to prevent the current
size of [source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md)
(58 STP entries) and [worked_examples/live_turn_drills.md](docs/pokemon_mastery/worked_examples/live_turn_drills.md)
(33+ drills). Going forward, it caps the playbook layer's growth at "rules
that explain a repeated, measured miss."

### Concrete next-action ordering for §9.5

1. **(30 min)** Document the allowlist (step 1) as a section at the top of
   [README.md](docs/pokemon_mastery/README.md), referencing the
   exclusion already in [live_core.md](docs/pokemon_mastery/live_core.md).
2. **(15 min + filesystem move)** Move [quick_tests/](docs/pokemon_mastery/quick_tests/)
   under a sibling `workspace/` subtree. This alone removes ~500k tokens
   from any default glob.
3. **(30 min)** Add the Topic Lookup table to
   [master_index.md](docs/pokemon_mastery/master_index.md) (step 3).
4. **(1-2 h, separate session)** Write **only the six decision-dense
   canon pages** the user named: sleep, phazing, crits, Pursuit, Spikes,
   Explosion. ~50 lines each. Source: the breadth agent's Smogon canon
   research already in this audit.
5. **(eventual, only after canon hit cap)** Write the seven decision-dense
   per-Pokemon pages: Snorlax (move from romhack_deltas/), Zapdos,
   Cloyster, Forretress, Tyranitar, Gengar, Jolteon. Stop there until
   measurement evidence calls for more.
6. **(ongoing)** Apply step 5's "promote on repeated miss" rule to all
   future card-creation.

The full §9 restructure is **not** part of the recommended next action.
ADV OU transfer, top-20 set sheets, cookbook split, and ledger URL strip
are **backlog** (§10), evaluated only after steps 1-6 ship.

## 10. Backlog: supporting actions, not first-pass

Pick up only after §9.5 steps 1-6 ship and there is measurement evidence
the playbook layer still isn't dense enough. Order is impact-per-effort.

| # | Action | Effort | Impact | Confidence in recommendation |
| ---: | --- | --- | --- | --- |
| 1 | Add a **Topic Lookup table** to [master_index.md](docs/pokemon_mastery/master_index.md) alongside the existing Decision Failure Lookup. Topics: Hazards, Sleep, Status, Setup, Pursuit, Phazing, Explosion, Lead RPS, Snorlax mirror, BoltBeam, Endgame PP, Crit math, DV/HP, Item meta, ADV OU transfer. Each row points at the right card / recipe / canon page. | ~30 min | High (closes the textbook-flipping gap) | High |
| 2 | Write the missing `canon/` pages (§5.3). VR list, Lead RPS, Sleep absorbers, Pursuit + spinblockers, BoltBeam coverage, crit mechanics, DV/HP, phazing-priority, GSC clauses, archetypes, ADV OU transfer. Each is 30-100 lines. Source: the breadth agent's Smogon canon notes. | ~2-3 h | High (closes the largest coverage gap) | High |
| 3 | Add per-Pokemon set sheets for top-20 GSC OU mons in the format of [snorlax_context.md](docs/pokemon_mastery/romhack_deltas/snorlax_context.md). Lead with Zapdos / Raikou / Cloyster / Skarmory / Steelix / Tyranitar (the next-most-relevant after Snorlax). | ~1 h each × ≤20 | Medium-high (closes per-Pokemon lookup gap) | Medium |
| 4 | Move [quick_tests/](docs/pokemon_mastery/quick_tests/) (180 files) into `workspace/quick_tests/`. Architectural exclusion already exists at [live_core.md:18](docs/pokemon_mastery/live_core.md); just filesystem-enforce. | ~15 min | High (removes ~300k tokens from playbook glob) | High |
| 5 | Strip quick_tests evidence URLs from each STP-NN in [source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md). Move them to a single footnote section per file. Should drop from 40k to ~12k tokens. | ~1 h | High (compression with no playbook info loss) | Medium-high (Codex verify on 5 random STP entries first) |
| 6 | Split [cookbook.md](docs/pokemon_mastery/cookbook.md) into a `cookbook/` directory with ~60 files. Mechanical work: every `## Recipe:` becomes a file. Add `cookbook/_index.md` with tag columns. | ~2-3 h | High (makes 60 recipes individually addressable) | High |
| 7 | Move date-stamped process audits, pro_notes, external_research_returns, measurement reports into `workspace/`. | ~15 min | Medium (clarifies playbook scope) | High |
| 8 | Once `canon/` exists, retrofit heuristic_core card headers to surface Smogon-canon synonyms. ("Branch Punish Ranking, a.k.a. predicting and punishing the opponent's pivot.") Keeps project vocab while bridging to canon. | ~30 min | Medium | Medium |
| 9 | Add `romhack/` deltas for Choice items / Assault Vest / Air Balloon / Eviolite / Life Orb / Metronome / Shell Bell / Rocky Helmet / Ditto Imposter / trainer rules. All affect move recommendations and damage math; none currently have a stand-alone page. | ~30 min each × 10 | Medium-high for romhack play, low for vanilla GSC | High |

## 11. What NOT to do

| Anti-action | Why |
| --- | --- |
| Delete any workspace file | Every workspace file is provenance for a measurement decision; deletion violates [doc_cleanup_audit_2026-05-14.md:52-58](docs/pokemon_mastery/doc_cleanup_audit_2026-05-14.md) "Do Not Remove" guidance and loses the audit trail. Move, don't delete. |
| Deduplicate heuristic_core / policy_cards / cookbook into one layer | The three layers serve different load budgets (tiny pre-freeze / boundary reference / postmortem recipe). The architecture is right. |
| Standardize project vocabulary onto Smogon canon — augment, don't replace | Project vocab ("converter", "owner", "branch punish") is more precise for "which move converts a route in this exact state". Smogon canon vocab is more precise for cross-referenceable Pokemon knowledge. Surface both. |
| Merge `cookbook.md` with `source_to_policy_ledger.md` | Cookbook is procedural recipes; ledger is single-rule policies with provenance. Different mental shapes. |
| Add Showdown-current-ladder content unless the goal explicitly changes | The framing is competitive GSC singles, which Smogon GSC OU is — but the romhack adds Choice / Assault Vest / Eviolite that are not GSC OU canon. A SOTA playbook here is "Smogon GSC OU + romhack deltas," not "Showdown current ladder." |

## 12. Coverage limits / what wasn't read

- [cookbook.md](docs/pokemon_mastery/cookbook.md) — sampled, not full read. 200 of 3,634 lines at the top, 200 mid, 17 closing. The other 3,200 lines are characterized via the section TOC only.
- [source_to_policy_ledger.md](docs/pokemon_mastery/source_to_policy_ledger.md) — first 120 lines (STP-001 and STP-002) read; STP-003 through STP-058 are characterized via the consistent format observed.
- [pro_notes/03_benchmark_architecture_and_policy_schema.md](docs/pokemon_mastery/pro_notes/03_benchmark_architecture_and_policy_schema.md) — 2,397 lines — only agent characterization, no direct read. Agent estimate: 85% process / 15% strategy.
- worked_examples/ — 17 of 111 sampled.
- reviews/ — 5 of 43 sampled.
- quick_tests/ — 12 of 180 sampled.
- boss_route_maps/ — 4-5 of 25 sampled.
- I did not exhaustively grep for ADV OU mentions. A few ADV URLs exist in the cookbook source list (Gyarados, Tauros, Swiss replays); not internalized as a transfer page.
- I did not verify every romhack mechanics claim against engine source — only the sampled ones in §6.2.

## 13. Open questions for Codex

Some of the original open questions were closed by the user's 2026-05-15
review (folded into §0.1 and §9.5). The remaining ones:

1. **Is the 85-90% "scoring metadata" estimate for quick_tests/ accurate
   at the live 315-file count?** Original sample was 12/180. Codex: read
   20 random quick_tests files sampled across `replay_turn_pause_*` and
   `*_probe_*` and report the true reusable-lesson fraction. Higher fraction
   weakens §9.5 step 2's "move quick_tests out wholesale" call.
2. **Is the cookbook genuinely SOTA, or are there hidden issues in the
   ~3,200 unread lines?** Codex: read 10 random `## Recipe:` sections and
   flag any that contradict Smogon canon or contradict
   [docs/mechanics_changes_from_base.md](docs/mechanics_changes_from_base.md).
   Cookbook is on the §9.5 allowlist; if it has rot, that's a step-1 problem.
3. **Is pro_notes/03 really 85% process / 15% strategy?** Codex: read it
   in full and report the actual fraction. If higher than 15% strategy,
   adjust the "move to workspace" recommendation.
4. **Does §9.5 step 5 ("promote on repeated miss") match the project's
   actual measurement workflow?** The rule sounds clean in audit prose;
   Codex should validate that it's implementable given the
   [replay_turn_pause_protocol.md](docs/pokemon_mastery/replay_turn_pause_protocol.md)
   error-class taxonomy. If the protocol already supports a "this miss
   class has appeared N times" query, perfect. If not, step 5 needs an
   instrumentation note.
5. **Is anywhere in the docs claiming GSC phazing priority = −6?** I did
   not find it; Codex grep to confirm. If found, it's wrong (§6.1).
6. **Is anywhere claiming GSC crits ignore stat boosts unconditionally?**
   I did not find it explicitly, but several variance-budget recipes
   assume crit math. Codex grep + check the implied math.
7. **Does the "no per-Pokemon set sheet besides Snorlax" claim survive a
   full grep?** If a per-Pokemon canonical-set doc exists elsewhere, the
   §5.2 finding and §9.5 step 5's "decision-dense seven" list need
   adjustment.
8. **Is the §9.5 staged plan itself worth shipping, or does it create more
   process overhead than the current ad-hoc workspace?** This is the
   meta-question. If the project would be better served by simply
   enforcing the existing [live_core.md](docs/pokemon_mastery/live_core.md)
   exclusion at the loader level — without any filesystem moves, allowlist
   docs, or topic-lookup tables — Codex should say so.

## 14. Numeric verification commands

For Codex spot-checks:

```bash
# Total token estimate (target: ~3.7M chars / 4 = ~925k tokens)
find docs/pokemon_mastery -name "*.md" -exec cat {} + | wc -c

# Per-subdir file counts
find docs/pokemon_mastery -mindepth 2 -type f -name "*.md" \
  | awk -F/ '{print $3}' | sort | uniq -c | sort -rn

# Biggest .md files (target: cookbook.md 3634, live_turn_drills.md 2713,
# source_to_policy_ledger.md 2670, pro_notes/03 2397, paused_turn_atlas 1749)
find docs/pokemon_mastery -name "*.md" -exec wc -l {} + | sort -n | tail -10

# Cookbook recipe count (target: 60)
grep -c "^## Recipe:" docs/pokemon_mastery/cookbook.md

# STP-NN count (target: 58)
grep -c "^## STP-" docs/pokemon_mastery/source_to_policy_ledger.md

# Hidden-info file count (target: ~70+)
grep -l "hidden" docs/pokemon_mastery -r | wc -l

# Boss-AI file count (target: ~50+)
grep -l -E "boss_ai|boss AI|BossAI" docs/pokemon_mastery -r | wc -l

# Per-Pokemon set sheets (target: 1, Snorlax only)
ls docs/pokemon_mastery/romhack_deltas/ | grep -E "_context.md$"
```

If any of these numbers differ materially from this audit, this document
is stale or wrong on that point. Report which.
