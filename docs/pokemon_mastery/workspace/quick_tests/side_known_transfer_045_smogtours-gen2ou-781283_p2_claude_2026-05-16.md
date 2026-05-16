# Side-Known Transfer 045 - Claude run - 2026-05-16 - smogtours-gen2ou-781283 (p2 mrsoup)

Source: https://replay.pokemonshowdown.com/smogtours-gen2ou-781283 (GSC OU Global Championship 2024 Finals, MrSoup vs Siatam game 1)
Mode: side-known reconstructed; p2 (mrsoup); standard GSC OU sets used as strong prior with per-turn fallbacks
Contamination control:
- Reconstruction peek: full log (turns 1-102) inspected ONCE for SPECIES list only (p2 = Charizard, Cloyster, Exeggutor, Snorlax, Steelix, Umbreon; p1 = Forretress, Gengar, Nidoking, Snorlax, Tyranitar, Zapdos). No moves / items / KO order / turn outcomes used from beyond the turn under freeze.
- Per-turn workflow: `python tools/pokemon_mastery/replay_turn_pause.py <log> prompt --turn N` → freeze → `... reveal --turn N` → score.
- No reading of the parallel `_codex_` artifact until both runners' done-marker lines are appended.
- Date in artifact name (2026-05-16) follows the packet spec's date convention even though the calendar date is 2026-05-15; this is the literal date the spec is parameterized on.

## Score Summary

```
Decisions:                       30 / 30  (T1-T31 minus T15 unscored sleep-no-action)
Top-match:                       15 / 30   (target: >=20/30 to claim intervention working) - NOT MET
Acceptable-match:                23 / 30   (baseline 044: 29/30 — fell 6 from baseline)
Positive-selection:              22 / 30
Route-converting move chosen:    21 / 30   (baseline 044: 22/30 — fell 1)
Branch-punish chosen:            18 / 30   (baseline 044: 21/30 — fell 3)
Role-package update obeyed:      24 / 30
Actual in frozen top three:      25 / 30   (baseline 044: 25/30 — held)
Actual branch named before:      21 / 30   (baseline 044: 27/30 — fell 6)
Severe blunders:                  1 / 30   (must be 0) - NOT MET (T12 Cloyster Boom into Gengar)
Hidden-info errors:               1 / 30   (must be 0) - NOT MET (T12 — failed to label "Forry stays" as strong-prior read)
State errors:                     0 / 30   ✓
Mechanics errors:                 0 / 30   ✓
Earliest meaningful error:       Turn 12 (Cloyster Explosion into Gengar Ghost immunity — severe blunder + hidden_info failure to price Ghost-pivot branch)
```

Per-turn `top_rank_failure` tags (across the 15 top-match misses):
- route_budget: T1, T3, T10, T11, T21, T25, T26 (7)
- candidate_weighting: T4, T14 (2)
- missing_candidate / H1-CG: T2, T9 (2)
- hidden_package_reveal: T7, T14, T24 (3)
- branch_probability / status_branch_obedience: T12, T23 (2)
- candidate_weighting (Curse vs ST): T29 (1)
- none (no miss): T5, T6, T8, T12 was top match but blunder, T13, T17-20, T22, T23 top match but state-branch failure, T27, T28, T30, T31 (15 top matches; some have audit failures)


## Pre-freeze loaded cards baseline

Always-loaded for every turn unless explicitly noted:
- `live_core.md` (with Load-Required Triggers block)
- `active_context.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/name_current_owner.md`

Triggered cards loaded per turn per the Load-Required Triggers block — listed in each turn's "Pre-freeze loaded cards" field.

Spec discrepancy: spec lists `heuristic_core/role_package_ledger.md` in the always-load baseline, but no such file exists in heuristic_core/. I substitute `name_current_owner.md` (closest live card on role tracking) and proceed; flagged for spec maintainer.

## Turn 1

Public state: turn-1 lead RPS. p1a Nidoking 100/100 (Siatam). p2a Exeggutor 100/100 (mrsoup).
Pre-freeze loaded cards: baseline + `heuristic_core/reset_loop_denial.md` (Rest-in-package strong prior — Snorlax behind), `heuristic_core/converter_before_script.md` (Sleep Powder is converter vs Nidoking; Psychic/safe switch both tempting).
Trigger compliance: reset_loop_denial loaded (Rest implied by Snorlax presence on team); spend_or_save_piece NOT loaded (no piece <80% / statused / Spikes tax yet); converter_before_script loaded (converter exists, safe-switch tempting).

My (p2) freeze:
- Recommended: Sleep Powder on Nidoking.
- Confidence: 50/30/20.
- Route reason: Sleep-clause Nidoking removes a hazard partner / coverage threat from Siatam's main line; one denied piece for a 75%-acc swing.
- Top three:
  1. Sleep Powder — converts to sleep-clause lock if it lands; opens Spikes-pressure for me later.
  2. Psychic — guaranteed chip on Nidoking (Poison/Ground takes 2x); no LK risk to Eggy.
  3. Switch Snorlax — preserves Eggy as sleep absorber + late breaker; eats Nidoking's main attacks; trades Lefties to Thief at worst.
- Serious alternatives: switch Steelix (resists Ice Beam, eats EQ for 1x, threatens back).
- Rejected tempting safe line: switch Cloyster (gives Nidoking a free turn, opens to Earthquake chip + sets nothing).
- Worst plausible branch: Nidoking is Lovely Kiss / mixed (Thunder/Ice Beam/EQ/LK). If LK on Eggy, I lose sleep clause; if I'd switched Snorlax, Snorlax eats LK (worse — sleep clause burned on tank). Sleep Powder hedges by racing Nidoking.
- Public-info tier: Nidoking moveset is `strong prior` (mixed Nidoking is the GSC norm); Snorlax-has-Rest is `strong prior`.
- Branch-punish audit per top-3:
  - Sleep Powder beats Thief/EQ/Ice Beam Nidoking turns; loses to Lovely Kiss / Thunder crit branches.
  - Psychic beats Thief/Lefties chip; loses to Lovely Kiss (Eggy slept, no Eggy progress) and Counter (mixed Nido carries Counter sometimes).
  - Switch Snorlax beats EQ/Ice Beam Nido but loses to Lovely Kiss Nido and to Thief (Snorlax loses Lefties).

Actual: switch Exeggutor -> Snorlax. Nidoking Thief stole Snorlax's Leftovers (95/100). Sleep clause untouched.

Grade: acceptable_match. Actual was my 3rd-ranked option; same defensive route family (preserve Eggy sleep slot for late-game high-value target) but mrsoup explicitly priced "Nidoking has no Lovely Kiss" higher than I did. My Sleep Powder pick spends sleep on the weakest mon in Siatam's win condition.
top_rank_failure: route_budget (under-weighted "save sleep for late-game tank Tyranitar / Snorlax / Zapdos" vs "lock Nidoking now"; sleep slot is a one-shot resource).
positive_selection: 1 (preserved sleep slot; switched into the right tank).
route_converting_move_chosen: 0 (switch is preservation, not conversion; but acceptable because the conversion would have been wrong-target).
branch_punish_chosen: 1 (named Nidoking branch family correctly; switch-Snorlax beats EQ/Ice Beam branch + tanks LK with the absorber that has Rest, NOT sleep clause loss... wait Snorlax slept = clause burned. So actually mrsoup's switch carries sleep-clause risk vs Nidoking-with-LK. The play assumes no-LK Nido.).

## Turn 2

Public state: p1a Nidoking 100/100 (Thief revealed, holding stolen Lefties). p2a Snorlax 95/100, itemless. p2 bench: Eggy + 4 unrevealed.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Rest-in-package strong prior on my Snorlax + Forretress phaze/Spikes possible), `spend_or_save_piece.md` (Snorlax is unique-role Curse/Rest piece facing future Spikes-entry tax from incoming Forretress switch), `converter_before_script.md` (Body Slam para is a converter; Curse and EQ are script-ish).
Trigger compliance: all three trigger blocks fired and loaded.

My (p2) freeze:
- Recommended: Curse.
- Confidence: 55/25/15.
- Route reason: Nidoking either stays (chip EQ, I get +1/+1 free) or pivots to Forretress / Tyranitar (still +1/+1 free); Snorlax becomes the late-game sweeper that bypasses Forretress's spin role and threatens Ttar more cleanly.
- Top three:
  1. Curse — turns 5% chip into +1 Atk/+1 Def free vs any common switch; key prep against Forretress phaze inability.
  2. Body Slam — 30% para chance on Nido; immediate route impact if para lands.
  3. Earthquake — 1x on Nidoking (~30%); strong vs Forretress switch (2x SE), bad vs Tyranitar switch (Ttar Rock Slide first).
- Serious alternatives: Lovely Kiss (only if Snorlax has it; strong prior is Curse Lax NOT LK Lax in 2024 GSC, so demote).
- Rejected tempting safe line: Rest (over-healing for 5% chip; burns Sleep Talk reset slot if STalk-less).
- Worst plausible branch: Lovely Kiss Nidoking (Snorlax slept; sleep clause burned for me). Curse hedges via "if Nido LK, I sack one turn into setup; if Nido switches Forry to absorb, I still get Curse off."
- Public-info tier: Nidoking has LK is `possible only`; Snorlax has Curse is `strong prior` (championship-level Curse Lax > LK Lax in 2024); Forretress has Spikes is `strong prior`.
- Branch-punish audit per top-3:
  - Curse beats Forry-switch + Ttar-switch + Nido-stay; loses to LK Nido.
  - Body Slam beats Nido-stay (para chance); loses to Forry-switch (resisted, no para useful on Forry) + LK Nido.
  - EQ beats Forry-switch (SE); loses to Ttar-switch (eats Rock Slide first) + LK Nido.

Actual: double switch — p1 Siatam Nidoking -> Forretress; p2 mrsoup Snorlax -> Exeggutor. Forretress 100/100 vs Exeggutor 100/100.

Grade: top_match miss. Actual was a switch-out (Eggy in), NOT in my Snorlax-stays top-3.
top_rank_failure: candidate_weighting / missing_candidate — I did not generate the "Nido is depleted on lead value (Thief used), Siatam will pivot to Forry for Spikes; pre-empt by bringing Eggy back in to threaten Sleep Powder on Forry / forced switch chain". My model defaulted to "active piece chooses its own best move" rather than "predict opponent pivot and counter-pivot Eggy in."
Acceptable_match: 0. The actual route is a counter-pivot to threaten Forry; my Curse keeps Snorlax in and does not threaten Forry's Spikes job at all. Different route entirely.
positive_selection: 0 (Curse on Snorlax that is leaving anyway / opponent leaving anyway = wasted setup turn). Net 0; the play would let Forry switch in and set Spikes for free.
route_converting_move_chosen: 0 (Curse converts vs a stay, not vs the obvious pivot chain).
branch_punish_chosen: 0 (I named Forretress as a possible switch-in but did not pick the action that punishes it — Sleep Powder on Eggy or even Eggy-switch-in to Forry pre-emptively).
role_package_update_obeyed: 0 (Snorlax-role update should have been "sit out, preserve" once Nido lost its Thief value).

This is the kind of plateau-class miss that the Load-Required Triggers intervention is targeting: `spend_or_save_piece.md` WAS loaded, the rule was there ("preserve if the job still owns a future route"), but my ranking ignored it. H2 (card-loaded-but-ignored), not H1.

## Turn 3

Public state: p1a Forretress 100/100. p2a Exeggutor 100/100. Eggy vs Forry direct. Nidoking 100/100 still healthy with Thief revealed + stolen Lefties. Snorlax 95/100 itemless behind.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Forretress = the Spikes/Spin reset engine), `spend_or_save_piece.md` (Eggy is the unique sleep-clause vehicle; spending here saves Cloyster for the right matchup), `converter_before_script.md` (Sleep Powder is the route converter; switch is the safe script).
Trigger compliance: all three loaded.

My (p2) freeze:
- Recommended: Sleep Powder on Forretress.
- Confidence: 60/25/15.
- Route reason: Forretress is Siatam's hazard engine (Spikes + Spin). Locking Forry asleep cripples Siatam's reset loop on my side AND lets my Cloyster set Spikes uncontested later. Highest-converting use of sleep clause.
- Top three:
  1. Sleep Powder — converts sleep clause on Siatam's spinner; Eggy is faster, hits before Forry's Spikes.
  2. Switch Cloyster — mirror Spikes / Spin engine; safer; preserves Eggy sleep slot for a higher-value target (Tyranitar / Snorlax).
  3. Stun Spore — para Forry (slower, future flinch chains); same 75% acc cost as Sleep Powder but burns para clause instead of sleep clause.
- Serious alternatives: Hidden Power on Forry (HP Bug is resisted; HP Fire would be great but uncommon on Eggy).
- Rejected tempting safe line: Psychic (Bug/Steel double resist Psychic = 0.25x; near no chip).
- Worst plausible branch: Forretress carries Sleep Talk (possible only in GSC). If so, Sleep Powder still burns my sleep clause for almost nothing; Forry sleep-talks to Spikes anyway. Fallback if read wrong: switch Eggy out to Steelix next turn.
- Public-info tier: Forry has Spikes/Spin/Explosion/HP-or-Toxic = `strong prior`. Forry has Sleep Talk = `possible only`. Forry has Earthquake = `possible only` (some sets carry EQ).
- Branch-punish audit per top-3:
  - Sleep Powder beats Forry-Spikes (locks); beats Forry-Spin (no Spikes to spin anyway, AND Forry sleeps); loses to Sleep Talk Forry + acc miss branch.
  - Switch Cloyster beats Forry-Spikes (mirror); loses to Forry-Explosion (KOs Cloyster) and Forry-EQ (4x SE on Cloyster — water/ice not resist to Ground; Cloyster Water/Ice takes EQ 1x; but Forry doesn't usually have EQ).
  - Stun Spore beats Forry-Spikes-Spin loop (slow Forry helps); loses to Sleep Talk-irrelevant (Stun Spore not sleep) BUT burns para clause instead of sleep — better hedge if I suspect Sleep Talk.

Actual: Siatam double-switch Forretress -> Zapdos; mrsoup Stun Spore on incoming Zapdos (MISS). Sleep clause untouched, para clause untouched.

Grade: top_match = 0. Actual was my #3.
Acceptable_match = 1. Stun Spore and Sleep Powder are same family (status the incoming threat); Stun Spore was the correct route-budget call to save sleep clause for higher-value targets (Snorlax mirror, Tyranitar) — the same "save sleep slot" diagnosis from Turn 1 applies.
top_rank_failure: route_budget — sleep-clause is a one-shot resource; mrsoup's prior is "Snorlax mirror is where sleep clause is worth most" or "Lovely Kiss Snorlax incoming → save my sleep slot." I underweighted this for the second time in three turns. This is the H2 class the `reset_loop_denial.md` card has language for ("progress counts only if the opponent cannot reset it for free") but I did not apply it to the SLEEP RESOURCE itself, only to the spinner/spike loop. The card is loaded, the rule is there, but my ranker chose the wrong target.
positive_selection: 1 (Stun Spore on Zapdos would para the main electric attacker; correctly aimed at converter even though it missed).
route_converting_move_chosen: 1.
branch_punish_chosen: 1 (Forry-Spikes branch named; Zapdos-pivot in worst-plausible was implicit via "Forry-Spikes" being the named branch).
role_package_update_obeyed: 1.
mechanics_error: 0.

## Turn 4

Public state: p1a Zapdos 100/100. p2a Eggy 100/100 (Stun Spore revealed, sleep slot untouched). p1 bench: Forry 100, Nido 100. p2 bench: Snorlax 95 itemless + 4 unrevealed.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Rest in package + Zapdos Thunder Wave is a route-reset threat), `spend_or_save_piece.md` (Eggy is the unique sleep-clause vehicle; preserving for Snorlax mirror / Ttar sleep), `converter_before_script.md` (Sleep Powder is the route converter; Steelix-switch is the safe script).
Trigger compliance: all three loaded.

My (p2) freeze:
- Recommended: switch Exeggutor -> Steelix.
- Confidence: 45/35/20.
- Route reason: Steelix is the Electric immunity (Ground typing immune to all Electric attacks). Zapdos cannot threaten Steelix's HP meaningfully; Steelix Roar threat phazes Zapdos away into a Spikes turn if I have Spikes up later. Preserves Eggy at 100/100 as the sleep vehicle for Snorlax-mirror late game.
- Top three:
  1. Switch Steelix — Electric-immune wall; preserves Eggy sleep slot; threatens Roar / Curse.
  2. Sleep Powder on Zapdos — burns sleep clause on the fastest threat (a strong route-budget call); Eggy takes Thunder / HP Ice first (Zapdos faster); maybe Eggy survives at 30/100.
  3. Switch Snorlax — Snorlax eats Thunder 1x (~25%); Curse setup; risks LK Zapdos (rare).
- Serious alternatives: Stun Spore on Zapdos (para'd Zapdos = slow Zapdos; doesn't burn sleep clause).
- Rejected tempting safe line: Psychic (neutral chip, ~25% on Zapdos; Eggy still likely KO'd by Thunder reply).
- Worst plausible branch: Zapdos has Thunder Wave (paralyzes Eggy on switch attempt? No, switches happen first, then moves — but if I switch Steelix in, Thunder Wave fails because Ground immune to Electric. If I stay and Sleep Powder, Zapdos Thunder Wave → Eggy para'd; then Sleep Powder fires anyway). Steelix-switch is the cleanest hedge.
- Public-info tier: Zapdos has Thunder/Drill Peck/HP-Ice/Thunder Wave = `strong prior`. Zapdos has Lovely Kiss = `possible only`. Zapdos has Reflect/Light Screen = `possible only`.
- Branch-punish audit per top-3:
  - Switch Steelix beats Thunder (immune), Thunder Wave (immune), HP Ice (Steel resists Ice = 0.5x); loses to Drill Peck (1x ~25% chip on Steelix) which is acceptable; loses worst-case to Zapdos-stays-and-spams-Drill-Peck eating Steelix HP slowly.
  - Sleep Powder beats Zapdos-Thunder-Wave (Eggy para'd but sleep fires; Zapdos slept); loses to Thunder + critical hit (Eggy KO'd before Sleep Powder fires? No, Zapdos faster but doesn't OHKO; Eggy survives at low HP and fires Sleep Powder). Acceptable hedge but variance-heavy.
  - Switch Snorlax beats Drill Peck (Normal eats Flying 1x; Snorlax bulky); loses to Thunder-crit and LK Zapdos.

Actual: Siatam Zapdos -> Forretress (double-pivot to Forry); mrsoup Stun Spore on incoming Forretress -> PARALYZED.

Grade: top_match = 0. Stun Spore (any target) was NOT in my ranked top-3 (only mentioned as "serious alternative" for Zapdos). Actual_in_top_3 = 0.
Acceptable_match = 1. Same route family as my #2 Sleep Powder (status the threat for clause value); the differentiator was that mrsoup correctly read Siatam's "predict-me-Steelix-and-pivot-Forry" line and chose Stun Spore — which is good vs BOTH outcomes (paralyzes Zapdos-stay OR incoming Forry).
top_rank_failure: candidate_weighting — Stun Spore was generated but ranked as "serious alternative" rather than top-3; the card content (`converter_before_script.md` saying "rank route-changing actions before default scripts") was loaded, but I treated Switch Steelix as the defensive primary instead of recognizing Stun Spore as the "good-on-both-branches" converter. This is H2 (loaded but underweighted).
positive_selection: 1 (Stun Spore para's Forry is a real route improvement — Forry now slow + 25% full-para → Spikes setup crippled).
route_converting_move_chosen: 1.
branch_punish_chosen: 0 (my Steelix-switch punishes the Zapdos branch but not the Forry-pivot branch; mrsoup's Stun Spore punishes BOTH).
role_package_update_obeyed: 1.
mechanics_error: 0. state_error: 0. hidden_info_error: 0. severe_blunder: 0.

## Turn 5

Public state: p1a Forretress 100/100 PAR (Stun Spore landed). p2a Eggy 100/100. p1 bench: Nido 100, Zapdos 100, +3 unrevealed. p2 bench: Snorlax 95 itemless +4 unrevealed.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Spikes/Spin/Boom loop active on Forry), `spend_or_save_piece.md` (Cloyster is the right matchup; bringing in for Spikes mirror is "use" not "spend"), `converter_before_script.md` (Sleep Powder on para'd Forry FAILS — Gen 2 status mutex; ruling out as candidate per mechanics).
Trigger compliance: all three loaded. Mechanics note: Sleep Powder fails on already-statused target in Gen 2.

My (p2) freeze:
- Recommended: switch Exeggutor -> Cloyster.
- Confidence: 50/25/25.
- Route reason: Para'd Forry is crippled (25% full-para risk + slowed). Bring in Cloyster to mirror Spikes job. Forry's Spikes setup is degraded by para; Cloyster's is not. Net hazard advantage.
- Top three:
  1. Switch Cloyster — Spikes mirror; Cloyster outspeeds para'd Forry (Spe 70 vs slowed-Forry); takes Boom for ~70% but survives; sets Spikes if Forry full-para's.
  2. Switch Steelix — Steelix EQ Forry 2x SE (Bug/Steel — Ground SE through Steel half); Steelix walls Boom for ~60% damage. Trades cleanly but burns my Zapdos answer.
  3. Psychic on Forry — 0.25x resisted (Bug/Steel double-resist Psychic); basically inert chip while Forry sets free Spikes. Listed for completeness only.
- Serious alternatives: Sleep Powder on Forry (FAILS — already statused; rejected on mechanics).
- Rejected tempting safe line: Stay-and-spore again (no second status fits; wasted turn).
- Worst plausible branch: Forry Explosion (Normal STAB Boom; Cloyster takes ~70%, Steelix takes ~60%, Snorlax takes ~50%). Cloyster-switch is the trade I prefer because Cloyster's job (Spikes) is achieved before Boom and Cloyster's late-game spin role is less critical than Steelix's wall role.
- Public-info tier: Forry has Explosion = `strong prior`. Forry has Sleep Talk = `possible only`.
- Branch-punish audit per top-3:
  - Switch Cloyster beats Spikes-Forry (mirror); loses to Boom-Forry (Cloyster takes 70%; trades route piece) and Forry-switch-out (free pivot).
  - Switch Steelix beats Spikes-Forry + Boom-Forry (Steelix EQ 2x KO threat next turn); loses to Forry-switch-out (Zapdos comes back and Steelix walls but doesn't damage = stall).
  - Psychic beats nothing.

Actual: p2 mrsoup switch Eggy -> Cloyster; p1 Forretress Spikes (1 layer on p2 side; Cloyster eats it).

Grade: top_match = 1 (EXACT). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
positive_selection = 1; route_converting = 1; branch_punish_chosen = 1; role_package_update = 1.
mechanics_error = 0; state_error = 0; hidden_info = 0; severe = 0.
top_rank_failure: none.

## Turn 6

Public state: p1a Forry 100 PAR (Spikes revealed). p2a Cloyster 100. p2 side has 1 layer of Spikes.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Spikes mirror war), `spend_or_save_piece.md` (Cloyster job is ongoing), `converter_before_script.md` (Spikes = converter, Spin = reactive).
Trigger compliance: all three loaded.

My (p2) freeze:
- Recommended: Spikes (Cloyster).
- Confidence: 60/25/15.
- Route reason: Mirror Forry's Spikes; Cloyster outspeeds para'd Forry (70 vs slow Forry); Spikes goes up on Siatam side this turn before Forry can act.
- Top three: 1) Spikes, 2) Rapid Spin, 3) Surf.
- Serious alternatives: Switch Steelix (overkill; Cloyster has the right matchup).
- Rejected tempting safe line: Surf (Water 0.5x on Bug/Steel; minimal chip).
- Worst plausible branch: Forry Explosion — Cloyster takes ~70% but survives (high Def 180); Forry dies. Trade favorable for me long-term.
- Public-info tier: Forry Boom = `strong prior`. Forry HP-Fire = `possible only`.
- Branch-punish audit: Spikes beats Forry-Spikes (mirror, even); loses to Boom (Cloyster damaged but survives; trade still net positive); Spin would over-react to current 1-layer state.

Actual: Cloyster Spikes (1 layer on p1 side). Forry Toxic -> Cloyster (tox; Cloyster badly poisoned).

Grade: top_match = 1 (EXACT). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1 (named Boom; Toxic was un-named branch — should have priced Forry-Toxic as possible-only).
positive_selection = 1; route_converting = 1; branch_punish_chosen = 1; role_package_update = 1.
mechanics_error = 0; state_error = 0; hidden_info = 0; severe = 0.
top_rank_failure: none. Note: Forry Toxic reveal shortens Cloyster's spin window — Cloyster now has ~6-7 turns of useful life. Trigger for `rescore_after_reveal.md` next turn.

## Turn 7

Public state: p1a Forry 100 PAR (Spikes/Toxic revealed; 1 layer on p1 side). p2a Cloyster 100 TOX (Spikes revealed; 1 layer on p2 side). Toxic-counter on Cloyster: 1 (6% chip at end of T7).
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (mirror Spike-Spin-Boom loop with Cloyster on death clock), `spend_or_save_piece.md` (Cloyster's spin/Boom is a cash-out window), `converter_before_script.md`, `rescore_after_reveal.md` (Toxic reveal from Forry just shortened Cloyster timeline).
Trigger compliance: all four loaded.

My (p2) freeze:
- Recommended: Rapid Spin (Cloyster).
- Confidence: 45/35/20.
- Route reason: Clear my 1 layer of Spikes so my Steelix/Snorlax/Char switch-ins land clean. Cloyster has ~4 turns left on Toxic clock; spending one of them on Spin is the highest-value defensive use. Spikes is already up on p1 side; further Spikes is marginal.
- Top three: 1) Rapid Spin, 2) Spikes (push to 2 layers on p1), 3) Explosion (cash out vs Forry — 1 layer Spikes on p1 + Forry KO'd would close hazard war).
- Serious alternatives: Switch out (preserves Cloyster but burns a free Forry turn).
- Rejected tempting safe line: Surf (0.5x resist; trivial chip).
- Worst plausible branch: Forry Explosion this turn (Cloyster takes ~70% Boom + 6% Tox = ~76%; Cloyster might just survive to Spin or Boom; Forry KO'd). Acceptable trade.
- Public-info tier: Forry Boom = `strong prior`. Forry Spin = `strong prior` (would clear MY Spikes on p1 side — bad). Forry HP-Fire = `possible only`.
- Branch-punish audit per top-3:
  - Rapid Spin beats Forry-Spikes-again (clears my side); ties Forry-Spin (mirror clear, both reset); loses to Forry-Boom (Cloyster KO'd but spin would still go if Cloyster outspeeds — Cloyster Spe 70, para'd Forry Spe ~10; Cloyster faster; Spin fires first, then Boom KOs).
  - Spikes beats Forry-Spin (Forry wastes its Spin turn while I net the layer); loses to Forry-Boom (Cloyster KO'd before Spike fires? Cloyster faster, so my Spike fires first then Boom KOs — clean trade).
  - Explosion beats Forry-Spikes-stays (Forry KO'd or ~30 HP, Cloyster gone); loses to Forry-Spin (wasted Boom; Cloyster dies to Tox).

Actual: Cloyster CLAMP on Forry (MISS, 75% acc); Forry Rapid Spin -> clears p1 Spikes layer; Cloyster -5% Tox, +5% Lefties (revealed Lefties!) -> 97 TOX. Net: I lose my Spikes on p1, Forry still para'd 100/100, Cloyster 97 TOX.

Grade: top_match = 0. Acceptable_match = 0 (Clamp is a TRAP converter, not a hazard/clear/cash-out — fundamentally different route). Actual_in_top_3 = 0.
top_rank_failure: hidden_package_reveal — Clamp on Cloyster is a non-standard set (standard prior is Spikes/Surf/Spin/Boom or Spikes/Surf/Spin/Toxic). My ranker did not include Clamp as a candidate. H1-CG (candidate-not-generated) by way of an off-meta set choice. Pricing this differently: this is closer to H4 (oracle ceiling / hidden package) than to a card-loading failure — mrsoup's set was hidden and non-standard.
positive_selection = 0 (my Spin defensive; Clamp would lock Forry + open Boom-Forry trap).
route_converting_move_chosen = 0 (my Spin is reactive, not converting).
branch_punish_chosen = 0 (Spin doesn't punish Spikes/Toxic Forry; Clamp would).
role_package_update_obeyed = 1 (Cloyster role recognized; just missed Clamp variant).
mechanics_error = 0; state_error = 0; hidden_info_error = 0 (did not anchor on hidden info as fact — just missed the candidate); severe_blunder = 0.
Cloyster Lefties revealed — useful for future calc (Cloyster Lefties = 6% per turn heal, partially offsets Toxic).

## Turn 8

Public state: p1a Forry 100 PAR (Spin/Spikes/Toxic revealed; p1 side clear). p2a Cloyster 97 TOX (Clamp/Spikes/Lefties revealed; p2 has 1 Spikes layer). Forry's 4th move unknown — strong prior Boom.
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Spike/Spin loop), `spend_or_save_piece.md` (Cloyster cash-out window), `converter_before_script.md` (Boom converter vs Spike script), `rescore_after_reveal.md` (Cloyster-Clamp reveal opens trap-Boom combo).
Trigger compliance: all four loaded.

My (p2) freeze:
- Recommended: Spikes (Cloyster, push to 2 layers on p1).
- Confidence: 45/30/25.
- Route reason: Forry has no Spin partner on p1's team (Nido/Zap/Snorlax/Ttar/Gen — none spin). If I push Spikes high and Forry eventually dies, my hazards lock in. Cloyster faster than para'd Forry — Spikes fire before Forry's Spike-mirror or Boom this turn.
- Top three:
  1. Spikes — push to 2 layers on p1.
  2. Explosion — borderline OHKO on Forry (Cloyster Atk 95 STAB Boom 250 vs Forry Def 140 — ~75% damage average; Cloyster faster but Boom KOs Cloyster first, leaving Forry alive at low HP to potentially Spin); high variance.
  3. Clamp — trap Forry; chip; set up future Boom on a guaranteed-locked target.
- Serious alternatives: Switch out Cloyster (Tox resets to regular psn on switch in Gen 2 — saves long-term HP) BUT Forry gets free turn (Spike 2nd layer on me; bad trade).
- Rejected tempting safe line: Surf (0.5x resist; trivial chip; wastes Tox turn).
- Worst plausible branch: Forry Explosion turn-8 (Cloyster KO'd at 97 - 78 Boom = 19 -> KO'd; Forry alive at low HP). My Spikes fires first if I Spike (Cloyster faster), so 2 layers up before I die. Good trade.
- Public-info tier: Forry has Boom = `strong prior` (4th slot). Forry's set complete: Spin/Spikes/Toxic/Boom (most likely).
- Branch-punish audit per top-3:
  - Spikes beats Forry-Spike (mirror; my layer fires first); beats Forry-Boom (my Spike fires first, then Boom KOs Cloyster but layer locked in); beats Forry-Spin (Spin redundant since p1 side is clear, my Spike still fires).
  - Boom beats Forry-Spike (trade); loses to Forry-Spin (Boom does ~75% on Forry, doesn't OHKO; Forry survives, spins my Spike if any).
  - Clamp beats Forry-switch-out attempts (locked); loses to Forry-Boom (Clamp does no damage; Cloyster dies for nothing).

Actual: Cloyster Spikes (1 layer on p1); Forry Rapid Spin clears it AGAIN. Cloyster -5% Tox -4% Spin +6% Lefties -> 87 TOX. Forry still 100 PAR. Spikes both sides cleared.

Grade: top_match = 1 (EXACT — Cloyster Spikes). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
positive_selection = 1 (Spike is route progress even though Spin reverses it).
route_converting = 1.
branch_punish_chosen = 0 (my move loses to Forry-Spin; Spin was named but my Spike doesn't punish it).
role_package_update = 1.
errors all 0.
Note: Forry's repeated Spin (2 of 2 attempted spins succeeded — only 25% full-para hits would have helped me) means my hazard war strategy is bottlenecked by Forry's spin spam. Need to remove Forry to lock hazards. Boom-Forry is the cleanest play but doesn't OHKO from full. Toxic Forry myself (Eggy or Snorlax has Toxic? Standard sets — no, my Toxic options are limited; Forry para'd is the chip clock I have on it).

## Turn 9

Public state: p1a Forry 100 PAR (no Spikes on p1). p2a Cloyster 87 TOX (1 Spike layer on p2). Tox counter on Cloyster at 3 (next 18% chip).
Pre-freeze loaded cards: baseline + `reset_loop_denial.md` (Forry's Spin spam is the reset engine; must be removed), `spend_or_save_piece.md` (Cloyster cash-out / preserve question), `converter_before_script.md`.
Trigger compliance: all three loaded.

My (p2) freeze:
- Recommended: switch Cloyster -> Steelix.
- Confidence: 45/30/25.
- Route reason: Forry has spun 2 of 2 Spikes attempts off; my hazard war is gridlocked unless Forry dies. Steelix EQ on Forry is 2x SE (through Steel half) -> ~45% per hit; 2HKOs Forry. Steelix eats Boom for ~50%. Trade Steelix HP for Forry kill = lock no-spinner-left on Siatam. Cloyster preserved (switching reverts Toxic to regular psn in Gen 2 -> 12% per turn flat instead of accelerating).
- Top three:
  1. Switch Steelix — fastest Forry kill; preserves Cloyster's future spin role at lower poison rate.
  2. Explosion — Cloyster Boom hits Forry for ~75% (Forry to ~25%); Cloyster KO'd; Forry survives but cripples.
  3. Switch Snorlax — Curse vs Forry; slow Body Slam kill; risks Forry Boom on incoming Snorlax (Snorlax takes ~70%).
- Serious alternatives: Clamp Forry (trap + chip + force Forry to stay 2-5 turns; Cloyster gets 3-4 trapped turns of value before dying); not as direct as Steelix swap.
- Rejected tempting safe line: Spikes again (Forry will Spin again = wasted).
- Worst plausible branch: Forry Boom on switch-in turn (Steelix takes 50% on entry + 12% Spike = ~38% remaining; still has 2 EQs to land before fainting). Survivable trade.
- Public-info tier: Forry Boom = `strong prior`. Forry has no Spin partner on Siatam team = `revealed` (none of Nido/Gen/Zap/Snor/Ttar typically spin).
- Branch-punish audit per top-3:
  - Switch Steelix beats Forry-Toxic (Steel immune to Toxic) + Forry-Spin (no Spikes on p1 to spin, Spin wasted) + Forry-Spikes (Steelix EQ next turn kills Forry; 2 layers on me but Steelix wall preserves Eggy/Snor); loses-partially to Forry-Boom (Steelix takes 50%; survives to finish Forry with EQ).
  - Boom beats Forry-Spike (Forry to 25%; Spike still set on p2 2 layers but Forry dies next turn anyway); loses-marginally to Forry-Spin (Spin wasted but Forry survives at 25%; trade Cloyster for Forry-low).
  - Switch Snorlax beats Forry-Toxic (Snorlax 1x neutral Body Slam; can Curse setup); loses to Forry-Boom (Snorlax takes ~70% — bigger HP loss than Steelix; Snorlax's late-game Curse role lost).

Actual: Cloyster CLAMP -> Forry (lands, Forry chipped to 84%; partially trapped). Forry Toxic on Cloyster (FAILS — Cloyster already toxic'd). Cloyster -18% Tox +6% Lefties -> 75% TOX. Forry takes Clamp chip 6 to 78 then Lefties +6 -> 84.

Grade: top_match = 0 (mine: Switch Steelix; actual: Clamp). Acceptable_match = 0 (Clamp is trap+chip+waste-Forry's-turn; switch-Steelix is hard-attack — different routes). Actual_in_top_3 = 0 (Clamp was "serious alternative" not top-3).
top_rank_failure: candidate_weighting — Clamp on a Toxic'd Cloyster locked into a para'd Forry is a high-value trap converter that wastes Forry's Toxic turn (Toxic failed because Cloyster already statused — predictable). My ranker treated Clamp as low-priority because the chip is small, missing the "force Forry to stay AND waste its turn" route value.
This is H2 (card-loaded-but-ignored): `converter_before_script.md` was loaded and says "rank route-changing actions before default scripts" — Clamp IS the route-changer (forces stay + wastes opponent turn), but I ranked Switch Steelix (preservation/repositioning) ahead.
positive_selection = 0 (my switch is fine but Clamp dominates the turn — wastes Forry's action entirely + chip + trap).
route_converting = 0 (my switch is reactive; Clamp converts via trap+waste).
branch_punish_chosen = 0 (my switch doesn't beat Forry-stay-and-spam-status-fails; Clamp does by trapping).
role_package_update = 0 (didn't recognize Cloyster as a Clamp-trap engine, treated as Spinner-Spiker-Boomer only).
mechanics_error = 0; state_error = 0; hidden_info = 0; severe = 0.

## Turn 10

Public state: Forry 84 PAR (trapped from Clamp), Cloyster 75 TOX (counter=4, next 24% chip).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece (Cloyster cash-out window — 1-2 turns left), converter_before_script, rescore_after_reveal.

Freeze:
- Recommended: Explosion (Cloyster).
- Confidence: 50/30/20.
- Route reason: Cash out Cloyster on the spinner Forry NOW — Cloyster has 1-2 turns left (Tox 24% then 30% = dead T12). Forry at 84%; Boom does ~75% (avg) = Forry to ~9%. Forry's spinner role dies T11 to any chip move. Locking the no-spinner state is the highest-value cash-out of Cloyster.
- Top three:
  1. Explosion — Forry to ~9% HP; effectively kills the spinner clock; trade Cloyster for Forry-dead.
  2. Clamp — re-trap if previous ended; chip Forry; waste another Forry turn (especially if Forry Toxics again — wasted attempt vs already-tox'd Cloyster).
  3. Spikes — push to 2 layers; Forry can still Spin them off. Risky if Forry isn't trapped.
- Serious alternatives: switch to Steelix to take Boom safely and finish Forry next turn.
- Rejected tempting safe line: Surf (0.5x resist; trivial).
- Worst plausible branch: Forry-Boom this turn (Cloyster slower? Cloyster Spe 70, Forry para'd Spe ~10; Cloyster faster). Cloyster Booms first; Forry dies or near-dies. Net positive.
- Public-info tier: Forry Boom = `strong prior` (4th move slot now nearly certain).
- Branch-punish audit:
  - Boom beats Forry-Spike (Cloyster faster, Boom first KOs Forry near-dead; my switch-in finishes); beats Forry-Toxic (wasted; Boom KO); beats Forry-Spin (Spin doesn't matter once Forry dies); loses-marginally to Forry-Boom (Forry tries to Boom Cloyster but Cloyster faster, Boom resolves first; Forry's Boom never fires since Forry KO'd).
  - Clamp beats Forry-stay-spam; loses to Cloyster's tox clock (Cloyster dies before Forry).
  - Spikes beats nothing meaningful (Forry can still Spin).

Actual: Cloyster Spikes (1 layer p1); Forry Spin (CRIT) clears them. Cloyster -24% Tox -7% Spin crit +6% Lefties -> 50 TOX. Forry +6% Lefties -> 90 PAR.

Grade: top_match = 0 (mine Boom, actual Spikes). Acceptable = 1 (same hazard war family). Actual_in_top_3 = 1 (Spikes was #3). Branch_named = 1.
top_rank_failure: route_budget — I prioritized Cloyster cash-out via Boom (higher EV — Forry dies); mrsoup prioritized lower-variance Spike-spam waiting for Forry full-para. Both defensible — my Boom locks the kill, mrsoup's Spike maintains pressure.
positive_selection = 1 (Boom IS positive selection — converts Cloyster's remaining HP into Forry-dead).
route_converting = 1 (Boom is converter).
branch_punish_chosen = 1 (Boom beats Forry-Spin branch).
role_package_update = 1.
errors all 0.

## Turn 11

Public state: Forry 90 PAR. Cloyster 50 TOX (counter=5, dies T12-13).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece (Cloyster final cash-out window), converter_before_script.

Freeze:
- Recommended: Explosion (Cloyster).
- Confidence: 55/25/20.
- Route reason: Cloyster has 1-2 turns left; Forry at 90% is OHKO-able by Cloyster max-roll Boom (~75-95% damage on Bug/Steel Def 140). Even partial Boom + Forry-Tox-fail loop has been wasting Forry turns. Forry-dead = no spinner = my hazards lock.
- Top three: 1) Boom, 2) Spikes (last try), 3) Switch out to preserve Cloyster as regular-psn.
- Serious alternatives: Clamp (re-trap; chip only).
- Rejected tempting safe line: Surf (resist; waste).
- Worst plausible branch: Forry-Boom this turn (Cloyster faster, my Boom fires first; Forry KO'd or near-dead; Cloyster gone).
- Public-info tier: Forry Boom = `strong prior`.
- Branch-punish: Boom beats all Forry branches except Forry-switch-out (Forry can't switch — Clamp trap should still be active from T9 if turns < 5 of trap; Forry has been trapped 2 turns; could be 3-5 more turns or already ended). Even if trap ended, Forry has not chosen to switch — Spike-spam mirror commitment.

Actual: Cloyster Spikes (1 layer p1). Forry FULL PARA — cant move. Cloyster -30% Tox +6% Lefties -> 26 TOX. Forry +6% Lefties -> 96 PAR. **mrsoup's spike-spam variance pays off** — 1 layer locks on p1 this turn.

Grade: top_match = 0 (mine Boom, actual Spikes). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
top_rank_failure: route_budget — same lesson as T10: I was wrong about variance economics. mrsoup's Spike-spam waits for full-para luck; ~25% per turn cumulative over multiple attempts. Boom is higher-EV but Spike-spam has wider win conditions.
positive_selection = 1 (Boom IS positive selection — would have locked Forry kill rather than rely on para variance).
route_converting = 1.
branch_punish_chosen = 1.
role_package = 1.
errors all 0.

## Turn 12

Public state: Forry 96 PAR (p1 has 1 Spike layer). Cloyster 26 TOX (counter=6, next chip 36% — KILLS Cloyster).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece (FINAL turn for Cloyster), converter_before_script.

Freeze:
- Recommended: Explosion (Cloyster).
- Confidence: 70/15/15.
- Route reason: Cloyster's last turn. Boom chips Forry to ~21%; even if Forry spins p1 (clears my T11 Spike), Forry-near-dead means my switch-in finishes Forry T13. Forry-permanent-dead = no spinner left = late-game hazards lock.
- Top three: 1) Explosion, 2) Spikes (one more layer; hopes for full-para repeat — low odds), 3) Clamp (chip; Cloyster dies anyway).
- Serious alternatives: Surf (resist, trivial).
- Rejected tempting safe line: switch (Cloyster dies on switch-back anyway; preserve gains nothing).
- Worst plausible branch: Forry-Boom this turn (Cloyster faster, my Boom fires first; Forry near-dead).
- Public-info tier: Forry Boom = `strong prior`.
- Branch-punish audit: Boom beats Forry-Spin (Spin happens but Forry-near-dead means next turn finishes Forry); beats Forry-Spike (Spike adds layers but my Boom already chip'd Forry near-KO); beats Forry-Tox (Cloyster dies anyway; Forry to 21% — net positive).

Actual: **Siatam read mrsoup's Boom — switched Forry -> Gengar.** Gengar takes 12% Spikes chip -> 88. Cloyster Explosion -> Gengar **IMMUNE** (Normal vs Ghost). Cloyster faints. Forced switch mrsoup brings Umbreon -> Umbreon takes 12% Spikes chip -> 88. Lefties +6%: Gengar 94, Umbreon 94.

Grade: top_match = 1 (EXACT — both Boom). Acceptable = 1. Actual_in_top_3 = 1.
**SEVERE_BLUNDER = 1**: Cloyster lost for 0 compensation. Boom into Ghost immunity = textbook severe blunder. Cloyster was the unique spinner / spiker / route piece; permanently lost without trading even a chip.
**HIDDEN_INFO_ERROR = 1**: I did not label "Forry stays" as a strong-prior read with named fallback. The live_core branch-punish audit rule ("for each top-3 candidate, name the branch it BEATS and the branch it LOSES TO") was loaded but I did not apply it rigorously enough to surface "Ghost-pivot" — a `strong prior` in GSC OU championship play, not `possible only`.
top_rank_failure: branch_probability — Boom-vs-Ghost-pivot is the textbook GSC consideration. Standard team archetype assumption: Siatam has Ghost coverage (Gengar OR Misdreavus). Should have demoted Boom or hedged via Spikes / Clamp.
positive_selection = 0 (Boom into immunity is net-negative).
route_converting = 0 (failed to convert).
branch_punish_chosen = 0.
role_package = 0 (didn't update opponent role-package with Ghost-pivot consideration; standard archetype miss).
mechanics_error = 0 (Ghost-Normal immunity correctly applied; just not priced into branch search).
state_error = 0.

**This turn alone fails the falsification gate for "plateau-broken" claim** (severe_blunders must be 0; hidden_info_errors must be 0). Honest accounting. See Interpretation section at end for full diagnosis.

## Turn 13

Public state: Gengar 94. Umbreon 94 (forced switch-in after Cloyster faint). Both sides 1 layer Spike. Cloyster revealed Clamp/Explosion/Spikes; 4th unknown (likely Surf).
Pre-freeze loaded cards: baseline + reset_loop_denial (Hypnosis risk on Gengar), spend_or_save_piece (Umbreon as Pursuit/trapper piece), converter_before_script (Pursuit converter on Ghost), public_info_tiers (Gengar set strong prior).

Freeze:
- Recommended: Pursuit (Umbreon).
- Confidence: 45/30/25.
- Route reason: Pursuit is 2x SE on Ghost (Dark vs Ghost = SE 2x). Doubles if Gengar switches out -> likely KO. Stays at 50% chip if Gengar stays. Both branches good for me.
- Top three: 1) Pursuit, 2) Mean Look (trap Gengar; long Pursuit game), 3) Switch Steelix (immune to Thunder; EQ Gengar 1x ~40%).
- Serious alternatives: Curse (Umbreon Curse +1 Atk +1 Def — sets up but Gengar Hypnosis branch sleeps Umbreon).
- Rejected tempting safe line: switch Snorlax (Normal can't damage Ghost; awful matchup).
- Worst plausible branch: Gengar Hypnosis (60% acc) — Umbreon slept; sleep clause filled on my side. Pursuit fires first regardless of Hypnosis hit (Umbreon faster? Umbreon 65 vs Gengar 110 — Gengar faster). Actually Gengar acts first — Hypnosis first, then Umbreon (if not slept) Pursuit.
- Public-info tier: Gengar Hypnosis/Tbolt/Ice Punch/Boom = `strong prior` (modal championship set). Gengar has Boom = `strong prior` (revealed in opponent meta; not yet revealed in this game).
- Branch-punish audit per top-3:
  - Pursuit beats Gengar-switch-out (doubled ~KO); ties Gengar-stay (50% chip); loses partially to Hypnosis (Umbreon slept).
  - Mean Look beats Gengar-switch attempt (locked); loses to Hypnosis-then-Boom combo (Umbreon slept and KO'd by Boom).
  - Switch Steelix beats Hypnosis (Steelix bulky; sleep tolerable on tank — but no Rest if standard set); takes Tbolt immune; takes Ice Punch 1x ~40%; threatens EQ next turn.

Actual: Gengar Hypnosis MISSED. Umbreon Pursuit -> Gengar 25% SE chip -> 69. Lefties: Gengar 75, Umbreon 99. (Gengar Hypnosis revealed.)

Grade: top_match = 1 (EXACT). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1 (Hypnosis-miss branch).
positive_selection = 1. route_converting = 1. branch_punish = 1. role_package = 1. errors = 0.

## Turn 14

Public state: Gengar 75 (Hypnosis revealed). Umbreon 99 (Pursuit revealed).
Pre-freeze loaded cards: baseline + reset_loop_denial (Hypnosis sleep risk), spend_or_save_piece (Umbreon Pursuit job alive), converter_before_script.

Freeze:
- Recommended: Pursuit.
- Confidence: 50/25/25.
- Route reason: Umbreon is the Pursuit lock on Gengar; Gengar can't switch out without doubled Pursuit KO; Gengar's chip moves (Tbolt/Ice/Boom) are manageable on Umbreon. Only loss line is Hypnosis sleep clause (60% acc per attempt).
- Top three: 1) Pursuit, 2) Curse (+1 Def hedges chip moves), 3) Switch Steelix (eat Hypnosis on Steelix instead).
- Worst plausible branch: Gengar Hypnosis lands -> Umbreon slept, sleep clause filled. Fallback: Eggy can still status, Pursuit-lock pivots to "Gengar walks free."
- Public-info tier: Gengar Boom = `strong prior`.
- Branch-punish: Pursuit beats Tbolt/Ice/Boom/Psy (Umbreon Dark immune Psy); loses to Hypnosis (60%).

Actual: Gengar Hypnosis MISSED. Umbreon **Zap Cannon** on Gengar MISSED. Lefties: Gengar 82, Umbreon 100. **Umbreon's set is non-standard — has Zap Cannon (50% acc, 100% para if hits).**

Grade: top_match = 0 (mine Pursuit, actual Zap Cannon). Acceptable = 0 (Zap Cannon is a 50%-acc para-chip play, different route than Pursuit-chip). Actual_in_top_3 = 0.
top_rank_failure: hidden_package_reveal — Umbreon Zap Cannon is rare; standard sets are Mean Look/Pursuit/Toxic/Moonlight or Curse/BSlam/Rest/Roar. H4 (oracle ceiling / hidden info — set was not predictable).
positive_selection = 1 (my Pursuit was a real chip; would have done ~25% guaranteed; better EV than Zap Cannon's 50% acc).
route_converting = 1.
branch_punish = 1.
role_package = 1.
errors = 0 (Zap Cannon reveal noted; not hidden_info_error since I labeled set as `strong prior` not as fact).

## Turn 15

Public state: Gengar 82 (Hypnosis revealed; HP went 75 -> 82 via Lefties). Umbreon 100 (Pursuit, Zap Cannon revealed).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script, rescore_after_reveal (Umbreon Zap Cannon reveal opens "Zap Cannon spam for para" line).

Freeze:
- Recommended: Pursuit again.
- Confidence: 45/35/20.
- Route reason: Guaranteed 25% SE chip vs Gengar; Zap Cannon's 50% acc just whiffed -> mrsoup may revert to reliable Pursuit. Gengar at 82 needs 3 more Pursuits to KO.
- Top three: 1) Pursuit, 2) Zap Cannon (try para again), 3) Mean Look.
- Worst plausible branch: Gengar Hypnosis hits (60% acc) -> Umbreon slept.
- Public-info tier: Gengar Boom = `strong prior`; could Boom Umbreon for ~50% damage trade if mrsoup commits to staying.
- Branch-punish: same as T14.

Actual: Gengar Hypnosis HIT. Umbreon SLEPT. Umbreon couldn't act. Sleep clause filled on p2 side.

**UNSCORED per protocol §Exclusions** ("no-action sleep/freeze/paralysis turns where the chosen move is not logged"). Decision not counted toward the 30-decision target.

## Turn 16

Public state: Gengar 88. Umbreon 100 SLP. Sleep clause filled on p2 side -> Gengar can't sleep another of my mons.
Pre-freeze loaded cards: baseline + reset_loop_denial (sleep clause = passive Gengar-Hypnosis-denial; Gengar's main threat is now Tbolt/Ice/Boom), spend_or_save_piece (Umbreon dead weight asleep — switch out to preserve), converter_before_script.

Freeze:
- Recommended: switch Umbreon -> Steelix.
- Confidence: 65/20/15.
- Route reason: Umbreon asleep = wasted in. Steelix walls Gengar's main attacks (Tbolt 0x immune, Ice 0.5x resist, Psychic 1x chip, Boom ~50% chip). Threatens EQ Gengar 1x ~40%. Sleep clause filled means no Hypnosis sleep risk for Steelix.
- Top three: 1) Switch Steelix, 2) Switch Eggy (Sleep clause means no powder back, takes Ice Punch SE ~80% — bad), 3) Stay Umbreon (no-action turn — wastes a turn but no HP cost).
- Branch-punish audit per top-3:
  - Switch Steelix beats Tbolt (immune), Hypnosis (clause), Ice Punch (resist); loses partially to Psychic chip and Boom; Snorlax-out-of-team-switch dead-move into Ghost-Boom-block — DEMOTED out of top-3 per audit.
  - Switch Eggy loses to Ice Punch (2x SE).
  - Stay loses by wasting turn.

Actual: Gengar Ice Punch -> Umbreon -15% -> 85 SLP. Umbreon can't act. Lefties: Gengar 94, Umbreon 91 SLP. **mrsoup did NOT switch** — kept Umbreon in despite sleep.

Grade: SCORED (mrsoup had switch option; chose to stay = decision). Top_match = 0 (mine = Switch Steelix; actual = Stay). Acceptable = 0 (different route — preserve-via-stay vs switch-out-with-Spike-chip). Actual_in_top_3 = 1 (Stay was my #3).
top_rank_failure: route_budget — mrsoup priced "save Steelix from Spike chip" higher than I did. The 1-layer Spike means Steelix takes 12% on entry; staying-Umbreon eats 15% Ice Punch. Net HP loss is similar but staying preserves the 4-attack switch-out option for later.
positive_selection = 1 (Switch Steelix actively brings in the right Gengar wall).
route_converting = 1.
branch_punish = 1 (Steelix walls Tbolt/Hypnosis).
role_package = 0 (didn't update "Steelix should preserve HP for Zapdos late game" — staying Umbreon is the route-budget call I missed).
errors = 0.

## Turn 17

Public state: Gengar 94 (Hypnosis, Ice Punch revealed). Umbreon 91 SLP.
Pre-freeze loaded cards: baseline + reset_loop_denial (sleep clause filled, Hypnosis denied), spend_or_save_piece (now applies to Steelix preservation — don't spend wall HP on Spike chip while Gengar isn't winning the matchup; the route-budget lesson from T16's miss), converter_before_script.

Freeze:
- Recommended: Stay (Umbreon SLP, no action).
- Confidence: 45/40/15.
- Route reason: Switching costs 12% Spike chip + likely Ice Punch on switch-in (Steelix takes ~18% net). Staying with Umbreon costs ~15% Ice on Umbreon (sleeping target). Stay is cheaper in HP terms and preserves Steelix for Zapdos. Applies the route-budget lesson learned from T16's miss.
- Top three: 1) Stay, 2) Switch Steelix, 3) Switch Snorlax (dead-move into Ghost-Boom branch — DEMOTED).
- Worst plausible branch: Gengar Boom on sleeping Umbreon (Boom Normal 1x on Umbreon Dark high SpDef ~50% damage; Umbreon at ~40% after; Gengar dies). Trade Gengar for half-Umbreon = positive trade. Even fine if it happens.
- Public-info tier: Gengar Boom = `strong prior`.
- Branch-punish audit per top-3:
  - Stay beats nothing actively, but Gengar's chip line is sustainable; Boom branch is a positive trade.
  - Switch Steelix beats Tbolt (immune) but accepts 30% chip on Steelix for nothing on Gengar (Gengar Boom or switch out).
  - Switch Snorlax is dead-move into Ghost; demoted.

Actual: Umbreon SLP can't move. **Siatam switched Gengar -> Forretress** (eats Spike chip 12% -> 84 PAR; +6% Lefties -> 90). mrsoup stayed.

Grade: top_match = 1 (EXACT — Stay). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
positive_selection = 0 (Stay is passive preservation, not active improvement).
route_converting = 0 (no conversion).
branch_punish = 0 (no active punish).
role_package_update = 1 (correctly preserved Steelix for Zapdos).
errors = 0.
Note: Siatam pivot Gengar -> Forry suggests Gengar was getting nothing on Umbreon; saved Gengar at 94%. Forry back to spin/spike. Good route position for me — Gengar can come back later when sleep clause clears.

## Turn 18

Public state: Forry 90 PAR. Umbreon 97 SLP.
Pre-freeze loaded cards: baseline + reset_loop_denial (Spike/Spin loop back active), spend_or_save_piece (Umbreon, Steelix preservation), converter_before_script.

Freeze:
- Recommended: Stay (Umbreon SLP).
- Confidence: 70/20/10.
- Route reason: Forry's only damaging option vs Umbreon is Boom; Spike/Spin/Toxic do 0 damage to active Umbreon. Stay -> Umbreon takes 0 damage, Lefties +6% -> 100%. Free turn for me. Forry para'd, no Boom is likely (Forry preserves for late hazard work).
- Top three: 1) Stay, 2) Switch Steelix (12% Spike chip + Forry can Toxic/Spike on incoming — but Steel immune to Toxic; Spike sets 2nd layer on me), 3) Switch Eggy (12% Spike + Forry Spike chips Eggy on entry).
- Worst plausible branch: Forry-Boom (Umbreon takes 50%, Forry dies; trade favorable but unexpected from para'd Forry).
- Public-info tier: Forry Boom = `strong prior`.
- Branch-punish audit: Stay beats Forry-Spike (no immediate damage; Umbreon heals via Lefties) + Forry-Spin (free for me — Spin clears my Spike on p1 which I haven't successfully set since T11). Loses to Forry-Boom (Umbreon -50%; net Forry-for-half-Umbreon trade).

Actual: Umbreon SLP cant. Forry Rapid Spin -> Umbreon -5% Spin + Lefties +6% -> 99 SLP. p1 Spike cleared. Forry +6% -> 96 PAR.

Grade: top_match = 1 (EXACT — Stay). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
positive_selection = 0 (passive); route_converting = 0; branch_punish = 0; role_package = 1; errors = 0.

## Turn 19

Public state: Forry 96 PAR. Umbreon 99 SLP. Both sides no Spikes (p2 still has 1, p1 cleared).

Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Stay (Umbreon SLP).
- Confidence: 70/20/10.
- Route reason: Same as T18 — Forry has no damaging move except Boom; staying = ~0 damage + Lefties heal.
- Top three: 1) Stay, 2) Switch Steelix, 3) Switch Eggy.
- Worst plausible: Forry Boom (Umbreon -50%; Forry dies; favorable trade).
- Branch-punish: Stay beats Forry-Spike/Spin/Toxic; loses to Forry-Boom (net positive trade).

Actual: Umbreon SLP cant. Forry **Hidden Power** -> Umbreon -7% -> 92 -> +6 Lefties -> 98 SLP. Forry +4 -> 100 PAR. **Forry's 4th slot is Hidden Power, NOT Boom. Major set reveal.**

Grade: top_match = 1 (EXACT — Stay). Acceptable = 1. Actual_in_top_3 = 1. Branch_named = 1.
positive_selection = 0; route_converting = 0; branch_punish = 0; role_package = 1; errors = 0.

Reveal note: Forry has no Boom -> switch-ins to Forry are SAFE. The "Forry-Boom" branch I'd been pricing as strong-prior across T6-T12 is no longer in play. Trigger for `rescore_after_reveal.md` going forward.

## Turn 20

Public state: Forry 100 PAR (full set revealed: HP/Spin/Spikes/Toxic; no Boom). Umbreon 98 SLP (5 turns asleep — likely waking soon).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece (Steelix can now switch in safely since no Forry-Boom), converter_before_script, rescore_after_reveal (post-no-Boom reveal).

Freeze:
- Recommended: switch Umbreon -> Steelix.
- Confidence: 50/30/20.
- Route reason: Forry has no Boom; Steelix safe to switch in (12% Spike chip + Forry HP chip ~10-40% depending on HP type). Steelix EQ 2x SE on Forry -> 2HKO Forry. Cash out Forry; Forry was the spinner so its death locks any future hazards I set.
- Top three: 1) Switch Steelix, 2) Stay (Umbreon wakes T20-21 hopefully), 3) Switch Eggy (no Sleep Powder vs para'd Forry; bad).
- Worst plausible: Forry HP Fighting -> Steelix takes 2x SE ~40% on entry. Trade still acceptable (Steelix EQ Forry to ~50% next turn).
- Public-info tier: Forry HP type unknown — `possible only` (HP Bug/Fighting/Steel etc).
- Branch-punish: Switch Steelix beats Forry-Spike (Steelix can EQ Forry next turn for 50%); beats Forry-Toxic (Steel immune); beats Forry-Spin (no Spike on p1 to spin); HP-Fighting branch hurts but Steelix survives.

Actual: mrsoup switch Umbreon -> Steelix. Steelix -12% Spike -> 88. Forry Toxic IMMUNE. Steelix +6% Lefties -> 94.

Grade: top_match = 1 (EXACT). Acceptable = 1. In_top_3 = 1. Branch_named = 1.
positive_selection = 1; route_converting = 1; branch_punish = 1; role_package = 1; errors = 0.

## Turn 21

Public state: Forry 100 PAR. Steelix 94. p2 has 1 Spike.
Pre-freeze loaded cards: baseline + reset_loop_denial (kill Forry to lock spinner-dead), spend_or_save_piece (Steelix spends HP for Forry kill), converter_before_script (EQ converter).

Freeze:
- Recommended: Earthquake (Steelix).
- Confidence: 70/15/15.
- Route reason: Steelix EQ 2x SE on Bug/Steel Forry -> ~50% per hit; 2HKO. Forry's HP chip on Steelix is the only damage path. Trade Steelix HP for Forry-dead = no more spinning = my hazards lock.
- Top three: 1) Earthquake, 2) Roar (phaze Forry; random opp mon eats... no, Forry's the only one out; Roar phazes Forry away, replacement eats my Spike chip), 3) Curse (set up while Forry chips; slower kill).
- Worst plausible: Forry HP Fighting (Steel weak to Fighting; 2x SE on Steelix Steel/Ground combined) -> ~40% chip on Steelix.
- Branch-punish: EQ beats all Forry moves (Toxic immune, Spin useless, Spike 1 layer mine, HP 10-40% chip — but Forry dies next turn anyway).

Actual: **Steelix CURSE** (+1 Atk, +1 Def, -1 Spe). Forry HP -> Steelix SE (HP Fighting most likely) -> 66; Lefties -> 72. **Forry's HP is Fighting (2x SE on Steel/Ground).**

Grade: top_match = 0 (mine EQ, actual Curse). Acceptable = 1 (Curse is setup converter, same Forry-eventual-kill route family). In_top_3 = 1 (Curse was #3). Branch_named = 1.
top_rank_failure: route_budget — I prioritized immediate EQ kill; mrsoup prioritized Curse compounding (next-turn EQ does ~75% with +1 Atk; +1 Def tanks Forry HP Fighting better; setup for Zapdos lategame).
positive_selection = 1 (my EQ pick was real route improvement).
route_converting = 1. branch_punish = 1. role_package = 1. errors = 0.

## Turn 22

Public state: Forry 100 PAR. Steelix 72 +1 Atk +1 Def -1 Spe.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Earthquake (Steelix).
- Confidence: 50/35/15.
- Route reason: +1 Atk EQ does ~75% on Forry; 2 EQs KO. Mrsoup might Curse-stack one more turn for guaranteed OHKO via +2 EQ. EQ now is the safer line (cash out Forry).
- Top three: 1) Earthquake, 2) Curse again (+2 setup for guaranteed OHKO next), 3) Roar (no chip on p1 side; mostly preserves Steelix HP).
- Worst plausible: Forry switches out to Tyranitar (Pursuit-trap target normally; but Steelix slower can be Rock-Slide chip).
- Branch-punish: EQ beats all Forry-stay branches; loses-marginally to Forry-pivot (Steelix EQ on incoming).

Actual: Steelix EQ -> Forry 60 PAR (40% damage; my 75% estimate was off — Forry has max Def). Forry HP SE -> Steelix 41 -> 47 Lefties. Forry +6 Lefties -> 66.

Grade: top_match = 1 (EXACT). Acceptable = 1. In_top_3 = 1. Branch_named = 1.
positive_selection = 1; route_converting = 1; branch_punish = 1; role_package = 1; errors = 0.
Mechanics note: my EQ damage estimate (~75%) was off; actual ~40%. +1 Atk Curse'd EQ on max-Def Forry is ~40%, not 75%. Lesson logged.

## Turn 23

Public state: Forry 66 PAR. Steelix 47 +1/+1.

Freeze:
- Recommended: Earthquake.
- Confidence: 65/20/15.
- Route reason: Forry at 66; +1 EQ does ~40% -> Forry 26 -> +6 Lefties -> 32. Next turn EQ kills. Steelix takes Forry HP chip ~25% per turn (-1 Def from Curse partial offset). Two more EQs finishes Forry.
- Top three: 1) EQ, 2) Curse (+2 setup), 3) Roar.
- Branch-punish: same as T22. [NOTE: I did NOT specifically run "EQ loses to Zapdos-pivot" through the branch-punish audit. Forry-pivot branch was named generically but Zapdos's Flying immunity to EQ was not specifically priced.]

Actual: **Siatam switched Forry -> Zapdos**. Steelix EQ -> Zapdos IMMUNE (Flying). Steelix +6% Lefties -> 53.

Grade: top_match = 1 (EXACT — both EQ). Acceptable = 1. In_top_3 = 1. Branch_named = 1 (Forry-pivot named generically, not Zapdos-specific).
**top_rank_failure: branch_probability / status_branch_obedience** — this is essentially the packet-044 Turn-22 class error: I named Forry-pivot as a possible branch but did NOT price "Siatam pivots Zapdos for EQ immunity" specifically. The pre-freeze branch-punish audit (the H2 fix from live_core intervention) was supposed to catch this. The audit text says "for each top-3 candidate, name the branch it BEATS and the branch it LOSES TO. A dead move into a named branch ... demotes itself." EQ loses dead to Zapdos pivot; the audit should have demoted EQ or surfaced Roar-to-phaze as the hedge.
This is H2 (card-loaded-but-ignored). The intervention rule is present in `live_core.md`'s Load-Required Triggers block; my ranker didn't apply it rigorously enough.
positive_selection = 0 (EQ wasted on immunity).
route_converting = 0.
branch_punish_chosen = 0.
role_package = 0 (didn't update opp-team-role-map to include "Zapdos can immune EQ").
mechanics_error = 0 (Flying/Ground correctly applied; just not priced).
state_error = 0 (Zapdos team-presence was revealed and known; this is branch-punish miss, not state-state miss).
hidden_info_error = 0.
severe_blunder = 0 (Steelix didn't die or trade; just wasted a turn).

## Turn 24

Public state: Zapdos 100. Steelix 53 +1/+1.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece (Steelix on low HP, must preserve right piece), converter_before_script (Sleep Powder Eggy is a converter), public_info_tiers, rescore_after_reveal.

Freeze:
- Recommended: switch Steelix -> Snorlax.
- Confidence: 45/30/25.
- Route reason: Steelix can't damage Zapdos (Ground vs Flying = 0x). Snorlax is the proper Zapdos absorber — eats Tbolt 1x neutral (Snor SpDef 110), Drill Peck 1x, HP Ice 1x; bulky. Body Slam Snorlax on Zapdos = 1x neutral + 30% para; para Zapdos cripples Siatam.
- Top three: 1) Switch Snorlax (Zapdos absorber + Body Slam para chance), 2) Switch Eggy (Sleep Powder Zapdos threat; fragile to Drill Peck/HP Ice 2x SE), 3) Roar Zapdos (forces Siatam pivot — high variance: 1/5 Gengar/Ttar bad outcomes).
- Worst plausible: Zapdos has Lovely Kiss / non-standard set (Snorlax slept = catastrophic). Snorlax LK Lax variants common; Zapdos LK rare.
- Public-info tier: Zapdos standard set Tbolt/Drill Peck/HP Ice/TW = `strong prior`. Zapdos LK = `possible only`.
- Branch-punish: Switch Snorlax beats Tbolt + Drill Peck + HP Ice (all 1x manageable) + TW (Snorlax can be para'd but no Ground immunity since Snor is Normal; TW para'd Snor still works with BSlam); loses to LK Zapdos rare.

Actual: Zapdos HP -> Steelix 29 (Steelix takes SE chip from HP Ice or similar). **Steelix EXPLOSION on Zapdos -> Zapdos KO. Steelix faints (self-Boom).** Forced switches: Siatam Nidoking (100/100); mrsoup Snorlax (95 -> 83 from p2 Spike).

Grade: top_match = 0 (mine: Switch Snorlax; actual: Explosion). Acceptable = 0 (preservation route vs active cash-out KO). In_top_3 = 0 (Boom Steelix not in my top-3). Branch_named = 0 (didn't name Steelix-Boom-on-Zapdos branch).
top_rank_failure: hidden_package_reveal — **Steelix Explosion is non-standard set**. Three hidden-package reveals so far in this packet (Cloyster Clamp T7, Umbreon Zap Cannon T14, Steelix Boom T24). mrsoup's team has multiple off-meta sets. H1-CG (candidate-not-generated due to set prior failure) shading to H4 (oracle ceiling — non-public set).
positive_selection = 0 (my switch is preservation, not Zapdos-kill).
route_converting = 0 (switch doesn't convert; Boom would).
branch_punish_chosen = 0.
role_package = 0 (didn't model Steelix as Boomer).
mechanics_error = 0 (Boom mechanics correctly understood; just unexpected candidate).
state_error = 0; hidden_info_error = 0 (set was unrevealed; not anchored as fact); severe_blunder = 0 (my Switch wasn't catastrophic — Snorlax just chip; mrsoup's actual move was strongly positive trade Steelix-for-Zapdos).

## Turn 25

Public state: Nidoking 100 (active). Snorlax 83 (active). Siatam down 1 mon (Zapdos dead). Sleep clause filled p2 side (Umbreon SLP) — Siatam's LK on me FAILS. Sleep clause empty Siatam side — my Sleep Powder works.
Pre-freeze loaded cards: baseline + reset_loop_denial (sleep clauses both sides), spend_or_save_piece (Snorlax/Eggy preservation), converter_before_script (Curse / Body Slam / Sleep Powder converters).

Freeze:
- Recommended: Curse (Snorlax).
- Confidence: 50/30/20.
- Route reason: Curse Lax setup; +1 Atk/+1 Def cripples Nido's chip moves; Nidoking can't OHKO Snorlax. Sleep clause filled on Siatam side prevents LK Nido (my Umbreon SLP burns Siatam's sleep slot). Curse Lax is a natural sweeper-build vs the rest of Siatam's team.
- Top three: 1) Curse, 2) Body Slam (BSlam chip + 30% para chance on Nido), 3) Switch Eggy (Sleep Powder Nido — locks Siatam sleep clause).
- Worst plausible: Nidoking has Counter (mixed Nido carries Counter sometimes; +1 Atk BSlam returned for huge damage). My Curse doesn't BSlam this turn so safe vs Counter.
- Public-info tier: Nidoking has Counter/Mixed = `possible only`. Nidoking has LK = `possible only` (clause-blocked anyway).
- Branch-punish: Curse beats Nido-Thief (itemless target so useless); beats Nido-Ice Beam/Thunder chip (Snorlax tank); Nido-Counter is irrelevant since I'm not attacking.

Actual: Nido EQ -> Snorlax 53. Snorlax **Body Slam** -> Nido 65 -> 71 Lefties.

Grade: top_match = 0 (mine Curse, actual Body Slam). Acceptable = 1 (same chip-and-para family). In_top_3 = 1 (BSlam was #2). Branch_named = 1.
top_rank_failure: route_budget — Curse vs BSlam is the recurring "compounding setup vs immediate damage" question; both defensible.
positive_selection = 1. route_converting = 1. branch_punish = 1. role_package = 1. errors = 0.

## Turn 26

Public state: Nido 71. Snor 53.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Curse (Snorlax).
- Confidence: 40/35/25.
- Route reason: +1 Atk +1 Def setup; +1 Def helps Snorlax tank Nido's EQ chip; BSlam next turn does more damage. Snorlax at 53 is approaching low-HP — Curse needs to happen before Snorlax drops too low.
- Top three: 1) Curse, 2) Body Slam (chip + para chance), 3) Rest (heal to full but burn 2 turns of sleep without Sleep Talk).
- Worst plausible: Nido has Counter (turns my BSlam into KO on me). Curse doesn't attack so Counter-safe.
- Branch-punish: Curse beats Nido-Thief (no item), Nido-EQ (chip but +1 Def helps), Nido-Ice Beam (chip, normal); loses-marginally to Nido-Counter (irrelevant since I'm not attacking).

Actual: Nido EQ -> Snor 27. **Snor REST -> 100 SLP**. Nido +6 Lefties -> 77.

Grade: top_match = 0 (mine Curse, actual Rest). Acceptable = 0 (Rest is preservation, Curse is setup — different routes). In_top_3 = 1 (Rest was #3). Branch_named = 1.
top_rank_failure: candidate_weighting — `spend_or_save_piece.md` rule ("preserve if the job still owns a future route") was loaded but I privileged setup over Rest-preservation when Snorlax was approaching low HP. H2 (card-loaded-but-ignored).
positive_selection = 1 (Curse improves route; not a throw); route_converting = 1; branch_punish = 0 (Curse doesn't punish Nido EQ; Rest does by recovering); role_package = 0 (didn't update Snor as RestTalk variant); errors = 0.

Snor reveal: Rest confirmed. Snor set likely Curse/BSlam/Rest/Sleep Talk (RestTalk Lax variant).

## Turn 27

Public state: Nido 77. Snor 100 SLP (just Rested). Sleep clause: Umbreon (slept by Hypnosis) counts; Snor (self-Rest) does NOT count. Siatam side sleep clause filled (one of my mons asleep by his Hypnosis). Mrsoup side empty (can still sleep one of Siatam's mons).
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script, rescore_after_reveal (Snor RestTalk set inferred).

Freeze:
- Recommended: Stay (Sleep Talk attempt).
- Confidence: 50/30/20.
- Route reason: Snor likely has Sleep Talk (RestTalk Lax is standard variant). Sleep Talk -> random of Curse/BSlam/Rest. Curse compounds setup; BSlam chips Nido + para. Both positive.
- Top three: 1) Stay (Sleep Talk gamble), 2) Switch Eggy (Sleep Powder Nido locks Siatam clause; Eggy takes Ice Beam SE 2x on entry), 3) Switch Charizard (BD setup unrevealed but possible).
- Worst plausible: Snor doesn't have Sleep Talk -> wasted turn. Or Nido Counter could hit BSlam-from-ST for huge damage. Or Nido has Curse + setting up itself.
- Public-info tier: Snor has Sleep Talk = `strong prior` (RestTalk variant standard). Charizard set = `possible only`.
- Branch-punish: Stay-Sleep-Talk-BSlam beats Nido-stay (chip+para); Stay-ST-Curse beats Nido-stay (setup); ST-Rest is the wasted line.

Actual: **Siatam pivoted Nido -> Snorlax**. mrsoup Snor SLP, but **Sleep Talk** fired -> BSlam -> Siatam Snor 74 -> 80 Lefties. mrsoup stayed.

Grade: top_match = 1 (EXACT — Stay; Sleep Talk + BSlam fired). Acceptable = 1. In_top_3 = 1. Branch_named = 1 (Siatam-Snor-pivot wasn't specifically named, but my "stay" play handled it equally well).
positive_selection = 1 (Sleep Talk fired BSlam — active progress on incoming Snor mirror). route_converting = 1. branch_punish = 1. role_package = 1. errors = 0.
Reveals: Snor Sleep Talk confirmed (RestTalk Snor). Siatam has Snorlax (5th p1 mon revealed publicly).

## Turn 28

Public state: Siatam Snor 80, mrsoup Snor 100 SLP. Sleep counter on Snor mid-cycle. Snor mirror.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Stay (mrsoup Snor) -> Sleep Talk gamble.
- Confidence: 55/25/20.
- Route reason: Sleep Talk fires randomly through Snor's moves. BSlam hits Siatam Snor for ~25% chip + para chance. Curse compounds setup. Rest wastes. Net positive expected.
- Top three: 1) Stay (ST), 2) Switch Eggy (Sleep Powder Siatam Snor — locks Siatam Snor in sleep clause), 3) Switch Charizard (Flying immune to my own Spikes? Yes Spikes don't damage Flying — Char enters at 100%).
- Worst plausible: Siatam Snor Curse-stacks (Siatam Snor +1/+1 vs mine; trade Curses).
- Public-info tier: Siatam Snor set = `strong prior` (Curse/BSlam/EQ/Rest or BSlam/EQ/Rest/Sleep Talk).
- Branch-punish: Stay-ST beats Siatam-Snor-Curse (chip + para potential pressure); Switch Eggy locks Siatam Snor sleep clause (uses my one sleep clause slot on Siatam side — big value).

Actual: mrsoup Snor SLP cant. Sleep Talk -> BSlam -> Siatam Snor 54 + **PARALYZED**. Siatam Snor Curse (+1/+1/-1 Spe). Lefties Siatam Snor 60 PAR.

Grade: top_match = 1 (EXACT — Stay). Acceptable = 1. In_top_3 = 1. Branch_named = 1 (Snor-Curse branch named).
positive_selection = 1 (BSlam fired, chip + para'd opponent Snor). route_converting = 1. branch_punish = 1. role_package = 1. errors = 0.

## Turn 29

Public state: Siatam Snor 60 PAR +1/+1/-1. mrsoup Snor 100 SLP.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script, rescore_after_reveal (Siatam Snor Curse revealed; Snor mirror).

Freeze:
- Recommended: Stay (Sleep Talk).
- Confidence: 50/30/20.
- Route reason: Sleep Talk picks BSlam (chip + para attempt) or Curse (mrsoup Snor sets up too, mirroring). Both positive. Rest excluded from ST pool in Gen 2.
- Top three: 1) Stay (ST), 2) Switch Eggy (Sleep Powder Siatam Snor — locks in sleep clause; locks Curse Snor for several turns), 3) Switch Charizard (Char immune to Spikes via Flying-type).
- Worst plausible: Sleep Talk picks BSlam and Siatam Snor full-para'd (25%) -> dodged the chip. Or Siatam Snor Curse again (+2/+2/-2 Spe stack).
- Public-info tier: Siatam Snor has BSlam = `strong prior`; has EQ = `strong prior`; has Rest = `strong prior` (CurseLax).
- Branch-punish: Stay-ST-BSlam beats Siatam-Snor-Curse (chip damage works against setup); Stay-ST-Curse compounds my setup; Switch Eggy locks Snor in sleep (big route convert).

Actual: **mrsoup Snor WOKE UP** (sleep ended). Snor **Curse** (+1 Atk/+1 Def/-1 Spe). Siatam Snor Rest -> 100 SLP. Snor mirror Curse setup.

Grade: top_match = 0 (my "Stay" was move-agnostic; mrsoup specifically picked Curse). Acceptable = 1 (Stay-ST-Curse was in my top-3 branch coverage — same setup family). In_top_3 = 1 (Curse was in my ST branch). Branch_named = 1.
top_rank_failure: candidate_weighting — I framed "Stay" too vaguely; should have committed to specific move Curse (anticipating Snor wake at end of 4 sleep turns; Gen 2 max sleep is 5 but mean ~3.5). mrsoup's specific Curse pick is the cleaner answer.
positive_selection = 1 (Curse improves route compounding); route_converting = 1; branch_punish = 1 (Curse compounds vs Siatam Snor's Curse mirror); role_package = 1; errors = 0.

## Turn 30

Public state: Siatam Snor 100 SLP +1/+1/-1. mrsoup Snor 100 +1/+1/-1. Mirror.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Curse (mrsoup Snor).
- Confidence: 50/30/20.
- Route reason: Snor mirror, both +1/+1, Siatam Snor asleep -> 1-3 free turns for me. Pump Curse to +2/+2 then +3/+3, etc. mrsoup Snor wins the Curse race since Siatam Snor is asleep + para'd (when it wakes). With +N stacking, mrsoup Snor sweeps after Siatam Snor wakes.
- Top three: 1) Curse, 2) Body Slam (chip Siatam Snor ~25% while it sleeps), 3) Rest (over-heal — wasteful at full HP).
- Worst plausible: Siatam Snor wakes T30 and Curses too (both at +2/+2). But Siatam Snor para'd -> 25% full-para risk.
- Public-info tier: Siatam Snor has BSlam = `strong prior` (CurseLax has BSlam).
- Branch-punish: Curse beats Siatam-Snor-wake-Curse (mirror, but Siatam Snor para'd = slower setup); beats Siatam-Snor-wake-BSlam (my +2 Def absorbs); loses to Siatam-Snor-wake-EQ-crit (rare).

Actual: mrsoup Snor Curse -> +2/+2/-2. Siatam Snor SLP cant; Sleep Talk -> Rest (already asleep — wasted move).

Grade: top_match = 1 (EXACT — Curse). Acceptable = 1. In_top_3 = 1. Branch_named = 1.
positive_selection = 1; route_converting = 1; branch_punish = 1; role_package = 1; errors = 0.

## Turn 31

Public state: mrsoup Snor 100 +2/+2/-2. Siatam Snor 100 SLP +1/+1/-1.
Pre-freeze loaded cards: baseline + reset_loop_denial, spend_or_save_piece, converter_before_script.

Freeze:
- Recommended: Curse (mrsoup Snor).
- Confidence: 60/25/15.
- Route reason: Keep stacking. Siatam Snor still asleep this turn (likely). +3/+3 puts mrsoup Snor in OHKO range on most of Siatam team.
- Top three: 1) Curse, 2) Body Slam (chip Siatam Snor ~30%), 3) Rest (full HP — wasteful).
- Branch-punish: same as T30.

Actual: Siatam Snor SLP cant. Sleep Talk -> **Double-Edge** -> mrsoup Snor -30% (70 HP). DE recoil -> Siatam Snor 93 -> 99 Lefties SLP. mrsoup Snor Curse -> +3/+3/-3.

Grade: top_match = 1 (EXACT — Curse). Acceptable = 1. In_top_3 = 1. Branch_named = 1.
positive_selection = 1; route_converting = 1; branch_punish = 1; role_package = 1; errors = 0.
Reveal: Siatam Snor has Double-Edge (non-standard; explains the higher Atk pressure than BSlam Snor).

---

## Interpretation

**Did the trigger block fire on every relevant board?** Yes. `reset_loop_denial.md` was loaded on every turn from T1 onward (Snorlax-Rest in package satisfied trigger). `spend_or_save_piece.md` was loaded on every turn with a unique-role piece in play. `converter_before_script.md` was loaded whenever a status/converter alternative existed. The Load-Required Triggers were honored on every relevant turn — no H1 (card-not-loaded) misses in this packet.

**H1/H2/H3/H4 split of the 15 top-match misses:**

| Mode | Count | Share | Turns |
|---|---|---|---|
| H1 card-not-loaded | 0 | 0% | (intervention eliminated this class) |
| H2 card-loaded-but-ignored | 8 | 53% | T2, T4, T9, T10, T11, T21, T25, T26 (route_budget + candidate_weighting failures despite card load) |
| H3 card-content-vague | 1 | 7% | T29 (move-pick vs "Stay" categorization edge case) |
| H4 oracle ceiling / hidden non-standard sets | 4 | 27% | T7 (Cloyster Clamp), T14 (Umbreon Zap Cannon), T24 (Steelix Boom), T31-Snorlax-DE (Siatam's DE Snor) |
| State-branch failures (subclass of H2) | 2 | 13% | T12 (Boom-vs-Ghost-pivot), T23 (EQ-vs-Zapdos-pivot) |

**Total: 15 misses, H1 share = 0%.**

**Compared to packet 044's diagnosis:**
- Packet 044: H1 67%, H2 13%, H3 7%, H4 13% — H1 dominant
- Packet 045: H1 0%, H2 53%+13% = 66%, H3 7%, H4 27% — H2 dominant

The intervention successfully eliminated H1 (card-not-loaded) failures. But this did NOT lift top-match from 15/30 because the H2 misses (cards loaded but their rules not rigorously applied at ranking time) now dominate. This is exactly the "audit ceiling" scenario the falsification gate flagged as triggering Issue 21 (pairwise contrastive drills) or Issue 22 (multi-oracle pivot).

**Why H2 is now dominant:**

The Load-Required Triggers forced loading of `reset_loop_denial`, `spend_or_save_piece`, `converter_before_script` — but loading is necessary not sufficient. The ranker still:
- Prioritized in-place setup over preservation pivots (T2 Curse-Snor instead of pivot-Forry to preserve Snor; T26 Curse instead of Rest);
- Underweighted "save sleep clause for higher-value target" route-budget (T1 + T3 — sleep on Nido vs save for Ttar/Snor);
- Failed the end-of-rank branch-punish audit on type-immunity branches (T12 Boom-vs-Ghost, T23 EQ-vs-Flying — both are PACKET-044-TURN-22-CLASS state-branch failures);
- Treated the post-cf87f141 audit as "name the branch" rather than "name the immune/dead-move branch AND demote candidates that lose to it."

**The branch-punish audit isn't strong enough as written.** The audit text says "for each top-three candidate, name the branch it beats AND the branch it loses to. A dead move into a named branch demotes itself." But it doesn't explicitly enumerate the type-immunity branches as named, so the ranker can satisfy the audit ("I named the branch") without surfacing the type-immunity demotion. T12 and T23 are textbook cases.

**Hidden non-standard sets compounded the miss rate.** mrsoup's team had four off-meta sets revealed mid-packet:
- Cloyster Clamp (T7) — trap converter mrsoup uses creatively.
- Umbreon Zap Cannon (T14) — Electric coverage on a Dark mon.
- Steelix Explosion (T24) — Boom-cash-out from a wall.
- Siatam Snorlax Double-Edge (T31) — high-damage Snor variant.

Three of these are on mrsoup's own team — my "side-known" reconstruction was species-only, not move-specific, so these came as `possible only` reveals. H4 ceiling for this specific opponent set; would normalize with a more standard-team-mix.

**Pass/fail gates per spec:**

| Gate | Target | Actual | Met? |
|---|---|---|---|
| Top-match | >=20/30 (preferably >=25) | 15/30 | NO |
| Severe/hidden/state/mechanics all 0 | all 0 | severe=1, hidden=1 | NO |
| Route-conversion not falling vs 22/30 | >=22 | 21 | NO (just under) |
| Branch-punish not falling vs 21/30 | >=21 | 18 | NO |
| Pre-freeze loaded-cards filled | every turn | every turn | YES |

The packet **does NOT meet "plateau-broken"** per spec. **Triggers were honored**, but several other gates failed.

Per spec, this maps to **"Ceiling-reached"** (exact-top < 20/30 despite trigger compliance). The per-turn loaded-cards field and top_rank_failure tag indicate **failures are H2 (cards loaded but ignored)** + H4 (oracle ceiling from non-standard sets), not H1.

**Recommended next action:**

1. **Keep the trigger block** — it successfully eliminated H1 (the dominant failure class in packet 044). The cards are loading. That's a real improvement even though it didn't move top-match.
2. **Strengthen the branch-punish audit** in `live_core.md` to explicitly enumerate type-immunity demotions: "For each top-3 candidate, list type/ability immunities on the opponent team that would make this move dead." T12 (Ghost-Boom) and T23 (Flying-EQ) are the same class as packet 044's Turn 22 (Toxic-into-sleeping-Snor) — the audit is named but not enforced.
3. **Pivot to pairwise contrastive drills (Inventory Issue 21)** for the route_budget H2 misses — the "Curse vs Rest vs BSlam" and "Sleep Powder on Nido vs save sleep for Snor" calls need explicit pairwise framing in the cards, not just "use the converter" general guidance.
4. **Multi-oracle (Inventory Issue 22)** is premature — single-oracle still has actionable improvement headroom in the audit and pairwise drills.
5. **Note for cross-model comparison**: if Codex run on the same replay produces similar top-match (~15) with similar H2 dominance, the diagnosis is model-agnostic. If Codex produces materially higher top-match, the cards may be tuned for Codex priors and need Claude-side audit hardening.

**Honesty note:** the severe blunder + hidden_info failure on T12 (Cloyster Explosion into Gengar Ghost immunity) is the highest-value lesson from this packet. The intervention's branch-punish audit was supposed to catch this exact class. It didn't because:
(a) "Ghost-pivot to block Boom" was a `strong prior` in GSC OU but I treated it as `possible only` — pricing failure;
(b) The audit's "demote dead moves into named branches" only fires when the branch is explicitly named, and I did not name "Siatam pivots Gengar to immune my Boom" specifically before freezing.

The fix for this class is to make the audit list type-immunity branches even when no specific pivot is in flight (e.g., "Normal moves: list every Ghost on opponent's revealed/known team; Ground moves: list every Flying; Electric moves: list every Ground; Psychic moves: list every Dark"). This is one additional line in the live_core audit, not a new card.


