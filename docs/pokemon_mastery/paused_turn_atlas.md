# Paused-Turn Atlas

Status: training index. These are practice prompts drawn from existing reviews
and worked examples. They are not sealed benchmarks.

Use each entry by hiding the expected policy, giving only the public state to
the advisor, and requiring the live-turn answer shape.

## PTA-001: Phaze Before Conversion

Source: `worked_examples/smogtours_935544_phaze_before_conversion.md`

Format: vanilla GSC strategic review.

Skill tested: spend a control move at the route boundary.

Public prompt:

```text
Our active has Roar/Whirlwind/Haze/Encore-style control and survives the public
punish. Opponent has a sleeping anchor or setup attacker active. Hazards,
sleep turns, or answer-map improvement can make a forced switch matter.

Rank: control move / attack / switch / preserve PP.
```

Expected policy: control rises only if it works mechanically, denies the live
route, and the forced reset creates progress. Without those fields, it may only
delay.

Related source-to-policy entries: `STP-001`, `STP-008`.

## PTA-002: Support Delivery Cascade

Source: `worked_examples/smogtours_604744_support_delivery_cascade.md`

Format: vanilla GSC strategic review.

Skill tested: support moves must name a receiver and blocker.

Public prompt:

```text
A support Pokemon can sleep, boost, pass, screen, or create safe entry. A
receiver exists, but the opponent still has blockers and denial branches.

Rank: support move / direct attack / switch / deny the opponent route.
```

Expected policy: support is progress only when the receiver, blocker, public
punish, and post-support route are all named.

Related source-to-policy entries: `STP-002`, `STP-006`, `STP-011`.

## PTA-003: Trap-Lure Contract

Source: `worked_examples/smogtours_604804_trap_lure_contract.md`

Format: vanilla GSC strategic review.

Skill tested: one-time tech should remove the actual route blocker.

Public prompt:

```text
A trap, lure, Destiny Bond, Perish Song, Pursuit, or one-time coverage move can
remove a target. A later converter is blocked by one specific defensive or
support role.

Rank: trap/lure / attack / pivot / preserve the one-time tool.
```

Expected policy: the move is strong only if target, beneficiary, route opened,
role lost, and next blocker are all known.

Related source-to-policy entries: `STP-003`, `STP-007`, `STP-011`.

## PTA-004: Converter Support Ladder

Source: `worked_examples/smogtours_531497_converter_support_ladder.md`

Format: vanilla GSC strategic review.

Skill tested: preserve, prepare, cash out, or abandon a converter.

Public prompt:

```text
We have a planned converter, but it cannot safely win yet. Several support jobs
could make it real: status, hazard, spin, phaze, chip, forced Rest, safe entry,
or sacrifice.

Rank: preserve converter / spend support move / use converter now / hand off to
backup route.
```

Expected policy: the best move completes one missing ledger line. The route is
dead only when the blocker map or entry condition cannot be repaired.

Related source-to-policy entries: `STP-006`, `STP-008`, `STP-011`.

## PTA-005: Late Support Job Preservation

Source: `worked_examples/smogtours_gen3ou_805152_late_support_job.md`

Format: ADV OU transfer review.

Skill tested: low HP is not expendability.

Public prompt:

```text
A support piece is low and cannot perform its original broad role, but may
still have one route-changing action: pass, screen, weather reset, spin, status
absorb, pivot, or sacrifice entry.

Rank: preserve narrow job / use job now / sacrifice / switch to converter.
```

Expected policy: preserve only if receiver, trigger, and route opened are live;
sacrifice only after proving no live receiver benefits or another route is
forced.

Related source-to-policy entries: `STP-007`, `STP-009`, `STP-010`.

## PTA-006: Delayed Explosion Contract

Source: `worked_examples/smogtours_451060_delayed_explosion_contract.md`

Format: vanilla GSC strategic review.

Skill tested: trade timing when the trade user has a recurring job.

Public prompt:

```text
A damaged Pokemon has Explosion/Self-Destruct/Destiny Bond or another one-time
trade. It also still has a live recurring job such as spin, phaze, hazards,
status absorption, or one forced hit.

Rank: trade now / preserve recurring job / use recurring job / switch.
```

Expected policy: trade only when the target is a named route blocker, the lost
job is replaceable or finished, and a post-trade converter exists.

Sleeping-target threshold: when the target is asleep, do not cash out only
because wake risk exists. First ask whether steady pressure or a lower-value
wake absorber covers the branch. Cash out when wake, Rest, Sleep Talk,
Self-Destruct, or preservation would otherwise undo the route.

Constructed regression:
`workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`.

Partial transfer replay:
`workspace/quick_tests/replay_turn_pause_021_cashout_threshold_partial_smogtours-gen2ou-934904_2026-05-14.md`.

Post-oracle receiver regression:
`workspace/quick_tests/selfdestruct_receiver_branch_regression_001_smogtours-gen2ou-934904_2026-05-14.md`.

Fresh receiver transfer:
`workspace/quick_tests/replay_turn_pause_022_receiver_counterplay_transfer_smogtours-gen2ou-935551_2026-05-14.md`.

Related source-to-policy entries: `STP-003`, `STP-007`.

## PTA-007: Hazard Contract Against Will

Source: `worked_examples/will_hazard_retention_stress_test.md`

Format: Gym Leader Lab transfer drill.

Skill tested: set-retain-convert hazard reasoning under romhack mechanics.

Public prompt:

```text
Will has Forretress/Starmie hazard control live. Local Spikes can stack to
three layers and Rapid Spin clears all layers. The player's route may depend on
hazards, but Will may spin, set its own layers, Toxic, Protect, Recover, or
Explode.

Rank: set layer / attack spinner / remove hazards / switch / trade.
```

Expected policy: hazard progress requires set, retain or price removal, and
convert before the layer disappears or Will's special route takes over.

Related source-to-policy entries: `STP-001`, `STP-005`.

## PTA-008: Status Absorber Assignment

Source: `worked_examples/status_absorber_assignment_boss_examples.md`

Format: Gym Leader Lab boss-facing drill.

Skill tested: assign sleep, paralysis, poison, or trap clocks without losing a
unique future job.

Public prompt:

```text
Boss can spread status. One player piece can absorb it, but that piece may also
be the only answer to a later route. Another piece is more expendable but gives
up tempo or entry.

Rank: absorb status / deny status user / attack route blocker / pivot /
shorten game.
```

Expected policy: absorption is correct only if the future job remains
functional, the status turn does not create a larger boss route, and the plan
after absorption is named.

Sleep Clause clause: when the absorbed status is sleep, first price the common
branch where the slept Pokemon switches out immediately and is preserved as
Sleep Clause material. Burning wake turns is correct only if the sleeper's
current board job is better than preserving Sleep Clause, or if the wake route
is itself the plan. A sleeping absorber may still be saved for Explosion,
Spikes, Rapid Spin, phazing, Sleep Talk, a controlled sack, or a wake attack.

Fresh replay exception: if the opponent's active cannot strongly punish the
sleeping Pokemon, or if Explosion/pivot scouting is material, one burned sleep
turn can be acceptable before switching under stronger pressure.

Later-job check: a sleeping Pokemon can still be the correct route piece before
it wakes if Sleep Talk, Heal Bell support, forced-switch absorption, predicted
coverage absorption, wake-and-act timing, or cheaper switches after hazard
removal changes the board.

Cash-out threshold: do not spend Explosion, Self-Destruct, Destiny Bond, or an
irreplaceable attacker into a sleeper only because wake risk exists. Spend it
when the wake move, Rest, Sleep Talk result, or endgame role would otherwise
undo the route; otherwise steady pressure or a wake absorber can be better.

Regression probe: `workspace/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`.

Fresh replay check:
`workspace/quick_tests/replay_turn_pause_018_sleep_clause_absorber_fresh_smogtours-gen2ou-934335_2026-05-14.md`.

Later-job replay check:
`workspace/quick_tests/replay_turn_pause_019_sleeper_later_job_smogtours-gen2ou-934335_2026-05-14.md`.

Constructed regression:
`workspace/quick_tests/sleeping_piece_later_job_probe_001_2026-05-14.md`.

Transfer replay:
`workspace/quick_tests/replay_turn_pause_020_sleeper_transfer_smogtours-gen2ou-935572_2026-05-14.md`.

Cash-out regression:
`workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`.

Related source-to-policy entries: `STP-002`, `STP-009`, `STP-010`.

## PTA-009: Screen Window Or Wrong Category

Source: `worked_examples/live_turn_drills.md#drill-014-screen-window-versus-wrong-category-autopilot`

Format: Gym Leader Lab boss-facing drill.

Skill tested: identify whether a screen turn is a route window, a category
shift, or fake defense.

Public prompt:

```text
Light Screen or Reflect can be set, is already active, or is one turn from
delivering a receiver. The player's current plan may rely on the blocked damage
category.

Rank: deny screen setter / attack through unblocked category / stall screen
turns / preserve answer / setup.
```

Expected policy: count screen turns, name the receiver or payoff, and only keep
attacking into the blocked category if the damage still crosses a route
threshold.

Related source-to-policy entries: `STP-019`.

## PTA-010: Faster Cleaner Or Priority Trap

Source: `worked_examples/live_turn_drills.md#drill-015-faster-cleaner-versus-priority-range`

Format: Gym Leader Lab boss-facing drill.

Skill tested: separate normal Speed control from priority, Quick Claw, Focus
Band, Endure, and next-piece revenge range.

Public prompt:

```text
The player has a faster attacker that can KO if it moves. The boss has a
priority or turn-order exception still live, and the attacker may be needed for
a later route.

Rank: attack / preserve cleaner / use bulkier answer / controlled sack / force
recoil or lock first.
```

Expected policy: "faster" is insufficient. The move is correct only after
priority damage, entry HP, survival items, and the next boss piece fail to
break the route.

Related source-to-policy entries: `STP-020`.

## PTA-011: Status Assignment And Reset

Source: `worked_examples/live_turn_drills.md#drill-016-status-absorber-versus-status-reset`

Format: Gym Leader Lab boss-facing drill.

Skill tested: choose between using status, absorbing status, denying status, or
forcing a cure item / Rest window.

Public prompt:

```text
Status can land this turn, but the target may have a future job, a cure item,
Rest, Safeguard, Sleep Clause, or a status-indifferent route.

Rank: status / absorb status / deny status user / attack threshold / pivot /
preserve status move.
```

Expected policy: status is progress only when the assigned target, future job,
reset map, and value gained before reset are all named.

Related source-to-policy entries: `STP-002`, `STP-021`.

## PTA-012: Support Chain Stop Turn

Source: `worked_examples/live_turn_drills.md#drill-017-support-chain-versus-visible-one-on-one`

Format: Gym Leader Lab boss-facing drill.

Skill tested: judge a support chain by the receiver and the last stop turn, not
by the current support Pokemon's damage.

Public prompt:

```text
A support Pokemon can screen, boost, pass, trap, Encore, or create safe entry
for a later receiver. The current active can damage the support user, but may
also be the only answer to the receiver.

Rank: remove support / preserve receiver answer / deny pass / use control /
chip / set hazard.
```

Expected policy: name the receiver, delivered support, answer after support,
and last denial turn. Slow value loses if the pass makes the receiver
unanswerable first.

Related source-to-policy entries: `STP-019`, `STP-022`.

## PTA-013: Degraded Role Relabel

Source: `worked_examples/live_turn_drills.md#drill-018-degraded-role-versus-throwaway-sack`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: after bad luck or heavy chip, relabel the piece's remaining jobs
instead of following the old plan or sacking it automatically.

Public prompt:

```text
A Pokemon missed, slept, got paralyzed, lost its first target, or took enough
chip that its original role is no longer reliable. It may still have one
route-changing job such as Explosion, RestTalk endgame, pass, phaze, spin,
status, screen, priority, or sack entry.

Rank: preserve narrow job / spend narrow job now / sacrifice / switch to
backup route / continue original plan.
```

Expected policy: name the failed original job, the remaining narrow job, its
target or receiver, and the route it opens. Preserve only if that job is live;
sacrifice only if no remaining job changes the route.

Related source-to-policy entries: `STP-007`, `STP-023`.

## PTA-014: Temporary Disable Cash-Out

Source: `worked_examples/live_turn_drills.md#drill-019-temporary-disable-versus-route-ownership`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: convert freeze, sleep, confusion, recharge, lock, or trap states
before the target resets the position.

Public prompt:

```text
The opponent's key piece is frozen, asleep, confused, recharging, locked, or
otherwise temporarily denied. It may still have Rest, Sleep Talk, item cure,
switch access, or a teammate that can trade for the converter.

Rank: cash out now / preserve converter / deny reset / force trade into a less
important piece / abandon route for backup plan.
```

Expected policy: temporary control is a route discount, not a win. Name the
converter, the cash-out move, the reset branch, and the material that must stay
alive until the route is closed.

Related source-to-policy entries: `STP-002`, `STP-021`, `STP-024`.

## PTA-015: Trade Cascade Remap

Source: `worked_examples/live_turn_drills.md#drill-020-trade-cascade-versus-momentum-autopilot`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: after a one-time resource is spent, rebuild both route maps
before choosing the next trade.

Public prompt:

```text
One Explosion, Destiny Bond, Focus Band survival, phazer, status absorber,
controlled sack, or lure has already been spent. A second one-time trade is
available and looks attractive, but the remaining route map has changed.

Rank: trade now / preserve one-time resource / pivot / use recurring job /
force clearer target first.
```

Expected policy: the next trade is judged only from the new board. Name the
target, lost role, post-trade converter, and uncovered opposing route before
spending another one-time resource.

Related source-to-policy entries: `STP-003`, `STP-007`, `STP-025`.

## PTA-016: PP Budget Or Fake Stall

Source: `worked_examples/live_turn_drills.md#drill-021-pp-budget-versus-empty-stalling`

Format: Gym Leader Lab boss-facing drill.

Skill tested: decide whether PP is the actual route resource or just a vague
stall label.

Public prompt:

```text
A long loop is possible. Recovery, phazing, Haze, Rapid Spin, Rest, or a
low-PP attack may matter, but HP, status, entry access, and hazards may fail
first.

Rank: force scarce PP / conserve scarce PP / attack threshold / pivot for
entry / abandon PP plan.
```

Expected policy: name the scarce move, owner, remaining PP, what forces it,
what conserves it, and what changes at zero. If zero PP does not change the
route, choose a non-PP form of progress.

Related source-to-policy entries: `STP-001`, `STP-017`, `STP-026`.

## PTA-017: Contained Waiting Or Passive Donation

Source: `worked_examples/live_turn_drills.md#drill-022-contained-waiting-versus-passive-donation`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: distinguish a low-effect waiting turn inside a winning loop from
a donated free turn.

Public prompt:

```text
A low-effect move, recovery, repeated pivot, or no-effect hazard click is
available. The opponent may already be losing to poison, hazards, recoil,
weather, screen expiration, Rest sleep, or another external clock.

Rank: wait / recover / pivot / active denial / trade / abandon loop.
```

Expected policy: waiting is legal only if the external clock is named, the
opponent's punish branches are covered, and the irreplaceable answer stays
healthy enough.

Related source-to-policy entries: `STP-017`, `STP-026`, `STP-027`.

## PTA-018: Hazard Contract Or Layer Autopilot

Source: `worked_examples/live_turn_drills.md#drill-023-hazard-contract-versus-layer-autopilot`

Format: vanilla GSC, later-generation transfer, and Gym Leader Lab hazard
drill.

Skill tested: decide whether a hazard turn has set, retain, and convert
covered, or whether it is only generic layer-clicking.

Public prompt:

```text
A hazard can be set, reset, preserved, spun, blocked, or exploited. The layer
may be durable, temporary, already maxed, or immediately removable.

Rank: set layer / pressure spinner / preserve setter / spin / spinblock /
attack threshold / abandon hazard route.
```

Expected policy: name the setter, retention plan, and conversion route. If
retention is gone, convert immediately or change plans. If the side is already
at max layers, classify the hazard click by mechanics before strategy.

Related source-to-policy entries: `STP-001`, `STP-005`, `STP-028`.

## PTA-019: Koga First-Three-Turn Clock Ownership

Source: `worked_examples/koga_first_three_turn_clock_ownership_drill.md`

Format: Gym Leader Lab boss-facing drill.

Skill tested: choose a lead or first move against Ariados by pricing Spikes,
Toxic, and Spider Web into the next two turns, not just the current matchup.

Public prompt:

```text
Koga opens with Ariados: Spikes / Toxic / Leech Life / Spider Web. Tentacruel,
Muk, Nidoking, Umbreon, and Crobat are still unrevealed in back.

Rank: attack Ariados / pivot to absorber / set hazards / use status / setup /
recover-wait / sacrifice for clean entry.
```

Expected policy: classify the proposed active first. If it is expendable and
pressures Ariados before poison or trap matters, attack can own the clock. If
it is the only Nidoking or Crobat answer, do not let early Toxic or Spider Web
turn it into the route casualty. If it is a setup or hazard piece, name the
Tentacruel Rapid Spin / Haze punish before choosing the slow line.

Related source-to-policy entries: `STP-021`, `STP-027`, `STP-028`.

## PTA-020: Board Inheritor After First Route Denial

Source: `worked_examples/live_turn_drills.md#drill-024-board-inheritor-after-first-route-denial`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: after stopping one visible route, identify the next opposing
route that inherits the damaged, statused, or repositioned board.

Public prompt:

```text
The active threat was just checked, phazed, statused, traded with, or forced
out. The answer paid HP, status, PP, item, hazard, reveal, or positioning cost.
The opponent still has at least one meaningful route in back.

Rank: continue old plan / preserve answer / hand off to backup / deny next
converter / trade now / contained wait.
```

Expected policy: name the first route stopped, answer used, cost paid, board
inheritor, and remaining answer before choosing. If the same piece no longer
covers the inheritor, hand off now.

Related source-to-policy entries: `STP-006`, `STP-025`, `STP-029`.

## PTA-021: Shared-Answer Overload

Source: `worked_examples/live_turn_drills.md#drill-025-shared-answer-overload-versus-isolated-matchups`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: detect when multiple opposing routes are spending the same answer
and make the move that preserves, duplicates, or cashes out that answer.

Public prompt:

```text
Two or more opposing routes are answered by the same player piece or resource.
The active route can chip, status, trap, force PP, or reposition that answer
before the later route appears.

Rank: preserve shared answer / create backup answer / attack current route /
trade now / absorb status / sacrifice for clean entry.
```

Expected policy: list every live route the answer still covers and how many
entries or actions remain. Spend it only if the current route is more urgent,
a backup answer exists, or the spend creates an immediate forced win.

Related source-to-policy entries: `STP-009`, `STP-012`, `STP-030`.

## PTA-022: Route Switch-In Targeting

Source: `worked_examples/live_turn_drills.md#drill-026-route-switch-in-targeting-versus-active-autopilot`

Format: competitive singles transfer and Gym Leader Lab boss-facing drill.

Skill tested: decide when to aim status, coverage, phazing, hazards, or a pivot
at the expected route switch-in rather than the current active Pokemon.

Public prompt:

```text
The active opponent is pressured, but a likely switch-in blocks our route. The
stay branch may be safe, dangerous, or unsupported by local AI evidence.

Rank: attack active / status switch-in / coverage switch-in / double-switch /
set hazard / phaze / preserve answer.
```

Expected policy: target the switch-in only when the active stay branch is
covered and the switch-in is route-relevant. Against boss AI, require local
switch evidence before treating human-style switch incentives as likely.

Related source-to-policy entries: `STP-004`, `STP-013`, `STP-031`.

## PTA-023: Entry Method Or Manual Switch Autopilot

Source: `worked_examples/live_turn_drills.md#drill-027-entry-method-versus-manual-switch-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: distinguish a true hard-switch answer from a free-entry check or
revenge check, then create the required entry state.

Public prompt:

```text
A Pokemon answers the boss route only if it enters cleanly. A hard switch may
take damage, status, hazards, trap, lock, item loss, PP loss, or setup pressure
that breaks the job.

Rank: hard switch / create forced entry / soft pivot / controlled sack /
attack now / abandon route.
```

Expected policy: name the route piece, hard-switch failure branch, entry
method, and after-entry action. Hard switch only if it still preserves the
piece's required job or if delaying creates a worse route.

Related source-to-policy entries: `STP-007`, `STP-009`, `STP-030`.

## PTA-024: Variance Budget Or Lucky-Line Autopilot

Source: `worked_examples/live_turn_drills.md#drill-028-variance-budget-versus-lucky-line-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: decide whether to remove variance, accept forced risk, or cover
a public item / turn-order branch.

Public prompt:

```text
The move choice depends on miss chance, crits, full paralysis, sleep turns,
secondary effects, Quick Claw, Focus Band, damage rolls, or a prediction
coinflip.

Rank: safer route / faster high-variance route / forced-risk comeback /
cover item branch / sacrifice for cleaner variance.
```

Expected policy: name route posture first. If ahead or stable, remove avoidable
variance while preserving the route. If losing, accept variance only when safe
play has no concrete winning route and the chance branch has a follow-up.

Related source-to-policy entries: `STP-004`, `STP-023`, `STP-032`.

## PTA-025: Delayed Effect Resolution Turn

Source: `worked_examples/live_turn_drills.md#drill-029-delayed-effect-versus-current-turn-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: plan around the future turn where Future Sight, Perish Song,
Leech Seed, Bide, trap damage, or another delayed effect resolves.

Public prompt:

```text
A delayed effect is active or available. The current turn looks safe, but the
resolution turn may stack with damage, hazards, Pursuit, trapping, recovery
denial, forced switching, or boss setup.

Rank: start delayed effect / deny user / pivot before landing / preserve answer
/ immediate attack / controlled sack / reset clock.
```

Expected policy: name the countdown, landing active, stacked pressure, escape
or reset options, and payoff before choosing. Delayed pressure is correct only
if the resolution turn improves a named route more than the setup turn costs.

Related source-to-policy entries: `STP-017`, `STP-024`, `STP-033`.

## PTA-026: Boss AI Prior Versus Route Coverage

Source: `worked_examples/live_turn_drills.md#drill-030-boss-ai-prior-versus-route-coverage`

Format: Gym Leader Lab boss-facing drill.

Skill tested: use local AI evidence without overfitting to traces or importing
human prediction habits.

Public prompt:

```text
A trace, source note, or route map suggests one likely boss move. A different
legal move or later boss route may punish the user's plan harder.

Rank: cover likely move / cover worst route move / route-covering compromise /
hard punish trace / preserve answer / probe for AI behavior.
```

Expected policy: separate roster route, likely AI move, worst route move, trace
status, and player route before choosing. Current, state-matched traces inform
the prior; stale or first-decision traces do not become scripts.

Related source-to-policy entries: `STP-004`, `STP-012`, `STP-034`.

## PTA-027: Item Removal Or Route Discount

Source: `worked_examples/live_turn_drills.md#drill-031-item-removal-versus-clever-button-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: decide whether stealing, consuming, removing, or routing around
an item actually changes the battle route.

Public prompt:

```text
A held item supports a route: recovery, status cure, survival, damage threshold,
move lock, setup safety, or endgame clock. Item control is available but may
spend a key role or hit the wrong target.

Rank: remove item / consume item / attack threshold / preserve user / target
different holder / ignore item branch.
```

Expected policy: item control is correct only if the item supports a live route,
the user can afford the turn, and the follow-up converts the item loss.

Related source-to-policy entries: `STP-014`, `STP-021`, `STP-035`.

## PTA-028: Staged One-Time Trade Or Low-HP Autopilot

Source: `worked_examples/live_turn_drills.md#drill-032-staged-one-time-trade-versus-low-hp-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: decide whether Explosion, Destiny Bond, Perish Song, Focus Band
cash-out, or a controlled sacrifice should be spent now or held until the
blocker map is clear.

Public prompt:

```text
A low-HP or mostly spent Pokemon has a one-time trade available. The target is
valuable, but blockers, protection, immunity, survival branches, or remaining
support jobs may still matter.

Rank: trade now / preserve support job / attack threshold / scout blocker /
switch to converter / controlled sack for entry / rebuild route map.
```

Expected policy: trade only when the target is the actual route blocker, the
user's lost role is accounted for, the fail branch is priced, and the next
converter or forced line is named.

Related source-to-policy entries: `STP-003`, `STP-007`, `STP-025`.

## PTA-029: Retaliation Punish Or Damage Autopilot

Source: `worked_examples/live_turn_drills.md#drill-033-retaliation-punish-versus-damage-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: decide whether Counter, Mirror Coat, Bide, Destiny Bond, or a
similar punish should change the attack, not merely scare the advisor away from
damage.

Public prompt:

```text
The boss has a retaliation move and ordinary route pressure. The player's
strongest attack may hit the relevant category, but the KO, speed/order, AI
likelihood, and later-route cost are not all solved.

Rank: direct KO / safer category attack / status-control / pivot / controlled
sack / preserve attacker / accept forced risk.
```

Expected policy: attack when the hit KOs or the trade opens the route; avoid
the retaliation only when the avoiding line still changes the state and does
not lose to ordinary coverage or setup.

Related source-to-policy entries: `STP-004`, `STP-032`, `STP-036`.

## PTA-030: Encore Last-Move Lock Or Support Autopilot

Source: `worked_examples/live_turn_drills.md#drill-038-encore-target-versus-safe-looking-support`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: decide whether a support, setup, recovery, hazard, or scouting
move donates an exploitable last move to Encore.

Public prompt:

```text
An Encore user can act after or before the current Pokemon. A passive or
low-immediate-value move looks useful now, but being forced to repeat the last
executed move may give the opponent spin, screen, recovery, setup, receiver
entry, phazing, or cleanup tempo.

Rank: support move / attack / pivot / status-control / use Encore ourselves /
switch to spend lock turns / ignore Encore as illegal or tolerable.
```

Expected policy: name the exact last executed move, local Encore legality,
speed/timing, PP, lock duration, and boss follow-up route. Avoid the support
move when the lock opens a stronger route for the opponent. Do not over-fear
Encore when the last move is invalid, still productive, out of PP, already
locked, or when switching would surrender more route material.

Related source-to-policy entries: `STP-016`, `STP-040`.

## PTA-031: Obvious KO Into Temporary Trade State

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-012-morty-destiny-bond--temporary-control-turn`

Format: Gym Leader Lab boss-facing drill.

Skill tested: decide whether a KO should be delayed, redirected, or taken when
Destiny Bond, Curse, sleep, confusion, Perish-style clocks, or another
temporary control state changes the post-KO route map.

Public prompt:

```text
The boss active is in KO range. The obvious attack may end the current matchup,
but the target can force a trade or the board has temporary-control clocks that
make losing the attacker costly.

Rank: take KO / non-KO control / switch / lower-value sacrifice / stall clock /
status or setup.
```

Expected policy: taking the KO is correct only if the trade state is inactive,
tolerable, or route-winning. If the KO spends the clean answer to a remaining
boss route, choose the line that clears the trade state, uses a lower-value
piece, or preserves the answer. Temporary control is a route discount, not a
license to ignore the remaining map.

Related source-to-policy entries: `STP-024`, `STP-025`, `STP-036`.

## PTA-032: Clock Ownership Or Slow-Control Autopilot

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-013-koga-poison--trap-clock-ownership`

Format: Gym Leader Lab boss-facing drill.

Skill tested: decide whether poison, hazards, trapping, recovery, waiting, or
direct pressure owns the next three turns.

Public prompt:

```text
Either side can create or continue a clock: Toxic, Spikes, Spider Web,
Confuse Ray, Pursuit, Moonlight, Rest, Rapid Spin, Haze, or fast cleanup range.
The current active may be expendable or may be the only answer to a later route.

Rank: attack / pivot / status / hazards / wait / sacrifice / preserve answer.
```

Expected policy: name who benefits if both sides keep playing low-effect moves
for three turns. Slow control is correct only when it damages the right target,
beats recovery/removal, and creates a forced follow-up. Pivot or direct pressure
rises when the clock would land on an irreplaceable answer or when the opponent
can reset the clock before it matters.

Related source-to-policy entries: `STP-013`, `STP-027`, `STP-029`.

## PTA-033: Set-Retain-Convert Hazard War

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-014-jasmine-set-retain-convert-hazard-war`

Format: Gym Leader Lab boss-facing drill.

Skill tested: choose between setting hazards, removing hazards, pressuring the
setter/spinner/phazer, preserving the converter answer, or accepting a trade.

Public prompt:

```text
Both sides can affect hazards. One side can set layers, one side can remove
them, and phazing, forced switches, Explosion, Protect, recovery, or setup can
convert the layer into a route. A key answer may be chipped while the hazard
exchange is happening.

Rank: set hazard / remove hazard / attack setter / punish spinner / preserve
answer / phaze or force switch / sacrifice or trade.
```

Expected policy: split the plan into set, retain, and convert. A layer is
progress only if it is retained long enough to change a route or immediately
creates a threshold before removal. Removing hazards is progress only if it
preserves a concrete answer or denies a phaze/setup/cleanup route. Do not win a
minor hazard exchange while losing the answer that decides the fight.

Related source-to-policy entries: `STP-001`, `STP-005`, `STP-028`, `STP-029`.

## PTA-034: Receiver-First Support Chain

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-015-bugsy-support-chain-into-scyther`

Format: Gym Leader Lab boss-facing drill.

Skill tested: decide whether to attack the support user, preserve the receiver
answer, deny the pass, or abandon slow value when support is about to reach the
real converter.

Public prompt:

```text
A low-damage support Pokemon can pass or create screens/boosts/status that make
a backline receiver harder to answer. The current active can beat the support
Pokemon but may also be the only answer to the receiver.

Rank: attack support / preserve receiver answer / phaze or Haze / status /
set hazards / setup / sacrifice for clean entry.
```

Expected policy: name the receiver, the support being delivered, the stop turn,
and the piece that still answers the receiver after support lands. Denial
outranks slow value when the chain is one turn from becoming unanswerable.
Preservation outranks winning the support one-on-one when the current active is
the only receiver answer.

Related source-to-policy entries: `STP-022`, `STP-023`, `STP-029`.

## PTA-035: Rest-Only Anchor Versus RestTalk Autopilot

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-016-will-slowbro-rest--amnesia-anchor`

Format: Gym Leader Lab boss-facing drill.

Skill tested: decide whether forcing Rest creates progress, and avoid
conflating Rest-only recovery anchors with RestTalk anchors.

Public prompt:

```text
A bulky anchor can boost, attack, and Rest. The current damage may force Rest,
but the player may or may not have a follow-up that converts the sleep turns.
Other boss routes remain and may inherit the board if the anchor resets.

Rank: force Rest / breaker entry / status timing / phaze or Haze / hazards /
pivot preserve answer / continue chip.
```

Expected policy: forcing Rest is progress only if the sleep turns create a
named route: safe entry, setup, phaze/Haze, hazard conversion, status timing,
PP pressure, or KO threshold. Check whether the anchor has Sleep Talk before
assuming it can or cannot act while asleep. If no follow-up exists, preserve the
answer map instead of feeding a reset loop.

Related source-to-policy entries: `STP-017`, `STP-024`, `STP-026`.

## PTA-036: Delayed Hit Resolution Or Current-Turn Autopilot

Source: `worked_examples/boss_live_turn_prompt_cards.md#card-017-will-future-sight--pursuit-resolution-turn`

Format: Gym Leader Lab boss-facing drill.

Skill tested: choose between immediate pressure, scheduled pivot, staying,
sacrifice, healing, or control when a delayed hit will resolve into a Pursuit
or stacked-damage route.

Public prompt:

```text
A delayed hit such as Future Sight is active or can be started. The current
one-on-one has an obvious-looking attack or switch, but the resolution turn may
put the only answer to a later boss route in front of stacked damage, Pursuit,
weather-boosted coverage, hazards, or cleanup range.

Rank: attack delayed-effect user / schedule absorber / stay / pivot / heal /
status-control / sacrifice lower-value piece / ignore as tolerable.
```

Expected policy: judge the move by the resolution turn, not the setup turn.
Name the countdown, the Pokemon expected to be active when the delayed hit
lands, what current attack or teammate entry can stack with it, and whether
Pursuit punishes the escape. Immediate pressure rises before the delayed effect
starts. After it is active, staying, sacrificing, or scheduling a specific
absorber can outrank a clean-looking pivot if that pivot spends the only answer
to the remaining boss route.

Related source-to-policy entries: `STP-003`, `STP-024`, `STP-029`, `STP-033`,
`STP-034`.

## PTA-037: Paused Converter Or Dead Route

Source: `worked_examples/live_turn_drills.md#drill-039-paused-converter-versus-dead-route-panic`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether a denied converter should be preserved, supported,
cashed out, or abandoned for a backup route.

Public prompt:

```text
A planned converter is asleep, statused, checked, forced out, or apparently
inactive. Long hazard, spin, recovery, pivot, or PP loops may be preserving its
future entry, or they may be proving that its route is dead.

Rank: preserve converter / support blocker removal / keep loop / break loop /
cash out converter / hand off to backup / sacrifice for clean entry.
```

Expected policy: classify the route as live, paused, damaged, or dead before
choosing. Preserve or support the converter only if the HP, PP, recovery,
status reset, entry method, and blocker-removal path still exist. Break the
loop or hand off when the support ledger is gone or the loop is preserving the
opponent's reset more than our route.

Related source-to-policy entries: `STP-006`, `STP-023`, `STP-027`, `STP-029`.

## PTA-038: Reset Hub Or Damage Autopilot

Source: `worked_examples/live_turn_drills.md#drill-040-reset-hub-versus-damage-autopilot`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether to keep attacking, force switches, set or retain
hazards, remove an item, trade, pivot, or hand off when a reset hub is erasing
visible progress.

Public prompt:

```text
The opponent has a recovery, cleric, screen, spin, RestTalk, Protect, phaze, or
weather reset function. Direct damage looks useful, but the reset hub may erase
status, reduce the damage category, remove hazards, heal the target, or keep
the same route alive.

Rank: direct damage / set-retain-convert hazard / force switch / pressure
spinner or cleric / item removal / one-time trade / preserve answer / hand off.
```

Expected policy: name the reset function before choosing. Direct damage is
progress only if it crosses a route threshold before the reset. Hazards and
forced switches rise when the entry ledger is retained and the dragged targets
matter. Item removal or one-time trade rises when it removes the function
keeping the route alive. Hand off or break the loop when the reset hub owns the
clock.

Related source-to-policy entries: `STP-013`, `STP-019`, `STP-021`, `STP-028`,
`STP-029`.

## PTA-039: Information Boundary Or Team-Preview Autopilot

Source: `worked_examples/live_turn_drills.md#drill-041-information-boundary-versus-team-preview-autopilot`

Format: Gym Leader Lab information-model drill.

Skill tested: decide what facts may be used when advising the player, reviewing
a replay, or designing boss AI.

Public prompt:

```text
The boss roster may be source-known, but the player team may be partly or fully
unrevealed depending on the role being advised. A proposed plan may rely on
knowing an unrevealed player bench piece, hidden move, item, or route.

Rank: use known boss roster / use revealed public state / legal-source prior /
ask for missing player info / reject hidden-info line / re-plan after reveal.
```

Expected policy: first name the information model. Player-side boss preparation
may use known boss rosters and a declared user team. Boss AI may use only public
state, seen player species, revealed moves, observed battle facts, and
explicitly allowed priors. Replay review must score each turn from information
available then. Do not import later-generation Team Preview into Gen 2 or Gym
Leader Lab.

Related source-to-policy entries: `STP-012`, `STP-034`.

## PTA-040: No-Preview Lead Contact Or Perfect Anti-Lead

Source: `worked_examples/live_turn_drills.md#drill-042-no-preview-lead-contact-versus-perfect-lead-autopilot`

Format: vanilla GSC lead review and Gym Leader Lab transfer drill.

Skill tested: choose a lead by robust first-contact value and later route fit
when the full opening matchup is not symmetrically previewed.

Public prompt:

```text
Several openers are plausible from GSC lead trends or local fixed/adaptive boss
source. One lead hard-wins a favorite opener but risks spending the only later
answer or collapsing into a bad second opener. Another lead creates lower but
broader contact value through status, hazards, item removal, phazing, forced
switching, scouting, or safe pivot tempo.

Rank: robust contact lead / focused anti-lead / scout or pivot lead / preserve
later answer / forced-risk lead / re-plan after actual opener.
```

Expected policy: first confirm whether the format has Team Preview, a
source-fixed opener, an adaptive opener set, or only metagame frequency. In
no-preview states, prefer the lead that keeps the route map playable across the
plausible opener field unless the focused anti-lead branch is route-winning and
the bad opener branch is covered. Boss AI must not choose a perfect anti-player
lead from unrevealed player-team knowledge.

Related source-to-policy entries: `STP-010`, `STP-012`, `STP-034`.

## PTA-041: Phaze Loop Exit Or Setup Autopilot

Source: `worked_examples/live_turn_drills.md#drill-043-phaze-loop-exit-versus-setup-autopilot`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether to keep setting up, remove hazards, pressure the
control user, trade, trap, pivot, or hand off after a setup route has already
been reset.

Public prompt:

```text
Our setup Pokemon can survive or wall the active attack, but a revealed control
move has already erased the boost once. Hazards or passive damage are active,
so each forced reset may chip the backline more than the boost helps.

Rank: boost again / attack control user / remove hazards / trap or force Rest /
trade / pivot to backup converter / preserve only answer / accept clean-entry
sack.
```

Expected policy: after a forced reset, treat the next boost as a fresh move.
Boost again only if a new fact stops or prices the next control move: hazards
gone, phazer low, control PP scarce, trap active, sleep/lock state favorable,
mechanics deny the reset, or the boost crosses an immediate route threshold.
If the same reset plus entry-tax board repeats, exit the loop.

Related source-to-policy entries: `STP-008`, `STP-028`, `STP-029`, `STP-041`.

## PTA-042: Final Trade Target Or Active-Target Autopilot

Source: `worked_examples/live_turn_drills.md#drill-044-final-trade-target-versus-active-target-autopilot`

Format: all singles formats; Gym Leader Lab boss-facing drill.

Skill tested: choose whether to spend a final one-time resource on the active
Pokemon, a likely route switch-in, or no trade at all.

Public prompt:

```text
The endgame is simplified. We have one final trade resource and one remaining
converter. The active target is valuable, but another remaining target is the
piece our converter cannot beat.

Rank: trade active / target switch-in or blocker / preserve trade / attack /
controlled sack / rebuild final material.
```

Expected policy: write the final material after each branch. Spend the trade
on the target that lets the remaining converter win, unless the active branch
is still urgent or the fail branch is unpriced. After any trade, rebuild before
spending the next one-time resource.

Related source-to-policy entries: `STP-003`, `STP-025`, `STP-031`, `STP-042`.

## PTA-043: Support Contact Or Damage-Only Autopilot

Source: `worked_examples/live_turn_drills.md#drill-045-support-contact-versus-damage-only-autopilot`

Format: all singles formats; Gym Leader Lab transfer drill.

Skill tested: decide whether a low-damage support move is real progress,
fake progress, or a route handoff to a later receiver.

Public prompt:

```text
A low-damage support move is available: debuff, trap, status, screen, spin,
Protect, phaze, Haze, or scout. It does not win the visible exchange, but it
may create a future receiver turn. The opponent may escape through immunity,
phazing, Haze, cure, Rest, switch, Protect, faster KO, or item reset.

Rank: support now / attack / pivot / preserve support user / deny escape /
hand off to receiver / abandon support route.
```

Expected policy: name receiver, support effect, escape branch, and payoff turn.
Support rises when it changes a future route before the opponent erases it.
Support falls when the target can ignore, reset, or punish it before any
receiver benefits.

Related source-to-policy entries: `STP-021`, `STP-022`, `STP-023`, `STP-044`.

## PTA-044: Contained Hold Or Winning Loop

Source: `worked_examples/live_turn_drills.md#drill-046-contained-hold-versus-winning-loop`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: distinguish a defensive loop that merely prevents immediate
loss from a contained loop with a real conversion endpoint.

Public prompt:

```text
Our current line repeatedly contains the visible threats with recovery,
debuffs, pivots, Pursuit, Protect, phazing, Haze, trapping, or RestTalk.
The opponent may rotate targets, recover, Rest, cure, spin, or reset chip.
Our converter may be low, asleep, PP-limited, recoil-exposed, or gone.

Rank: hold loop / wait / force endpoint / preserve converter / trade / attack /
abandon loop / rebuild final material.
```

Expected policy: do not call the loop winning until the endpoint is named:
forced KO range, Rest timing, poison / hazard / weather / recoil clock, scarce
PP, trap, switch denial, final trade, or a preserved converter. If no endpoint
is public, treat the line as a hold and search for progress.

Related source-to-policy entries: `STP-017`, `STP-023`, `STP-026`, `STP-027`,
`STP-045`.

## PTA-045: Phaze Target Pool Or Last-Mon Autopilot

Source: `worked_examples/live_turn_drills.md#drill-047-phaze-target-pool-versus-last-mon-autopilot`

Format: vanilla GSC strategic review and Gym Leader Lab mechanics transfer.

Skill tested: decide whether Roar / Whirlwind is real route control, or
whether timing or the target pool makes it fail.

Public prompt:

```text
Roar or Whirlwind is available. Hazards, setup, RestTalk, or recovery timing
would normally make phazing attractive. The opponent may have a bench target,
or may be on its last Pokemon. Move order may also make Gen 2 phazing fail.

Rank: phaze / attack / status / recover / setup / pivot / trade / conserve PP.
```

Expected policy: phazing is legal route control only if it resolves under
local timing, has a living non-active target to drag, and improves the target
map. If the opponent is last Pokemon or the move acts too early, choose another
route.

Related source-to-policy entries: `STP-008`, `STP-028`, `STP-041`, `STP-046`.

## PTA-046: Post-Converter Handoff Or Dead-Sweeper Panic

Source: `worked_examples/live_turn_drills.md#drill-048-post-converter-handoff-versus-dead-sweeper-panic`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether a fainted or paused converter left behind a live
route for a different closer, or whether the route really died.

Public prompt:

```text
Our converter just fainted, was forced out, or no longer owns the route.
Before that happened, it may have removed blockers, forced recovery, exposed
the opponent's final route, or simply failed. We still may have utility or
one-time resources: Rapid Spin, phazing, Explosion, status, pivoting, recovery,
or a controlled sack.

Rank: preserve old route / rebuild blocker map / spin / phaze / trade / pivot /
deliver new closer / abandon route.
```

Expected policy: list what the converter removed, name the new closer, and
choose the move that delivers that closer. If no closer or blocker-removal path
exists, mark the handoff fake and move to a backup route.

Related source-to-policy entries: `STP-006`, `STP-020`, `STP-027`, `STP-047`.

## PTA-047: Anti-Pass Reset Or Receiver Endpoint

Source: `worked_examples/live_turn_drills.md#drill-049-anti-pass-reset-versus-receiver-endpoint`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether to keep resetting a Baton Pass / support chain or
cash out by damaging the support source or exposed receiver.

Public prompt:

```text
The opponent has a support source that can Baton Pass, set screens, boost, or
deliver safe entry. At least one receiver can convert if support lands. We have
phazing, Haze, Encore, status, direct attack, or sacrifice available.

Rank: reset / attack source / attack receiver / preserve control user / trade /
pivot / abandon anti-pass route.
```

Expected policy: name the support source, receiver map, control legality, and
endpoint. Reset while the receiver would win and no endpoint exists; attack or
trade once the source or receiver is in range and the return branch is priced.

Related source-to-policy entries: `STP-017`, `STP-044`, `STP-046`, `STP-048`.

## PTA-048: Reset Hub Leak Audit

Source: `worked_examples/live_turn_drills.md#drill-050-reset-hub-leak-audit`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: decide whether a low-damage recovery/debuff/cure loop is only
stabilizing or has become the real endpoint.

Public prompt:

```text
We have a reset hub: recovery, cleric cure, debuff, phaze, spin, screen,
Protect, RestTalk, or status reset. It contains the active threat but does not
deal much damage. The opponent may still have leaks that break the loop:
setup, mixed damage, Explosion, hazards, PP, phazing, trapping, or a one-time
trade.

Rank: keep resetting / recover / preserve hub / attack leak / trade / phaze /
handoff / abandon loop.
```

Expected policy: list the leak branches first. Reset is only a win condition
after the leaks are removed or controlled; before that, it is stabilization
and must preserve or deliver the answer to the leak.

Related source-to-policy entries: `STP-017`, `STP-027`, `STP-040`, `STP-045`,
`STP-049`.

## PTA-049: Surprise Function Reclassification

Source: `worked_examples/live_turn_drills.md#drill-051-surprise-function-reclassification`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: update a route after public information reveals that a familiar
Pokemon is performing a different job than its species label implied.

Public prompt:

```text
The opponent has revealed a nonstandard function: damage from a wall, screens,
Haze, phazing, trapping, spin, recovery, or a lock/ramp setup route. Our old
plan assumed the Pokemon was passive, standard, or setup bait.

Rank: continue old route / heal / attack / preserve answer / scout companion
move / phaze or Haze / sacrifice / handoff.
```

Expected policy: reclassify by the revealed function. If the function changes
the route, stop using the old species assumption; if it only suggests an
unrevealed companion move, preserve the answer and state the inference level.
Boss AI cannot use hidden player-team knowledge for the reclassification.

Related source-to-policy entries: `STP-014`, `STP-017`, `STP-045`, `STP-050`.

## PTA-050: Accuracy Disruption Endpoint

Source: `worked_examples/live_turn_drills.md#drill-052-accuracy-disruption-endpoint`

Format: vanilla GSC strategic review and Gym Leader Lab transfer drill.

Skill tested: price an accuracy drop as a real reliability change without
mistaking it for a win condition before it feeds a concrete endpoint.

Public prompt:

```text
The opponent has changed accuracy or evasion. Our old route required repeated
hits from the affected Pokemon, but poison, phazing, Protect, switching, PP
pressure, setup handoff, or direct damage may be available.

Rank: keep attacking / switch to clear stages / poison / phaze or Haze /
Protect-stall / preserve answer / attack with a different piece / repeat
accuracy disruption.
```

Expected policy: re-score current hit reliability, identify which Pokemon
carries the stage change, and name the endpoint. Accuracy disruption is support
unless it buys a concrete miss, receiver turn, clock, PP route, safe switch, or
KO threshold before the opponent clears or routes around it. Boss AI cannot use
hidden player-team knowledge to prove the endpoint.

Related source-to-policy entries: `STP-044`, `STP-045`, `STP-048`, `STP-051`.

## PTA-051: Spinblocker Entry Or Roster Checkbox

Source: `reviews/2026-05-14_smogtours-gen2ou-912653.md`

Format: vanilla GSC strategic review and Gym Leader Lab hazard transfer.

Skill tested: decide whether a hazard-retention answer can actually act on the
removal turn.

Public prompt:

```text
Our hazards are up. The opposing spinner is active or can enter, and our Ghost,
trapper, or spinner-punish option is alive but not necessarily active. The
spinner may use Rapid Spin, attack the blocker, Recover, or switch.

Rank: switch to spinblocker / attack spinner / set or reset hazard / preserve
blocker / abandon hazard route / hand off to another converter.
```

Expected policy: retention is an entry condition, not a roster label. Switch
to the blocker only if it can enter the spin turn and survive the punish. Attack
the spinner only if the damage denies removal, denies recovery, or creates a
concrete post-spin endpoint. If neither is true, stop treating the hazard layer
as the main route.

Related source-to-policy entries: `STP-028`, `STP-052`, `STP-053`.

## PTA-052: Support First, Cash Out Second

Source: `reviews/2026-05-14_smogtours-gen2ou-740650.md`

Format: vanilla GSC strategic review and Gym Leader Lab support-transfer drill.

Skill tested: order a support move and one-time trade from a support Pokemon
whose future value is collapsing.

Public prompt:

```text
Our support Pokemon can still set a layer, remove a layer, phaze, screen,
status, or otherwise deliver a route support action. It is also likely to be
heavily damaged or KOed soon, and it may have Explosion, Self-Destruct, a
sacrifice pivot, or another one-time cash-out. The opposing active is asleep,
recovering, locked, forced into low damage, or otherwise giving a short window.

Rank: support now / cash out now / attack / switch preserve / double to
converter / abandon the support route.
```

Expected policy: deliver the support first only if it changes a named
converter's route before the opponent resets. Cash out afterward when the
support user's future role is gone and the trade improves that converter's
range or entry. Cash out first only when the trade target is the required
blocker or the support will not survive long enough to matter.

Related source-to-policy entries: `STP-003`, `STP-024`, `STP-025`, `STP-044`,
`STP-047`, `STP-055`.

## PTA-053: Spacer Sack Or Throwaway Faint

Source: `reviews/2026-05-14_smogtours-gen2ou-890958.md`

Format: vanilla GSC strategic review and Gym Leader Lab endgame-transfer drill.

Skill tested: identify when a low-value piece still has a route job as a
spacer that creates clean final entry or removes a bad branch.

Public prompt:

```text
The battle is near the endgame. A low-HP, statused, or nearly spent Pokemon can
switch in, faint, phaze, absorb a boosted/wake/locked hit, force recoil, or
otherwise create entry for the converter. Keeping it alive looks hard, but
throwing it away may also remove the last buffer against variance.

Rank: spacer sack / direct attack / recover / phaze or Haze / preserve low
piece / hard switch converter / abandon converter route.
```

Expected policy: write the final material before choosing. Spacer sack only
when the sacrificed piece has no higher-value remaining job and its death
creates cleaner entry, absorbs a bad branch, forces recoil, or removes
variance that otherwise breaks the converter. If the converter still cannot
force the win after entry, the sack is cosmetic rather than strategic.

Related source-to-policy entries: `STP-007`, `STP-009`, `STP-042`, `STP-049`,
`STP-056`.

## PTA-054: Visible Setter Or Real Support Map

Source: `workspace/quick_tests/replay_turn_pause_001_smogtours-gen2ou-912131_2026-05-14.md`

Format: vanilla GSC turn-pause replay and Gym Leader Lab hazard-transfer drill.

Skill tested: avoid assuming the active support Pokemon is also the whole
hazard-control plan.

Public prompt:

```text
Both sides are entering a support exchange. The visible opposing Pokemon can
set hazards, spread status, phaze, or trade, but the opponent may also have a
different reserve that removes hazards or absorbs the forced attack. Our active
Pokemon can attack the visible support piece, set or remove hazards, double to
the expected support entrant, or preserve the current answer.

Rank: attack visible support / set hazard / remove hazard / status support /
double to support entrant / preserve answer / abandon hazard route.
```

Expected policy: build the support map before choosing. Name who sets, who
spins, who poisons, who phazes, and who gets entry after the forced switch.
Attack the visible support only if that denies the actual route. If the active
setter is only creating a poisoned or symmetric hazard state so a reserve
spinner can enter safely, target the reserve entry or preserve the answer to
it.

Related source-to-policy entries: `STP-052`, `STP-053`, `STP-055`, `STP-057`.

## PTA-055: Re-Solve After The Reveal

Source: `cross_domain_autonomy_policy.md`, poker-AI transfer sprint, and
`workspace/quick_tests/replay_turn_pause_002_smogtours-gen2ou-917186_2026-05-14.md`.

Format: no-Team-Preview Pokemon transfer drill.

Skill tested: rebuild the local decision after a route-changing reveal instead
of continuing the old line.

Public prompt:

```text
A route-changing event just resolved: a hidden move was revealed, a spinner or
phazer entered, Sleep Talk showed a move, Explosion became likely, a key piece
Rested, or a support role moved from one Pokemon to another. The old plan was
reasonable before this reveal, but the local subgame may have changed.

Rank: continue old plan / attack / switch preserve / sack correct piece /
support move / double to route answer / abandon route.
```

Expected policy: re-solve the local subgame before choosing. Name the new
public belief state and test the candidate against three branches: obvious
punish, route-preserving switch, and greed/support continuation. Choose the
robust line when stable or ahead; take the sharper exploitative line only when
the robust line is losing or public incentives make the branch very likely.

Related source-to-policy entries: `STP-004`, `STP-034`, `STP-050`, `STP-057`,
`STP-058`.

## PTA-056: Stop The Setup Route Before Support Economy

Source:
`workspace/quick_tests/replay_turn_pause_005_status_route_smogtours-gen2ou-903666_2026-05-14.md`

Format: vanilla GSC turn-pause replay and Gym Leader Lab support-priority
drill.

Skill tested: choose the support move that stops the current route, not the
support move that is generically valuable.

Public prompt:

```text
Our support Pokemon is active into a setup anchor or recovery anchor. We can
set hazards, remove hazards, status, phaze, attack, Explode, or switch. The
opponent can keep attacking, boost again, Rest, switch out to reset tempo, or
use the existing hazard/status state to force a long route.

Rank: status route-stopper / phaze / set hazard / remove hazard / attack /
Explode / switch preserve.
```

Expected policy: first ask whether the opponent's active setup or recovery
route becomes permanent if not interrupted this turn. If yes, prefer the
route-stopper that changes that clock, even over Spikes or Rapid Spin. After
the stopper lands or the setup route is contained, re-score hazard economy:
setting reciprocal Spikes may outrank spinning if the active pressure is now
on a clock.

Related source-to-policy entries: `STP-024`, `STP-050`, `STP-055`, `STP-058`.

## PTA-057: Cash-Out Or Handoff Before Explosion

Source:
`workspace/quick_tests/replay_turn_pause_008_cashout_handoff_fresh_smogtours-gen2ou-907674_2026-05-14.md`

Format: vanilla GSC turn-pause replay and Gym Leader Lab support-transfer
drill.

Skill tested: avoid overcalling Explosion or Self-Destruct when status,
phazing, hazard control, or a recurring teammate handoff solves the current
route while preserving the one-time trade.

Public prompt:

```text
Our support Pokemon can plausibly Explode, Self-Destruct, Destiny Bond, or
otherwise cash out. It can also use a support route-stopper such as Toxic,
paralysis, phazing, Rapid Spin, Spikes, or a switch to a recurring teammate
that pressures the current answer. The opposing active is dangerous but not
yet guaranteed to win this turn.

Rank: status route-stopper / phaze / hand off to recurring teammate / set or
remove hazard / attack / cash out now / switch preserve.
```

Expected policy: first ask whether a non-cash-out action stops the current
route and keeps the one-time trade available. Prefer status, phazing, or a
handoff when it contains the threat and gives a recurring teammate a better
board. Cash out now only when the target is the actual route blocker, the
support user has no better remaining job, or the handoff gives the opponent a
stronger route than the trade removes.

Related source-to-policy entries: `STP-003`, `STP-025`, `STP-043`, `STP-055`,
`STP-058`.

## PTA-058: Support Choice Before Handoff Or Cash-Out

Source:
`workspace/quick_tests/replay_turn_pause_011_support_choice_smogtours-gen2ou-928706_2026-05-14.md`

Format: vanilla GSC turn-pause replay and Gym Leader Lab support-action
ordering drill.

Skill tested: choose the support action that changes the current route before
defaulting to more support, handoff, attack, Rapid Spin, phazing, or Explosion.

Public prompt:

```text
Our support Pokemon has at least two useful jobs available: it can set or
remove hazards, spread status, phaze, attack, switch to a recurring teammate,
or cash out with a one-time trade. The current board already has some support
state in play, and the opponent can either exploit the active matchup, pivot to
the next route, reset status or hazards, or preserve a damaged converter.

Rank: route-changing status / set hazard / remove hazard / phaze / hand off
to recurring teammate / attack / cash out now / preserve support piece.
```

Expected policy: first ask whether the last support action has already changed
the local route. If it has, name the teammate or opponent route that now
benefits before clicking another support move. Prefer the support action that
creates a concrete receiver or denies the opponent's next route; prefer handoff
when the receiver is already better than another support turn; accept Rapid
Spin or phazing when skipping it lets the opponent's route become live. Cash
out only if the current target is the route blocker or the support piece cannot
deliver a better job first.

Boundary clause: once the support job has been delivered, do not keep
preserving by inertia. If the active target is now the route piece and the
support Pokemon no longer improves the board by preserving, phazing, spinning,
or handing off, the correct support choice may be Explosion or another
one-time trade.

Defense clause: if the opponent's cash-out is the branch being covered, name
the piece we are willing to lose before choosing. Stay in only when the active
piece is already expendable or the trade opens a better route. If a lower-value
absorber exists and the active piece still defines a route, preserve before
attacking.

Handoff clause: if status or chip on the target makes Rest or another passive
reset likely, price the route handoff before the one-time trade. In 935045,
paralyzing and chipping Raikou did not force Exeggutor Explosion; it created a
Marowak handoff into Raikou's Rest. The same replay also showed the defense
clause working against low Cloyster: preserve Marowak by spending lower-value
Smeargle, then let Smeargle deliver one last Spikes before it dies.

Status follow-up clause: after support status lands on a boosting anchor,
re-score the exact follow-up order. In 935022, Cloyster's sequence was Toxic,
then Spikes, then Explosion into the boosted Snorlax. The defending side must
state whether staying depends on a non-crit or damage roll, and whether a
lower-value absorber preserves the anchor without losing the only remaining
route.

Related source-to-policy entries: `STP-003`, `STP-024`, `STP-055`,
`STP-058`.

## PTA-059: Focus Energy Retaliation Branch

Source:
`workspace/quick_tests/focus_energy_counter_branch_regression_001_smogtours-gen2ou-935022_2026-05-14.md`

Format: vanilla GSC replay drill and Gym Leader Lab crit-pressure drill.

Skill tested: after Focus Energy or another crit-stage/setup move is revealed,
re-price the whole route bundle instead of treating the next turn as ordinary
coverage or ordinary retaliation.

Public prompt:

```text
The opposing active has revealed Focus Energy or a similar setup/punish state.
It is damaged enough to look expendable, but it may still move first, attack
with coverage, threaten a crit branch, or punish the obvious attack with
Counter, Mirror Coat, Bide, Destiny Bond, or a similar move.

Rank: attack for KO / safer category attack / switch preserve / status-control
/ controlled sack / scout / accept forced risk.
```

Expected policy: name the current public setup state, speed/order, KO ranges,
whether our active can move before dying, whether our obvious attack triggers a
retaliation move, and whether an odd-category move such as Hidden Power changes
punish legality. Low HP does not make the boosted attacker harmless. Attack
only if the KO or forced trade opens a named route, or if preserving gives the
opponent a stronger converter.

Related source-to-policy entries: `STP-036`, `STP-055`, `STP-058`.

## PTA-060: Baton Pass Route Is Not A Script

Source:
`workspace/quick_tests/replay_turn_pause_016_baton_pass_resolve_smogtours-gen2ou-934428_2026-05-14.md`

Format: vanilla GSC replay drill and Gym Leader Lab setup-transfer drill.

Skill tested: after a setup move or Baton Pass reveal, re-solve the current
route instead of defaulting to "boost more" or "pass now."

Public prompt:

```text
Our active has a setup-transfer route online: Agility, Swords Dance, Growth,
Substitute, or Baton Pass has been revealed or strongly implied. The passer can
add another boost, attack with the current boost, pass to a named receiver,
use Baton Pass as a fast pivot into a low-value teammate, or abandon the chain.
The opponent can attack, phaze, status, Explode, switch to a route answer, or
let the current active become expendable.

Rank: add boost / attack with passer / Baton Pass to receiver / Baton Pass as
fast pivot / ordinary switch / status-control / controlled sack / abandon.
```

Expected policy: name the receiver before passing and name the board the
receiver inherits. Do not pass automatically if the passer's boosted attack
changes the range map first. Do not keep boosting if the opponent's punish now
breaks the chain. Treat Baton Pass as a move-speed switch option even when no
boost payload matters, but only when the pivot target's loss is priced.

Comeback clause: when direct damage loses, search for the receiver route before
calling the position dead. If the exact receiver is not public in spectator
practice, label it as an inferred archetype branch, not a known species. In
`934428`, Jolteon's damage into Tyranitar was not the comeback route; Agility
plus Baton Pass to the last receiver was.

Related source-to-policy entries: `STP-006`, `STP-034`, `STP-055`, `STP-058`.
