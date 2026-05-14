# Live-Turn Drills

Status: training material, not sealed benchmarks. The expected policies are
visible because this file is for practice and notebook calibration.

Use these drills with the live-turn answer template: recommendation,
confidence, route reason, state read, candidate ranking, next turn, and missing
information.

## Drill 001: Vanilla Spikes First Layer Versus No-Op

Source policies: `STP-001`, `STP-005`.

Public state A:

- Mechanics: `vanilla_gsc`.
- Our active: Cloyster at 83%, moves `Spikes / Surf / Toxic / Explosion`.
- Opponent active: Raikou at 74%, revealed `Thunderbolt / Roar`; likely to
  switch or pressure.
- Opponent side: 0 Spikes layers.
- Our plan: create switching cost for a grounded defensive core before phazing
  or Explosion pressure.
- Our Cloyster is not the only answer to a live threat this turn.

Expected policy A: Spikes is favored if the Thunderbolt branch is tolerable and
the layer changes future switching or Rest pressure.

Public state B mutation:

- Same position, but opponent side already has the vanilla maximum of 1 Spikes
  layer.

Expected policy B: Spikes becomes a no-op failure. Re-rank Surf, switch,
Toxic, or Explosion by route value.

Lesson: "set hazards" loses instantly to mechanics truth.

## Drill 002: Romhack Layer Three Versus Fourth Click

Source policies: `STP-001`, `STP-005`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Our active: Forretress at 61%, moves `Spikes / Rapid Spin / Hidden Power Bug
  / Explosion`.
- Opponent active: bulky grounded setup Pokemon at 68%, boosted once.
- Opponent side: 2/3 Spikes layers.
- Our side: 1/3 Spikes layers.
- Our plan: force repeated grounded entries and make later damage thresholds
  real.

Expected policy A: third layer can be favored only if the extra layer changes a
route and the setup punish is not immediate or unanswerable.

Public state B mutation:

- Same position, but opponent side is already 3/3 Spikes layers.

Expected policy B: Spikes is catastrophic/no-effect. Explosion, Rapid Spin, or
switching must be compared by whether they deny the active route.

Lesson: romhack three-layer Spikes raises the value of layers 2-3 but makes the
fourth click a state error.

## Drill 003: Sleep As Route Creation Versus Sleep As Script

Source policy: `STP-002`.

Public state A:

- Mechanics: `vanilla_gsc` unless local romhack sleep evidence is supplied.
- Our active: fast sleep user at 72%, move `Sleep Powder`.
- Opponent active: setup blocker at 80%, no status, not known to use Sleep
  Talk.
- Sleep clause: unused.
- Miss branch: opponent attacks but does not KO or create an unanswerable
  route.
- Our plan: sleep the blocker, then reassess whether setup or attack is safer.

Expected policy A: sleep can be favored because it targets a route blocker and
the miss branch is survivable.

Public state B mutation:

- Same position, but target is already paralyzed, or sleep clause is already
  used.

Expected policy B: sleep no longer creates the intended state. Rank attack,
switch, status alternative, or setup from the current board.

Lesson: sleep value depends on the state it creates; it is not a generic setup
permission slip.

## Drill 004: Explosion Conversion Versus Lost Unique Role

Source policy: `STP-003`.

Public state A:

- Mechanics: `vanilla_gsc` or romhack with Explosion behavior verified.
- Our active: Forretress at 38%, hazards already completed, no longer needed
  as the only spinner.
- Opponent active: special wall at 70% that blocks our cleaner.
- Opponent Ghost/Protect branch: not revealed and low-plausibility from the
  visible roster.
- Our cleaner is healthy enough to use the opened route.

Expected policy A: Explosion can be favored if the target's removal makes a
named cleaner route real and Forretress's lost jobs are replaceable.

Public state B mutation:

- Same position, but Forretress is the only remaining answer to a later setup
  threat, or a healthy Ghost/Protect branch is revealed and incentivized.

Expected policy B: Explosion drops sharply or becomes catastrophic.

Lesson: Explosion is not "low HP means expendable"; it is a trade between the
route opened and the route closed.

## Drill 005: Prediction When Ahead Versus Forced Risk When Behind

Source policy: `STP-004`.

Public state A:

- We are ahead and have a stable defensive answer.
- Straightforward move covers the opponent's likely action and worst plausible
  switch while preserving our win route.
- A hard read would KO a secondary target but loses if the opponent attacks.

Expected policy A: use the straightforward route-preserving move. Prediction is
unnecessary when the safe move keeps control.

Public state B mutation:

- Same board shape, but the straightforward move loses slowly because the
  opponent's primary route is already converting.
- The hard read is the only line that creates a live winning route.

Expected policy B: accept the risk if the alternative is a controlled loss.

Lesson: prediction quality is determined by risk budget and route necessity,
not by whether the move looks clever.

## Drill 006: Converter Preservation Versus Early Greed

Source policies: `STP-006`, `STP-008`.

Public state A:

- Our cleaner can win after the opposing physical wall is below 60%.
- The wall is still at 92%, unrevealed coverage exists, and our cleaner would
  take status or heavy chip on entry.
- Another teammate can safely force the wall toward recovery or chip this turn.

Expected policy A: do not bring in or set up with the cleaner yet. Use the
teammate to prepare the board first.

Public state B mutation:

- Same cleaner, but the wall is at 48%, the phazer is gone, and the current
  active gives a free setup turn unless it reveals a low-plausibility move.

Expected policy B: setup or converter entry rises because the boost changes
the next board and blockers are already priced.

Lesson: the question is not "can this Pokemon sweep?" but "has the board been
prepared enough for its first committed turn?"

## Drill 007: Check, Counter, And Entry Creation

Source policy: `STP-009`.

Public state A:

- Our answer beats the threat one-on-one from full HP.
- It is currently at 54%, hazards are up, and it cannot survive switch-in damage
  plus the revealed attack.
- A different low-value teammate can be sacrificed to give the answer free
  entry.

Expected policy A: do not call the answer a counter from the current board.
Consider creating free entry before relying on it.

Public state B mutation:

- Hazards are removed and the answer survives two revealed hits after entry.

Expected policy B: hard switch rises because entry is now real.

Lesson: an answer label changes with HP, hazards, status, and entry method.

## Drill 008: Lead Role Fit

Source policy: `STP-010`.

Public state A:

- Boss roster is known.
- Our fastest attacker has a good lead matchup but is also the only revenge
  answer to the boss's final cleaner.
- A bulkier lead loses some tempo but denies the opening status/hazard route
  and keeps the revenge answer untouched.

Expected policy A: prefer the bulkier lead unless the fast lead's opening gain
is route-deciding.

Public state B mutation:

- The final cleaner is already covered by another teammate, and the fast lead
  can remove the boss's support piece before it acts.

Expected policy B: fast lead rises because its later job is duplicated and the
opening denial is concrete.

Lesson: lead choice is part of the whole battle plan, not a turn-1 matchup
contest.

## Drill 009: Reveal Timing Versus Wasted Surprise

Source policy: `STP-014`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Our active: Suicune at 88%.
- Boss active: Clair Dragonair at 74%, with Thunder and Outrage revealed.
- Our revealed move: Surf, which barely changes the Dragonair route.
- Our hidden move: Ice Beam, locally checked as a guaranteed KO from this HP.
- Boss bench: Kingdra, Mantine, Steelix, Gligar, and another Dragonair.

Expected policy A: reveal Ice Beam now. Dragonair is the current route blocker,
the reveal removes it, and hiding the move lets Clair keep Thunder / Outrage
pressure while Surf fails to change the board.

Public state B mutation:

- Same Suicune, but the active target is Kingdra at full HP and the Ice move
does not remove or meaningfully cripple the route blocker.

Expected policy B: do not reveal the hidden move just because it is unusual or
superficially strong. Choose the move or pivot that addresses Kingdra's actual
route, and preserve the reveal if a Dragonair or Gligar branch is the real
target.

Lesson: reveal a hidden resource when the route-specific blocker is present or
forced. Otherwise it may win no route and teach the opponent or boss trace the
wrong lesson.

## Drill 010: Scouting Turn Versus Donated Setup

Source policy: `STP-015`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Brock Omastar with Spikes / Surf / Ice Beam / Protect and
  Leftovers.
- Our active threatens enough damage that Omastar cannot safely combine Spikes
  plus repeated Protect recovery.
- Our scout/protection move blocks Surf or Ice Beam and creates a free setup,
  recovery, pivot, or hazard-denial follow-up.

Expected policy A: the scout/protection move can be correct if the protected
turn has a named job and the follow-up punishes Omastar's route.

Public state B mutation:

- Same position, but our protected turn only gains minor HP or information,
  while Omastar can use the turn to set Spikes, switch to Corsola, or preserve
  itself with Leftovers without losing a route.

Expected policy B: attack, pivot, or deny hazards instead. Scouting is not
progress if the protected turn gives Brock the exact free resource turn his
fight is built around.

Lesson: a protected turn must buy route value. If it only reduces anxiety while
the opponent improves hazards, recovery, setup, or position, it is a donated
turn.

## Drill 011: Locked Move Commitment Versus Flexible Pressure

Source policy: `STP-016`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Whitney Miltank at 92%, with Body Slam / Milk Drink / Rollout
  revealed and Mint Berry unspent.
- Player active: Geodude at 78%, with Rock Throw / Defense Curl revealed and
  Magnitude plausible.
- No paralysis yet. No screens or weather.

Expected policy A: do not start Rollout from the boss side. Body Slam is the
better pressure move because it preserves Milk Drink / switch flexibility and
can create the paralysis branch that makes a later Rollout safer. From the
player side, punish early Rollout as a predictable commitment rather than
treating it as an already completed sweep.

Public state B mutation:

- Same board, but Geodude is paralyzed, already chipped below the relevant
  survival range, and the player's immediate punish branches are reduced.

Expected policy B: Rollout rises because the first locked hit now starts a
conversion route instead of donating flexibility. The answer still needs a plan
for the board after the forced sequence ends.

Lesson: a locked move is not good because it snowballs in theory. It is good
only when the current state makes the forced turns winning turns.

Public state C:

- Boss active: Blue Pidgeot with Choice Band has just used Double-Edge.
- Player has a durable resist or recovery piece that can enter without losing
  the Gyarados denial role.

Expected policy C: exploit the lock if the entry is real. Do not keep treating
Pidgeot as a flexible attacker after the lock is known, but also do not spend
the only Gyarados / Arcanine answer merely to punish Pidgeot.

Answer-changing information:

- Whether the lock is confirmed or only suspected.
- Whether the locked move is resisted, immune, or still strong under the local
  chart and passive rules.
- Whether the chosen entry piece is needed for a later setup, priority, or
  recovery route.

Public state D:

- Boss active is in a restricted-move state: Rollout / Outrage / recharge /
  Encore / Choice lock / Disable / Taunt.
- The previous turn involved a miss, failed move, flinch, confusion, paralysis,
  Protect, recharge, or move that continued from a prior selection.
- The candidate answer depends on whether the move was selected, executed,
  successful, and whether PP was spent.

Expected policy D: do not reason from the message text alone. Classify
selection, execution, success, PP loss, and remaining lock turns before
choosing the punish or reset.

Answer-changing information:

- Local source or fixture for whether the move restriction checks selection,
  execution, success, or PP.
- Remaining lock/recharge/rampage/Encore turns.
- Whether switching, phazing, fainting, or item removal clears the state.

## Drill 012: Recovery Window Versus Fake Progress

Source policy: `STP-017`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Misty Starmie at 46%, with Recover / Hydro Pump / Psychic
  revealed and Thunder plausible.
- Player active: Meganium at 68%, with Razor Leaf revealed.
- Rain and Reflect are active.
- Local damage note: Razor Leaf KOs Starmie from the shown HP.

Expected policy A: attack with Razor Leaf. Recovery is not a real reset if the
opponent is already in route-ending KO range and the attacker survives the
public punish branch. The route gained is removal of Misty's fast recovery
bridge before Recover can matter.

Public state B mutation:

- Same Starmie, but Starmie is at 78%, Razor Leaf does not KO, and the player
  has a breaker or status user that can enter safely on Recover.

Expected policy B: do not repeat shallow chip if Recover owns the cycle. Force
Recover, then use the recovery turn to enter the real breaker, apply decisive
status, set a threshold, or pivot to the piece that punishes the reset.

Public state C:

- Boss active: Blue Porygon2 or Brock Corsola is above the direct-KO threshold
  and can Recover through weak damage.
- Our current attack is visible chip but does not force a two-turn KO, status,
  PP pressure, or safe entry.

Expected policy C: attack falls unless it creates a concrete recovery punish.
Use status, item denial, setup, Taunt/Encore-style control if available, or a
pivot that makes Recover a losing turn instead of a reset.

Lesson: recovery is not passive. It either resets the route in the user's favor
or creates a timing window for the other side. Label which one before clicking
damage, healing, or a pivot.

## Drill 013: Weather Ownership Versus Clear-Weather Autopilot

Source policy: `STP-018`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Misty Politoed with Rain Dance / Hypnosis / Surf / Ice Beam.
- Boss bench includes Starmie with Recover / Hydro Pump / Psychic / Thunder
  and Lapras with Rain Dance / Surf / Ice Beam / Thunder.
- Player lead can 2HKO Politoed and is not the only Starmie/Lapras answer.
- No rain is active.

Expected policy A: pressure Politoed immediately. Do not give Politoed a free
Rain Dance or Hypnosis turn when those turns make the later Starmie/Lapras
route harder to answer. If rain goes up anyway, count turns and try to make
Misty spend them switching, recovering, or using low-impact coverage.

Public state B mutation:

- Same board, but the player lead is the only reliable Starmie/Lapras answer,
  and trading it into Hypnosis or rain-boosted chip loses the Water route.

Expected policy B: preservation or pivoting rises. The correct move may be a
sleep/rain buffer or a lower-value attack that keeps the irreplaceable answer
out of the status/weather trap.

Public state C:

- Boss active: Blaine Ninetales with Sunny Day / Fire Blast / Psychic /
  Safeguard.
- Player's current plan relies on Water damage and status to handle the Fire
  core.

Expected policy C: do not follow the clear-weather Water/status script after
Sunny Day or Safeguard. Either deny Ninetales immediately, change weather, or
burn sun turns without giving Rapidash Agility, Arcanine priority cleanup, or
Magmar coverage a clean route.

Lesson: weather changes whose clock is winning. The move is correct only if it
either converts our weather turns or denies / stalls the boss's payoff turns
without spending the answer needed after the weather expires.

## Drill 014: Screen Window Versus Wrong-Category Autopilot

Source policy: `STP-019`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Sabrina Mr. Mime with Light Screen / Reflect / Encore /
  Psychic.
- Boss bench includes Jynx, Espeon, Alakazam, and Hypno.
- No screen is active yet.
- Player active can attack, switch, status, recover, or set up, but the setup
  route is vulnerable to Encore.

Expected policy A: deny Mr. Mime's screen / Encore support job if the screen
would deliver Jynx, Espeon, Alakazam, or Hypno safely. Attack if it removes or
forces Mr. Mime before the screen; otherwise choose a move that still advances
a route through Encore or a screen rather than giving the receiver a protected
entry.

Public state B mutation:

- Same fight, but Reflect is already active with four turns remaining.
- The player's current route relies on physical damage into the protected
  receiver.
- A special attacker, status route, phaze route, or screen-stalling pivot may
  be available.

Expected policy B: do not keep using the blocked physical route unless it still
crosses a KO, forced-recovery, or preservation threshold. Switch category,
force progress that ignores Reflect, burn screen turns only if that does not
give setup / sleep / recovery, or preserve the answer until the screen expires.

Public state C:

- Boss active: Lt. Surge Electrode or Ampharos with Light Screen available.
- Player route is special-only unless a physical pivot is preserved.
- The later Electric route becomes harder if the screen setter gets a free
  support turn.

Expected policy C: Light Screen changes the plan. Pressure the screen setter
before it delivers the protected route, pivot to the physical plan if it is
real, or preserve the special answer instead of spending screen turns on fake
progress.

Answer-changing information:

- Exact remaining screen turns and whether the screen is already active.
- Whether the planned damage category still crosses a route threshold through
  the screen.
- Whether the boss has an immediate receiver that converts the protected turn.
- Whether Encore, sleep, recovery, or setup punishes the screen denial move.

Lesson: a screen is a timed delivery window, not generic defense. Count the
turns, name the receiver or payoff, and re-rank damage categories before
recommending another attack, setup move, or stall turn.

## Drill 015: Faster Cleaner Versus Priority Range

Source policy: `STP-020`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Blaine Arcanine with ExtremeSpeed still unrevealed but legal
  from the local route sheet.
- Boss bench is nearly exhausted.
- Player active is a faster Water or Rock attacker at low HP after Spikes,
  sun, recoil, or prior Fire damage.
- The player's attack KOs Arcanine if it moves.

Expected policy A: do not call this a clean sweep until ExtremeSpeed range is
priced. If ExtremeSpeed KOs or puts the attacker into the final boss route's
range, preserve the cleaner, use a bulkier answer, force recoil, or create a
controlled sack entry. If ExtremeSpeed is nonlethal and the KO closes the
route, attack and stop over-preserving.

Public state B mutation:

- Same Arcanine, but the player attacker is safely above ExtremeSpeed range and
  no later boss piece can revenge after the chip.

Expected policy B: attack rises. Priority exists, but it does not change the
route, so preserving the cleaner may only donate a Fire Blast, setup, or
coverage turn.

Public state C:

- Boss active: Bruno Hitmonchan or Hitmontop with Mach Punch available.
- Player active is a faster Psychic / Flying-style cleaner that is also needed
  for Machamp, Heracross, or the remaining Fighting route.
- The cleaner can KO the current target if it moves first.

Expected policy C: calculate whether Mach Punch removes the cleaner or breaks
its later job. If it does, use the bulkier answer, sack entry, status, or
damage setup that keeps the later Fighting route covered. If it does not, the
fast revenge line can be correct.

Answer-changing information:

- Exact priority damage range under the romhack chart and passives.
- Whether the boss priority user is still alive, locked, low on PP, or forced
  to spend priority this turn.
- Whether Focus Band, Endure, Protect, Quick Claw, recharge, or paralysis
  creates a survival or turn-order exception.
- Whether the fast attacker has another irreplaceable job after this KO.

Lesson: "faster" is not a route label. A cleaner is real only after priority,
Quick Claw, survival items, entry damage, and next-piece revenge range fail to
break the line.

## Drill 016: Status Absorber Versus Status Reset

Source policy: `STP-021`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Misty Politoed with Hypnosis / Rain Dance / Surf / Ice Beam.
- Boss bench includes Starmie and Lapras that become stronger if the player's
  main Water answer is asleep.
- Player has one bulky status absorber and one faster Water answer.
- No rain is active yet.

Expected policy A: assign sleep only if the absorber has no unique later job or
still functions asleep. If sleeping the Water answer loses the Starmie / Lapras
route, deny Politoed with damage, pivot to a true absorber, or choose the line
that prevents rain plus sleep from landing on the same critical piece.

Public state B mutation:

- Same fight, but Misty still has Full Heal and the proposed status target is
  Starmie at high HP with Recover available.
- The player's Toxic or paralysis does not force a KO, recovery punish, safe
  entry, or item-spending turn that improves the route.

Expected policy B: status falls. It may only prompt a cheap Full Heal while
Starmie keeps the Recover route. Direct damage, forcing a threshold, preserving
status for Quagsire / Lanturn, or using the cure turn as a named entry plan
must outrank "status because status is good."

Public state C:

- Boss active: Sabrina Hypno with Thunder Wave / Rest / Seismic Toss /
  Psychic.
- Player's special wall can take Thunder Wave, but it is also the only
  Alakazam or Espeon answer.
- A slower bulky pivot or immediate pressure line may be available.

Expected policy C: do not automatically let the special wall absorb Thunder
Wave. If paralysis breaks its later answer job through Speed loss or
full-paralysis risk, pressure Hypno, route Thunder Wave into a slower piece, or
force Rest / damage before accepting the status.

Answer-changing information:

- Which boss cure items, Rest users, Safeguard users, or cleric-style effects
  are still live.
- Whether Sleep Clause is unused and whether the intended absorber has a later
  awake-turn job.
- Whether poison or paralysis combines with hazards, recovery denial, or forced
  Rest before it can be reset.
- Whether the status user is also offering a setup, rain, screen, trap, or
  recovery turn if we pivot.

Lesson: status is not a binary good or bad event. Before using or absorbing it,
name the piece receiving it, the job that piece still owes, the reset that can
erase it, and the route value gained before that reset happens.

## Drill 017: Support Chain Versus Visible One-On-One

Source policy: `STP-022`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Bugsy Ledian with Reflect / Quiver Dance / Leech Life /
  Baton Pass.
- Boss bench includes Scyther with Swords Dance / Quick Attack / Wing Attack.
- Player active can damage Ledian but is also the only healthy Scyther answer.
- Reflect is not active yet, and Ledian has not boosted.

Expected policy A: preserve the Scyther answer unless the hit on Ledian either
removes it before support happens or makes any later pass harmless. The visible
one-on-one is not the route; the route is whether Scyther receives Reflect,
boosts, or a clean entry while the answer is chipped.

Public state B mutation:

- Same board, but the player active KOs Ledian before it can Reflect, Quiver
  Dance, or Baton Pass, and a separate Scyther answer remains healthy.

Expected policy B: attacking Ledian rises. Removing the support user before it
delivers the receiver route is real progress, and preserving the current active
is less important because the receiver map remains covered.

Public state C:

- Ledian already has Quiver Dance and Reflect is active with several turns
  remaining.
- Scyther enters safely if Baton Pass succeeds.
- The player has Haze, phazing, Encore, status, immediate KO, or a controlled
  sack route, but not all of them are safe.

Expected policy C: choose the denial line that still works after local
mechanics are checked. Do not set hazards or use generic chip if Baton Pass
delivers supported Scyther first. If no denial works, preserve the one answer
that can survive supported Scyther and create a controlled entry for it.

Answer-changing information:

- Whether Ledian survives the proposed hit and moves before the player.
- Whether Baton Pass keeps the relevant boosts / screens under local source.
- Whether phazing, Haze, Encore, status, or direct KO works before the pass.
- Whether Scyther survives the planned answer after Reflect, Berry,
  SilverPowder, Swords Dance, and Quick Attack range are priced.

Lesson: support chains are not separate fights. Before choosing damage,
hazards, status, or preservation, name the receiver, the support delivered, and
the last turn where the chain can still be stopped.

## Drill 018: Degraded Role Versus Throwaway Sack

Source policy: `STP-023`.

Public state A:

- Format: vanilla GSC strategic review.
- Source shape: `smogtours-gen2ou-908690`.
- Our Exeggutor has missed Sleep Powder several times and is now too low to
  keep acting as a repeated sleep-pressure piece.
- It still has Explosion, and the opposing RestTalk Snorlax is the main
  stabilizer blocking the preserved Zapdos route.

Expected policy A: relabel Exeggutor from "sleep threat" to "one-time Snorlax
converter." Do not sack it just because the first role failed. Preserve or
spend it only around the target that opens the named endgame.

Public state B mutation:

- Same damaged Exeggutor, but the opposing Snorlax has already been removed,
  the next Explosion targets are replaceable, and Exeggutor cannot sleep,
  status, or damage a remaining blocker before fainting.

Expected policy B: Exeggutor can become sack material. Preserving a degraded
piece without a live narrow job is just attachment to the old plan.

Public state C:

- Our Zapdos absorbed opening sleep because it has RestTalk and late-game
  matchup value.
- Midgame, it looks inactive while other teammates trade around Snorlax,
  Forretress, Golem, Gengar, and Exeggutor.

Expected policy C: do not treat sleeping Zapdos as spent. The route may be to
remove the blockers while preserving Zapdos as the eventual converter. If the
support map fails to remove those blockers, then the Zapdos route must be
downgraded or handed off.

Answer-changing information:

- Which original job failed and which exact narrow jobs remain.
- Whether the narrow job has a live target, receiver, timing window, and
  survival path.
- Whether spending the degraded piece opens a route or only removes an
  impressive but replaceable target.
- Whether local mechanics preserve the job: RestTalk behavior, Explosion
  damage, Baton Pass, screen turns, hazards, priority, status, and items.

Lesson: bad luck changes job labels. After a miss, sleep, paralysis, chip, or
unexpected reveal, rewrite each affected piece as a current-role object before
calling it preserved, expendable, or the converter.

## Drill 019: Temporary Disable Versus Route Ownership

Source policy: `STP-024`.

Public state A:

- Format: vanilla GSC strategic review.
- Source shape: `smogtours-gen2ou-905952`.
- Opponent's RestTalk Snorlax is frozen and looks like the main anchor has
  been removed from the game.
- Our Snorlax and paralyzed Gengar are the remaining material that can exploit
  the frozen target.
- Opponent Exeggutor is low but still has Explosion.

Expected policy A: do not call the game won because Snorlax is frozen. Preserve
the piece that makes the frozen-state route real, or force Exeggutor to spend
Explosion into the less important target. The cash-out is only real if the
frozen Snorlax is kept from reaching Rest while our converter remains alive.

Public state B mutation:

- Same frozen anchor, but the target is already in guaranteed KO range this
  turn and no Rest, switch, cure, Sleep Talk, or trade branch can interrupt the
  converter.

Expected policy B: cash out now. Over-preserving gives the disabled target more
turns to defrost, wake, switch, cure, or force another reset.

Public state C:

- Boss fight transfer: a boss ace is asleep, frozen, confused, recharging, or
  locked after a resisted move.
- The player's intended converter is low, statused, or also the only answer to
  the next boss route.
- The boss has plausible Rest, Full Restore, switch, priority, Focus Band, or
  sacrifice branches.

Expected policy C: name the cash-out turn and reset branch before choosing. If
the converter must survive for the disabled-state route, preserve it. If the
reset branch is unavoidable, move to the backup route instead of repeating the
old "they are disabled" plan.

Answer-changing information:

- Exact duration or odds of the control state: sleep turns, freeze behavior,
  confusion turns, recharge, lock, Encore, or trap.
- Whether the disabled target has Rest, Sleep Talk, item cure, switch access,
  or a teammate that can trade for the converter.
- Whether the converter can finish before the reset, and whether it is still
  needed if the reset happens.
- Whether local romhack mechanics alter status, lock, recharge, cure items,
  Focus Band, Quick Claw, or AI switch behavior.

Lesson: temporary disable is only a route discount. The move is correct when it
cashes out the discount before reset or preserves the material needed after
reset; it is wrong when it spends the converter because the target merely looks
disabled.

## Drill 020: Trade Cascade Versus Momentum Autopilot

Source policy: `STP-025`.

Public state A:

- Format: vanilla GSC strategic review.
- Source shape: `smogtours-gen2ou-930772`.
- Our Cloyster already set Spikes, is poisoned, and can Explode on opposing
  Cloyster, which still provides hazard / Toxic value.
- Both teams have several route pieces left.

Expected policy A: Explosion can be correct because Cloyster's main job is
spent and opposing Cloyster remains a live hazard-control piece. After the
trade, immediately rewrite the answer map instead of assuming the next
Explosion or sacrifice is also correct.

Public state B:

- Later, our Steelix has phazed Tyranitar through Spikes and can Explode on a
  sleeping Zapdos.
- Steelix also still checks or slows some remaining routes.
- Our likely post-trade plan is Gengar plus Zapdos pressure.

Expected policy B: Explosion is legal only if the post-trade route is named:
what wins after Steelix is gone, what answers Tyranitar, and whether Gengar /
Zapdos can actually convert before wake, trade, or revenge branches. A good
first trade does not make this second trade good by default.

Public state C mutation:

- Opponent has one clear remaining converter, and our one-time trade removes
  that converter while our remaining team covers the rest.

Expected policy C: trade now. Rebuilding the route map can make the second
trade even clearer, as with removing the last credible converter instead of a
merely strong Pokemon.

Boss transfer:

- The player has already spent one unique resource against a Gym Leader:
  Explosion, Focus Band, phazer, sleep absorber, item cure, or controlled sack.
- The next tempting trade removes the active boss Pokemon but may uncover the
  ace, weather user, spinner, recovery anchor, or setup sweeper.

Expected policy transfer: before spending the next one-time resource, name the
new boss route priority, the lost role, and the post-trade converter. If those
fields are blank, preserve or pivot rather than continuing the trade cascade.

Answer-changing information:

- Which route each side gained or lost from the previous trade.
- Which one-time resources remain and what roles they still cover.
- Whether the next target is the current live converter or only a valuable
  piece.
- Whether local mechanics make the trade fail, such as Ghost, Protect,
  Substitute, Focus Band, type passives, or damage range.

Lesson: trade cascades need fresh maps after every exchange. The next trade is
judged from the new board, not from the fact that the previous trade looked
good.

## Drill 021: PP Budget Versus Empty Stalling

Source policy: `STP-026`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active: Sabrina Espeon or Red Espeon with Morning Sun available.
- Morning Sun has a small local PP budget compared with Recover-style moves.
- Player damage does not KO but reliably forces Morning Sun without sacrificing
  the later Alakazam / Snorlax / Blastoise answer.

Expected policy A: PP pressure can be real. Count Morning Sun uses and explain
what happens when the PP runs out or when Espeon must choose between healing
and a different support route. Do not call recovery unbeatable just because HP
resets this turn.

Public state B mutation:

- Same recovery target, but the player's repeated attack has lower PP than the
  recovery move, does not force setup denial, safe entry, status, hazard, or KO
  progress, and exposes an irreplaceable answer.

Expected policy B: stop attacking into the reset budget. This is not PP
pressure; it is spending scarce attacking / answer PP into a loop the boss
owns.

Public state C:

- Boss route includes Dragon Dance, Curse, Calm Mind, or another setup route.
- Player has limited phazing or Haze PP.
- Current boost is contained by another answer, but a later boost route is more
  dangerous.

Expected policy C: conserve emergency PP unless the current phaze / Haze denies
a live route, creates hazard damage, forces recovery, or reveals a needed
piece. Spending the last phaze because "setup might happen" can lose the
actual final setup turn.

Public state D:

- Hazard war against a spinner with Rapid Spin's large PP budget.
- Player has layered Spikes but spinner entry, HP, status, or spinblock timing
  is fragile.

Expected policy D: do not default to "PP stall Rapid Spin." Pressure entry,
health, status, spinblock timing, or the turn cost first unless the board is
already a true endgame loop where spin PP is the bottleneck.

Answer-changing information:

- Exact local PP for the scarce move.
- Whether the move is the route gate or only an abundant reset.
- Whether forcing the move creates safe entry, setup, status, hazards, KO
  range, or a preserved answer.
- Whether local weather, RestTalk, three-layer Spikes, items, or boss AI
  changes the PP clock.

Lesson: PP is material only when a specific move gates the route. Count the
move that matters, then choose whether to force it, conserve it, or stop
spending into a loop the opponent already owns.

## Drill 022: Contained Waiting Versus Passive Donation

Source policy: `STP-027`.

Public state A:

- Format: vanilla GSC strategic review.
- Source shape: `smogtours-gen2ou-909431`.
- Our Raikou still answers poisoned Zapdos and low Jolteon.
- Our Forretress still contains Snorlax and can Rest if needed.
- Our side has removed Spikes; opponent side still pays Spikes.
- Opponent Zapdos is poisoned, Jolteon is low enough that Spikes matter, and
  Snorlax lacks a revealed setup route that breaks Forretress.

Expected policy A: low-effect Forretress turns can be acceptable. The progress
is external: poison, Spikes, and contained opponent routes. The answer must
name the clock and covered punish, not pretend the move text itself is
progress.

Public state B mutation:

- Same Forretress / Snorlax faceoff, but Snorlax has Curse and Forretress
  cannot stop the boost route.

Expected policy B: waiting fails. A low-effect move gives Snorlax a free
converter turn, so attack, phaze / Haze if available, pivot to the answer,
trade, status, or change routes.

Public state C:

- Boss transfer: a boss is losing to poison / recoil / weather / screen
  expiration / Rest sleep / hazard clock, and our current active can preserve
  the answer.
- However, the boss can also use the free turn for setup, recovery, Safeguard,
  weather, spin, or a support pass.

Expected policy C: waiting is legal only if the punish branch is covered and
the external clock keeps winning. Otherwise, choose active denial.

Answer-changing information:

- What external clock is actually advancing.
- Which opponent punish branches are covered.
- Whether the answer still has HP / PP / status to keep entering.
- Whether local AI, items, recovery, weather, screens, or hazards reset the
  clock.

Lesson: waiting is not the absence of a plan. It is a move class that is
correct only when containment plus an external clock already owns the position.

## Drill 023: Hazard Contract Versus Layer Autopilot

Source policy: `STP-028`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Our active can set a second Spikes layer.
- Opponent has three grounded Pokemon that must switch repeatedly.
- Opponent spinner is either removed, too low to enter safely, or punished by a
  named spinblock / KO / setup / trap route.
- The added layer changes a recovery, phaze, KO, or cleaner threshold.

Expected policy A: set the layer. The answer must name all three jobs: who sets
it, why it stays or is punished if removed, and what route it converts.

Public state B mutation:

- Same chance to set Spikes, but the opponent spinner enters freely next turn.
- The spinblocker is gone, too low, or loses the spin turn.
- The layer does not create an immediate KO, forced Rest, or safe converter
  entry before Rapid Spin.

Expected policy B: do not treat the layer as progress. Attack, trap, pivot,
status, preserve the setter, or pressure the spinner first.

Public state C:

- The hazard cannot be retained long-term.
- However, the layer immediately puts the next forced switch-in into KO range
  or makes the boss spend a recovery / item / spin turn that gives a clean
  converter entry.

Expected policy C: temporary hazard can be correct. The answer must say the
layer is being used as a one-turn conversion tool, not as a durable plan.

Public state D:

- Opponent side is already at max local Spikes layers.
- Re-clicking Spikes would not create a new layer.

Expected policy D: Spikes is a no-effect or low-effect move unless a separate
contained-waiting loop is already proven. State legality dominates hazard
enthusiasm.

Answer-changing information:

- Current layer count and local max layer count.
- Grounded opposing targets and forced-switch frequency.
- Spinner, spinblocker, Haze, phaze, recovery, and item status.
- Whether the layer changes an actual threshold before removal.
- Whether the setter has another irreplaceable role.

Lesson: hazards are a contract, not a button. If set, retain, and convert are
not all named, the hazard plan is unfinished.

## Drill 024: Board Inheritor After First Route Denial

Source policy: `STP-029`.

Public state A:

- The opponent's first setup route has been stopped by status, phazing, Haze,
  sacrifice, revenge damage, or a forced switch.
- The answer that stopped it took meaningful HP, status, PP, item loss, hazard
  tax, or positioning cost.
- The opponent still has a second converter, cleaner, weather route, anchor, or
  breaker that can exploit that cost.

Expected policy A: do not continue the old plan automatically. Name the board
inheritor, the answer used, the cost paid, and the remaining answer. Choose the
move that prevents the second route from entering for free.

Public state B mutation:

- The first denial also removed the only remaining converter.
- The opponent's backline cannot exploit the cost paid, or a healthy backup
  answer covers the next route.

Expected policy B: simplify. Cleanup, contained waiting, recovery, or hazard
conversion may become correct, but the backup answer must still be named.

Public state C:

- Boss transfer: Bugsy Scyther, Koga Crobat / Nidoking, Lance next Dragon,
  Blue's next breaker, or Red's Espeon / Snorlax / sun / Blastoise can inherit
  the board after the visible route is checked.

Expected policy C: the correct move is the handoff-denial move. Preserve or
move into the piece that covers the inheritor, even if the active threat was
just handled.

Public state D:

- We can KO the boss active this turn.
- The boss has two possible replacements: one a human would likely choose by
  matchup, and one that local AI source/trace/route evidence says may be
  preferred.
- One replacement is harmless to our current active; the other starts setup,
  weather, priority revenge, recovery, or status pressure.

Expected policy D: do not choose the post-KO entry by human intuition alone.
Either use the local replacement evidence, or choose the move / post-KO
position that covers the highest-severity replacement family.

Answer-changing information:

- Cost paid by the first answer.
- Which boss piece benefits from that cost.
- Whether the same answer still survives entry and damage thresholds.
- Whether a backup answer, phazer, Haze user, priority, item, or sacrifice
  covers the inheritor.
- Whether the original plan still has a concrete next move after the public
  state changed.
- Local AI source, trace, or observed replacement policy after a KO.

Lesson: stopping a route is not the same as owning the game. The next move is
judged by who inherits the board.

## Drill 025: Shared-Answer Overload Versus Isolated Matchups

Source policy: `STP-030`.

Public state A:

- Two boss routes are both currently answered by the same player Pokemon.
- That answer can switch into either one once, but hazards, poison, paralysis,
  PP, weather, item loss, or chip make repeated entries uncertain.
- The active boss Pokemon can damage, status, trap, or force that shared answer
  before the later route appears.

Expected policy A: preserve or protect the shared answer unless the current
route is immediately worse. The answer must name every route that still needs
the piece and how many entries or actions remain.

Public state B mutation:

- A backup answer has become real through damage, status, item use, speed
  control, phazing, Haze, priority, or a forced lock.
- The shared answer no longer has to cover both routes.

Expected policy B: the shared answer can be spent more freely. Attack, trade,
absorb status, or sacrifice can be correct if it opens the concrete route.

Public state C:

- Boss transfer: Koga can Toxic the Nidoking / Crobat answer, Lance can chip
  the final Dragon answer with earlier waves, Misty can sleep or paralyze the
  one Water anchor, or Red can make the Snorlax / Espeon answer pay too much
  before the real route appears.

Expected policy C: do not evaluate only the active matchup. Choose the move
that keeps the overloaded answer above its final-route threshold or creates a
second answer before the boss finishes overloading it.

Answer-changing information:

- Which routes still require the same piece.
- Entry count after hazards, status, weather, priority, and recovery.
- Whether the current turn creates a backup answer.
- Whether the boss can intentionally lure, trap, poison, or chip the shared
  answer.
- Whether spending the answer now creates an immediate forced win.

Lesson: "we have an answer" is incomplete if multiple routes spend the same
answer. Count the answer budget, not the isolated one-on-one.

## Drill 026: Route Switch-In Targeting Versus Active Autopilot

Source policy: `STP-031`.

Public state A:

- Our active threatens the opposing active enough to force or heavily
  incentivize a switch.
- The expected switch-in is the main blocker to our winning route.
- The active's stay-in branch is survivable or already covered.

Expected policy A: target the switch-in. Use the status, coverage, phaze,
double, hazard, or pivot that damages the route blocker more than the active.
The answer must name the switch-in and the stay branch.

Public state B mutation:

- The active can stay and use setup, recovery, spin, phazing, trapping, or a KO
  that creates a worse route.
- The predicted switch-in is plausible but not forced.

Expected policy B: cover the active first. Prediction loses to immediate route
catastrophe.

Public state C:

- Boss transfer: a Gym Leader Lab boss has the route blocker in back, but local
  AI evidence does not support a switch from the current active.

Expected policy C: do not import human switch prediction. Use this rule only if
the AI switch branch is supported by public state or trace/source behavior.
Otherwise, target the route blocker when it becomes active and choose the move
that covers the current boss route now.

Answer-changing information:

- Whether the opponent or boss is actually incentivized and able to switch.
- The active's best stay-in punish.
- Whether the expected switch-in is already statused, chipped, or no longer a
  route blocker.
- Whether the predicted move exposes an irreplaceable answer if wrong.
- Local AI trace/source evidence for switching.

Lesson: switch-in targeting is not fancy prediction. It is route targeting
only when the stay branch is priced.

## Drill 027: Entry Method Versus Manual Switch Autopilot

Source policy: `STP-009`.

Public state A:

- A player Pokemon cleanly answers the boss route if it enters without damage,
  status, trap, lock, hazard tax, item loss, or PP loss.
- A manual hard switch gives the boss the exact damage, status, setup,
  recovery, trap, or lock branch that breaks that answer's job.
- Another move can create entry through a KO, forced recovery, forced lock,
  phazing/Haze turn, controlled sack, or soft pivot.

Expected policy A: do not hard switch. Choose the move that creates the entry
method, or shorten the route if no clean entry exists. The answer must name the
route piece, bad hard-switch branch, entry method, and after-entry action.

Public state B mutation:

- The answer survives hard switch with enough HP, status, PP, and item state to
  perform its required job.
- Waiting to create a cleaner entry gives the boss a worse setup, status,
  weather, hazard, or recovery route.

Expected policy B: hard switch can be correct. Entry perfection loses to
immediate route catastrophe.

Public state C:

- The only possible entry method is a controlled sack or trade.
- The sack piece has no remaining unique role, or its role is already
  duplicated.
- The clean entry creates a forced denial route or a winning route.

Expected policy C: sack or trade for entry is legal only with target, lost
role, beneficiary, and next move named.

Answer-changing information:

- Whether the route piece is a hard-switch answer, free-entry check, or revenge
  check.
- Damage, status, hazard, trap, lock, item, and PP cost of the manual switch.
- Whether a forced turn, KO, recovery turn, lock, phaze, soft pivot, or sack
  creates entry.
- Whether delaying entry lets the boss start a worse route.
- What the route piece does immediately after entry.

Lesson: preserving the answer in the back is not enough. The plan must create
the entry state where the answer still functions.

## Drill 028: Variance Budget Versus Lucky-Line Autopilot

Source policy: `STP-032`.

Public state A:

- Our current route is ahead or stable.
- A powerful move wins faster but introduces a miss, crit exposure, full
  paralysis, Quick Claw, Focus Band, damage-roll, sleep-turn, secondary-effect,
  or prediction coinflip branch.
- A steadier move wins one turn slower while preserving the same route.

Expected policy A: reduce variance. Choose the steadier line unless the faster
line crosses a route threshold the slower line cannot reach. The answer must
name the variance branch it removed.

Public state B mutation:

- The stable route is gone. Safe play only delays a losing loop.
- A high-variance move creates the only named comeback route: opponent miss,
  secondary effect, Focus Band fail, Quick Claw fail, crit, or damage roll.

Expected policy B: accept forced risk, but label it as forced risk. The answer
must name the chance branch, the route it opens, and the next state if it hits.

Public state C:

- The apparent KO depends on bypassing a public item or variance branch, such
  as Focus Band or Quick Claw.
- If the branch triggers, the attacker either remains safe or loses an
  irreplaceable future job.

Expected policy C: do not call the KO guaranteed. Either cover the survival /
turn-order branch, or choose a different line if the branch costs the route.

Answer-changing information:

- Whether we are ahead, stable, losing slowly, or already forced into risk.
- Whether a steadier move preserves the same route.
- Which piece is exposed if variance goes wrong.
- Whether the high-variance line has a concrete follow-up.
- Local move accuracy, crit behavior, damage rolls, Quick Claw, Focus Band,
  sleep, status, and boss AI incentives.

Lesson: variance is not good or bad in isolation. Strong play removes
unnecessary variance while winning and accepts purposeful variance only when no
non-variance route remains.

## Drill 029: Delayed Effect Versus Current-Turn Autopilot

Source policy: `STP-033`.

Public state A:

- Future Sight, Perish Song, Leech Seed, Bide, trapping damage, or another
  delayed effect is active.
- The current one-on-one looks safe if judged only by this turn.
- On the resolution turn, the delayed effect can combine with damage, Pursuit,
  hazards, trap state, sleep, recovery denial, or forced switching to break an
  irreplaceable answer.

Expected policy A: plan around the resolution turn. Choose the move that keeps
the required answer off the bad landing turn, creates a safe pivot, forces the
delayed-effect user out, or shortens the route before the clock resolves.

Public state B mutation:

- We can start a delayed effect now, but the setup turn gives the boss free
  recovery, spin, setup, Haze, trapping, or a KO.
- The delayed effect can be pivoted into an expendable Pokemon or reset cheaply.

Expected policy B: do not start the delayed effect just because it looks clever.
Use immediate pressure, denial, or preservation unless the resolution turn has
a named payoff.

Public state C:

- The delayed effect is ours and will force the opponent to cover two threats
  on the same future turn.
- The user no longer has a more urgent job and the payoff creates safe entry,
  forced recovery, a KO threshold, or a route-blocker removal.

Expected policy C: the delayed effect can be best. The answer must name setup
cost, resolution turn, target/landing active, and the converting follow-up.

Answer-changing information:

- Exact countdown / landing turn and whether switching resets it.
- Which side controls the active Pokemon at resolution.
- Whether the effect stacks with current damage, hazards, Pursuit, trap,
  recovery, or status.
- Whether an expendable pivot can absorb or reset the effect.
- Local Future Sight, Perish Song, Leech Seed, Bide, trapping, and AI switching
  mechanics.

Lesson: delayed pressure is a turn ledger, not flavor. The right move is the
one that owns the future resolution turn.

## Drill 030: Boss AI Prior Versus Route Coverage

Source policy: `STP-034`.

Public state A:

- A current, state-matched trace or source note says the boss is likely to use
  one move.
- Another legal public move is less likely but would immediately damage the
  player's main route or irreplaceable answer.
- One player response covers both; another response hard-punishes only the
  likely move.

Expected policy A: choose the route-covering response unless the hard punish
creates a forced win or the wrong branch is tolerable. The answer must separate
likely AI move from worst route move.

Public state B mutation:

- The trace is first-decision-only, stale, or from a failed manifest/hash
  audit.
- The boss's roster route and public moves still create several plausible
  branches.

Expected policy B: downgrade the trace to a historical prior. Use roster route
plus worst plausible branch, not "the AI always clicks X."

Public state C:

- The boss is known to have fixed or adaptive opener behavior from current
  source/trace evidence.
- The user's lead or first move must preserve answers to the boss's later
  routes, not merely win the captured opening click.

Expected policy C: price the fixed/adaptive opener as an opening route, then
choose the move that keeps the later answer map intact.

Answer-changing information:

- Whether the trace is current, state-matched, first-decision-only, or stale.
- Score gap or near-tie behavior if source evidence exposes it.
- Boss roster route and remaining legal moves.
- The move that most damages the player's plan if chosen.
- Whether human-style switching, bluffing, or double-switching is supported by
  local AI evidence.
- Which player piece becomes irreplaceable after the predicted branch.

Lesson: boss prediction is not human mind-reading and not a script. It is a
weighted prior that must stay subordinate to route coverage.

## Drill 031: Item Removal Versus Clever-Button Autopilot

Source policy: `STP-035`.

Public state A:

- Opponent or boss anchor holds Leftovers, Mint Berry, Focus Band, Choice item,
  Life Orb, type-boost item, or another route-supporting item.
- We can remove, consume, or route around the item this turn.
- The item supports a live route: recovery loop, one-shot status cure, survival
  branch, damage threshold, lock exploitation, setup safety, or endgame clock.
- The item-control user is not needed for a more important future answer, or
  the route opened is stronger than the lost job.

Expected policy A: item removal / consumption rises. The answer must name
item, route supported, user cost, and converting follow-up.

Public state B mutation:

- The target is about to faint, the item does not change any threshold, or a
  later boss anchor has the item that matters.
- The item-control user is an irreplaceable answer or already holds an item
  needed later.

Expected policy B: do not press item control just because it is available.
Attack, preserve, switch, or target the real item holder.

Public state C:

- The boss has item-control or item-supported pressure, but local AI trace or
  source evidence does not support the item move in this state.
- Another legal move is the worse route move.

Expected policy C: treat the item branch as possible but not dominant. Cover
it only if severity and cost justify it, or if current source/trace evidence
makes it likely.

Answer-changing information:

- Exact held item and whether it is still active.
- Whether Thief can legally steal: user has no item, target has non-mail item.
- Which route the item supports.
- What follow-up converts after removal or consumption.
- Whether the item-control user loses an irreplaceable role.
- Local item mechanics and boss AI evidence.

Lesson: item removal is a discount on a future route. It is progress only if
the next state spends that discount before the opponent stabilizes elsewhere.

## Drill 032: Staged One-Time Trade Versus Low-HP Autopilot

Source policy: `STP-025`.

Public state A:

- A one-time trade is available: Explosion, Self-Destruct, Destiny Bond, Perish
  lock, Focus Band survival cash-out, or a controlled sacrifice.
- The active user is low or has mostly finished its original job.
- The current target is valuable, but an immunity, protection, phazer, survival
  item, faster KO, or alternate blocker still exists.
- The trade user still has one support job that may matter: spin, phaze, sleep,
  status, hazard pressure, scouting, or safe-entry creation.

Expected policy A: preserve or use the remaining support job unless the trade
removes the actual route blocker now and the blocker branch has been priced.
Low HP alone is not expendability.

Public state B mutation:

- The immunity / protection / survival branch is gone or too costly for the
  opponent.
- The target is the route blocker, not merely a good Pokemon.
- The user's remaining job is replaceable or already spent.
- The next converter or forced endgame is named.

Expected policy B: the one-time trade rises. The answer must name route opened,
lost role, blocker cleared, and the next Pokemon or move that converts.

Public state C:

- A previous one-time trade was correct and simplified one route.
- A second one-time trade is available immediately.
- The board now has a different live route or different irreplaceable piece.

Expected policy C: rebuild the route map before pressing the second trade. The
previous trade being good does not make the next trade good by momentum.

Answer-changing information:

- Whether a Ghost, Protect, Substitute, Endure, Focus Band, faster KO, phazer,
  or immunity branch is still live.
- Whether the target is the actual route blocker.
- What job the trade user still performs if preserved.
- Which piece converts after the trade.
- Local execution order, type/passive, protection, item, and AI evidence.

Lesson: one-time trades are staged around blocker maps. "Low HP, click boom"
is a slogan; "blocker gone, user job spent, converter ready" is a policy.

## Drill 033: Retaliation Punish Versus Damage Autopilot

Source policy: `STP-036`.

Public state A:

- Boss active has Counter, Mirror Coat, Bide, Destiny Bond, or another
  retaliation move.
- The player's strongest attack is in the relevant category and would deal
  heavy damage but not verified lethal damage.
- The attacker is still needed for a later route.
- The boss also has ordinary coverage, recovery, setup, or weather that can
  punish passive avoidance.

Expected policy A: do not choose damage by base power alone. Price category,
speed/order, KO range, retaliation legality, and what the boss does if it
attacks instead. Avoiding the punish is correct only if the alternative still
changes the route.

Public state B mutation:

- Public damage evidence says the attack KOs before the retaliation user can
  act.
- The next opposing route after the KO is covered.

Expected policy B: direct damage rises. A retaliation move that cannot resolve
after the target faints should not scare the policy away from a route-ending
KO.

Public state C mutation:

- The non-retaliation move avoids Counter or Mirror Coat but is weak chip.
- The boss's ordinary attack puts the user's only remaining answer below its
  next-job threshold.
- The strong attack would at least force a trade or shorten a losing route.

Expected policy C: avoiding the punish is not enough. Choose the move that
keeps a live route, even if that means accepting risk or spending a lower-value
piece first.

Answer-changing information:

- Exact retaliation move and its category/timing requirements.
- Whether the attack KOs before the retaliation user can act.
- Speed relation, priority, and whether the opponent has already acted.
- Whether the attacker is irreplaceable after this turn.
- What the boss gains if it attacks, recovers, sets weather, sets a screen, or
  sets up instead of using the punish move.
- Local AI trace/source evidence for the retaliation branch.

Lesson: retaliation moves price damage by route cost. "Strong attack" and
"avoid the punish" are both incomplete until the next state is named.

## Drill 034: Known-Set Threatlist Versus Lead-Matchup Autopilot

Source policy: `STP-037`.

Public state A:

- Boss roster is known before battle.
- The obvious lead plan beats or pressures the most likely opener.
- A backline boss Pokemon has a known route that can win if the lead answer is
  slept, paralyzed, chipped below threshold, or spent too early.
- The player has only one stable answer to that backline route.

Expected policy A: do not approve the lead plan until the backline threat has
a reasonable play line. Preserve the shared answer, change the lead, or label
the matchup as forced risk with mitigation.

Public state B mutation:

- The player has a second verified answer or a route that removes the backline
  threat's blocker before it enters.
- The lead plan wins the opener while preserving the separate answer.

Expected policy B: the aggressive lead rises. The answer must name why the
former glaring weakness is now covered instead of merely saying the lead
matchup is good.

Public state C mutation:

- The type chart says the proposed answer resists or is immune to the boss's
  main STAB.
- The boss set has coverage, recovery, status, hazards, or partner support
  that can still break or bypass that answer.
- The player's team can survive the boss threat but may not be able to break
  its defensive set before recovery, Rest, or hazards take over.

Expected policy C: keep the threat on the list. Type synergy is only the first
filter; the answer must survive the set and the team must have a conversion
route through the defensive or utility plan.

Misty-shaped public card:

- Misty can open Politoed, Starmie, or Quagsire.
- Politoed threatens Hypnosis / Rain Dance.
- Starmie threatens Recover plus rain-accurate Thunder pressure.
- Quagsire threatens Curse / Earthquake / Surf / Rest.
- Lapras can extend rain, and Lanturn can paralyze a speed-reliant route.
- Our proposed lead pressures Politoed but is also the only verified Starmie
  and Lapras answer.

Expected Misty policy: reject a Politoed-only opening script. The pre-battle
plan must say how Starmie, Quagsire, Lapras, and Lanturn are handled if the
lead is slept, paralyzed, or chipped. If no stable answer exists, recommend a
different lead or call the fight forced risk.

Answer-changing information:

- Whether the boss opener is fixed or adaptive.
- Exact boss moves, items, and local AI opening policy.
- Whether the player has redundant answers to the severe backline route.
- Damage and speed evidence for the alleged answer.
- Whether local type-chart/passive evidence changes the answer.
- Whether a lower-variance two-turn route exists.
- Whether the threat is offensive, defensive, utility, hazard, or core-based.

Lesson: known roster knowledge is valuable only if it prevents the plan from
losing to a known route. A good lead matchup is not a good battle plan when it
spends the only answer to the next boss threat.

## Drill 035: AI Move-Bias Loop Versus Safe-Switch Autopilot

Source policy: `STP-038`.

Public state A:

- Boss active has one move that likely KOs or heavily threatens our current
  active.
- We have a teammate immune to or strongly resistant to that expected move.
- The boss has a second coverage/status/speed-control move that threatens the
  switch-in.
- Our original active can re-enter safely on that second move.
- The repeated cycle drains a scarce move PP or burns a finite weather/status
  clock that matters to the route.

Expected policy A: the switch loop is plausible. The answer must name the AI
move-likelihood evidence, both sides of the loop, what PP/clock is being
drained, and the conversion after the loop.

Public state B mutation:

- The switch-in resists the expected move once, but repeated entries expose it
  to hazards, burn/freeze/paralysis, Pursuit, trapping, or critical-hit range.
- The PP being drained is abundant or not route-relevant.
- The boss's second-best move is still plausible under local weighted scoring.

Expected policy B: do not call the switch safe just because the first move is
resisted. Pivot once if it creates a route, then attack, recover, status, or
preserve instead of looping.

Public state C mutation:

- The AI move-likelihood evidence is from generic Maison behavior, not the
  current Gym Leader Lab source/trace/state.
- Local boss route data says the boss may choose speed control, setup denial,
  weather, or anti-loop status over raw damage.

Expected policy C: downgrade the prediction. The answer should cover the
worst plausible local branch or ask for the minimum trace/source evidence if
the loop is the only winning route.

Answer-changing information:

- Boss move scores, trace top-3, or source-backed AI tendency for the current
  state.
- Exact PP of the move being drained.
- Hazard layers, Pursuit/trap state, weather turns, and secondary-effect risk.
- Whether both loop members remain useful after chip or status.
- What move or setup opportunity converts after the loop succeeds.

Lesson: AI move bias can make switching powerful, but a switch loop is a route
tool, not a type-chart reflex. The loop must survive the second move and cash
out into progress.

## Drill 036: Minimum Sufficient Boost Versus Greedy Setup

Source policy: `STP-008`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Our active has `Swords Dance` plus a reliable attack.
- The boss active survives the unboosted attack, cannot KO or status through
  one setup turn, and the +2 attack forces either a KO or a Rest/recovery turn
  that gives our next route clean entry.
- The boss has a later backup that is also pushed into range by the first
  boost.

Expected policy A: set up once. The answer must name the route the boost
changes and the exact cash-out move after the boost.

Public state B mutation:

- Same position after the first boost.
- The boosted attack now KOs the active or forces the recovery turn the route
  wanted.
- A second Swords Dance does not change the next target's threshold, while the
  boss can phaze, Haze, Encore, status, heal, or revenge into range if given a
  free turn.

Expected policy B: attack or use the route-cash-out move. Continuing setup is
greedy and should be rejected unless the answer names a new breakpoint crossed
by the second boost.

Public state C mutation:

- Same original board, but the unboosted attack already KOs the active and the
  boss replacement threatens setup, weather, priority, or status if it receives
  a free switch after our setup turn.

Expected policy C: attack now. Setup is not better when the immediate move
already removes the blocker and the boost does not survive the next public
branch.

Public state D mutation:

- The setup move is `Dragon Dance`, and the planned cash-out move may use the
  user's lower offensive stat under the romhack's Gen 2 category rules.
- Local mechanics evidence for the affected stat, move category, and damage
  threshold is missing.

Expected policy D: cap confidence or ask for the missing mechanics/damage
evidence before calling Dragon Dance the route. Local docs say Dragon Dance
raises the user's current higher offensive stat plus Speed, so the answer must
not assume a modern plain Attack boost if that affects the move.

Answer-changing information:

- Exact damage before and after the next boost.
- Whether the boss has phazing, Haze, Encore, status, recovery, priority, or a
  lethal hit.
- Whether the next boss Pokemon still survives after the current boost.
- Local stat-stage, move-category, and Dragon Dance behavior.
- Whether the setup user is still an irreplaceable answer after spending HP.

Lesson: setup is a threshold tool. The first boost can be correct while the
second boost is a blunder; cash out when the route is live.

## Drill 037: Foresight Ladder Versus Good-Looking Turn

Source policy: `STP-039`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Our active can hit the boss active for relevant but non-decisive damage.
- The boss active can Recover, Rest, set weather, set hazards, or pivot to a
  backline threat after taking the hit.
- We have a switch, status move, hazard move, or breaker entry that does less
  this turn but creates a route step next turn.

Expected policy A: do not recommend the damage move unless it forces a concrete
next step. Prefer the move that creates the clearest route ladder: safe entry,
forced recovery, status clock, hazard punishment, setup denial, or blocker
removal.

Public state B mutation:

- The same damage now crosses a threshold: it KOs, forces Rest, prevents
  Recover from escaping the cycle, or puts the target into confirmed hazard /
  priority range.
- The follow-up after the hit is known and does not expose an irreplaceable
  piece.

Expected policy B: attack rises because the local value now has a route ladder.
The answer must name the next board and the follow-up, not just "take damage."

Public state C mutation:

- A low-HP teammate can stay in for one more attack.
- That attack is not guaranteed to KO, force recovery, burn scarce PP, create
  safe entry, or put the target into a relevant range.
- The teammate still has a later route job: sleep absorber, priority range,
  phazer, spinner, status user, sack for clean entry, or one-time trade.

Expected policy C: preserve or reposition. Do not sacrifice for an extra attack
unless the extra attack is guaranteed to matter to the route.

Public state D mutation:

- The boss has an immediate setup, KO, status, or recovery route that becomes
  irreversible if not denied now.
- The denial move has no elaborate long-term ladder, but it stops that route
  without spending an irreplaceable future answer.

Expected policy D: deny the live route now, then re-score. Foresight does not
mean ignoring emergencies; it means knowing which emergency decides the future.

Answer-changing information:

- Whether the hit crosses a KO, Rest, recovery, hazard, priority, or PP
  threshold.
- Whether the current active still has a later route job.
- Whether the alternative creates a safe entry or only delays.
- Whether the boss's next route is immediate, accumulating, or endgame-only.
- Local damage/type/passive evidence for any claimed threshold.

Lesson: a good-looking turn is not enough. Strong advice names the next state
and the route after it.

## Drill 038: Encore Target Versus Safe-Looking Support

Source policy: `STP-040`.

Public state A:

- Mechanics: `romhack_gym_leader_lab`.
- Boss active has Encore and can plausibly move before the player's current
  active.
- The player wants to click hazards, setup, recovery, screen, Protect-style
  scouting, or another move that does not immediately deny the boss route.
- If that move is Encored, the boss has a concrete follow-up: Rapid Spin,
  screen support, receiver entry, recovery reset, phaze cycle, or setup.

Expected policy A: reject the passive move unless being locked still advances a
named route. Prefer attack, pivot, status, direct denial, or a support move that
stays valuable under Encore. The answer must name the exact locked move and the
boss follow-up it enables.

Public state B mutation:

- The same support move now creates immediate route value even if repeated: it
  denies the boss's only live route, forces a KO/Rest threshold, or the Encore
  user cannot exploit the lock before being forced out.

Expected policy B: the support move can remain acceptable. Do not treat Encore
as an automatic veto; show why the locked sequence is tolerable or beneficial.

Public state C mutation:

- The player has Encore, and the boss's last executed move was recovery,
  hazards, setup, screen, phazing, or a low-damage move with PP remaining.
- The player's follow-up after the lock is available and does not expose an
  irreplaceable piece.

Expected policy C: Encore rises only if the follow-up is named: safe entry,
setup, hazard, healing, forced KO, or endgame simplification. "Encore for tempo"
is not enough.

Public state D mutation:

- The boss has Encore, but the last move is invalid locally, missed Encore would
  not matter, the target is already Encored, the move has no PP remaining, or
  switching out would surrender the more important route.

Expected policy D: do not overplay Encore fear. Use local legality and route
costs instead of treating the word Encore as a generic stop sign.

Answer-changing information:

- Exact last executed move and whether it is legal for local Encore.
- Speed order and whether Encore can force the last move this turn.
- Remaining PP of the last move.
- Whether the locked move remains productive.
- Boss follow-up route after the lock.
- Switch cost under hazards, status, screens, and current HP.

Lesson: Encore control is not "avoid support moves." The real policy is to
avoid donating an exploitable last move, or to use Encore only when the forced
move creates a named route.

## Drill 039: Paused Converter Versus Dead-Route Panic

Source policies: `STP-006`, `STP-023`, `STP-027`, `STP-029`.

Expert source shape: `reviews/2026-05-13_smogtours-gen2ou-933547.md`.

Public state A:

- Format: vanilla GSC strategic review.
- Our planned converter has been statused, forced to Rest, or repeatedly
  checked by an opposing anchor.
- The converter still has recovery, PP, matchup value, and a support path if
  teammates can keep the blocker map busy.
- The current turn offers a tempting short-term attack, trade, or handoff to a
  backup route.

Expected policy A: classify the route as paused, damaged, live, or dead before
changing plans. Preserve or support the converter if the denial can still be
covered and the remaining blockers can be worn down, forced to Rest, spun,
trapped, or traded later. Do not spend the converter just because it is not
winning this turn.

Public state B mutation:

- The same converter is statused or asleep, but its required support has failed:
  the spinner cannot keep hazards off, the phazer remains healthy, the blocker
  cannot be removed, or the recovery/PP path is gone.

Expected policy B: hand off or shorten the route. Preserving a converter after
its required resources are gone is attachment to a dead plan, not long-term
thinking.

Public state C:

- A long hazard, spin, Rest, or pivot loop appears to create no visible
  progress.
- The loop is keeping the opponent's answer map stretched while preserving the
  planned converter's HP, PP, status reset, or entry condition.

Expected policy C: the loop can be correct only if it has a named protected
route. Count what the loop preserves and what it pressures: PP, hazards,
recovery timing, reveal state, chip thresholds, entry access, or blocker
fatigue.

Public state D:

- The opponent's loop creates the same surface no-progress pattern, but it
  heals the blocker, removes hazards, burns our PP, or chips the preserved
  converter's support faster than we can convert.

Expected policy D: break the loop with direct pressure, route handoff, trade,
or a higher-risk line. Waiting is legal only inside a contained winning loop.

Answer-changing information:

- Which converter actually wins the planned endgame.
- Whether the converter's HP, PP, recovery, status state, and entry method are
  still sufficient.
- Which blocker is denying the route and how it can still be removed or taxed.
- Whether the current loop preserves our route or the opponent's reset.
- What concrete observation proves the route has become dead.
- Local mechanics for Rest, Sleep Talk, hazards, spin, status reset, items,
  trapping, and boss AI if transferred to Gym Leader Lab.

Lesson: "not converting now" is different from "not a win condition." Strong
advice preserves a paused route only while the support ledger still exists, and
hands off as soon as evidence says the route is dead.

## Drill 040: Reset Hub Versus Damage Autopilot

Source policies: `STP-013`, `STP-019`, `STP-021`, `STP-028`, `STP-029`.

Expert source shape: `reviews/2026-05-13_smogtours-gen2ou-902727.md`.

Public state A:

- Format: vanilla GSC strategic review.
- The opponent has a recovery, cleric, screen, spin, or RestTalk hub that keeps
  undoing visible progress.
- Direct damage into the active target looks reasonable, but the hub can heal,
  cure status, reduce the damage category, remove hazards, or reset the route.
- Our side has one or more ways to attack the reset function: hazards, phazing,
  item removal, status timing, direct KO pressure, or a one-time trade.

Expected policy A: stop grading only the current HP bar. Name the reset
function, then choose the move that breaks or taxes that function. Direct
damage is best only if it crosses a recovery, KO, forced-switch, Rest, or
trade threshold before the hub resets it.

Public state B mutation:

- Hazards are active, a phazer or forced-switch move survives the public
  punish, and the opponent's reset pieces have prior chip or limited recovery
  turns.

Expected policy B: forced switching rises because the reset hub is now paying
an entry ledger. The answer must name which dragged targets are being taxed and
what happens if the hub enters again.

Public state C mutation:

- The same phaze or hazard plan exists, but the opponent can spin for free,
  Heal Bell / screen / Recover faster than the tax accumulates, or the forced
  target map gives the opponent a better route.

Expected policy C: break the loop, pressure the spinner or cleric directly,
  remove the item, trade for the reset hub, or hand off. Repeating the external
  clock is bad when the clock belongs to the opponent.

Public state D:

- A one-time trade can remove the reset hub, but the trade user still has a
  live future job or the target is only one of several redundant reset pieces.

Expected policy D: trade only if the reset function removed is the route
  blocker and the lost role is accounted for. Do not explode, Destiny Bond, or
  sacrifice merely because the target is annoying.

Answer-changing information:

- Which reset function is live: recovery, cleric cure, screen, spin, RestTalk,
  phazing, Protect, weather, or item recovery.
- Whether hazards or another external clock are active and retained.
- Whether forced switches drag targets that matter or only give free entries.
- Whether a one-time trade removes the reset function or a replaceable piece.
- Whether our control user is on an HP, poison, PP, or status deadline.
- Local romhack mechanics for screens, cures, Rapid Spin, phazing, items,
  Explosion, RestTalk, and type/passive behavior.

Lesson: a reset hub is a system, not a wall. Strong advice identifies the
reset function and attacks that function with the smallest move that converts.

## Drill 041: Information Boundary Versus Team-Preview Autopilot

Source policies: `STP-012`, `STP-034`.

Local source anchors: `boss_turn_advice_template.md`,
`pre_battle_route_sheet.md`, `romhack_deltas/boss_opening_policy.md`, and
`docs/agent_navigation/subsystems/boss_ai_logic.md`.

Public state A:

- Role: player-side advisor before a planned Gym Leader Lab boss fight.
- The boss roster and local fixed/adaptive opener policy are known from source.
- The user's team is declared by the user.
- No battle turns have happened yet.

Expected policy A: use the known boss roster and opener policy to build a route
map, choose a player lead, and name abandon conditions. This is allowed
player-side preparation, not symmetrical Team Preview.

Public state B mutation:

- Role: boss AI or boss-AI policy design.
- The player's full team exists in memory or a fixture, but only the active
  player Pokemon and revealed moves are public.
- A move would be best only if the AI secretly knows an unrevealed bench answer
  or hidden player move.

Expected policy B: reject the hidden-info line. The boss AI may use public
state, seen player species, revealed player moves, observed damage/status/
switches, and explicitly allowed source/legal priors only. It must not plan
from the unrevealed player team.

Public state C:

- Role: vanilla GSC replay review.
- The replay log eventually reveals both full teams, but the turn being scored
  happened before some Pokemon or moves were known.

Expected policy C: score the decision from the information available at that
turn. Later reveals can audit whether the line was punished, but they cannot be
used as if the player had Team Preview.

Public state D:

- Role: live player-side boss advice after several turns.
- More player and boss information has become public through switches, moves,
  damage, status, and source-validated mechanics.

Expected policy D: re-plan from the new public state. It is correct to narrow
the route map as information is revealed; it is not correct to pretend the
whole player team was known by the boss from turn 0.

Answer-changing information:

- Which role is being advised: player-side advisor, boss AI, or replay review.
- Which facts are source-known boss data versus public battle state.
- Which player species, moves, items, HP, status, and bench pieces have been
  revealed.
- Whether a local AI helper is allowed to use legal priors or only revealed
  facts.
- Whether a recommendation would change if hidden player-team data were removed.

Lesson: known boss data is not Team Preview. Strong advice names the
information model before route planning, then refuses any line that only works
because hidden player-team knowledge leaked into the decision.

## Drill 042: No-Preview Lead Contact Versus Perfect-Lead Autopilot

Source policies: `STP-010`, `STP-012`.

Expert source: Smogon,
`An Analysis of Leads in GSC OU`.

Public state A:

- Format: vanilla GSC or Gym Leader Lab no-preview transfer.
- Several openers are plausible from metagame frequency or local adaptive-lead
  source.
- One lead hard-wins the most attractive opener but becomes useless or
  catastrophic if the second opener appears.
- Another lead has a lower ceiling into the best matchup but creates contact
  value across the opener field: status, hazard, item removal, phaze/scout,
  forced switch, or safe pivot tempo.

Expected policy A: prefer the lead that keeps the route map playable across
the plausible opener field unless the hard-win opener is route-deciding and the
bad branch is covered. No-preview lead choice is a contact-value problem, not a
perfect anti-lead puzzle.

Public state B mutation:

- The opener is fixed by local source or already revealed by battle state.
- The anti-lead wins that fixed opener without spending the only later answer.

Expected policy B: the focused lead rises. Do not over-generalize no-preview
uncertainty after local source or public state has removed it.

Public state C:

- Role: boss AI.
- The AI would choose an opener or first move differently only because it knows
  the player's unrevealed bench.

Expected policy C: reject that line. Boss AI can use source-fixed/adaptive
opener policy and public player information; it cannot choose a perfect
anti-player lead from hidden player-team knowledge.

Answer-changing information:

- Whether the format actually has Team Preview.
- Whether local source fixes the opener or defines an adaptive opener set.
- Which lead jobs stay valuable in a bad matchup.
- Whether the lead is also the only later answer to a boss route.
- Whether the risky anti-lead branch is covered by a backup route.
- Which player-side facts are public to the boss AI.

Lesson: in no-preview formats, the lead is chosen for robust first-contact
value and later route fit. Perfect counter-lead thinking is only legal after
the opener is source-fixed or publicly revealed.

## Drill 043: Phaze Loop Exit Versus Setup Autopilot

Source policies: `STP-008`, `STP-028`, `STP-029`, `STP-041`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-902619.md`.

Public state A:

- Format: vanilla GSC or Gym Leader Lab no-preview transfer.
- Opponent has a revealed control move such as Roar, Whirlwind, Haze, Encore,
  or Perish timing.
- Hazards or passive damage are active on our side.
- Our setup Pokemon can sit in front of the active attack, but its boosts have
  already been erased once by the control move.
- Re-entering the setup Pokemon gives the opponent another chance to reset the
  boost while the dragged team pays entry damage.

Expected policy A: do not call setup progress merely because the current attack
is walled. Re-score the next boost as a new move. If no new fact stops the next
control move, exit the loop by removing hazards, pressuring the control user,
trapping, forcing recovery, trading, pivoting, or handing off to a different
converter.

Public state B mutation:

- Hazards have been removed or the setup Pokemon is not paying entry tax.
- The control user is now low enough, trapped, asleep, locked, PP-limited, or
  mechanically unable to reset the next boost.
- The boost immediately crosses a KO, recovery-denial, or endgame threshold.

Expected policy B: setup can rise again. The key difference is that the next
boost changes the board instead of replaying the same phaze loop.

Public state C mutation:

- The control user has already completed its route job and can trade itself for
  the setup Pokemon.
- The setup Pokemon is also the only answer to a later cleaner.

Expected policy C: price the one-time trade before setting up again. If the
trade removes the only answer to the backline route, preserve or pivot even if
the visible matchup looks favorable.

Public state D:

- Role: boss AI.
- The boss can see the active player's setup move and the public hazard state,
  but would choose the control move only because it knows hidden player bench
  details.

Expected policy D: the control line is legal only from public evidence: visible
boosts, active matchup, revealed moves, known hazards, damage, status, and
source-allowed priors. Do not let hidden player-team knowledge decide whether
the boss phazes, Hazes, Encores, or trades.

Answer-changing information:

- Whether the format and local source make the control move work in this speed
  and turn-order state.
- Hazard layers and whether the setup Pokemon or dragged targets pay entry
  damage.
- Whether the setup boost crosses a concrete threshold before the reset.
- Control PP, accuracy, immunity, last-Pokemon rules, and Encore/Haze timing.
- Whether the control user can be forced to Rest, KOed, trapped, or traded.
- Whether a one-time trade opens the opponent's backline converter.
- Which facts are public to the boss AI.

Lesson: after a phaze or control reset, setup is no longer a slogan. Strong
advice asks what changes before the next reset; if nothing changes, leave the
loop before it turns the whole team into hazard progress for the opponent.

## Drill 044: Final Trade Target Versus Active-Target Autopilot

Source policies: `STP-003`, `STP-025`, `STP-031`, `STP-042`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-902089.md`.

Public state A:

- The game is simplified to a small endgame.
- We have one final one-time resource: Explosion, Self-Destruct, Destiny Bond,
  Perish timing, Focus Band cash-out, or a controlled sack.
- We also have one remaining converter or wall that can beat some opposing
  pieces but loses to one specific target.
- The active opposing Pokemon is valuable, but a switch-in or backline target
  is the piece our remaining converter cannot beat.

Expected policy A: choose the trade target by final material, not by the active
slot. If the active branch is already covered, target or punish the piece that
blocks the remaining converter. Name the post-trade board before spending the
resource.

Public state B mutation:

- The active Pokemon can immediately heal, KO, set up, phaze, spin, trap,
  status, or trade into a worse route.
- The supposed blocker target is not likely to enter or can still be handled
  by the remaining converter.

Expected policy B: trade, attack, or preserve against the active route instead.
Do not predict a final-material target while the active branch is still losing.

Public state C mutation:

- A previous one-time trade just resolved.
- The next trade is available immediately, but the remaining material has
  changed through a crit, miss, wake, switch, or forced KO.

Expected policy C: rebuild the final-material proof before the second trade.
The previous trade being correct is not evidence that the next trade is still
correct.

Public state D:

- Role: boss AI.
- A final trade looks perfect only if the AI knows an unrevealed player bench
  Pokemon.

Expected policy D: reject the hidden-info trade. Boss AI can trade from public
boosts, HP, status, hazards, revealed moves, observed damage, active matchup,
and source-allowed priors, not from the unrevealed player team.

Answer-changing information:

- Exact remaining material after each trade branch.
- Which target the remaining converter cannot beat.
- Whether the active branch is already covered or still urgent.
- Ghost, Protect, Substitute, Focus Band, immunity, faster KO, and survival
  branches.
- Local move timing, damage, priority, switch behavior, and AI evidence.
- Which player-side facts are public to boss AI.

Lesson: final trades are not aimed at the loudest target. Strong advice proves
the last material map, removes the blocker the remaining converter cannot beat,
and re-scores after every one-time resource is spent.

## Drill 045: Support Contact Versus Damage-Only Autopilot

Source policies: `STP-021`, `STP-022`, `STP-023`, `STP-044`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-904753.md`.

Public state A:

- A low-damage support move is available: Growl, Charm, Screech, Sand Attack,
  Mean Look, Spider Web, Toxic, screen, Rapid Spin, Protect, phaze, Haze, or
  scout.
- The support move does not win the visible one-on-one.
- A later receiver or converter benefits if the support sticks: safer setup,
  forced Rest, lower incoming damage, hazard retention, status clock, or clean
  entry.
- The opponent may have an escape branch such as phazing, Haze, immunity,
  curing, Rest, switching, Protect, or a faster KO.

Expected policy A: support is correct only after naming receiver, support
effect, escape branch, and payoff turn. Do not choose it because it is
generally annoying, and do not reject it because it lacks immediate damage.

Public state B mutation:

- The support target is immune, can immediately Roar/Haze/cure/switch, or KOs
  the support user before the receiver acts.
- No alternative payoff is created by the failed branch.

Expected policy B: abandon or lower the support line. Attack, pivot, preserve,
or use a different control move that actually changes the route.

Public state C mutation:

- The support move appears to fail as a trap or debuff, but it creates a safe
  hazard, spin, switch, recovery, or status-clock turn that a named receiver
  can use later.

Expected policy C: keep the support in the ledger. A move can fail as one route
and still succeed as another, but the new payoff must be named.

Public state D:

- Role: boss AI.
- A support move would be best only because the boss secretly knows an
  unrevealed player bench receiver or hidden player cure move.

Expected policy D: reject the hidden-info support line. Boss AI can use public
active state, revealed moves, observed status/damage, seen species, source
priors, and legal public inference, not unrevealed player-team knowledge.

Answer-changing information:

- The receiver that benefits and the exact future turn it benefits on.
- Escape branches: phazing, Haze, immunity, cure, Rest, switch, Protect, faster
  KO, or item reset.
- Whether support creates a different payoff if the first plan fails.
- Whether the support user is still needed for a later job.
- Local mechanics for trapping, stat drops, status, phazing, Haze, Rapid Spin,
  Protect, and boss AI public memory.

Lesson: support is route material, not decoration. Strong advice asks who
receives the support, how the opponent escapes it, and what future turn becomes
better because the support happened.

## Drill 046: Contained Hold Versus Winning Loop

Source policies: `STP-017`, `STP-023`, `STP-026`, `STP-027`, `STP-045`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-905628.md`.

Public state A:

- Late-game or boss endgame.
- Our defensive or support piece repeatedly contains the visible threats with
  Charm, Growl, other stat drops, RestTalk, Protect, Pursuit, phazing, Haze,
  trapping, recovery, or pivots.
- The opponent can rotate at least two targets, heal, Rest, or collect item
  recovery.
- Our only high-damage converter is low, asleep, statused, PP-limited, trapped,
  recoil-exposed, or otherwise hard to cash out.

Expected policy A: call the position a hold until a conversion endpoint is
named. The answer must identify the finite resource being reduced and the
piece that converts it. If no endpoint exists, attack, trade, force Rest, trap,
count PP, preserve the converter, or admit the loop is only preventing an
immediate loss.

Public state B mutation:

- The same loop also owns a real endpoint: poison, hazards, weather, Perish
  count, sleep turns, scarce PP, denied recovery, forced Rest timing, trapped
  target, or a healthy converter that enters after the loop.

Expected policy B: waiting or repeated containment can be correct. Name the
clock, the contained punish branch, and the action that happens when the clock
expires.

Public state C mutation:

- A one-time trade, risky attack, or recoil move can create the only endpoint,
  but it may also remove the last converter if it fails or trades poorly.

Expected policy C: run the execution gate and final-material proof before
spending it. Do not use the one-time resource just because the loop feels
stalled.

Public state D:

- Role: boss AI.
- The loop looks winning only if the boss knows an unrevealed player bench
  Pokemon, hidden move, item, or PP count.

Expected policy D: reject the hidden-info endpoint. Boss AI can use public
active state, revealed moves, observed damage, status, hazards, seen species,
and legal public inference, not unrevealed player-team knowledge.

Answer-changing information:

- What finite resource is actually shrinking.
- Whether the opponent can reset chip with Rest, item recovery, switching,
  curing, Haze, phazing, or spin.
- Which converter finishes after the loop, and whether it has enough HP, PP,
  status, sleep turns, and recoil budget.
- Whether a one-time trade can execute and leaves winning final material.
- Local mechanics for PP, RestTalk, Pursuit, hazards, items, recoil, trapping,
  and boss AI public memory.

Lesson: contained is not the same word as winning. Strong advice distinguishes
a defensive hold from a loop with a named endpoint.

## Drill 047: Phaze Target Pool Versus Last-Mon Autopilot

Source policies: `STP-008`, `STP-028`, `STP-041`, `STP-046`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-904815.md`.

Public state A:

- Roar or Whirlwind is available.
- Hazards are up, or the opponent is trying to stabilize with RestTalk, setup,
  recovery, or a trapped route.
- The target has at least one living non-active Pokemon available.
- The phazer acts last under the current mechanics.

Expected policy A: phazing can be correct if the dragged target pays a real
cost: hazard damage, sleep-turn loss, recovery denial, setup reset, answer-map
improvement, or forced entry into a bad matchup. Name the target map after the
drag.

Public state B mutation:

- The opponent is on its last Pokemon, or no legal non-active target is public.
- The same hazards or setup pressure are still present.

Expected policy B: do not choose Roar or Whirlwind as route control. Attack,
status if it beats Rest / cure timing, conserve PP, recover, setup, pivot, or
trade. If phazing is suggested, mark it as a mechanics failure unless a
separate payoff is named.

Public state C mutation:

- A legal bench target exists, but the phazing move will act before the target
  under Gen 2 / local timing.

Expected policy C: phazing fails the timing gate. Use direct denial, Haze,
Encore, attack, switch, or sacrifice unless a slower order can be created.

Public state D:

- Role: boss AI.
- The boss would prefer Roar / Whirlwind only because it secretly knows the
  player has or lacks an unrevealed bench Pokemon.

Expected policy D: reject the hidden-info phaze label. Boss AI can use public
state, revealed species, observed switches/faints, and source-allowed memory,
not unrevealed player-team knowledge.

Answer-changing information:

- Confirmed remaining Pokemon and whether any non-active target is legal.
- Local move order, priority, paralysis, Quick Claw-like effects, and Sleep
  Talk call behavior.
- Hazards, poison, sleep turns, setup stages, recovery timing, and the target
  map after a successful drag.
- PP remaining for phazing versus damage / recovery.
- Whether boss AI is using public state or hidden player-team data.

Lesson: phazing is a mechanics-gated control move. It needs timing, a legal
target pool, and a route-improving drag.

## Drill 048: Post-Converter Handoff Versus Dead-Sweeper Panic

Source policies: `STP-006`, `STP-020`, `STP-027`, `STP-047`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-861526.md`.

Public state A:

- Our main converter, breaker, or setup piece has just fainted or been forced
  out.
- Before going down, it removed at least one major blocker, forced recovery, or
  exposed the opponent's final route.
- We still have another closer that can win if remaining blockers are removed
  or entry costs are controlled.
- A utility or one-time resource is available: Rapid Spin, phazing, status,
  Explosion, pivot, recovery, or a controlled sack.

Expected policy A: rebuild the blocker map. Name what the dead converter
removed, name the new closer, and choose the move that delivers that closer.
Utility can be best if it preserves entries, denies hazards, improves the
target map, or removes the remaining blocker.

Public state B mutation:

- The converter died without removing a required blocker, or the new closer is
  too low, statused, PP-starved, walled, phazed, trapped, or entry-denied to
  convert.

Expected policy B: call the handoff fake and move to a backup route. Do not
spend more turns preserving a route whose required closer or blocker-removal
path no longer exists.

Public state C mutation:

- The converter is still alive but preserving it gives the opponent a free
  recovery, hazard, phaze, spin, or setup turn. A teammate can convert better
  after a trade or pivot.

Expected policy C: handoff can happen before the converter faints. Compare the
remaining blocker map, not emotional ownership of the original plan.

Public state D:

- Role: boss AI.
- The handoff looks good only if the boss secretly knows an unrevealed player
  bench Pokemon, item, move, or PP count.

Expected policy D: reject the hidden-info handoff proof. Boss AI may use
public HP, status, hazards, revealed moves, observed damage, seen species,
faints, and legal public inference, not hidden player-team knowledge.

Answer-changing information:

- What blockers the converter actually removed.
- Which teammate is the new closer and what it still needs.
- Current hazards, status, sleep turns, weather, speed, HP, PP, and item state.
- Whether the utility move directly helps the new closer or only feels safe.
- Whether a one-time trade can execute and leaves winning final material.
- Local mechanics for spin, phazing, Explosion, RestTalk, status, hazards, and
  boss AI public memory.

Lesson: a dead converter is not automatically a dead route. Strong advice
rebuilds the blocker map and delivers the next closer.

## Drill 049: Anti-Pass Reset Versus Receiver Endpoint

Source policies: `STP-017`, `STP-044`, `STP-046`, `STP-048`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-861549.md`.

Public state A:

- The opponent has a support source with Baton Pass, screens, boosts, or
  safe-entry support.
- At least one receiver is alive and can convert if the support lands.
- We have phazing, Haze, Encore, status, direct attack, or a sacrifice route.
- The control move can resolve under the current mechanics.

Expected policy A: name the support source and receiver map before choosing
the control move. Resetting is correct when the receiver would otherwise act
with decisive support and no damage endpoint exists yet.

Public state B mutation:

- The dangerous receiver is exposed and in KO or forced-Rest range.
- The control user survives the receiver's return branch.
- The support source can keep restarting if only reset again.

Expected policy B: damage or final trade can outrank another reset. The point
of phazing/Haze/Encore was to reach an endpoint; do not keep resetting after
the endpoint is public.

Public state C mutation:

- The support source is low or vulnerable before it can pass, and removing it
  prevents the chain entirely.

Expected policy C: attack the source if that denies all meaningful receivers.
Do not tunnel on the receiver if the pass can be stopped first.

Public state D:

- Role: boss AI.
- The anti-pass decision depends on hidden player-team knowledge: an unrevealed
  phazer, Haze user, Encore user, receiver answer, item, or move.

Expected policy D: reject the hidden-info proof. Boss AI can use public HP,
status, hazards, revealed moves, observed switches/faints, seen species, and
source-allowed inference, not the unrevealed player team.

Answer-changing information:

- Receiver list, HP, status, Speed, damage, and entry hazards.
- Whether the support source can keep restarting after a reset.
- Phaze/Haze/Encore legality, timing, PP, and target pool.
- Whether direct damage into source or receiver creates a safer endpoint.
- Whether preserving the control user matters for another receiver.
- Local Baton Pass, screen, Quiver Dance, hazard, and AI information rules.

Lesson: anti-pass play is reset plus endpoint. Strong advice knows when to
stop clicking the control move and cash out on the receiver.

## Drill 050: Reset Hub Leak Audit

Source policies: `STP-017`, `STP-027`, `STP-040`, `STP-045`, `STP-049`.

Expert sources: replay reviews
`reviews/2026-05-13_smogtours-gen2ou-861180.md` and
`reviews/2026-05-13_smogtours-gen2ou-741084.md`.

Public state A:

- We have a recovery, cleric, debuff, phaze, spin, screen, Protect, RestTalk,
  or status-reset hub.
- The hub contains the visible active but does little immediate damage.
- The opponent still has at least one live leak: mixed damage, setup,
  Explosion, status, hazard retention, PP pressure, phazing, trapping, or a
  one-time trade.

Expected policy A: call the hub stabilization, not yet a win. Preserve or
deliver the answer to the leak, attack the leak directly, or shorten the game
before the leak breaks the reset loop.

Public state B mutation:

- The major leak branches are fainted, statused, PP-limited, trapped, phazed
  out of value, or otherwise controlled.
- The remaining active route is exactly what the reset hub handles.

Expected policy B: reset moves can become endpoint moves. Recover, Growl,
Charm, Heal Bell, spin, phaze, screen, Protect, or RestTalk can be correct if
they keep the last route from converting and no new leak is introduced.

Public state C mutation:

- The hub is low, poisoned, PP-limited, trapped, forced through hazards, or
  vulnerable to a newly revealed coverage move.

Expected policy C: re-open the leak audit. The hub may need recovery,
preservation, a trade, or a handoff instead of continuing the old reset loop.

Public state D:

- The hub contained the previous active, but the opponent has switched to a
  different revealed leak with a different damage class, phazing route, or
  setup profile.

Expected policy D: stop crediting the old containment line. Re-score the new
active and deliver the correct answer if it can still enter. If the correct
answer loses to the next revealed piece, label forced risk instead of calling
the hub winning.

Public state E:

- Role: boss AI.
- The "no leaks remain" conclusion depends on unrevealed player bench,
  hidden moves, hidden items, unknown PP, or future team knowledge.

Expected policy E: reject the hidden-info conclusion. Boss AI can use public
state, revealed moves, observed damage, seen species, status, hazards, and
source-allowed memory, not hidden player-team data.

Answer-changing information:

- Which leak branches remain and whether they are public.
- Current HP, status, PP, hazards, screens, weather, trapping, and forced
  switch maps.
- Whether reset moves outlast the opponent's setup, damage, or PP.
- Whether direct damage or one-time trade removes the last leak now.
- Local recovery, debuff, cure, phaze, Haze, Encore, spin, item, passive, and
  AI public-memory mechanics.

Lesson: a reset hub is not inherently passive or inherently winning. It wins
only after the leak audit says the opponent has no route through it.

## Drill 051: Surprise Function Reclassification

Source policies: `STP-014`, `STP-017`, `STP-045`, `STP-050`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-891177.md`.

Public state A:

- A familiar defensive species was part of the opponent's route.
- It publicly reveals damage, screen, recovery, trapping, Haze, phazing, spin,
  or another function that changes whether our setup or pivot route works.
- The old plan depended on that Pokemon being passive or standard.

Expected policy A: reclassify by function, not by species. Stop calling it
setup bait if the revealed move changes HP thresholds, PP, status, lock state,
or turn order.

Public state B mutation:

- The opponent uses a move that suggests a possible companion route, such as
  Defense Curl before any Rollout has been shown.
- We have a phaze, Haze, sacrifice, damage, or pivot answer that would punish
  the companion route if it appears.

Expected policy B: preserve the answer and state the inference level. The
companion route is plausible, not proven, unless it has been revealed or the
local source/known roster authorizes it.

Public state C mutation:

- The companion move is now publicly revealed and has started a forced or
  ramping sequence.

Expected policy C: switch from scouting language to route denial. Count the
lock/ramp turn, check Haze/phaze/legal target timing, price a sacrifice or
direct KO, and stop spending flexible turns.

Public state D:

- Role: boss AI.
- The reclassification depends on unrevealed player-team data: hidden moves,
  hidden items, hidden PP, or bench answers.

Expected policy D: reject the hidden-info proof. Boss AI may reclassify from
revealed moves, observed damage, status, hazards, screens, traps, and legal
source memory, not from the player's unrevealed team.

Answer-changing information:

- Which move or damage event was actually public.
- Whether the revealed function changes a named route or only creates chip.
- Whether the old route still has a handoff after reclassification.
- Whether a companion move is proven, inferred, or only legal.
- Local Present, Rollout, Haze, phazing, screen, trap, spin, PP, and AI memory
  mechanics.

Lesson: once a nonstandard function is public, update the route map. Surprise
is not just a reveal turn; it can permanently change what the active Pokemon
is allowed to set up on, ignore, or trade into.

## Drill 052: Accuracy Disruption Endpoint

Source policies: `STP-044`, `STP-045`, `STP-048`, `STP-051`.

Expert source: replay review
`reviews/2026-05-13_smogtours-gen2ou-891112.md`.

Public state A:

- The opponent has used Sand Attack, Smokescreen, Flash, evasion, or another
  accuracy-changing move.
- Our previous plan required one or more accurate hits from the affected
  Pokemon.
- We may have switching, poison, phazing, Protect, PP pressure, setup handoff,
  or direct damage available instead.

Expected policy A: re-score the hit route under current accuracy. Do not keep
the old route by inertia, and do not call the accuracy drop decisive unless it
buys a named endpoint.

Public state B mutation:

- The debuffed Pokemon can switch out without giving up the decisive route.
- A teammate has a cleaner clock, reset, or direct damage line.

Expected policy B: consider the switch as route progress. Clearing the
accuracy drop can be stronger than attacking through a worse reliability map.

Public state C mutation:

- The accuracy move belongs to the boss AI.
- The boss AI's proof that repeating it wins depends on hidden player moves,
  hidden items, or unrevealed bench answers.

Expected policy C: reject the hidden-info proof. Boss AI may price revealed
accuracy stages, observed damage, status, hazards, and legal local memory, but
it cannot use unrevealed player-team data to prove the endpoint.

Public state D:

- The accuracy drop has landed, but the opponent can poison, phaze, Protect,
  heal, switch, or finish with hazards before misses create a payoff.

Expected policy D: treat the drop as support that failed to convert. Switch to
the reliable endpoint or preserve the piece that protects it.

Answer-changing information:

- Which Pokemon currently carries the accuracy or evasion stage.
- Whether switching clears the stage without losing the route.
- The current hit odds after local stage multipliers and move accuracy.
- Whether the next hit or miss changes KO, poison, PP, setup, or switch
  thresholds.
- Local move accuracy, stat-stage reset, phazing/Haze, Protect, PP, item, and
  boss AI public-memory mechanics.

Lesson: accuracy disruption is real public information, but it must still
convert. After the drop, rebuild the route around hit reliability and the
endpoint that actually ends the problem.
