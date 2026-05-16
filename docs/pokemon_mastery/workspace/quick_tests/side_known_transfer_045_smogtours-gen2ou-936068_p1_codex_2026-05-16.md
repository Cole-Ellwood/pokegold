# Replay Turn-Pause Run - 2026-05-16 - smogtours-gen2ou-936068 - Codex

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-936068.log`
Mode: side-known reconstructed for p1 / shiloh.
Contamination control: local `rg` found zero prior `smogtours-gen2ou-936068` hits before selection. I did not read any `_claude_` packet. One earlier candidate (`smogtours-gen2ou-936075`) was discarded after accidental full-log exposure; it was not used for this run.
Side-known source: helper reconstruction from the full replay log before turn 1, for p1 own roster/moves only. Reconstruction peek turns: 1-62 for own-team reconstruction only.

## Score Summary

Decisions: 30
Top-match: 15/30                     (target: >=20/30 to claim intervention working)
Acceptable-match: 28/30
Positive-selection: 28/30
Route-converting move chosen: 27/30
Branch-punish chosen: 24/30
Role-package update obeyed: 30/30
Actual in frozen top three: 24/30
Actual branch named before reveal: 28/30
Severe blunders: 1
Hidden-info errors: 0
State errors: 0
Mechanics errors: 0
Earliest meaningful error: Turn 8 route-budget/type-owner miss; severe branch-audit failure on Turn 27

Pre-freeze baseline loaded every turn: `active_context.md`, `live_core.md`, `replay_turn_pause_protocol.md`, `heuristic_core/role_package_ledger.md`, `heuristic_core/branch_punish_ranking.md`, `heuristic_core/public_info_tiers.md`, `heuristic_core/name_next_board_owner.md`, `heuristic_core/reset_loop_denial.md`, `heuristic_core/spend_or_save_piece.md`, `heuristic_core/converter_before_script.md`, `canon/gsc_spikes_spin.md`, `canon/gsc_sleep_status.md`, `canon/gsc_phazing_priority.md`.

## Turn 1

Public state: Exeggutor 100% vs Forretress 100%, no hazards.
Pre-freeze loaded cards: baseline set above; converter loaded for status/switch temptation; reset loaded from own Rest package.
Answer: switch Marowak. Confidence: 45/35/20. Route reason: Forretress support wants free Spikes/Toxic, and Marowak's Fire Blast threatens the support piece before the hazard script stabilizes.
Top three: 1. switch Marowak; 2. switch Golem; 3. Stun Spore.
Serious alternatives: Golem preserves the future Spin route; Stun Spore catches a branch but lets Forretress act.
Rejected tempting safe/default line: Psychic chip into Forretress.
Worst branch + fallback: Forretress pivots to Heracross or Starmie; re-score to Zapdos/Cloyster.
Public-info tiers: Forretress support package strong prior; Heracross branch possible only.
Branch-punish audit: Marowak beats Forretress, loses to Water/Starmie; Golem beats Forretress and enables Spin, loses to Water/Grass; Stun Spore beats a fast branch, loses to Steel staying.
Actual: p2 switched Heracross; p1 Stun Spore paralyzed it.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=0; top_rank_failure=branch_probability.

## Turn 2

Public state: Exeggutor 100% vs paralyzed Heracross 100%; Forretress revealed by entry only.
Pre-freeze loaded cards: baseline set above.
Answer: switch Zapdos. Confidence: 45/35/20. Route reason: Heracross threatens Exeggutor by class; Zapdos is the typed pressure owner.
Top three: 1. switch Zapdos; 2. switch Cloyster; 3. switch Snorlax.
Serious alternatives: Cloyster covers the Forretress double and hazard mirror; Snorlax is broad but less route-active.
Rejected tempting safe/default line: stay Psychic into a bad Bug branch.
Worst branch + fallback: p2 doubles Forretress as Zapdos enters; go Cloyster/Golem sequencing.
Public-info tiers: Heracross attack package strong prior; Forretress double revealed by prior entry.
Branch-punish audit: Zapdos beats Heracross, loses to Electric/Rock counter-owner; Cloyster beats Forretress, loses to Electric/Starmie; Snorlax beats generic damage, loses momentum to Forretress.
Actual: p1 switched Cloyster; p2 switched Forretress.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=branch_probability.

## Turn 3

Public state: Cloyster 100% vs Forretress 100%, no hazards.
Pre-freeze loaded cards: baseline set above.
Answer: Spikes. Confidence: 70/20/10. Route reason: Cloyster can convert the support mirror first before Forretress fully stabilizes.
Top three: 1. Spikes; 2. Surf; 3. switch Golem.
Serious alternatives: Surf chips Forretress; Golem preserves Cloyster but gives tempo.
Rejected tempting safe/default line: immediate switch without progress.
Worst branch + fallback: Forretress Toxics or sets Spikes back; use Surf/Golem re-score.
Public-info tiers: Forretress Spikes/Toxic/Spin/Explosion package strong prior.
Branch-punish audit: Spikes beats passive support, loses to immediate Spin; Surf beats staying Forretress, loses to hazard tempo; Golem beats future Spin reset, loses to Toxic/Water branches.
Actual: p1 Spikes; p2 Toxic poisoned Cloyster.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 4

Public state: Cloyster 100% poisoned vs Forretress 100%; Spikes on p2.
Pre-freeze loaded cards: baseline set above.
Answer: Surf. Confidence: 65/25/10. Route reason: Cloyster's support job is delivered, so chip Forretress before it owns the hazard loop.
Top three: 1. Surf; 2. Explosion; 3. switch Golem.
Serious alternatives: Explosion may trade with the support piece; Golem prepares Spin but pays tempo.
Rejected tempting safe/default line: re-click Spikes.
Worst branch + fallback: Forretress sets p1 Spikes; Golem becomes the next reset piece.
Public-info tiers: Forretress support/cash-out strong prior.
Branch-punish audit: Surf beats Forretress staying, loses to Starmie/Water; Explosion beats active support, loses to Ghost/resist; Golem beats future hazard reset, loses to Toxic.
Actual: p1 Surf; p2 Spikes.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 5

Public state: Cloyster 100% poisoned vs Forretress 66%; Spikes both sides.
Pre-freeze loaded cards: baseline set above.
Answer: Surf. Confidence: 70/20/10. Route reason: Surf keeps active pressure and covers non-Water switch branches without spending Explosion into a Ghost risk.
Top three: 1. Surf; 2. Explosion; 3. switch Golem.
Serious alternatives: Explosion if Forretress must be removed now; Golem for Spin route.
Rejected tempting safe/default line: preserve Cloyster before forcing Forretress.
Worst branch + fallback: Starmie or Misdreavus enters; re-score Electric/Golem route.
Public-info tiers: Starmie/Ghost branches possible from opponent structure only.
Branch-punish audit: Surf beats Forretress and Misdreavus chip, loses to Starmie; Explosion beats Forretress, loses to Ghost; Golem beats hazard reset, loses to Water.
Actual: p2 switched Misdreavus; p1 Surf.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 6

Public state: Cloyster 95% poisoned vs Misdreavus 58%; Spikes both sides.
Pre-freeze loaded cards: baseline set above.
Answer: Surf. Confidence: 75/15/10. Route reason: Surf pressures the spinblocker while Explosion is illegal into the Ghost branch.
Top three: 1. Surf; 2. switch Zapdos; 3. switch Golem.
Serious alternatives: Zapdos pressures Ghost/Water; Golem threatens Spin only after Ghost leaves.
Rejected tempting safe/default line: Explosion into a Ghost.
Worst branch + fallback: Starmie enters and threatens Spin/Recover; Zapdos handoff.
Public-info tiers: Misdreavus Ghost immunity revealed by species; Starmie branch possible.
Branch-punish audit: Surf beats Ghost staying, loses to Starmie; Zapdos beats Starmie/Ghost, loses to Raikou/Blissey; Golem beats future Spin route, loses to Water.
Actual: p2 switched Starmie; p1 Surf.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 7

Public state: Cloyster 83% poisoned vs Starmie 78%; p1 Spikes up, p2 Spikes cleared later only if Starmie spins.
Pre-freeze loaded cards: baseline set above.
Answer: Explosion. Confidence: 45/35/20. Route reason: remove or heavily punish the spinner before it resets the p2-side hazard route.
Top three: 1. Explosion; 2. switch Zapdos; 3. Surf.
Serious alternatives: Zapdos preserves Cloyster and pressures Starmie; Surf keeps chip but does not deny Spin.
Rejected tempting safe/default line: Surf as low-commitment damage.
Worst branch + fallback: Misdreavus catches Explosion; if so, the line fails and Golem/Zapdos must recover the route.
Public-info tiers: Starmie spinner revealed; Ghost branch revealed by prior entry.
Branch-punish audit: Explosion beats Starmie, loses to Misdreavus; Zapdos beats Starmie, loses hazard tempo to Spin; Surf beats no switch, loses to Recover/Spin reset.
Actual: p1 switched Zapdos; p2 Rapid Spin removed p2-side Spikes.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=preservation.

## Turn 8

Public state: Zapdos 100% vs Starmie 84%; Spikes on p1 only.
Pre-freeze loaded cards: baseline set above.
Answer: Thunderbolt. Confidence: 60/25/15. Route reason: punish the active spinner immediately.
Top three: 1. Thunderbolt; 2. Thunder Wave; 3. switch Snorlax.
Serious alternatives: Thunder Wave catches Blissey/Raikou; Snorlax covers the Electric branch.
Rejected tempting safe/default line: passive switch before forcing Starmie.
Worst branch + fallback: Raikou enters on Thunderbolt; go Snorlax/Golem after the branch is public.
Public-info tiers: Raikou/Electric branch possible from structure, not revealed yet.
Branch-punish audit: Thunderbolt beats Starmie, loses to Raikou; Thunder Wave beats switch branches, loses to immediate Starmie value; Snorlax beats Electric, loses tempo to Starmie.
Actual: p2 switched Raikou; p1 switched Cloyster through Spikes.
Grade: top_match=0; acceptable_match=0; positive_selection=0; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=type_owner.

## Turn 9

Public state: Cloyster 64% poisoned vs Raikou 100%; Spikes on p1.
Pre-freeze loaded cards: baseline set above.
Answer: switch Snorlax. Confidence: 70/20/10. Route reason: Cloyster cannot act through Electric pressure; Snorlax is the broad absorber that preserves Golem from Hidden Power.
Top three: 1. switch Snorlax; 2. switch Golem; 3. switch Exeggutor.
Serious alternatives: Golem blocks Electric but risks Hidden Power; Exeggutor is a softer sponge.
Rejected tempting safe/default line: Surf or Explosion from a faster-threatened Cloyster.
Worst branch + fallback: Raikou uses Hidden Power or doubles Misdreavus; re-score to Golem/Zapdos.
Public-info tiers: Raikou Thunderbolt revealed next only after reveal; Hidden Power is strong prior, not fact.
Branch-punish audit: Snorlax beats Electric damage, loses to hard Ghost; Golem beats Thunderbolt, loses to HP Water/Ice; Exeggutor beats Ground-coverage absence, loses to HP Ice.
Actual: p1 switched Snorlax; p2 Thunderbolt.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 10

Public state: Snorlax 70% vs Raikou 100%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Earthquake. Confidence: 50/35/15. Route reason: Earthquake punishes the active Electric and the Forretress/Raikou branch without recoil.
Top three: 1. Earthquake; 2. Double-Edge; 3. Rest.
Serious alternatives: Double-Edge covers Heracross/Starmie better; Rest preserves Snorlax if overpricing Thunderbolt.
Rejected tempting safe/default line: immediate Rest at 70%.
Worst branch + fallback: Misdreavus enters; Earthquake still hits in GSC, so continue pressure.
Public-info tiers: Misdreavus branch revealed; no Levitate in GSC.
Branch-punish audit: Earthquake beats Raikou/Misdreavus/Forretress, loses to Starmie/Heracross; Double-Edge beats Starmie/Heracross, loses to Misdreavus; Rest beats chip race, loses tempo.
Actual: p2 switched Misdreavus; p1 Double-Edge was immune.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=oracle_style.

## Turn 11

Public state: Snorlax 77% vs Misdreavus 65%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: switch Golem. Confidence: 45/35/20. Route reason: Golem threatens the Ghost with Earthquake and may create the later Spin route if Misdreavus leaves.
Top three: 1. switch Golem; 2. switch Exeggutor; 3. switch Marowak.
Serious alternatives: Exeggutor pressures with Psychic; Marowak is stronger but more valuable.
Rejected tempting safe/default line: Double-Edge into an immune Ghost.
Worst branch + fallback: Toxic lands on Golem; use Earthquake/Spin before it is worn down.
Public-info tiers: Misdreavus Toxic revealed; Perish/trap possible only.
Branch-punish audit: Golem beats Ghost and enables Spin, loses to Toxic/Water; Exeggutor beats Ghost, loses to Toxic/Ice; Marowak beats Ghost, loses to status/Water.
Actual: p1 switched Zapdos; p2 Toxic poisoned Zapdos.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=preservation.

## Turn 12

Public state: Zapdos 100% poisoned vs Misdreavus 71%.
Pre-freeze loaded cards: baseline set above.
Answer: Thunderbolt. Confidence: 55/35/10. Route reason: damage pressures Misdreavus before Toxic consumes Zapdos.
Top three: 1. Thunderbolt; 2. Thunder Wave; 3. switch Golem.
Serious alternatives: Thunder Wave catches Raikou/Blissey; Golem pressures Ghost and Spin route.
Rejected tempting safe/default line: switch out immediately after taking Toxic.
Worst branch + fallback: Raikou enters; go Snorlax/Golem.
Public-info tiers: Raikou branch possible; no hidden moves assumed.
Branch-punish audit: Thunderbolt beats Misdreavus/Starmie, loses to Raikou; Thunder Wave beats switch branches, loses damage tempo; Golem beats Ghost, loses to Water/status.
Actual: p2 switched Raikou; p1 Thunder Wave paralyzed it.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=branch_probability.

## Turn 13

Public state: Zapdos 100% poisoned vs Raikou 100% paralyzed; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: switch Snorlax. Confidence: 70/20/10. Route reason: Snorlax is the safer Electric absorber while Golem must preserve Spin and fears Hidden Power.
Top three: 1. switch Snorlax; 2. switch Golem; 3. Thunderbolt.
Serious alternatives: Golem blocks Thunderbolt; Thunderbolt stays active but is resisted.
Rejected tempting safe/default line: stay and trade resisted Thunderbolt.
Worst branch + fallback: Raikou doubles to Misdreavus; re-score from Snorlax/Ghost.
Public-info tiers: Hidden Power strong prior, not revealed.
Branch-punish audit: Snorlax beats Electric damage, loses to Ghost handoff; Golem beats Electric, loses to HP; Thunderbolt beats no-switch only, loses to Raikou staying.
Actual: p1 switched Snorlax; p2 Thunderbolt.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 14

Public state: Snorlax 48% vs Raikou 100% paralyzed; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Rest. Confidence: 55/35/10. Route reason: Snorlax is the active Electric sponge and must preserve the route job before another Thunderbolt plus Spikes breaks it.
Top three: 1. Rest; 2. Earthquake; 3. Double-Edge.
Serious alternatives: Earthquake punishes Raikou; Double-Edge covers Starmie/Heracross.
Rejected tempting safe/default line: chase chip while the sponge is low.
Worst branch + fallback: Misdreavus enters on Rest; use Golem/Zapdos after wake state is priced.
Public-info tiers: Misdreavus branch revealed.
Branch-punish audit: Rest beats Electric damage race, loses tempo to Ghost; Earthquake beats Raikou/Ghost, loses Snorlax HP; Double-Edge beats non-Ghost branches, loses to Misdreavus.
Actual: p2 switched Misdreavus; p1 Rest.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 15

Public state: Snorlax asleep, Rest sleep actions 0, vs Misdreavus 77%.
Pre-freeze loaded cards: baseline set above.
Answer: switch Golem. Confidence: 45/35/20. Top three: 1. switch Golem; 2. switch Exeggutor; 3. Sleep Talk if legal from own side-known.
Actual: p2 switched Forretress; p1 stayed asleep with no chosen move logged.
Grade: unscored no-action sleep turn per protocol exclusions.

## Turn 16

Public state: Snorlax asleep, Rest sleep actions 1, vs Forretress 72%.
Pre-freeze loaded cards: baseline set above.
Answer: Sleep Talk. Confidence: 55/30/15. Top three: 1. Sleep Talk; 2. switch Golem; 3. switch Marowak.
Actual: p2 switched Heracross; p1 stayed asleep with no chosen move logged.
Grade: unscored no-action sleep turn per protocol exclusions.

## Turn 17

Public state: Snorlax will wake and act vs paralyzed Heracross 100%.
Pre-freeze loaded cards: baseline set above.
Answer: switch Zapdos. Confidence: 55/30/15. Route reason: Zapdos is the typed Heracross owner and preserves Snorlax for the special sponge route.
Top three: 1. switch Zapdos; 2. switch Cloyster; 3. Double-Edge.
Serious alternatives: Cloyster can take a hit and threaten; Double-Edge stays active but risks Fighting pressure.
Rejected tempting safe/default line: RestTalk inertia after wake.
Worst branch + fallback: Heracross doubles Misdreavus; re-score to Golem/EQ.
Public-info tiers: Heracross attack package strong prior.
Branch-punish audit: Zapdos beats Heracross, loses to Electric/Rock; Cloyster beats physical hit, loses to Electric; Double-Edge beats stay/switch chip, loses to Ghost/Fighting.
Actual: p2 switched Misdreavus; p1 woke and Double-Edge was immune.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=0; top_rank_failure=oracle_style.

## Turn 18

Public state: Snorlax 100% vs Misdreavus 83%.
Pre-freeze loaded cards: baseline set above.
Answer: switch Golem. Confidence: 50/35/15. Route reason: Golem pressures the Ghost with Earthquake and keeps the Spin route live.
Top three: 1. switch Golem; 2. switch Zapdos; 3. switch Exeggutor.
Serious alternatives: Zapdos blanks Toxic once already statused; Exeggutor pressures with Psychic.
Rejected tempting safe/default line: Normal attack into Ghost.
Worst branch + fallback: Toxic hits Golem; trade tempo for Earthquake/Spin.
Public-info tiers: Toxic revealed.
Branch-punish audit: Golem beats Ghost/Spinblock, loses to Toxic/Water; Zapdos beats Toxic and Ghost, loses to poison clock/Electric; Exeggutor beats Ghost, loses to Toxic/Ice.
Actual: p1 switched Zapdos; p2 Toxic failed into already-poisoned Zapdos.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=preservation.

## Turn 19

Public state: Zapdos 94% poisoned vs Misdreavus 89%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Thunderbolt. Confidence: 50/30/20. Route reason: Zapdos must convert damage before poison and can still punish Ghost/Starmie.
Top three: 1. Thunderbolt; 2. Thunder Wave; 3. switch Golem.
Serious alternatives: Thunder Wave catches branches; Golem preserves Zapdos and threatens Spin.
Rejected tempting safe/default line: passive switch without punishing Ghost.
Worst branch + fallback: Raikou enters; Golem/Snorlax response.
Public-info tiers: Raikou branch revealed by earlier entry.
Branch-punish audit: Thunderbolt beats Ghost/Starmie, loses to Raikou; Thunder Wave beats switch branches, loses damage tempo; Golem beats Raikou/Ghost, loses to Water/status.
Actual: p1 switched Golem; p2 switched Raikou.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget.

## Turn 20

Public state: Golem 94% vs Raikou 100% paralyzed; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Earthquake. Confidence: 55/35/10. Route reason: Earthquake punishes the active Electric and the likely Forretress/Ghost branches better than blind Spin.
Top three: 1. Earthquake; 2. Rapid Spin; 3. switch Exeggutor.
Serious alternatives: Rapid Spin resets p1-side Spikes; Exeggutor avoids Hidden Power if needed.
Rejected tempting safe/default line: Rapid Spin before naming the Ghost branch.
Worst branch + fallback: Starmie enters and pressures Golem; Zapdos/Snorlax handoff.
Public-info tiers: Hidden Power strong prior; Misdreavus branch revealed.
Branch-punish audit: Earthquake beats Raikou/Forretress/Misdreavus, loses to Starmie/Heracross; Rapid Spin beats hazard loop, loses to Ghost; Exeggutor beats Water-ish branch, loses to HP Ice.
Actual: p2 switched Forretress; p1 Earthquake.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 21

Public state: Golem 99% vs Forretress 51%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Rapid Spin. Confidence: 45/40/15. Route reason: Golem is active and healthy, so clearing p1 Spikes can reset the opponent's route if the Ghost does not enter.
Top three: 1. Rapid Spin; 2. Earthquake; 3. switch Marowak.
Serious alternatives: Earthquake keeps pressure and beats Misdreavus; Marowak punishes Forretress but spends a breaker.
Rejected tempting safe/default line: more Earthquake chip while hazards keep taxing every handoff.
Worst branch + fallback: Misdreavus blocks Spin; use Earthquake next if still available.
Public-info tiers: Misdreavus spinblock revealed; Forretress Explosion strong prior.
Branch-punish audit: Spin beats hazard loop, loses to Ghost; Earthquake beats Forretress/Ghost, loses hazard reset; Marowak beats Forretress, loses to Water/status.
Actual: p1 switched Zapdos; p2 switched Starmie.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=branch_probability.

## Turn 22

Public state: Zapdos 88% poisoned vs Starmie 90%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Thunderbolt. Confidence: 70/20/10. Route reason: Zapdos directly punishes the spinner and any non-Electric branch.
Top three: 1. Thunderbolt; 2. Thunder Wave; 3. switch Snorlax.
Serious alternatives: Thunder Wave catches Blissey/Raikou; Snorlax covers Electric/special wall branches.
Rejected tempting safe/default line: switch before Starmie is forced.
Worst branch + fallback: Blissey absorbs Thunderbolt; hand Snorlax/Marowak in.
Public-info tiers: Blissey branch possible only until reveal.
Branch-punish audit: Thunderbolt beats Starmie, loses to Blissey/Raikou; Thunder Wave beats Blissey branch, loses active pressure; Snorlax beats Blissey/Raikou, loses Starmie tempo.
Actual: p2 switched Blissey; p1 Thunderbolt crit.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 23

Public state: Zapdos 82% poisoned vs Blissey 78%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: switch Snorlax. Confidence: 60/25/15. Route reason: Blissey is the special wall/cleric package; Snorlax is the low-risk physical owner.
Top three: 1. switch Snorlax; 2. switch Marowak; 3. switch Golem.
Serious alternatives: Marowak can break harder; Golem preserves Snorlax but fears Ice Beam.
Rejected tempting safe/default line: continue Thunderbolt into Blissey.
Worst branch + fallback: Blissey uses Ice Beam/Heal Bell; Snorlax pressures next.
Public-info tiers: Heal Bell strong prior from Blissey class, revealed after this turn.
Branch-punish audit: Snorlax beats Blissey, loses to Misdreavus; Marowak beats Blissey, loses to Ice/status/Water; Golem beats Blissey modestly, loses to Ice.
Actual: p1 switched Snorlax; p2 Heal Bell.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 24

Public state: Snorlax 94% vs Blissey 84%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Earthquake. Confidence: 50/35/15. Route reason: Earthquake hits active Blissey without recoil and covers the Misdreavus/Forretress/Raikou branch better than Double-Edge.
Top three: 1. Earthquake; 2. Double-Edge; 3. switch Marowak.
Serious alternatives: Double-Edge is stronger into non-Ghost; Marowak threatens Blissey but spends a breaker through Spikes.
Rejected tempting safe/default line: Rest while healthy.
Worst branch + fallback: Heracross/Starmie enters; re-score to Zapdos/Snorlax.
Public-info tiers: Misdreavus branch revealed; no Levitate.
Branch-punish audit: Earthquake beats Blissey/Misdreavus/Forretress, loses to Heracross/Starmie; Double-Edge beats Blissey/Starmie, loses to Ghost; Marowak beats Blissey, loses to Water/status.
Actual: p1 switched Zapdos; p2 switched Misdreavus.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=route_budget.

## Turn 25

Public state: Zapdos 75% poisoned vs Misdreavus 96%.
Pre-freeze loaded cards: baseline set above.
Answer: Thunderbolt. Confidence: 55/35/10. Route reason: damage pressures Misdreavus and prevents pure Toxic-loop passivity.
Top three: 1. Thunderbolt; 2. Thunder Wave; 3. switch Golem.
Serious alternatives: Thunder Wave catches Blissey/Raikou; Golem pressures Ghost.
Rejected tempting safe/default line: switch out immediately after poison.
Worst branch + fallback: Blissey enters and absorbs; Snorlax/Marowak next.
Public-info tiers: Blissey branch revealed by prior turn.
Branch-punish audit: Thunderbolt beats Ghost/Starmie, loses to Blissey/Raikou; Thunder Wave beats Blissey branch, loses damage tempo; Golem beats Ghost, loses to Water/status.
Actual: p2 switched Blissey; p1 Thunder Wave paralyzed it.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=branch_probability.

## Turn 26

Public state: Zapdos 69% poisoned vs Blissey 90% paralyzed.
Pre-freeze loaded cards: baseline set above.
Answer: switch Snorlax. Confidence: 55/30/15. Route reason: Snorlax again owns Blissey without spending Marowak or risking Golem into Ice Beam.
Top three: 1. switch Snorlax; 2. switch Marowak; 3. switch Golem.
Serious alternatives: Marowak creates immediate breaker pressure; Golem preserves Snorlax but is worse into Ice Beam.
Rejected tempting safe/default line: Thunderbolt into special wall.
Worst branch + fallback: Blissey Ice Beams on a physical switch; Snorlax can Rest later.
Public-info tiers: Ice Beam not revealed yet but strong prior on Blissey.
Branch-punish audit: Snorlax beats Blissey/Ice, loses to Misdreavus; Marowak beats Blissey, loses to Ice/status; Golem beats Blissey weakly, loses to Ice.
Actual: p1 switched Exeggutor; p2 Ice Beam.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=missing_candidate.

## Turn 27

Public state: Exeggutor 55% vs Blissey 96% paralyzed; Blissey revealed Heal Bell and Ice Beam.
Pre-freeze loaded cards: baseline set above.
Answer: Explosion. Confidence: 45/35/20. Route reason: trade the low Exeggutor into the cleric/special wall before Heal Bell resets the status progress.
Top three: 1. Explosion; 2. switch Snorlax; 3. switch Marowak.
Serious alternatives: Snorlax preserves Explosion; Marowak pressures but pays Spikes.
Rejected tempting safe/default line: Psychic chip into Blissey.
Worst branch + fallback: Misdreavus enters and blanks Explosion; this branch should demote Explosion.
Public-info tiers: Misdreavus branch revealed and paralyzed.
Branch-punish audit: Explosion beats Blissey, loses hard to Misdreavus; Snorlax beats Blissey, loses to Ghost tempo; Marowak beats Blissey, loses to Water/status. Audit result: failed, because I kept Explosion first despite the named Ghost immunity branch.
Actual: p2 switched Misdreavus; p1 Stun Spore paralyzed it.
Grade: top_match=0; acceptable_match=0; positive_selection=0; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=status_branch_obedience. Severe blunder=1: top Explosion would have spent Exeggutor into a revealed Ghost immunity branch. No hidden/state/mechanics error.

## Turn 28

Public state: Exeggutor 61% vs Misdreavus 100% paralyzed.
Pre-freeze loaded cards: baseline set above.
Answer: Psychic. Confidence: 80/15/5. Route reason: Psychic is the clean active punish after the Ghost is paralyzed; Explosion remains dead into Ghost.
Top three: 1. Psychic; 2. switch Golem; 3. switch Marowak.
Serious alternatives: Golem threatens EQ/Spin route; Marowak pressures but spends a breaker.
Rejected tempting safe/default line: Explosion into Ghost.
Worst branch + fallback: Blissey enters; trade/switch after damage.
Public-info tiers: Blissey branch revealed.
Branch-punish audit: Psychic beats Misdreavus, loses to Blissey; Golem beats Ghost/Spinblock, loses to Water/status; Marowak beats Ghost, loses to Water/status.
Actual: p1 Psychic; Misdreavus fully paralyzed.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 29

Public state: Exeggutor 67% vs Misdreavus 61% paralyzed.
Pre-freeze loaded cards: baseline set above.
Answer: Psychic. Confidence: 75/15/10. Route reason: continue the active punish while covering the Blissey switch with chip before choosing a cash-out.
Top three: 1. Psychic; 2. switch Golem; 3. Explosion.
Serious alternatives: Golem pressures Ghost; Explosion is only for a hard Blissey read.
Rejected tempting safe/default line: explode before Ghost is removed.
Worst branch + fallback: Blissey enters and heals; consider Explosion next.
Public-info tiers: Blissey branch revealed.
Branch-punish audit: Psychic beats Ghost and chips Blissey, loses to cleric reset; Golem beats Ghost, loses to Water/status; Explosion beats Blissey, loses to Ghost.
Actual: p2 switched Blissey; p1 Psychic crit.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 30

Public state: Exeggutor 73% vs Blissey 77% paralyzed.
Pre-freeze loaded cards: baseline set above.
Answer: Explosion. Confidence: 65/25/10. Route reason: now the active cleric/special wall is exposed and the Ghost is paralyzed and no longer active, so cash-out converts.
Top three: 1. Explosion; 2. switch Snorlax; 3. switch Marowak.
Serious alternatives: Snorlax/Marowak preserve Exeggutor but let Heal Bell/Ice Beam continue.
Rejected tempting safe/default line: Psychic chip into a special wall.
Worst branch + fallback: Misdreavus hard-switches again; if so Explosion fails, but the prior Psychic/para makes that a lower-probability branch than Turn 27.
Public-info tiers: Ghost branch revealed; exact switch timing branch read.
Branch-punish audit: Explosion beats Blissey, loses to Misdreavus; Snorlax beats Blissey, loses Ghost tempo; Marowak beats Blissey, loses Water/status.
Actual: p1 Explosion KOed Blissey and Exeggutor; forced switch to Snorlax vs Forretress.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 31

Public state: Snorlax 88% vs Forretress 58%; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Earthquake. Confidence: 70/20/10. Route reason: Earthquake pressures Forretress and the Misdreavus branch without recoil.
Top three: 1. Earthquake; 2. Double-Edge; 3. Rest.
Serious alternatives: Double-Edge covers Starmie/Heracross; Rest preserves but gives Forretress support time.
Rejected tempting safe/default line: Rest while healthy.
Worst branch + fallback: Forretress Explodes or Starmie enters; use Golem/Zapdos after reveal.
Public-info tiers: Explosion strong prior, not revealed.
Branch-punish audit: Earthquake beats Forretress/Misdreavus/Raikou, loses to Starmie/Heracross; Double-Edge beats non-Ghost, loses to Misdreavus; Rest beats chip, loses support tempo.
Actual: p2 switched Misdreavus; p1 Earthquake.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Turn 32

Public state: Snorlax 94% vs Misdreavus 34% paralyzed; p1 Spikes.
Pre-freeze loaded cards: baseline set above.
Answer: Earthquake. Confidence: 80/15/5. Route reason: Earthquake removes or forces the low Ghost and still hits the Forretress/Raikou branch.
Top three: 1. Earthquake; 2. Rest; 3. switch Golem.
Serious alternatives: Rest preserves Snorlax; Golem threatens Spin if Ghost leaves.
Rejected tempting safe/default line: Double-Edge into Ghost.
Worst branch + fallback: Starmie/Heracross enters; handoff to Zapdos/Snorlax route.
Public-info tiers: Forretress/Raikou branches revealed.
Branch-punish audit: Earthquake beats Ghost/Forretress/Raikou, loses to Starmie/Heracross; Rest beats preservation, loses tempo; Golem beats Spin route, loses Water/status.
Actual: p2 switched Forretress; p1 Earthquake.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none.

## Interpretation

The trigger block fired on every trigger-relevant board. I over-loaded the mandatory trigger cards by keeping `reset_loop_denial.md`, `spend_or_save_piece.md`, and `converter_before_script.md` in context for the whole packet, so there were no missed load-trigger turns. That makes the result falsifying rather than inconclusive: exact-top stayed at 15/30 despite the required cards being available.

Remaining exact-top misses split roughly as H2-heavy rather than H1: H1/card-not-loaded = 0; H2/card-loaded-but-ignored = 4 (Turns 8, 21, 24, 27, with Turn 27 severe); H3/card-content-vague = 2 (Turns 11, 18 preservation/statused absorber ordering); H4/oracle/style or branch-probability = 9 (Turns 1, 2, 7, 10, 12, 17, 19, 25, 26). The most important failure is not missing card retrieval but applying the branch-punish audit at cash-out time: Turn 27 named Misdreavus as the losing branch for Explosion and still left Explosion first.

Recommended next action: keep the trigger block because it made H1 observable and prevented missed-load ambiguity, but do not expand it yet. The next work should be pairwise contrastive drills for loaded-card obedience, especially "cash-out into revealed immunity branch" and "route-budget switch versus active chip after hazard/status pressure." This packet does not support a plateau-broken claim.
