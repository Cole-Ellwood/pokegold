# Replay Turn-Pause Run - 2026-05-16 - smogtours-gen2ou-821941

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-821941.log`
Mode: side-known reconstructed for p1 / gorgie.
Contamination control: local `rg` found no prior `smogtours-gen2ou-821941` artifact before selection. Only p1 side-known prompts were opened.

Load packet before freezing: `active_context.md`, `playbook_manifest.md`, `live_core.md`, `replay_turn_pause_protocol.md`, `heuristic_core/role_package_ledger.md`, `heuristic_core/branch_punish_ranking.md`, `heuristic_core/public_info_tiers.md`, `heuristic_core/name_next_board_owner.md`, and `canon/gsc_lead_rps.md`.

## Score Summary

Decisions: 30
Top-match: 15/30
Acceptable-match: 29/30
Severe blunders: 0
State errors: 1
Hidden-info errors: 0
Mechanics errors: 0
Positive-selection: 28/30
Route-converting move chosen: 22/30
Branch-punish chosen: 21/30
Role-package update obeyed: 29/30
Actual in top three: 25/30
Actual branch named: 27/30
Earliest meaningful error: Turn 22 state/branch-obedience error

## Turn 1

Public state: p1 Snorlax 100% vs p2 Zapdos 100%, no revealed moves, no hazards.
Role/package update: lead RPS package. Our revealed side-known Snorlax is RestTalk attacker, not Lovely Kiss or Curse. Opponent Zapdos is an Electric lead package by strong prior: Thunder/TWave/Roar/RestTalk or coverage is possible but unrevealed.
Route transaction: Zapdos electric lead pressure -> Snorlax bulk and immediate damage -> Zapdos may stay to Thunder/Roar or hand to a Normal resist/Ghost/Rock -> we punish by taking chip now while preserving Cloyster/Skarmory/Raikou for later jobs.
Critical ledger: no sleep/wake; no boosts; no self-KO branch; immediate risk is Thunder paralysis/crit or Zapdos pivot. Earthquake cannot hit Zapdos.
Candidate comparison: Double-Edge hits active and most unknown switches; Earthquake only punishes grounded counter-owner and loses to active; switching to Raikou/Skarmory gives up Snorlax's lead advantage.
Top three:
1. Double-Edge - best route-converting pressure into active Zapdos and neutral branches.
2. Switch Raikou - preserves Snorlax but gives Zapdos the first support/pivot turn.
3. Earthquake - only for a hard grounded switch read; unacceptable as main line into active Zapdos.
Top action: Double-Edge.
Worst branch: Zapdos Thunder paralysis plus later phaze/rest loop, but damage still starts the route.
Public-info tiers: Zapdos set is strong-prior only; no hidden teammates assumed.
Actual: p1 switched Raikou; p2 switched Forretress.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=branch_probability. No severe/hidden/state/mechanics error.

## Turn 2

Public state: p1 Raikou 100% vs p2 Forretress 100%, no moves revealed, no hazards.
Role/package update: Forretress voluntarily entered the Electric. Public package is Spikes/Spin/Toxic/Explosion wall, with Spikes as the immediate route threat and Explosion as a cash-out branch. Our Raikou is RestTalk Electric pressure, no Hidden Power shown in side-known.
Route transaction: Forretress support package -> Raikou can punish before free Spikes -> their next owner is likely Zapdos/Snorlax/Ground after Forry takes damage -> our punish is keep Electric pressure while saving Cloyster for the actual hazard war.
Critical ledger: no sleep/wake; no boosts; Forretress Explosion is possible but not revealed; immediate reset risk is free Spikes if we hand off. No lethal threat this turn unless Explosion crit/damage swing.
Candidate comparison: Thunderbolt pressures active Forretress and denies a totally free support turn; Cloyster handoff enters the hazard mirror but gives Forry tempo; Snorlax handoff preserves Raikou but lets Forry set Spikes/Toxic.
Top three:
1. Thunderbolt - active pressure before support script; chip makes Spikes/Explosion less free.
2. Switch Cloyster - enters hazard mirror and can Spin/Surf/Toxic, but gives Forry first action.
3. Switch Snorlax - preserves Raikou but invites Spikes and does not punish package.
Top action: Thunderbolt.
Worst branch: Forretress Explodes into Raikou; acceptable fallback is that Explosion spends their spinner/spiker but loses our Electric route piece.
Public-info tiers: Forretress support/cash-out is strong prior; no hidden exact set anchored.
Actual: p1 Thunderbolt; p2 switched Snorlax, took 21% then Leftovers to 85%.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 3

Public state: p1 Raikou 100% with Thunderbolt revealed vs p2 Snorlax 85%, no Snorlax moves revealed.
Role/package update: Snorlax entered as the Electric absorber/counter-owner. Its exact package is unrevealed; Curse, Lovely Kiss, coverage, RestTalk, and Self-Destruct are branches, not facts.
Route transaction: Snorlax counter-owner -> our Skarmory phaze/physical wall absorber -> their next owner may be Zapdos/Forretress/electric-punish after Skarmory enters -> our punish is keep Raikou healthy and force Lax to reveal into Whirlwind/Toxic pressure.
Critical ledger: no sleep/wake; no boosts yet; possible Self-Destruct/cash-out but not revealed; immediate risk is Body Slam paralysis, Lovely Kiss, or Curse snowball if Raikou stays. Hidden Fire Blast/Thunder is possible-only/strong-prior lure risk with fallback.
Candidate comparison: Skarmory best answers active Snorlax and future Curse branch; Snorlax mirror preserves Skarmory but invites a slower mirror; Thunderbolt chip does not convert and leaves Raikou exposed.
Top three:
1. Switch Skarmory - preserves Electric and answers the Snorlax package by class.
2. Switch Snorlax - safe mirror, but worse at punishing Curse and gives less route clarity.
3. Thunderbolt - chip only; acceptable only if scouting for immediate Rest, not a real route.
Top action: switch Skarmory.
Worst branch: Snorlax reveals Fire Blast/Thunder/Lovely Kiss into the Skarmory entry; fallback is re-score as lure package, not assume it before reveal.
Public-info tiers: Snorlax as Electric absorber is revealed by entry; exact set is strong-prior/possible-only.
Actual: p1 switched Skarmory; p2 Snorlax used Double-Edge.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 4

Public state: p1 Skarmory 86% vs p2 Snorlax 88%, Snorlax revealed Double-Edge, no hazards.
Role/package update: Snorlax package is at least physical Double-Edge pressure; Skarmory now publicly owns that board unless Lax reveals lure coverage, Curse, Lovely Kiss, or exits to Forretress/Zapdos.
Route transaction: Double-Edge Snorlax -> Skarmory wall/phaze/status owner -> their next owner likely Forretress, Zapdos, or staying Lax -> our punish is Toxic pressure unless the Forretress branch is read hard enough to hand Cloyster in.
Critical ledger: no sleep/wake; no boosts; no self-KO branch; immediate risk is hidden Fire Blast/Thunder or Lovely Kiss, not revealed. Forretress is immune to Toxic and can make Toxic fail.
Candidate comparison: Toxic improves the active Lax and Zapdos/special-owner branches; Cloyster switch punishes Forretress but loses to Zapdos; Whirlwind is low value without boosts or Spikes.
Top three:
1. Toxic - converts Skarmory ownership into a clock on Lax or common non-Steel receivers.
2. Switch Cloyster - branch-punish if Forretress is entering, preserving hazard parity.
3. Whirlwind - acceptable only if expecting Curse/setup; low conversion now.
Top action: Toxic.
Worst branch: Forretress comes in and blanks Toxic, taking the hazard tempo; fallback is immediate Cloyster/Raikou re-score.
Public-info tiers: Forretress branch revealed by roster/entry, but exact switch is a read; hidden Lax lure coverage is possible-only until shown.
Actual: p1 Hidden Power; p2 Snorlax Double-Edge.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=missing_candidate/oracle_style. No severe/hidden/state/mechanics error.

## Turn 5

Public state: p1 Skarmory 73% with Hidden Power revealed vs p2 Snorlax 86% with Double-Edge revealed.
Role/package update: Snorlax has repeated physical pressure into Skarmory; Skarmory owns it but is losing HP while Lax takes recoil. Forretress remains the Steel branch that blanks Toxic.
Route transaction: Double-Edge Snorlax -> Skarmory status/chip wall -> their next owner is stay-Lax, Forretress, or Zapdos -> our punish should either status the non-Steel route or keep chipping without giving Forretress a free immunity turn.
Critical ledger: no sleep/wake; no boosts; no self-KO; immediate risk is another Double-Edge plus crit. Skarmory not in Rest range yet.
Candidate comparison: Toxic creates the strongest route if Lax or Zapdos stays/enters; Hidden Power covers the Forretress-immunity branch weakly while preserving Toxic; Rest is premature.
Top three:
1. Toxic - best converter if the active Lax stays or Zapdos absorbs.
2. Hidden Power - lower-risk chip line if expecting Forretress to blank Toxic.
3. Whirlwind - only if expecting setup or wanting to deny a hidden Curse branch.
Top action: Toxic.
Worst branch: Forretress enters and Toxic fails, giving Spikes tempo; fallback is Cloyster/Raikou re-score.
Public-info tiers: repeated Double-Edge is revealed; Forretress switch is a revealed roster branch but still a read.
Actual: p1 Toxic missed; p2 Snorlax Double-Edge.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 6

Public state: p1 Skarmory 59% with Toxic revealed/missed vs p2 Snorlax 89% with Double-Edge revealed.
Role/package update: Same physical Snorlax into Skarmory, but Toxic is now public and missed. Skarmory still owns, but HP is entering a Rest-clock soon.
Route transaction: Double-Edge Snorlax -> Skarmory status wall -> if Toxic lands, Snorlax must Rest/switch; if Forretress enters, it owns hazard tempo -> our punish is retry Toxic while it still converts the active route.
Critical ledger: no sleep/wake; no boosts; no cash-out; immediate risk is Double-Edge crit plus being forced to Rest next cycle.
Candidate comparison: Toxic still converts active Lax; Rest is too early and gives Lax free turns; Hidden Power chip does not change the route fast enough.
Top three:
1. Toxic - retry the missed converter before Skarmory is forced to Rest.
2. Hidden Power - chip plus recoil, acceptable if expecting a Steel switch.
3. Rest - preserve Skarmory only if expecting high damage/crit concern; premature now.
Top action: Toxic.
Worst branch: Forretress switches into Toxic and starts Spikes; fallback is Cloyster hazard mirror.
Public-info tiers: Forretress branch is a read; Lax physical pressure is revealed.
Actual: p1 switched Tyranitar; p2 Snorlax Double-Edge crit into Tyranitar.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=0; top_rank_failure=route_budget. No severe/hidden/state/mechanics error.

## Turn 7

Public state: p1 Tyranitar 70% vs p2 Snorlax 88%, Snorlax revealed Double-Edge, no hazards.
Role/package update: Tyranitar is now the lower-value Normal resist handoff preserving Skarmory's phaze/status job. Its side-known shown move is Rock Slide only, so do not assume hidden coverage.
Route transaction: Double-Edge Snorlax -> Tyranitar resist/check -> their next owner may be Forretress, Ground/Fighting, or staying Lax -> our punish is Rock Slide chip/flinch pressure while preserving Skarmory and Raikou.
Critical ledger: no sleep/wake; no boosts; no self-KO branch; immediate risk is revealed Double-Edge or unrevealed Earthquake, the latter is a strong-prior branch but not fact.
Candidate comparison: Rock Slide pressures active and at least makes the handoff do work; Skarmory back preserves Tyranitar but repeats the low-HP wall cycle; Snorlax mirror is safer but gives up the point of the TTar handoff.
Top three:
1. Rock Slide - convert the resist handoff into damage/flinch pressure without spending Skarmory.
2. Switch Skarmory - if fearing Earthquake, but Skarmory was just preserved and remains low.
3. Switch Snorlax - broad fallback into unknown Lax package.
Top action: Rock Slide.
Worst branch: Snorlax reveals Earthquake and turns Tyranitar into the wrong absorber; fallback is Skarmory/Snorlax re-score.
Public-info tiers: Double-Edge revealed; Earthquake is strong-prior, not an anchor.
Actual: p1 Rock Slide; p2 Snorlax Double-Edge.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 8

Public state: p1 Tyranitar 58% with Rock Slide revealed vs p2 Snorlax 62% with Double-Edge revealed.
Role/package update: Tyranitar's resist handoff converted: Rock Slide plus recoil put Snorlax in a real damage race. Snorlax still has not revealed Rest, Curse, or Earthquake.
Route transaction: damaged Double-Edge Snorlax -> Tyranitar resist pressure -> their next owner may be stay-Lax/Rest or switch Forretress/Zapdos -> our punish is keep Rock Slide pressure until a reset or bad branch appears.
Critical ledger: no sleep/wake; no boosts; no cash-out; immediate risk is Double-Edge crit or Earthquake reveal. TTar remains healthy enough for another noncrit Double-Edge.
Candidate comparison: Rock Slide can force Lax low or toward Rest; switching wastes the successful handoff; Skarmory/Snorlax fallback only if fearing Earthquake now.
Top three:
1. Rock Slide - route-converting damage while TTar still survives the revealed line.
2. Switch Skarmory - covers Earthquake/physical Lax but spends the preserved phazer.
3. Switch Snorlax - stable fallback into unrevealed Lax reset package.
Top action: Rock Slide.
Worst branch: Earthquake reveal or crit turns TTar into the wrong spend; fallback is Skarmory/Snorlax.
Public-info tiers: Rest/Earthquake remain unrevealed strong priors.
Actual: p1 Rock Slide; p2 Snorlax revealed Earthquake.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 9

Public state: p1 Tyranitar 27% vs p2 Snorlax 40%; Snorlax revealed Double-Edge and Earthquake.
Role/package update: Snorlax package is now DE+EQ physical coverage. Tyranitar's resist job has delivered chip; staying now risks spending it before exact removal. Skarmory is the public EQ-immune/DE-resist owner.
Route transaction: DE/EQ Snorlax -> Skarmory immune/resist owner -> their next owner may be Forretress/Zapdos or Rest Lax -> our punish is preserve low Tyranitar for Zapdos/Rock Slide utility and re-enter the Skarmory wall route.
Critical ledger: no sleep/wake; no boosts; no self-KO. Immediate risk: Earthquake KOs or nearly removes TTar; Rock Slide does not clearly remove Lax before the reply.
Candidate comparison: Skarmory beats both revealed attacks; Rock Slide is a flinch/damage push that likely spends TTar; Snorlax mirror is safe but less precise.
Top three:
1. Switch Skarmory - answers revealed package and preserves TTar.
2. Rock Slide - only if accepting a high-risk trade/flinch line; not clean removal.
3. Switch Snorlax - broad fallback if fearing a coverage lure into Skarmory.
Top action: switch Skarmory.
Worst branch: Snorlax Rests or switches Forretress on Skarmory, resetting the damage race; fallback is Toxic/Cloyster re-score.
Public-info tiers: DE/EQ revealed; Rest/Curse still unrevealed.
Actual: p1 switched Cloyster; p2 Snorlax used Rest.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=1; top_rank_failure=route_budget/branch_probability. No severe/hidden/state/mechanics error.

## Turn 10

Public state: p1 Cloyster 100% vs p2 Snorlax 100% asleep from Rest, Rest sleep actions 0. Opponent has Forretress unrevealed moves and Zapdos.
Role/package update: Rest converted the Snorlax damage race into a sleep-window hazard route. Cloyster is now the spiker/spinner package that can convert the free turn.
Route transaction: sleeping RestLax -> Cloyster hazard converter -> their next owner likely Forretress spinner/spiker or Zapdos pressure -> our punish is set Spikes now, then price Spin/Forretress.
Critical ledger: Rest sleep actions 0; no boosts; no self-KO; immediate risk is unrevealed Sleep Talk fourth move, but not public. Forretress can later contest hazards.
Candidate comparison: Spikes converts the sleep turn into long-term pressure; Surf only chips a sleeping target that just reset; Toxic into a Resting/sleeping Lax is low value.
Top three:
1. Spikes - best route conversion from the Rest window.
2. Surf - chip if fearing immediate Forretress/Spin tempo, but less route value.
3. Toxic - weak into RestLax; only useful if expecting a non-Steel switch.
Top action: Spikes.
Worst branch: Snorlax reveals Sleep Talk or Forretress enters and later spins; fallback is price spinblock absence and use Surf/Toxic/Rapid Spin tempo.
Public-info tiers: Sleep Talk is possible-only until revealed; Forretress as hazard contest is revealed by team entry but exact moves are hidden.
Actual: p1 Spikes; p2 Snorlax Sleep Talk called Rest.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 11

Public state: p1 Cloyster 100%, Spikes on p2 side, vs p2 Snorlax 100% asleep, Rest sleep actions 1, Sleep Talk revealed.
Role/package update: Snorlax is confirmed RestTalk DE/EQ. Cloyster already completed Spikes; now its job is convert hazard pressure without giving Forretress a clean Spin/Spikes reset.
Route transaction: sleeping RestTalk Lax -> Cloyster damage/hazard owner -> their next owner may be Forretress spinner/spiker or Zapdos -> our punish is Surf because it chips Lax and any Forretress branch while preserving Spin.
Critical ledger: Rest sleep actions 1; Sleep Talk can call Double-Edge, Earthquake, or Rest. No boosts/cash-out. Cloyster can absorb the physical rolls.
Candidate comparison: Surf converts damage and hits Forretress branch; switching gives the sleeping Lax or Forry tempo; Toxic cannot status sleeping Lax.
Top three:
1. Surf - active damage plus Forretress branch coverage.
2. Switch Raikou - if expecting Zapdos/Forretress handoff, but risks giving Lax free Sleep Talk.
3. Switch Skarmory - walls DE/EQ but spends the low phazer and does not convert hazard pressure.
Top action: Surf.
Worst branch: Zapdos enters on Surf and threatens Cloyster; fallback is Raikou/Tyranitar handoff.
Public-info tiers: RestTalk package revealed; Forretress/Zapdos handoffs are revealed-team branches, not exact reads.
Actual: p1 switched Skarmory; p2 Sleep Talk called Double-Edge.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/preservation. No severe/hidden/state/mechanics error.

## Turn 12

Public state: p1 Skarmory 46% vs p2 Snorlax 100% asleep, Rest sleep actions 2; helper says it will wake and can act this turn. Spikes on p2 side.
Role/package update: Snorlax is fully revealed RestTalk DE/EQ with no Curse/lure coverage. Skarmory owns the package and can convert with Toxic before Rest becomes necessary.
Route transaction: waking RestTalk Lax -> Skarmory wall/status owner -> their next owner is either poisoned Lax, Forretress, or Zapdos -> our punish is Toxic to put the reset loop on a clock while Spikes taxes exits.
Critical ledger: Lax wakes and can act; no boosts; no cash-out; immediate risk is Double-Edge crit. Earthquake is blanked by Skarmory. Skarmory can survive ordinary DE.
Candidate comparison: Toxic converts the wake turn; Rest preserves Skarmory but gives unpoisoned Lax freedom; Hidden Power is chip only.
Top three:
1. Toxic - best route conversion into revealed RestTalk Lax.
2. Rest - preserve Skarmory if overpricing crit/long-term wall health.
3. Hidden Power - chip plus Spikes pressure, but weaker than poison.
Top action: Toxic.
Worst branch: Forretress enters and blanks Toxic; fallback is Cloyster/Raikou re-score around hazard control.
Public-info tiers: Lax set revealed; Forretress switch still a branch read.
Actual: p2 Snorlax woke, used Double-Edge; p1 Skarmory used Whirlwind and dragged Zapdos.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=0; top_rank_failure=missing_candidate/oracle_style. No severe/hidden/state/mechanics error.

## Turn 13

Public state: p1 Skarmory 34% vs p2 Zapdos 100%, p2 side has Spikes. Zapdos unrevealed.
Role/package update: Whirlwind shifted the board from RestTalk Lax to Electric pressure. Skarmory is now a low phazer/status piece that should not absorb Zapdos unless it converts immediately.
Route transaction: Zapdos Electric pressure -> Raikou RestTalk Electric absorber -> their next owner likely Snorlax/Ground/Forretress -> our punish is preserve low Skarmory and force Zapdos to reveal.
Critical ledger: no sleep/wake active; no boosts; no cash-out. Immediate lethal/paralysis risk from Thunder/Thunder Wave into Skarmory. Spikes do not affect Zapdos.
Candidate comparison: Raikou best absorbs Zapdos and preserves Skarmory; Snorlax is broader but invites pressure; Tyranitar is low and should not be spent into possible coverage.
Top three:
1. Switch Raikou - typed absorber, keeps Skarmory's later phaze/Rest job.
2. Switch Snorlax - broad special sponge, but less precise and may invite status.
3. Toxic - only if making a high-risk stay read; threatens Zapdos but risks Thunder.
Top action: switch Raikou.
Worst branch: Zapdos doubles to Snorlax/Ground on the Raikou handoff; fallback is public-tier class pricing, not hidden exact teammate.
Public-info tiers: Zapdos Electric pressure is strong prior; exact moves hidden.
Actual: p1 switched Raikou; p2 Zapdos used Thunder Wave.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 14

Public state: p1 Raikou 100% paralyzed vs p2 Zapdos 100%, Zapdos revealed Thunder Wave, p2 side Spikes.
Role/package update: Zapdos is confirmed support/status Electric pressure. Raikou absorbed the paralysis and still owns the electric mirror as RestTalk pressure.
Route transaction: Zapdos status/electric package -> Raikou statused absorber -> their next owner likely Snorlax/Forretress/Ground -> our punish is Thunderbolt chip without exposing lower-value pieces.
Critical ledger: no sleep/wake; no boosts; no self-KO; immediate risk is full paralysis or Thunder. Raikou can Rest later.
Candidate comparison: Thunderbolt makes the absorber active and pressures Zapdos or switch branches; switching Snorlax gives up the statused absorber's job; Rest is premature at full HP.
Top three:
1. Thunderbolt - converts the handoff into pressure.
2. Switch Snorlax - broad special sponge if fearing Roar/Thunder loops, but passive.
3. Rest - not needed at full HP.
Top action: Thunderbolt.
Worst branch: Ground-type enters on Thunderbolt; fallback is public-tier re-score because exact Ground is hidden.
Public-info tiers: Ground/Forretress/Snorlax handoff is class-level strong prior, not exact hidden team fact.
Actual: p2 switched Snorlax through Spikes; p1 Thunderbolt.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 15

Public state: p1 paralyzed Raikou 100% vs p2 Snorlax 69%, p2 side Spikes. Snorlax fully revealed RestTalk DE/EQ.
Role/package update: Snorlax again counter-owns Raikou, but Spikes and prior chip make the damage race real. Skarmory is low; Cloyster is healthy and has already delivered Spikes.
Route transaction: RestTalk Lax counter-owner -> Cloyster bulky water/spiker converter -> their next owner likely Forretress/Zapdos or Resting Lax -> our punish is preserve Raikou and low Skarmory while keeping Surf pressure.
Critical ledger: no sleep now; no boosts; no cash-out. Immediate risk is Double-Edge/Earthquake into the handoff. Cloyster survives both better than low Skarmory.
Candidate comparison: Cloyster preserves both Electric and phazer while threatening Surf; Skarmory answers the revealed moves but is low; Snorlax mirror is safe but passive.
Top three:
1. Switch Cloyster - best route-budget handoff into revealed Lax.
2. Switch Skarmory - exact wall, but spends a low phazer.
3. Switch Snorlax - broad fallback but less pressure.
Top action: switch Cloyster.
Worst branch: Snorlax Rests as Cloyster enters, but that still gives Surf/Spin/hazard tempo.
Public-info tiers: Lax set revealed; Forretress/Zapdos followups are revealed roster branches.
Actual: p1 switched Skarmory; p2 Snorlax Double-Edge.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/oracle_style. No severe/hidden/state/mechanics error.

## Turn 16

Public state: p1 Skarmory 22% vs p2 Snorlax 72%, p2 side Spikes. Snorlax revealed RestTalk DE/EQ.
Role/package update: Skarmory has taken the wall job but is now low; its remaining job is phaze/status wall, so preservation is the route action.
Route transaction: RestTalk Lax physical pressure -> Skarmory wall at low HP -> their next owner after our recovery may be Forretress/Zapdos or continuing Lax -> our punish is Rest now, preserving the phazer while Spikes remain up.
Critical ledger: no sleep on Skarmory yet; no boosts; no cash-out. Immediate risk: Double-Edge before negative-priority Whirlwind can nearly remove or crit-kill Skarmory. Rest moves before ordinary DE if Skarmory is faster.
Candidate comparison: Rest preserves the needed route piece; Whirlwind risks taking the hit first due negative priority; Toxic/Hidden Power spend the low wall for little conversion.
Top three:
1. Rest - preserve the phazer/wall job.
2. Whirlwind - if forcing Lax out is worth the pre-phaze hit; risky at 22%.
3. Switch Cloyster - preserves Skarmory but gives up immediate recovery.
Top action: Rest.
Worst branch: Snorlax switches Forretress/Zapdos on Rest and gains tempo; fallback is sleep-turn handoff/absorber mapping.
Public-info tiers: Lax set revealed; switch branch is class read.
Actual: p1 Skarmory used Rest; p2 Snorlax Double-Edge.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 17

Public state: p1 Skarmory 88% asleep from Rest, Rest sleep actions 0, vs p2 Snorlax 76%; p2 side Spikes.
Role/package update: Skarmory successfully preserved its wall job and is now the asleep absorber into a fully revealed DE/EQ RestTalk Snorlax.
Route transaction: RestTalk Lax physical pressure -> sleeping Skarmory absorber -> their next owner may keep attacking or hand to Forretress/Zapdos -> our punish is stay in to soak the low-value sleep turn rather than spend Cloyster.
Critical ledger: Skarmory sleep actions 0; no boosts; no cash-out; immediate risk is Double-Edge chip/crit. No Sleep Talk on Skarmory side-known, so a non-switch action likely fails this turn.
Candidate comparison: staying keeps Cloyster/Raikou/Snorlax healthy while Skarmory absorbs; Cloyster switch creates pressure but spends the healthy spiker; Snorlax mirror is unnecessary.
Top three:
1. Stay in/select Whirlwind - likely asleep, but preserves pieces and absorbs the revealed line.
2. Switch Cloyster - more active but spends healthy hazard piece into DE/EQ.
3. Switch Snorlax - broad fallback, less precise.
Top action: stay in/select Whirlwind.
Worst branch: opponent switches Forretress/Zapdos while Skarmory sleeps, gaining tempo; fallback is wake-count handoff next turn.
Public-info tiers: Lax package revealed; opponent switch is a branch read.
Actual: p2 switched Forretress through Spikes; p1 Skarmory was asleep.
Grade: top_match=1; acceptable_match=1; positive_selection=0; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error. Preservation was correct enough, but the named Forretress hazard branch was not actively punished.

## Turn 18

Public state: p1 Skarmory 94% asleep from Rest, Rest sleep actions 1, vs p2 Forretress 94%; p2 side Spikes.
Role/package update: Forretress is now the revealed hazard-control package by role even though exact moves are hidden. Sleeping Skarmory cannot stop Spin/Spikes this turn; Cloyster is the healthy hazard-control mirror and Surf punisher.
Route transaction: Forretress hazard-control package -> Cloyster hazard mirror/converter -> their next owner is Zapdos/Snorlax or Forretress staying to Spin/Spikes/Explode -> our punish is switch Cloyster now, then Surf or reset hazards instead of donating a second sleep turn.
Critical ledger: Skarmory Rest sleep actions 1, so it is still expected to be asleep this prompted turn; no boosts; no self-KO revealed, but Forretress Explosion is a possible-only high-risk branch; immediate risk is Rapid Spin removing Spikes or Spikes going up on our side.
Candidate comparison: staying in preserves Cloyster but gives Forretress a free hazard-control action; Raikou pressures with Thunderbolt but spends the paralyzed Zapdos absorber and risks an Explosion/status branch; Cloyster keeps the hazard war in the correct package and threatens Surf.
Top three:
1. Switch Cloyster - best route conversion into the Forretress hazard branch while Skarmory sleeps.
2. Stay in/select Whirlwind - preserves pieces, but concedes Spin/Spikes tempo while asleep.
3. Switch Raikou - stronger immediate Forretress pressure, but spends the electric absorber into possible-only Explosion/status.
Top action: switch Cloyster.
Worst branch: Forretress Explodes into Cloyster or doubles Zapdos; fallback is re-score around losing the hazard mirror versus preserving Raikou/Skarmory.
Public-info tiers: Forretress as hazard control is strong-prior by species/role and public entry; exact Spin/Spikes/Explosion moves remain hidden possible-only branches.
Actual: p1 Skarmory was asleep; p2 Forretress used Spikes, setting Spikes on p1's side.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/wake_count. No severe/hidden/state/mechanics error. The top was an active punish of the Forretress branch, but the replay spent the last guaranteed sleep turn on Skarmory instead.

## Turn 19

Public state: p1 Skarmory 99% asleep from Rest, Rest sleep actions 2 and will wake/action this turn, vs p2 Forretress 99%; both sides have Spikes.
Role/package update: Forretress has revealed Spikes and remains the hazard-control/reset package. Skarmory is now awake this turn and can phaze; Cloyster remains the cleaner hazard mirror for later Spin/Surf.
Route transaction: Forretress hazard-control package -> waking Skarmory phaze absorber -> their next owner is a dragged Snorlax/Zapdos/unknown grounded piece -> our punish is Whirlwind to deny Forretress repeated free hazard turns while preserving Cloyster for the follow-up Spin/Surf job.
Critical ledger: Skarmory wakes and can act this turn; no boosts; Forretress Explosion is possible-only and should be priced as high-risk, not assumed; Rapid Spin is also possible-only but role-strong. Whirlwind has negative priority, so Forretress can act first if it has Spin/Explosion.
Candidate comparison: Whirlwind uses the newly awake Skarmory to remove the hazard package and scout the next owner; switching Cloyster starts hazard cleanup but spends it into possible Explosion and still lets Forretress act; Hidden Power is low-value chip unless it is a hidden super-effective type, which is not public.
Top three:
1. Whirlwind - best immediate route reset into Forretress while Skarmory wakes.
2. Switch Cloyster - best longer hazard-control handoff, but risks possible Explosion and gives Forretress the same action.
3. Hidden Power - chip only; acceptable if trying to punish Forretress staying, but weaker than phazing.
Top action: Whirlwind.
Worst branch: Forretress Rapid Spins before the phaze or Explodes into Skarmory; fallback is Cloyster spin/hazard reset after the dragged board.
Public-info tiers: Spikes is revealed; Forretress Spin/Explosion are strong-prior/possible-only role branches, not confirmed moves.
Actual: p2 switched Snorlax through Spikes; p1 Skarmory woke and used Hidden Power.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=branch_probability/precision. No severe/hidden/state/mechanics error. I named the Snorlax next-owner branch but did not rank the direct chip punish high enough.

## Turn 20

Public state: p1 Skarmory 100% vs p2 Snorlax 63%; both sides have Spikes. Snorlax revealed RestTalk Double-Edge/Earthquake.
Role/package update: Snorlax again owns the physical pressure lane, but p2-side Spikes makes phazing a real route converter. Skarmory is airborne, full, and can wall while p1-side Spikes punish grounded switches away from it.
Route transaction: RestTalk Lax physical/reset package -> full Skarmory phaze wall -> their next owner is forced through Spikes unless Zapdos/Forretress timing dodges value -> our punish is Whirlwind to deny a clean Rest reset and convert the existing Spikes layer.
Critical ledger: no active sleep/wake; no boosts; no self-KO branch. Immediate risk is Double-Edge chip or Snorlax using Rest before negative-priority Whirlwind; if Rest happens, phazing the sleeping Lax is still a route gain.
Candidate comparison: Whirlwind converts the hazard layer and punishes Rest/attack by changing owner; Toxic is good if Lax attacks or stays un-Rested but can be blanked by immediate Rest or Forretress; Hidden Power chips the Snorlax branch but does not deny the reset loop.
Top three:
1. Whirlwind - best route conversion with Spikes and a full phazer.
2. Toxic - best if calling attack/no-Rest, weaker into immediate Rest or Forretress.
3. Hidden Power - direct chip into Lax/switch, but lower reset-denial value.
Top action: Whirlwind.
Worst branch: Forretress gets dragged or switches in later and contests hazards; fallback is Cloyster Spin/Surf sequencing.
Public-info tiers: Snorlax set is revealed; Forretress hazard-control follow-up is public role pressure, not exact hidden move knowledge.
Actual: p1 Skarmory used Toxic and missed; p2 Snorlax used Rest.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=candidate_weighting/oracle_style. No severe/hidden/state/mechanics error.

## Turn 21

Public state: p1 Skarmory 100% vs p2 Snorlax 100% asleep from Rest, Rest sleep actions 0; both sides have Spikes. Snorlax is confirmed RestTalk Double-Edge/Earthquake.
Role/package update: Snorlax reset itself but is now in the first sleep turn; Skarmory remains the full phazer that can convert p2-side Spikes by forcing a sleeping Lax out.
Route transaction: sleeping RestTalk Lax reset package -> full Skarmory phaze wall -> their next owner is forced through Spikes unless airborne -> our punish is Whirlwind during the sleep window to turn the Rest reset into entry-tax and matchup reveal.
Critical ledger: Snorlax Rest sleep actions 0; Sleep Talk is revealed and can call Double-Edge, Earthquake, or Rest. No boosts or self-KO branch. Whirlwind moves after Sleep Talk if it attacks, but Skarmory blanks Earthquake and absorbs ordinary Double-Edge.
Candidate comparison: Whirlwind converts the sleep window and denies a clean RestTalk loop; Hidden Power is low chip into a fresh Rest; switching Cloyster starts cleanup but pays Spikes and spends the hazard mirror while Skarmory already owns Lax.
Top three:
1. Whirlwind - strongest conversion of the Rest sleep window with Spikes up.
2. Hidden Power - small chip if avoiding a random phaze, but poor into fresh RestTalk.
3. Switch Cloyster - possible hazard cleanup pivot, but pays Spikes and spends the wrong piece.
Top action: Whirlwind.
Worst branch: Sleep Talk calls Double-Edge crit before phaze or Forretress is dragged to contest hazards; fallback is preserve Skarmory with Rest later and use Cloyster to reset p1-side Spikes.
Public-info tiers: Sleep Talk package revealed; dragged target is unknown random public branch, not chosen hidden knowledge.
Actual: p2 Snorlax Sleep Talk called Earthquake, which failed into Skarmory; p1 Skarmory used Whirlwind and dragged Rhydon through Spikes.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 22

Public state: p1 Skarmory 100% vs p2 Rhydon 94%; both sides have Spikes. Rhydon has no revealed moves.
Role/package update: Rhydon is a public Ground/Rock pressure and Electric-immunity package. Skarmory is the current airborne wall/status owner; Cloyster is the stronger damage counter but would pay Spikes and expose the hazard mirror.
Route transaction: Rhydon Ground/Rock pressure -> Skarmory airborne status wall -> their next owner is Rhydon staying, Forretress absorbing status, Zapdos, or sleeping Snorlax -> our punish is Toxic first, using the airborne owner without paying p1-side Spikes.
Critical ledger: no active sleep on board except benched Snorlax Rest sleep actions 1; no boosts; no self-KO branch revealed. Immediate risk is Rock Slide damage/crit/flinch from Rhydon; Earthquake is blanked by Skarmory.
Candidate comparison: Toxic converts the Rhydon/Zapdos/Snorlax branch into a clock while preserving Cloyster; switching Cloyster threatens Surf and future Spin but pays Spikes and invites Zapdos/Forretress; Whirlwind maintains Spikes churn but may donate a better owner without statusing Rhydon.
Top three:
1. Toxic - best route conversion while Skarmory already owns the board.
2. Switch Cloyster - stronger immediate Rhydon damage and future Spin, but spends hazard-control tempo.
3. Whirlwind - acceptable Spikes churn, weaker than poisoning the new Ground.
Top action: Toxic.
Worst branch: Forretress switches into Toxic for free and continues hazard control; fallback is Cloyster Surf/Rapid Spin sequencing.
Public-info tiers: Rhydon Ground/Rock role is public species pressure; exact moves remain hidden, with Rock Slide/Earthquake strong-prior and not a revealed set.
Actual: p2 switched sleeping Snorlax through Spikes; p1 Skarmory used Whirlwind and dragged Zapdos.
Grade: top_match=0; acceptable_match=0; positive_selection=0; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=0; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=status_branch_obedience. State error=1 because I named sleeping Snorlax as a branch but ranked Toxic first, which cannot convert an already-statused Snorlax. No severe/hidden/mechanics error.

## Turn 23

Public state: p1 Skarmory 100% vs p2 Zapdos 100%; both sides have Spikes. Zapdos has revealed Thunder Wave; p2 Snorlax is asleep on the bench at Rest sleep actions 1.
Role/package update: Whirlwind successfully pushed the sleeping Snorlax out but dragged the Electric/status package. Skarmory should now hand off to the statused Electric absorber rather than donate HP or paralysis value.
Route transaction: Zapdos Electric/status pressure -> paralyzed Raikou absorber -> their next owner is Snorlax/Rhydon/Forretress -> our punish is accept Spikes on Raikou and answer with Thunderbolt/re-score instead of spending Skarmory into Thunder.
Critical ledger: benched Snorlax sleep actions 1; no boosts; no self-KO branch. Immediate risk is Thunder/Thunder Wave into Skarmory; Raikou is already paralyzed, so Thunder Wave is lower value into the handoff.
Candidate comparison: switching Raikou preserves Skarmory and uses the correct absorber; Snorlax is a broader special sponge but pays Spikes and is needed for the mirror; Toxic from Skarmory is a high-risk stay that loses hard to Thunder.
Top three:
1. Switch Raikou - correct Zapdos absorber despite p1-side Spikes.
2. Switch Snorlax - acceptable broad special sponge, less precise and more route cost.
3. Toxic - high-risk stay punish if expecting Zapdos not to attack, but not the default.
Top action: switch Raikou.
Worst branch: Rhydon enters on the Raikou handoff or Zapdos doubles to Snorlax; fallback is immediate board re-score, not assuming hidden moves.
Public-info tiers: Zapdos Electric pressure and Thunder Wave are revealed/strong-prior; Thunder/Rhydon branch are public species/team-pressure branches, not confirmed exact moves.
Actual: p1 switched Raikou through Spikes; p2 Zapdos used Thunderbolt.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 24

Public state: p1 Raikou 76% paralyzed vs p2 Zapdos 100%; both sides have Spikes. Zapdos revealed Thunder Wave and Thunderbolt; p2 has Rhydon, Forretress, and sleeping Snorlax in reserve.
Role/package update: Raikou is now the active Electric absorber and pressure piece. Rhydon is the public counter-owner branch, but it is not active and should not anchor a blind switch.
Route transaction: Zapdos Electric/status package -> Raikou mirror absorber/converter -> their next owner is Rhydon/Snorlax/Forretress -> our punish is Thunderbolt now, forcing Zapdos or a grounded receiver to accept damage/Spikes tempo.
Critical ledger: benched Snorlax Rest sleep actions 1; no boosts; no self-KO branch. Immediate risk is full paralysis, Zapdos Thunderbolt chip, or Rhydon absorbing Thunderbolt on a switch.
Candidate comparison: Thunderbolt makes the correct absorber active and pressures Zapdos; Rest at 76 preserves Raikou but donates momentum while not yet necessary; switching predicts Rhydon/Snorlax too hard and pays more Spikes elsewhere.
Top three:
1. Thunderbolt - best active pressure from the absorber.
2. Rest - acceptable preservation if overpricing paralysis/chip, but passive now.
3. Switch Snorlax - broad fallback if reading Rhydon, but not enough public pressure to anchor.
Top action: Thunderbolt.
Worst branch: Rhydon switches into Thunderbolt for free; fallback is immediate Cloyster/Skarmory re-score after the revealed counter-owner.
Public-info tiers: Rhydon is a revealed team counter-owner, but exact switch timing is a branch read; do not anchor on it over the active Zapdos.
Actual: p2 switched sleeping Snorlax through Spikes; p1 Raikou used Rest.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/preservation. No severe/hidden/state/mechanics error.

## Turn 25

Public state: p1 Raikou 100% asleep from Rest, Rest sleep actions 0, vs p2 Snorlax 82% asleep from Rest, Rest sleep actions 1; both sides have Spikes. Snorlax is confirmed RestTalk Double-Edge/Earthquake.
Role/package update: Raikou has preserved itself but is the wrong sleeping absorber into a Lax that can Sleep Talk Earthquake. Skarmory is healthy, airborne, and owns the revealed Snorlax package without paying p1-side Spikes.
Route transaction: sleeping RestTalk Lax physical package -> Skarmory airborne wall/phazer -> their next owner is Sleep Talk output, Rest continuation, or a switch to Zapdos/Forretress/Rhydon -> our punish is switch Skarmory now, preserving Raikou's Zapdos job and setting up the phaze/status route.
Critical ledger: Raikou Rest sleep actions 0; Snorlax Rest sleep actions 1. Snorlax Sleep Talk can call Double-Edge, Earthquake, or Rest; Earthquake is the key immediate risk if Raikou stays. No boosts or cash-out branch.
Candidate comparison: switching Skarmory is free of Spikes and covers every revealed Lax attack; Sleep Talk with Raikou burns a sleep turn but risks Earthquake damage and weak random output; Cloyster pays Spikes and spends the hazard mirror unnecessarily.
Top three:
1. Switch Skarmory - correct package handoff and preserves sleeping Raikou.
2. Sleep Talk with Raikou - active but risky into Sleep Talk Earthquake.
3. Switch Cloyster - acceptable physical sponge, but pays Spikes and gives up hazard-control budget.
Top action: switch Skarmory.
Worst branch: Snorlax switches Zapdos as Skarmory enters; fallback is Raikou/Snorlax handoff once board is public.
Public-info tiers: Snorlax RestTalk/EQ is revealed; Zapdos/Forretress/Rhydon switches are revealed roster branches, not hidden-move reads.
Actual: p1 switched Skarmory; p2 switched Zapdos.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error. The Lax handoff was correct into the active package, but it did not punish the named Zapdos double branch.

## Turn 26

Public state: p1 Skarmory 100% vs p2 Zapdos 100%; both sides have Spikes. Zapdos revealed Thunder Wave and Thunderbolt. p1 Raikou is asleep from Rest at sleep actions 0.
Role/package update: The Zapdos double forced the Electric/status package back in while Raikou is not immediately ready. Snorlax is the healthy broad special sponge; Raikou remains the sleeping long-term Zapdos answer.
Route transaction: Zapdos Electric/status pressure -> Snorlax special sponge -> their next owner is Rhydon/Forretress/Snorlax or Zapdos staying -> our punish is switch Snorlax to absorb the hit without spending sleeping Raikou or low Tyranitar.
Critical ledger: p1 Raikou Rest sleep actions 0; p2 Snorlax Rest sleep actions 1 on the bench. No boosts or self-KO branch. Immediate risk is Thunderbolt/Thunder Wave into Skarmory; Snorlax pays Spikes but takes the Electric hit best while Raikou sleeps.
Candidate comparison: Snorlax gives the stable absorber without requiring asleep Raikou to take immediate damage; switching Raikou is acceptable if intentionally burning sleep turns, but it pays Spikes and risks taking Thunderbolt while asleep; Toxic from Skarmory is a high-risk stay.
Top three:
1. Switch Snorlax - best current absorber while Raikou is asleep.
2. Switch Raikou - acceptable long-term absorber, but spends the sleeping piece immediately.
3. Toxic - high-risk Zapdos punish; bad into Thunderbolt.
Top action: switch Snorlax.
Worst branch: Zapdos doubles Rhydon/Forretress as Snorlax enters; fallback is re-score from the new owner without assuming hidden coverage.
Public-info tiers: Zapdos Thunderbolt/Thunder Wave are revealed; Rhydon/Forretress doubles are public roster branches.
Actual: p1 switched Snorlax through Spikes; p2 Zapdos used Thunderbolt.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 27

Public state: p1 Snorlax 69% vs p2 Zapdos 100%; both sides have Spikes. Zapdos revealed Thunder Wave and Thunderbolt; p2 has Rhydon, Forretress, and sleeping Snorlax available.
Role/package update: Snorlax has taken the special sponge job and must now convert the forced Zapdos contact before it is worn down by Spikes plus Thunderbolt. Rhydon is the counter-owner branch but Zapdos remains active.
Route transaction: Zapdos Electric pressure -> Snorlax special sponge/converter -> their next owner is Zapdos staying, Rhydon/Forretress entering, or sleeping Snorlax -> our punish is Double-Edge to hit the active Zapdos and grounded receivers without overcalling Rhydon.
Critical ledger: p1 Raikou Rest sleep actions 0 on bench; p2 Snorlax Rest sleep actions 1 on bench. No boosts or cash-out branch. Immediate risk is another Thunderbolt, Thunder Wave, or a Rhydon pivot.
Candidate comparison: Double-Edge converts the absorber into damage against Zapdos and most receivers; Earthquake is a Rhydon/Forretress read that fails into Zapdos; Rest at 69 preserves but gives too much tempo while not yet forced.
Top three:
1. Double-Edge - best broad conversion from Snorlax's sponge position.
2. Rest - acceptable if valuing long-term Snorlax HP, but passive now.
3. Earthquake - branch punish for Rhydon/Forretress, too narrow into active Zapdos.
Top action: Double-Edge.
Worst branch: Rhydon enters and takes modest damage while threatening back; fallback is Skarmory/Cloyster re-score.
Public-info tiers: Rhydon pivot is revealed roster pressure, but exact switch timing remains a branch read.
Actual: p1 switched sleeping Raikou through Spikes; p2 Zapdos revealed Whirlwind and dragged Heracross through Spikes.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=0; actual_branch_named=0; top_rank_failure=hidden_package_reveal. No severe/hidden/state/mechanics error; I did not anchor on hidden Whirlwind before it was public.

## Turn 28

Public state: p1 Heracross 94% vs p2 Zapdos 100%; both sides have Spikes. Zapdos has revealed Thunder Wave, Thunderbolt, and Whirlwind. p1 Raikou is asleep at Rest sleep actions 0.
Role/package update: Zapdos is now confirmed Electric/status/phaze pressure. Because Whirlwind is negative priority, an active Heracross can punish a repeat phaze or switch with Megahorn before being forced out.
Route transaction: Zapdos Electric/phaze package -> Heracross active branch-punisher -> their next owner is Zapdos staying/phazing, sleeping Snorlax, Rhydon, or Forretress -> our punish is Megahorn now instead of paying Spikes again on a predictable switch.
Critical ledger: p1 Raikou Rest sleep actions 0; p2 Snorlax Rest sleep actions 1. No boosts or self-KO branch. Immediate risk is Thunderbolt damage, Thunder Wave status, Megahorn miss, or another Whirlwind after we attack.
Candidate comparison: Megahorn attacks before Whirlwind and punishes Snorlax/Rhydon/Forretress switch branches; switching Raikou is type-correct but repeats the Spikes plus Whirlwind vulnerability while asleep; switching Snorlax is broad but too low after Spikes plus Thunderbolt.
Top three:
1. Megahorn - best branch punish into revealed Whirlwind/switch pressure.
2. Switch Raikou - correct Electric absorber, but asleep and phaze-vulnerable.
3. Switch Snorlax - broad sponge, but HP budget is poor after Spikes.
Top action: Megahorn.
Worst branch: Zapdos Thunder Waves or Thunderbolts and Megahorn misses; fallback is RestTalk Heracross if statused or Raikou/Snorlax re-score if damaged.
Public-info tiers: Zapdos Whirlwind is revealed; no hidden coverage is assumed. Snorlax/Rhydon/Forretress are public roster branches.
Actual: p1 switched sleeping Raikou through Spikes; p2 Zapdos used Thunderbolt.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/type_owner. No severe/hidden/state/mechanics error.

## Turn 29

Public state: p1 Raikou 66% asleep from Rest, Rest sleep actions 0, vs p2 Zapdos 100%; both sides have Spikes. Zapdos revealed Thunder Wave, Thunderbolt, and Whirlwind.
Role/package update: The replay spent Raikou as the Zapdos owner; now the job is to make that spent sleep turn active rather than switch again through Spikes. Sleep Talk is the side-known RestTalk route button.
Route transaction: Zapdos Electric/phaze pressure -> sleeping Raikou RestTalk absorber -> their next owner is Zapdos staying, Rhydon immune pivot, Snorlax, or Forretress -> our punish is Sleep Talk to threaten Thunderbolt while burning the sleep turn.
Critical ledger: Raikou Rest sleep actions 0; p2 Snorlax Rest sleep actions 1 on the bench. No boosts or self-KO branch. Immediate risk is Thunderbolt chip, Whirlwind phaze after our action, full paralysis no longer relevant while asleep, or Sleep Talk calling Rest/non-damage.
Candidate comparison: Sleep Talk converts the chosen absorber into pressure; switching wastes the Spikes payment and may get phazed again; hard Snorlax/Heracross handoffs are lower budget while Zapdos is still active.
Top three:
1. Sleep Talk - best active use of the sleeping Zapdos owner.
2. Switch Snorlax - broad fallback if refusing Raikou damage, but pays Spikes and is already chipped.
3. Switch Heracross - branch-punish into Whirlwind/switch, but worse into Thunderbolt.
Top action: Sleep Talk.
Worst branch: Sleep Talk rolls Rest or Zapdos Whirlwinds after low-value output; fallback is re-score from the dragged board.
Public-info tiers: Raikou Sleep Talk is side-known own information; Rhydon immunity and Zapdos phaze are public/revealed branches.
Actual: p1 Raikou used Sleep Talk, called Thunderbolt into Zapdos, then p2 Zapdos used Whirlwind and dragged Snorlax through Spikes.
Grade: top_match=1; acceptable_match=1; positive_selection=1; route_converting_move_chosen=1; branch_punish_chosen=1; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=none. No severe/hidden/state/mechanics error.

## Turn 30

Public state: p1 Snorlax 63% vs p2 Zapdos 70%; both sides have Spikes. Zapdos has revealed Thunder Wave, Thunderbolt, and Whirlwind. p1 Raikou is asleep at Rest sleep actions 1.
Role/package update: Zapdos is now chipped and repeatedly using phaze to force grounded Spikes tax. Snorlax is the active special sponge and must punish Zapdos before being cycled out again.
Route transaction: Zapdos Electric/phaze package -> Snorlax damage converter -> their next owner is Zapdos staying/phazing, Rhydon/Forretress pivoting, or sleeping Snorlax -> our punish is Double-Edge for broad immediate damage before any Whirlwind.
Critical ledger: p1 Raikou Rest sleep actions 1; p2 Snorlax Rest sleep actions 1 on bench. No boosts or cash-out branch. Immediate risk is Thunderbolt chip, Thunder Wave, or Whirlwind after our priority-0 move.
Candidate comparison: Double-Edge attacks before Whirlwind and pressures Zapdos plus most receivers; Rest preserves Snorlax but may donate a phaze/switch tempo; Earthquake is too narrow because Zapdos is active and immune.
Top three:
1. Double-Edge - best broad punish into active Zapdos and phaze.
2. Rest - acceptable if preserving Snorlax before another Thunderbolt, but passive.
3. Earthquake - branch punish for Rhydon/Forretress only; bad into active Zapdos.
Top action: Double-Edge.
Worst branch: Rhydon enters on Double-Edge and starts Rock/Ground pressure; fallback is Skarmory/Cloyster re-score.
Public-info tiers: Zapdos Whirlwind is revealed; Rhydon/Forretress are public branch owners, not exact reads.
Actual: p2 switched Rhydon through Spikes; p1 Snorlax used Rest.
Grade: top_match=0; acceptable_match=1; positive_selection=1; route_converting_move_chosen=0; branch_punish_chosen=0; role_package_update_obeyed=1; actual_in_top_three=1; actual_branch_named=1; top_rank_failure=route_budget/preservation. No severe/hidden/state/mechanics error.

## Stop Note

Stopped after 30 scored side decisions before freezing Turn 31 because the
same `route_budget/preservation` family repeated enough to trigger the
plateau-loop stop condition. Continuing the replay would add volume before the
ranking problem is repaired.

## Score Summary

- Decisions: 30.
- Top-match: 15/30.
- Acceptable-match: 29/30.
- Positive-selection: 28/30.
- Route-converting move chosen: 22/30.
- Branch-punish chosen: 21/30.
- Role-package update obeyed: 29/30.
- Actual in frozen top three: 25/30.
- Actual branch named before reveal: 27/30.
- Severe blunders: 0.
- Hidden-info errors: 0.
- State errors: 1, on Turn 22.
- Mechanics errors: 0.

Interpretation: simplified docs and the role/package ledger helped keep
candidate generation broad and severe/hidden/mechanics gates clean, but did
not improve exact top ranking. The main wall remains route-budget ordering:
when pressure is already created by Spikes, Rest, phaze, or a correct owner
handoff, I still over-rank active chip/status/branch punish over the lower-cost
preservation or sleep-window move too often.
