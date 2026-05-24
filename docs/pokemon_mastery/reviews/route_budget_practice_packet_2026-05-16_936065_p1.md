# Route-Budget Practice Packet - 2026-05-16 - smogtours-gen2ou-936065 p1

Source: `docs/pokemon_mastery/workspace/raw/smogtours-gen2ou-936065.log`
Mode: `semi_blind_practice`, reconstructed side-known for `p1 / s.islands`.
Contamination control: before freezing this packet, only the new live module files and the p1 side-known prompt for this replay were loaded. Two other raw logs were inspected for roster suitability and are not counted. This packet is practice/method evidence, not clean validation.

## Score Summary

Decisions: 25
Top-match: 13/25
Acceptable-match: 22/25
Actual in top three: 21/25
Promoted correctly or acceptable co-top when actual was in top three: 18/21
Severe blunders: 0
State errors: 0
Hidden-info errors: 0
Mechanics errors: 0
Top-one discrimination field present: 25/25
Rejected safe/default field present: 25/25
Actually rejected safe/default line: 21/25
Positive-selection: 21/25
Route-converting move chosen: 21/25
Branch-punish chosen on branch-relevant turns: 12/17

Primary top-rank failure tags on 12 misses:
`route_budget` 3, `resource_identity` 3, `missing_candidate` 3, `oracle_style` 1, `branch_probability` 1, `branch_punish` 1.

## Turn 1

Top move: Raikou Thunder
Confidence: medium-low
Route transaction: Smeargle lead sleep/Spikes -> Raikou immediate damage/paralysis converter -> sleep/pivot owner -> RestTalk absorbers and Ttar/Skarm punish.
Top three: 1. Thunder 2. switch Snorlax 3. Hidden Power
#1 over #2 because: Thunder pressures Smeargle before it stacks utility; switching concedes the first route action.
#2 becomes #1 if: preserving Raikou as the unique electric route piece outweighs the lead-tempo damage.
Rejected safe/default line: switch straight to a sleep absorber; it gives free Spikes or pass setup.
Positive-selection check: convert/deny lead setup.
Opponent incentive: Spikes or sleep.
Critical resource: Raikou health and sleep budget.
Worst plausible branch: Thunder misses and Smeargle gets both tempo and sleep pressure.
If wrong: accept Raikou sleep/chip and stabilize with RestTalk/Skarm.
Info that changes answer: full Smeargle route or damage threshold showing Thunder cannot force.
Actual: Raikou Hidden Power; Smeargle Spikes.
Score: top_match 0; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 0; top_rank_failure `oracle_style`.

## Turn 2

Top move: switch Snorlax
Confidence: medium
Route transaction: low Smeargle sleep package -> Snorlax sleep absorber -> opponent Snorlax/electric owner -> Skarm/Ttar/Raikou punish.
Top three: 1. switch Snorlax 2. Thunder 3. Hidden Power
#1 over #2 because: I overvalued clean sleep absorption and Thunder miss risk.
#2 becomes #1 if: Thunder removes Smeargle before sleep and the hit rate is worth the route.
Rejected safe/default line: repeat Hidden Power chip; it leaves Smeargle alive.
Positive-selection check: intended preserve/absorb, but too passive.
Opponent incentive: Spore after Spikes.
Critical resource: sleep absorber identity.
Worst plausible branch: Smeargle survives and sleeps the wrong piece.
If wrong: kill Smeargle next and repair sleep resource.
Info that changes answer: Thunder damage threshold from 71%.
Actual: Raikou Thunder KO.
Score: top_match 0; acceptable_match 0; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 0; positive_selection 0; route_converting_move_chosen 0; branch_punish_chosen 0; top_rank_failure `route_budget`.

## Turn 3

Top move: switch Skarmory
Confidence: medium
Route transaction: Snorlax normal/sleep package -> Skarmory absorber -> Fire/electric/water owner -> Ttar/Raikou/Snorlax punish.
Top three: 1. switch Skarmory 2. switch Tyranitar 3. Thunder
#1 over #2 because: Skarmory is the normal absorber and Tyranitar risks Earthquake.
#2 becomes #1 if: phaze/rock pressure matters more than sleep absorption.
Rejected safe/default line: Thunder chip; I thought it repeated damage without owning the Snorlax route.
Positive-selection check: none; this was a preservation default.
Opponent incentive: Curse, attack, or sleep.
Critical resource: correct sleep absorber and Skarmory's later Marowak job.
Worst plausible branch: Lovely Kiss hits the unique physical wall.
If wrong: Raikou should have been the RestTalk sleep absorber while damaging.
Info that changes answer: Snorlax sleep move revealed or Raikou's RestTalk role prioritized.
Actual: Raikou Thunder; Snorlax Lovely Kiss.
Score: top_match 0; acceptable_match 0; actual_in_top_three 1; actual_branch_named 0; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 0; positive_selection 0; route_converting_move_chosen 0; branch_punish_chosen 0; top_rank_failure `resource_identity`.

## Turn 4

Top move: Raikou Sleep Talk
Confidence: medium
Route transaction: Lovely Kiss Snorlax pressure -> asleep RestTalk Raikou converter -> electric/special pivot -> Ttar or Snorlax punish.
Top three: 1. Sleep Talk 2. switch Skarmory 3. switch Tyranitar
#1 over #2 because: Raikou is already the sleep absorber and can still create damage.
#2 becomes #1 if: Snorlax is about to convert with Curse/Earthquake and Raikou must be preserved.
Rejected safe/default line: immediate Skarmory switch; it spends the physical wall under Spikes.
Positive-selection check: convert from the sleeping route piece.
Opponent incentive: attack, Curse, or pivot.
Critical resource: Raikou sleep counter and Ttar's anti-electric role.
Worst plausible branch: hidden electric pivot catches Sleep Talk.
If wrong: move Ttar in after the pivot.
Info that changes answer: opponent electric pivot strongly signaled.
Actual: p1 switched Tyranitar; p2 switched Jolteon.
Score: top_match 0; acceptable_match 1; actual_in_top_three 1; actual_branch_named 0; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 0; top_rank_failure `branch_probability`.

## Turn 5

Top move: Tyranitar Roar
Confidence: medium
Route transaction: Jolteon pass package -> Tyranitar phaze denial -> pass receiver -> forced random owner.
Top three: 1. Roar 2. Rock Slide 3. switch Snorlax
#1 over #2 because: Baton Pass is the route threat; Roar denies the package rather than hitting only the active.
#2 becomes #1 if: Jolteon is only dry-passing or the receiver takes decisive Rock Slide damage.
Rejected safe/default line: switch out; it gives the pass chain a free owner.
Positive-selection check: pass denial.
Opponent incentive: Baton Pass to a water/ground owner.
Critical resource: Tyranitar health for future Roars.
Worst plausible branch: HP Water or pass to Vaporeon.
If wrong: use Skarm/Snorlax to absorb the receiver.
Info that changes answer: no boost/pass threat from Jolteon.
Actual: Jolteon Baton Pass to Vaporeon; Tyranitar Rock Slide.
Score: top_match 0; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure `branch_punish`.

## Turn 6

Top move: switch Snorlax
Confidence: medium-low
Route transaction: Vaporeon water/growth package -> Snorlax special absorber -> Jolteon/Vaporeon owner -> Ttar/Raikou punish.
Top three: 1. switch Snorlax 2. switch Raikou 3. Roar
#1 over #2 because: Raikou was asleep and Snorlax could absorb the water route immediately.
#2 becomes #1 if: Growth/Baton Pass is the main route and electric pressure is required now.
Rejected safe/default line: stay and Roar with Tyranitar; too slow into Surf.
Positive-selection check: preserve Ttar, but wrong route owner.
Opponent incentive: Surf, Growth, or switch Jolteon.
Critical resource: Starmie spinner was underpriced.
Worst plausible branch: opponent doubles Jolteon.
If wrong: pivot to the electric/ground answer and find a spin window.
Info that changes answer: prioritizing the active spin window over water absorption.
Actual: p1 switched Starmie; p2 switched Jolteon.
Score: top_match 0; acceptable_match 1; actual_in_top_three 0; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 0; positive_selection 0; route_converting_move_chosen 0; branch_punish_chosen 0; top_rank_failure `missing_candidate`.

## Turn 7

Top move: switch Tyranitar
Confidence: medium
Route transaction: Jolteon electric/pass package -> Tyranitar blocker/phazer -> pass receiver -> Roar/Rock Slide punish.
Top three: 1. switch Tyranitar 2. Rapid Spin 3. switch Snorlax
#1 over #2 because: Jolteon can immediately Thunder Starmie, and Ttar owns that branch.
#2 becomes #1 if: Baton Pass is more likely than Thunder and Spikes removal is the key route conversion.
Rejected safe/default line: stay Recover; it loses tempo.
Positive-selection check: branch-punish electric.
Opponent incentive: Thunder or pass setup.
Critical resource: Starmie spinner health.
Worst plausible branch: Agility before Baton Pass.
If wrong: use Snorlax/Ttar to absorb the passed owner.
Info that changes answer: stronger read on Agility over Thunder.
Actual: p1 switched Snorlax; Jolteon Agility.
Score: top_match 0; acceptable_match 1; actual_in_top_three 1; actual_branch_named 0; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure `resource_identity`.

## Turn 8

Top move: Snorlax Double-Edge
Confidence: medium
Route transaction: +2 Jolteon pass package -> Snorlax broad absorber/converter -> pass receiver -> Double-Edge chip or later Skarm/Ttar punish.
Top three: 1. Double-Edge 2. Earthquake 3. switch Skarmory
#1 over #2 because: Double-Edge hits the likely receiver harder than Earthquake into active-only Jolteon.
#2 becomes #1 if: Jolteon stays rather than passing.
Rejected safe/default line: switch out; it lets the pass complete without damage.
Positive-selection check: branch-punish the receiver.
Opponent incentive: Baton Pass to a ground/water owner.
Critical resource: Snorlax bulk and Skarmory's Marowak job.
Worst plausible branch: pass to Marowak.
If wrong: use Skarmory on Marowak and poison it.
Info that changes answer: hard read that Ttar can phaze the receiver safely.
Actual: p1 switched Tyranitar; Jolteon Baton Pass to Marowak.
Score: top_match 0; acceptable_match 1; actual_in_top_three 0; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure `missing_candidate`.

## Turn 9

Top move: switch Skarmory
Confidence: high
Route transaction: passed Marowak sweep package -> Skarmory ground/physical absorber -> Fire/electric owner -> Ttar/Raikou/Snorlax punish.
Top three: 1. switch Skarmory 2. Roar 3. Rock Slide
#1 over #2 because: Tyranitar may die before negative-priority Roar; Skarmory is the real route owner.
#2 becomes #1 if: Marowak is certain to Swords Dance and Ttar survives.
Rejected safe/default line: Rock Slide chip; it does not deny +2 Marowak.
Positive-selection check: deny passed sweeper.
Opponent incentive: Earthquake or Swords Dance.
Critical resource: Skarmory as unique Marowak wall.
Worst plausible branch: Fire Blast into Skarmory.
If wrong: poison/rest loop with Skarmory if it survives.
Info that changes answer: revealed Fire Blast.
Actual: p1 switched Skarmory; Marowak Swords Dance.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 10

Top move: Skarmory Toxic
Confidence: high
Route transaction: boosted Marowak -> Skarmory wall plus poison clock -> electric/water owner -> Ttar/Raikou punish.
Top three: 1. Toxic 2. Curse 3. Rest
#1 over #2 because: Toxic creates the finite clock; Curse only sits in front of crit/fire risk.
#2 becomes #1 if: damage requires immediate defense boosting to survive.
Rejected safe/default line: Rest at full health; no progress.
Positive-selection check: convert with poison clock.
Opponent incentive: Rock Slide or Fire Blast.
Critical resource: Skarmory HP and Toxic accuracy.
Worst plausible branch: Rock Slide crit or Fire Blast.
If wrong: Rest next if Skarmory survives.
Info that changes answer: damage calc showing Rock Slide always 2HKOs without Curse.
Actual: Marowak Rock Slide; Skarmory Toxic.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 11

Top move: Skarmory Rest
Confidence: high
Route transaction: poisoned boosted Marowak -> Skarmory Rest preserves wall -> Marowak poison clock -> Sleep Talk/Curse wall route.
Top three: 1. Rest 2. switch Snorlax 3. Curse
#1 over #2 because: Skarmory is the unique absorber and Rest converts the poison clock; a sack loses the route.
#2 becomes #1 if: Rock Slide always KOs before Rest.
Rejected safe/default line: Curse or Toxic again; it does not preserve the route piece.
Positive-selection check: preserve correct resource.
Opponent incentive: Rock Slide.
Critical resource: Skarmory HP, poison clock, crit risk.
Worst plausible branch: Rock Slide KO or crit.
If wrong: sacrifice and revenge with poison damage.
Info that changes answer: exact Rock Slide damage showing no survival.
Actual: Marowak Rock Slide; Skarmory Rest.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 12

Top move: Skarmory Sleep Talk
Confidence: high
Route transaction: poisoned boosted Marowak -> sleeping Skarmory absorber -> Marowak poison clock -> Sleep Talk Curse/Toxic pressure.
Top three: 1. Sleep Talk 2. switch Snorlax 3. switch Tyranitar
#1 over #2 because: staying preserves the only wall while poison works.
#2 becomes #1 if: crit odds or fire coverage makes Skarmory unusable.
Rejected safe/default line: switch out; it sacrifices the route.
Positive-selection check: preserve/convert.
Opponent incentive: Rock Slide.
Critical resource: Rest sleep action 0 and poison ramp.
Worst plausible branch: Rock Slide crit.
If wrong: continue with Skarmory if alive.
Info that changes answer: Fire Blast reveal.
Actual: Marowak Rock Slide missed; Skarmory Sleep Talk -> Curse.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 13

Top move: Skarmory Sleep Talk
Confidence: high
Route transaction: poisoned Marowak or Jolteon reset branch -> sleeping boosted Skarmory -> switch owner -> Toxic/Curse pressure.
Top three: 1. Sleep Talk 2. switch Tyranitar 3. switch Snorlax
#1 over #2 because: Skarmory still owns Marowak and can hit the switch with Sleep Talk status/boost.
#2 becomes #1 if: Jolteon entry is certain and Skarmory must be saved.
Rejected safe/default line: switch immediately; it lets the opponent choose the pass owner.
Positive-selection check: preserve while pressuring branch.
Opponent incentive: switch Jolteon or keep pressing Rock Slide.
Critical resource: Rest sleep action 1 and Marowak poison.
Worst plausible branch: Jolteon enters and absorbs a useless Sleep Talk roll.
If wrong: pivot Tyranitar next.
Info that changes answer: confirmed electric switch.
Actual: p2 switched Jolteon; Skarmory Sleep Talk -> Toxic.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 14

Top move: switch Tyranitar
Confidence: high
Route transaction: Jolteon pass/electric package -> Tyranitar phazer/check -> Vaporeon/Marowak receiver -> Roar/Rock Slide plus Skarm/Snorlax punish.
Top three: 1. switch Tyranitar 2. switch Snorlax 3. stay Skarmory
#1 over #2 because: Tyranitar directly denies the Baton Pass route; Snorlax only absorbs.
#2 becomes #1 if: HP Water or direct Thunder damage makes Ttar too expensive.
Rejected safe/default line: stay with Skarmory; it loses the electric/pass exchange and risks the Marowak wall.
Positive-selection check: branch-punish and preserve Skarmory.
Opponent incentive: Agility, Thunder, or Baton Pass.
Critical resource: Skarmory's wall job and Ttar's phaze job.
Worst plausible branch: HP Water.
If wrong: Snorlax absorbs and Skarmory handles Marowak.
Info that changes answer: Jolteon coverage reveal.
Actual: p1 switched Tyranitar; Jolteon Agility.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 15

Top move: Tyranitar Roar
Confidence: high
Route transaction: +2 Jolteon pass package -> Tyranitar Roar denial -> receiver -> dragged owner with no boost.
Top three: 1. Roar 2. Rock Slide 3. switch Snorlax
#1 over #2 because: the boosted pass converts now; Roar denies the route, while Rock Slide may leave a boosted owner.
#2 becomes #1 if: Jolteon stays or the receiver is already in decisive chip range.
Rejected safe/default line: switch out; it gives a free boost pass.
Positive-selection check: pass denial.
Opponent incentive: Baton Pass to Vaporeon/Marowak.
Critical resource: Tyranitar HP for Roar.
Worst plausible branch: HP Water before Roar.
If wrong: use the dragged board to reset.
Info that changes answer: no pass threat.
Actual: Jolteon Baton Pass to Vaporeon; Tyranitar Roar dragged Tyranitar.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 16

Top move: switch Starmie
Confidence: medium-low
Route transaction: opposing Tyranitar wall/phaze package -> Starmie spin/reset converter -> Jolteon/Vaporeon owner -> Snorlax/Raikou punish.
Top three: 1. switch Starmie 2. switch Skarmory 3. switch Snorlax
#1 over #2 because: Spikes are taxing every route and Ttar seemed like a spin-entry window.
#2 becomes #1 if: Tyranitar coverage threatens Starmie or Skarmory must own the immediate board first.
Rejected safe/default line: Rock Slide mirror; it does not improve the route.
Positive-selection check: attempted reset-loop denial, but premature.
Opponent incentive: coverage into Tyranitar or phaze.
Critical resource: Starmie spinner health.
Worst plausible branch: Dynamic Punch or Crunch into Starmie.
If wrong: use Skarmory as immediate absorber first.
Info that changes answer: revealed coverage from opposing Tyranitar.
Actual: p1 switched Skarmory; opposing Tyranitar Dynamic Punch missed.
Score: top_match 0; acceptable_match 0; actual_in_top_three 1; actual_branch_named 0; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 0; top_rank_failure `resource_identity`.

## Turn 17

Top move: Skarmory Toxic
Confidence: high
Route transaction: Tyranitar coverage package -> Skarmory absorber/status converter -> electric/water owner -> Ttar/Raikou punish.
Top three: 1. Toxic 2. Curse 3. switch Starmie
#1 over #2 because: Toxic makes progress on Ttar or the switch; Curse only prepares without forcing.
#2 becomes #1 if: the target is already statused or Toxic-immune.
Rejected safe/default line: switch Starmie for spin; too risky before Ttar coverage is settled.
Positive-selection check: convert with status.
Opponent incentive: switch Jolteon or coverage.
Critical resource: Skarmory wakes this turn.
Worst plausible branch: Fire coverage.
If wrong: pivot Tyranitar on Jolteon.
Info that changes answer: known poison target on switch.
Actual: p2 switched Jolteon; Skarmory Toxic failed because Jolteon was already poisoned.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 18

Top move: switch Tyranitar
Confidence: high
Route transaction: poisoned Jolteon pass/electric package -> Tyranitar check/phazer -> pass receiver -> Roar/Rock Slide punish.
Top three: 1. switch Tyranitar 2. switch Snorlax 3. stay Curse
#1 over #2 because: Tyranitar threatens the pass route directly; Snorlax only absorbs.
#2 becomes #1 if: Ttar is too low or HP Water is likely.
Rejected safe/default line: stay with Skarmory; it risks the Marowak wall.
Positive-selection check: branch-punish and preserve.
Opponent incentive: Thunder or Baton Pass.
Critical resource: Tyranitar HP and Skarmory preservation.
Worst plausible branch: Thunder hit into low Ttar.
If wrong: hand off to Snorlax.
Info that changes answer: coverage damage.
Actual: p1 switched Tyranitar; Jolteon Thunder.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 19

Top move: Tyranitar Rock Slide
Confidence: medium
Route transaction: poisoned Jolteon/pass package -> Ttar damage/denial -> Vaporeon/Marowak receiver -> Skarm/Snorlax/Raikou punish.
Top three: 1. Rock Slide 2. Roar 3. switch Snorlax
#1 over #2 because: with no boost active, chip into the receiver converts more than random phazing without Spikes.
#2 becomes #1 if: Agility or pass is weighted higher than direct attack.
Rejected safe/default line: switch Snorlax; it gives free pass/setup.
Positive-selection check: branch-punish receiver.
Opponent incentive: Baton Pass.
Critical resource: Ttar health and poison clock.
Worst plausible branch: Agility into Marowak.
If wrong: Roar next if boosted route appears.
Info that changes answer: boost setup before pass.
Actual: Jolteon Baton Pass to Vaporeon; Tyranitar Rock Slide.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 20

Top move: switch Raikou
Confidence: medium-low
Route transaction: Vaporeon water/growth package -> Raikou electric converter -> Jolteon/ground owner -> Ttar/Skarm punish.
Top three: 1. switch Raikou 2. switch Snorlax 3. Rock Slide
#1 over #2 because: Vaporeon needs immediate electric pressure; Snorlax can let Growth/BP continue.
#2 becomes #1 if: Raikou's sleep turn makes it too slow or too valuable.
Rejected safe/default line: stay Rock Slide; Ttar can die to Surf.
Positive-selection check: converter handoff, but wrong resource timing.
Opponent incentive: Growth, Surf, or Baton Pass.
Critical resource: Starmie spinner was again underpriced.
Worst plausible branch: Growth on the handoff.
If wrong: bring Starmie to spin or chip.
Info that changes answer: recognizing Vaporeon as a Starmie spin window.
Actual: p1 switched Starmie; Vaporeon Growth.
Score: top_match 0; acceptable_match 1; actual_in_top_three 0; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 0; top_rank_failure `missing_candidate`.

## Turn 21

Top move: Starmie Rapid Spin
Confidence: high
Route transaction: boosted Vaporeon plus Spikes reset loop -> Starmie spin converter -> Vaporeon/Jolteon owner -> Snorlax/Raikou punish.
Top three: 1. Rapid Spin 2. switch Snorlax 3. Recover
#1 over #2 because: this is the clear spin window; switching keeps the Spikes loop alive.
#2 becomes #1 if: Vaporeon can immediately convert with boosted Surf/BP.
Rejected safe/default line: Psychic chip; it does not clear the route tax.
Positive-selection check: reset-loop denial.
Opponent incentive: Growth, Surf, or Baton Pass.
Critical resource: Starmie spin.
Worst plausible branch: second Growth.
If wrong: Snorlax/Raikou must absorb +2.
Info that changes answer: damage threshold showing Starmie cannot stay.
Actual: Starmie Rapid Spin; Vaporeon Growth.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 22

Top move: switch Snorlax
Confidence: medium
Route transaction: +2 Vaporeon water/pass route -> Snorlax special absorber -> Vaporeon/Jolteon owner -> Double-Edge/Earthquake punish.
Top three: 1. switch Snorlax 2. switch Raikou 3. Recover
#1 over #2 because: Raikou was asleep and Snorlax could absorb +2 immediately.
#2 becomes #1 if: Thunder pressure is required before Vaporeon passes or Rests.
Rejected safe/default line: repeat Rapid Spin/no-progress action.
Positive-selection check: none; this was too much defensive handoff.
Opponent incentive: Surf, Growth, or Rest.
Critical resource: Starmie could survive and actively damage.
Worst plausible branch: Vaporeon keeps boosting.
If wrong: use Starmie's Psychic window.
Info that changes answer: +2 Surf damage is survivable for Starmie.
Actual: Starmie Psychic; Vaporeon Surf.
Score: top_match 0; acceptable_match 1; actual_in_top_three 0; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 0; positive_selection 0; route_converting_move_chosen 0; branch_punish_chosen 0; top_rank_failure `route_budget`.

## Turn 23

Top move: Starmie Psychic
Confidence: high
Route transaction: low +2 Vaporeon -> Starmie damage converter -> Rest/switch owner -> Raikou/Snorlax punish.
Top three: 1. Psychic 2. Recover 3. switch Snorlax
#1 over #2 because: Vaporeon is in a force-now window; Recover lets it reset or pass.
#2 becomes #1 if: Starmie must stay above a Surf/crit threshold.
Rejected safe/default line: switch Snorlax; it gives Vaporeon a route reset.
Positive-selection check: convert damage before reset.
Opponent incentive: Surf or Rest.
Critical resource: Starmie HP and Vaporeon Rest threshold.
Worst plausible branch: Rest at low HP.
If wrong: punish Rest sleep window.
Info that changes answer: Psychic fails to force Rest or KO pressure.
Actual: Starmie Psychic; Vaporeon Rest.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Turn 24

Top move: switch Raikou
Confidence: medium
Route transaction: sleeping boosted Vaporeon -> Raikou electric converter -> Jolteon/ground owner -> Ttar/Skarm punish.
Top three: 1. switch Raikou 2. Psychic 3. Recover
#1 over #2 because: the sleep window looked like the time to install the electric owner rather than chip into a Rest loop.
#2 becomes #1 if: Starmie chip plus Special Defense drop pressure beats the handoff.
Rejected safe/default line: Recover; it wastes the sleep turn.
Positive-selection check: converter handoff.
Opponent incentive: Sleep Talk, switch Jolteon, or stay asleep.
Critical resource: Vaporeon Rest sleep action 0 and Raikou sleep action 0.
Worst plausible branch: Sleep Talk Surf or Growth.
If wrong: Starmie should keep active pressure.
Info that changes answer: Vaporeon has Sleep Talk and Starmie safely pressures.
Actual: Starmie Psychic; Vaporeon Sleep Talk -> Growth.
Score: top_match 0; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 0; top_rank_failure `route_budget`.

## Turn 25

Top move: Starmie Psychic
Confidence: high
Route transaction: sleeping +3 Vaporeon with SpD drop -> Starmie damage converter -> wake/reset owner -> Snorlax/Raikou punish.
Top three: 1. Psychic 2. switch Snorlax 3. Recover
#1 over #2 because: Special Defense drop plus sleep turn makes Psychic the route-converting damage; switching lets RestTalk stabilize.
#2 becomes #1 if: +3 Sleep Talk Surf or crit makes Starmie too valuable to risk.
Rejected safe/default line: Recover; no pressure before wake.
Positive-selection check: convert and deny Rest loop.
Opponent incentive: Sleep Talk Surf/Growth.
Critical resource: Starmie HP and Vaporeon sleep action 1.
Worst plausible branch: Sleep Talk Surf crit.
If wrong: finish with Raikou/Snorlax after Starmie softens.
Info that changes answer: Surf damage KO range.
Actual: Starmie Psychic; Vaporeon Sleep Talk -> Surf.
Score: top_match 1; acceptable_match 1; actual_in_top_three 1; actual_branch_named 1; top_one_discrimination_obeyed 1; rejected_safe_line_obeyed 1; positive_selection 1; route_converting_move_chosen 1; branch_punish_chosen 1; top_rank_failure none.

## Practice Read

The format helped most after the route owner was correctly named: turns 9-15 and 21/23/25 were cleaner because the answer had to commit to the absorber/converter and the reset loop. The misses before that were not broad GSC knowledge failures; they were mostly wrong owner selection or missing the route-converting Starmie action while still naming plausible top candidates.

Next session should keep the format, but add one explicit line before the top three: "current active can safely convert now? yes/no." This would have pressured turns 20, 22, and 24 where I handed off despite Starmie being able to convert.
