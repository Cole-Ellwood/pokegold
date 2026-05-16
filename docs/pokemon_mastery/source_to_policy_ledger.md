# Source-To-Policy Ledger

Status: active. This file converts expert-source study into move-choice policy.
Keep entries short enough to use during real turn advice.

## STP-001: Spikes Require A Route, Not Just A Turn

Source: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes)

Trigger: we can set or preserve hazards.

Policy: set Spikes when the layer changes switch costs, Rest pressure,
phazing value, or KO ranges and the setter is not giving up a more urgent job.

Exceptions: max layers, immediate setup punish, free spin without counterplay,
or setter is irreplaceable for another route.

Worst branch: the layer does not stick or does not matter, and the opponent
uses the free turn to advance a stronger route.

Local status: romhack has three-layer Spikes; layer behavior and Rapid Spin
clearing have fixture coverage, but exact battle-flow timing still needs more
runtime evidence.

## STP-002: Sleep Creates A Re-Score Window, Not A Script

Source: Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
and Smogon Forums,
[SPL XVII GSC Discussion](https://www.smogon.com/forums/threads/spl-xvii-gsc-discussion.3775984/)

Trigger: a sleep move is available, just landed, missed, or was answered by a
switch.

Policy: use sleep when the target blocks a route and the miss branch is not
terminal. After any miss, wake, switch, Sleep Talk reveal, or phazing event,
discard the old script and re-score.

Sleep Clause material update:
`workspace/quick_tests/replay_turn_pause_017_sleep_route_marowak_continuation_smogtours-gen2ou-934428_2026-05-14.md`
showed that a slept target is often switched out immediately and preserved as
Sleep Clause material. After sleep lands, ask whether the sleeping Pokemon
should stay to burn turns or switch out to keep Sleep Clause active while
retaining a later route job: Explosion, Spikes, Rapid Spin, phazing, Sleep
Talk, a controlled sack, or a wake attack. The default reason to preserve it is
that waking can clear Sleep Clause and let the opponent sleep a more valuable
piece later. Do not set up automatically if the sleeper can be preserved and
the opponent can punish with another teammate.
`workspace/quick_tests/replay_turn_pause_018_sleep_clause_absorber_fresh_smogtours-gen2ou-934335_2026-05-14.md`
adds the exception: immediate switching is a default branch, not a script. If
the opponent's active cannot strongly punish one sleep turn, or if
Explosion/pivot scouting matters, burning one turn before switching can be
acceptable.
`workspace/quick_tests/replay_turn_pause_019_sleeper_later_job_smogtours-gen2ou-934335_2026-05-14.md`
adds the later-job check: a sleeping Pokemon can still be the correct piece
before it wakes if Sleep Talk, Heal Bell support, forced-switch absorption,
predicted coverage absorption, wake-and-act timing, or hazard removal changes
the route.
`workspace/quick_tests/replay_turn_pause_020_sleeper_transfer_smogtours-gen2ou-935572_2026-05-14.md`
adds a cash-out threshold: do not spend Explosion or another one-time trade
into a sleeper merely because wake risk exists. Spend it when the wake move,
Rest, Sleep Talk, or endgame role would otherwise undo the route.
`workspace/quick_tests/replay_turn_pause_034_sleep_clause_wake_cashout_transfer_smogtours-gen2ou-934415_2026-05-14.md`
adds wake-window timing: a low-punish sleep turn can be correct early, but the
position must be re-solved before each likely wake turn because Explosion,
phazing, or a switch may become correct once the sleeper can wake and remove
the active target.
`workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`
adds the late absorber transfer: the already-sleeping Pokemon can be switched
back into pressure later because it both blocks another sleep attempt under
Sleep Clause and still has a matchup job. Do not burn wake turns just to wake;
stay only when Sleep Talk, Rest timing, sacrifice value, or immediate pressure
is better than preserving the sleep-clause shield.
`workspace/quick_tests/replay_turn_pause_038_sleep_clause_overcorrection_smogtours-gen2ou-934314_2026-05-14.md`
adds the anti-overcorrection: switching the slept Pokemon out is common, not
automatic. If the sleeper is already a boosted active win condition, switching
would erase the route, and the opponent's current punishment is only slow chip
or a conditional unrevealed cash-out, staying asleep to reach wake/Rest or
wake/action can be correct.
`workspace/quick_tests/sleep_clause_four_choice_probe_001_2026-05-14.md` turns this into
an eight-scenario regression: switch out, Sleep Talk, stay with the boosted
route, cover revealed cash-out, leave phaze bait, stop preserving spent
sleepers, cover wake self-KO, and re-solve after Rest converts the status.
`workspace/quick_tests/replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`
adds the transfer check: when Sleep Talk is revealed, the slept Pokemon is an
active board piece first and Sleep Clause material second. If Sleep Talk is
not revealed, preserve remains plausible, but after the reveal the policy must
flip immediately.
`workspace/quick_tests/replay_turn_pause_045_sleep_clause_clamp_explosion_growth_smogtours-gen2ou-927169_2026-05-14.md`
adds the low-HP shield case. A sleeping Pokemon can be worth switching out
even when Spikes make future re-entry impossible, because the asleep status
still blocks another Lovely Kiss. Preserve the sleep-clause shield with a
lower-value spacer when fainting would reopen sleep and the sleeper no longer
needs to perform an active combat job.
`workspace/quick_tests/replay_turn_pause_049_coverage_reveal_absorber_smogtours-gen2ou-924921_2026-05-14.md`
adds the sleeping absorber trade case. A sleeping Sleep Talk user can pivot
into a support Pokemon not to wake or fight immediately, but to protect a more
important route piece from Explosion while still keeping Sleep Clause active.
`workspace/quick_tests/coverage_reveal_absorber_probe_001_2026-05-14.md` isolates that
branch as a regression prompt.
`workspace/quick_tests/replay_turn_pause_052_lovely_kiss_snorlax_sleep_pivot_smogtours-gen2ou-923076_2026-05-14.md`
adds the team-level sleep-source check. Modern GSC offense can put Lovely Kiss
on Snorlax, which frees Exeggutor or Gengar from carrying Sleep Powder or
Hypnosis. Do not assign the sleep job by species alone. Until the sleep move is
revealed, ask which teammate's set would make the current move coherent; after
sleep lands, preserve the sleeping Pokemon as Sleep Clause material unless its
active route is better.
`workspace/quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
adds the anti-overfit: Lovely Kiss Snorlax is a live branch, not a default.
If Snorlax reveals Curse and Body Slam before any sleep move, keep Curse/Rest
or RestTalk structure live and stop assigning sleep until it is revealed.
`workspace/quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`
adds the reverse boundary: Curse first does not rule out Lovely Kiss. After
Snorlax revealed Curse in a mirror, the next move was Lovely Kiss into
Forretress. Keep sleep, attack, Rest, and coverage branches live until public
moves or a team sheet actually narrow the set.

Exceptions: sleep clause used, target already statused, likely Sleep Talk
absorber, or immediate attack/switch creates the better route.

Worst branch: sleep is treated as ownership of the game, then a wake or
Sleep Talk action punishes setup.

Local status: verify romhack sleep, Rest, and Sleep Talk behavior before making
exact timing claims.

Local drills:
`workspace/quick_tests/replay_turn_pause_017_sleep_route_marowak_continuation_smogtours-gen2ou-934428_2026-05-14.md`,
`workspace/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_018_sleep_clause_absorber_fresh_smogtours-gen2ou-934335_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_019_sleeper_later_job_smogtours-gen2ou-934335_2026-05-14.md`,
`workspace/quick_tests/sleeping_piece_later_job_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_020_sleeper_transfer_smogtours-gen2ou-935572_2026-05-14.md`,
`workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_034_sleep_clause_wake_cashout_transfer_smogtours-gen2ou-934415_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_038_sleep_clause_overcorrection_smogtours-gen2ou-934314_2026-05-14.md`,
`workspace/quick_tests/sleep_clause_four_choice_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_045_sleep_clause_clamp_explosion_growth_smogtours-gen2ou-927169_2026-05-14.md`.

## STP-003: Explosion Is A Route Trade

Source: Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion)

Trigger: a one-time self-KO move can remove or cripple a blocker.

Policy: Explode when the target's removal opens a named route and the user has
no remaining role more valuable than that route.

Sleeping-target threshold:
`workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`
tests the `replay_turn_pause_020` miss. Do not Explode into a sleeping target
just because wake risk exists. First ask whether steady pressure or a
lower-value absorber covers the wake branch. Cash out when wake, Rest, Sleep
Talk, Self-Destruct, or preservation would otherwise undo a named route and the
post-trade converter is clear.
`workspace/quick_tests/replay_turn_pause_021_cashout_threshold_partial_smogtours-gen2ou-934904_2026-05-14.md`
adds the target-identification check: the one-time trade target may be the
active route converter, not the sleeping Pokemon. Before setting up with a
passed receiver into Snorlax, price Self-Destruct explicitly.
`workspace/quick_tests/selfdestruct_receiver_branch_regression_001_smogtours-gen2ou-934904_2026-05-14.md`
turns that miss into a regression: before boosting with a passed receiver,
choose between immediate damage, an absorber switch, or setup only after the
self-KO branch is named.
`workspace/quick_tests/replay_turn_pause_022_receiver_counterplay_transfer_smogtours-gen2ou-935551_2026-05-14.md`
adds the calibration check: pricing Explosion, phazing, status, and immediate
damage does not mean hallucinating them. If the public counterplay is only
damage and Substitute covers it, setup can be correct.
`workspace/quick_tests/route_trade_active_pressure_probe_001_smogtours-gen2ou-934329_2026-05-14.md`
adds the active-pressure threshold: Self-Destruct or Explosion can be correct
as soon as the target has started or revealed the route that must be stopped,
such as Curselax or RestTalk Electric pressure. Before cashing out, still name
the lost-role successor, execution gate, and final converter.
`workspace/quick_tests/replay_turn_pause_024_route_trade_threshold_smogtours-gen2ou-934148_2026-05-14.md`
adds the timing boundary: an active route threat does not automatically mean
cash out on the first legal turn. Toxic, Spikes, recoil, and absorber cycling
can make the eventual trade cleaner; cash out when the target is exact, prior
jobs are delivered, and delay gives the opponent a reset or escape.
`workspace/quick_tests/route_trade_timing_probe_001_2026-05-14.md` turns that boundary
into a six-step timing ladder: Toxic first, Spikes first, absorber pivot,
preserve the exploder, immediate Explosion, and delayed Self-Destruct into the
exact target.
`workspace/quick_tests/replay_turn_pause_025_route_trade_timing_transfer_smogtours-gen2ou-934874_2026-05-14.md`
adds the final-gate check: after Toxic and Spikes are delivered, do not cash
out automatically. Price whether the target is likely to stay, whether a
plausible absorber or double switch punishes Explosion, and whether the
exploder still has future utility if preserved.
`workspace/quick_tests/route_trade_final_gate_probe_001_2026-05-14.md` turns that miss
into a checklist: exact target likelihood, absorber branch, remaining exploder
job, ordinary damage or double-switch coverage, and whether delay gives Rest,
setup, recovery, Spin, or escape.
`workspace/quick_tests/explosion_absorber_resource_probe_001_2026-05-14.md` adds the
defensive mirror: when the opponent's self-KO move is live, choose the absorber
by remaining route job. A sleeping anchor can be the correct absorber if the
spinner, hazard setter, Electric answer, or cleaner still has the live job; but
preserve the sleeping anchor when it is the only future check.
`workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`
adds a low-HP support split: low HP does not by itself mean immediate
Explosion. Cloyster at 31% still used Surf for useful chip before fainting,
while Gengar at 13% correctly Exploded only after the target and post-trade
Zapdos route were clear.
`workspace/quick_tests/replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`
adds the trapper cash-out branch: once Houndoom had revealed Pursuit and Gengar
was low, switching lost to the named punish. Explosion was the correct route
trade because it removed the trapper and restored Zapdos/Tyranitar pressure.
`workspace/quick_tests/replay_turn_pause_050_lead_trade_support_coverage_smogtours-gen2ou-924499_2026-05-14.md`
adds the lead-trade boundary: a lead sleep threat does not force a sleep
script. Immediate Explosion can be correct if it removes the opposing lead's
route job and the exploding lead is not needed for a later route.
`workspace/quick_tests/replay_turn_pause_051_support_entry_explosion_absorber_smogtours-gen2ou-923748_2026-05-14.md`
adds the support-entry mirror. After Cloyster claimed the support seat and
dropped low, Explosion was live, but the player-side answer was to switch
Gengar and blank it. Before cashing out or accepting the trade, ask whether a
side-known Ghost absorber exists and whether preserving it matters more than
absorbing the self-KO now.
`workspace/quick_tests/replay_turn_pause_056_immediate_route_trade_converter_smogtours-gen2ou-922569_2026-05-14.md`
adds the anti-overcorrection. Preservation lessons do not mean refusing
Explosion. Immediate or early Explosion is correct when the target is exact,
the support job is complete or expendable, delay lets the route continue, and
the next converter is named. In the replay, Exeggutor removed Zapdos, then
Forretress set Spikes before Exploding into boosted Snorlax to hand Machamp
the board.
`workspace/quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`
adds the defender-selection mirror. Explosion into a boosted Snorlax route can
be correct for the exploding side, while the defending side can still make the
right preservation switch by losing a different route piece. In that replay,
Exeggutor Exploded after taking Double-Edge, but Zapdos absorbed the trade so
the boosted Lovely Kiss Snorlax stayed live.

Exceptions: plausible Ghost or Protect branch, target is replaceable, exploder
is the only answer to a live threat, or damage does not change the route.

Worst branch: the self-KO fails or hits the wrong target, and the lost role
was still needed.

Local status: GSC strategic lesson is useful, but romhack type/passive and
move-behavior interactions need local checks before exact advice.

Local drills:
`workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md` and
`workspace/quick_tests/replay_turn_pause_021_cashout_threshold_partial_smogtours-gen2ou-934904_2026-05-14.md`,
and
`workspace/quick_tests/selfdestruct_receiver_branch_regression_001_smogtours-gen2ou-934904_2026-05-14.md`,
and `workspace/quick_tests/explosion_absorber_resource_probe_001_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_022_receiver_counterplay_transfer_smogtours-gen2ou-935551_2026-05-14.md`,
and
`workspace/quick_tests/route_trade_active_pressure_probe_001_smogtours-gen2ou-934329_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_024_route_trade_threshold_smogtours-gen2ou-934148_2026-05-14.md`,
and
`workspace/quick_tests/route_trade_timing_probe_001_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_025_route_trade_timing_transfer_smogtours-gen2ou-934874_2026-05-14.md`,
and
`workspace/quick_tests/route_trade_final_gate_probe_001_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`,
and
`workspace/quick_tests/replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`.

## STP-004: Prediction Is A Risk Budget, Not A Personality

Sources: Smogon, [Risk/Reward](https://www.smogon.com/resources/beginner/bw_risk_reward) and
[An Introduction to Prediction](https://www.smogon.com/smog/issue1/introduction_to_prediction)

Trigger: a tempting read differs from the straightforward route-preserving
move.

Policy: predict when the wrong branch is tolerable or the safe line loses
anyway. When ahead or stable, prefer the move that covers the worst plausible
branch while still improving the route.

Branch-coverage update:
`workspace/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`
separates naming a branch from covering it. After naming the bad branch, verify
that the selected action actually improves that branch or explicitly accepts it
as a priced trade. In the replay, Earthquake into Gengar covered the spinblock
branch; preserving 14% Golem did not cover Psychic because Spikes made future
Golem entry fake.
`workspace/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md` turns this
into a six-branch regression: clean Spin on a forced switch, reset Spikes,
Roar into the spinblocker, direct Ghost punish, low-resource sack for clean
entry, and distinguishing a covered branch from an accepted Explosion trade.
`workspace/quick_tests/replay_turn_pause_041_branch_coverage_transfer_smogtours-gen2ou-931101_2026-05-14.md`
adds the failed transfer: branch identification and branch coverage are
separate scores. If Snorlax or Misdreavus is named as a likely pivot, the top
move must either hit that pivot, punish it through a double, or explicitly
accept it as a priced branch. Thunderbolt into a named Snorlax pivot and
Dynamic Punch into a named Misdreavus pivot fail this gate even when the move
looks active or matches the replay.
`workspace/quick_tests/named_pivot_coverage_probe_001_2026-05-14.md` turns that miss into
a three-prompt midground check: double to Tyranitar for the Snorlax pivot,
Earthquake rather than Dynamic Punch for Misdreavus, and Fire Blast for the
Skarmory/Forretress pivot. If the active-target move fails a named pivot,
either downgrade the pivot, choose the midground/double, or state why the
accepted branch is worth it.
`workspace/quick_tests/replay_turn_pause_042_named_pivot_transfer_smogtours-gen2ou-931095_2026-05-14.md`
shows the regression has not transferred yet. The final-answer gate must be
mechanical: after naming a pivot, ask whether the selected action affects that
pivot. Earthquake into a named Zapdos pivot and Thunder into a named Steelix
pivot are uncovered branches, not acceptable active-target pressure. Spikes
into Thunder is different: it explicitly accepts the attack branch for a route
gain.
`workspace/quick_tests/replay_turn_pause_043_named_pivot_gate_transfer_smogtours-gen2ou-930771_2026-05-14.md`
shows the mechanical gate transferred: all four p1 decisions checked whether
the chosen action affected the named pivot. The next ordering problem is that
the active target can still be the larger branch after the pivot gate. In the
replay, Gengar's Hypnosis, Gengar's escape/trap branch, and sleeping
Tyranitar's current trapper seat mattered more than over-centering Steelix.
`workspace/quick_tests/replay_turn_pause_044_active_target_after_pivot_gate_smogtours-gen2ou-929268_2026-05-14.md`
adds the next split: after the pivot gate, distinguish an active attack that is
easy for the opponent to cover from an active progress move that improves
through the expected response. Zapdos attacking Skarmory was easy to answer
with revealed Raikou, so the Snorlax double was stronger. One turn later,
Snorlax did not need the immediate Zapdos double because Curse improved
through the expected Skarmory response. Do not double just because the pivot
is obvious if the active move already changes the next board through that
pivot. `workspace/quick_tests/pivot_progress_after_gate_probe_001_2026-05-14.md` turns
this into a four-way regression: active attack, active progress, route denial,
and side-known own-team answer.
`workspace/quick_tests/replay_turn_pause_045_sleep_clause_clamp_explosion_growth_smogtours-gen2ou-927169_2026-05-14.md`
shows the regression is not yet stable. Espeon Psychic hit the active
Nidoking, but the expected Snorlax pivot made Growth the better active
progress move. When a wall pivot is obvious, ask whether setup or status makes
that pivot worse before choosing direct damage into the current target.
`workspace/quick_tests/replay_turn_pause_046_special_wall_pivot_ladder_smogtours-gen2ou-925777_2026-05-14.md`
adds the pivot ladder. If the active attack is cleanly covered by a revealed
absorber, double. If the active Pokemon has coverage into the expected wall,
use coverage rather than generic setup. If setup, status, or hazards improve
through the expected response, take that progress. If a recurring answer such
as Roar can deny the active route, do not cash out with Explosion merely
because the route is scary.
`workspace/quick_tests/special_wall_pivot_ladder_probe_001_2026-05-14.md` turns the
ladder into a four-scenario regression: absorber double, coverage into wall,
preserve support for a recurring answer, and Roar before Explosion.
`workspace/quick_tests/replay_turn_pause_047_special_wall_pivot_ladder_transfer_smogtours-gen2ou-925686_2026-05-14.md`
adds two refinements. First, ask whether the active route needs a status clock
before hazards; Toxic into +1 Snorlax was better than Spikes-first. Second,
forced switch does not automatically mean setup. If the incoming pivot can
threaten status, Explosion, recovery, or immediate counterplay, direct damage
or coverage into that pivot can beat boosting. Zapdos also showed the same
coverage principle: Thunder into Exeggutor lost to the Steelix branch, while
Hidden Power covered it.
`workspace/quick_tests/forced_switch_pivot_damage_probe_001_2026-05-14.md` turns this
into four checks: status before hazard, hazard after clock, damage before setup
into a punishing pivot, and coverage before Electric STAB into a Ground/Steel
branch.
`workspace/quick_tests/replay_turn_pause_048_hard_answer_before_status_smogtours-gen2ou-924922_2026-05-14.md`
adds the clean-answer exception. If support is already delivered and a
recurring hard answer can enter without losing the route, use the answer before
adding status. After the hard answer enters, do not assume the next move is
always Toxic or phazing; if the attacker has shown only resisted physical
damage, counter-setup can improve the answer's position before phazing becomes
necessary. `workspace/quick_tests/hard_answer_before_status_probe_001_2026-05-14.md`
turns this into three checks: hard answer before more support, counter-setup
before phaze, and re-solve immediately if coverage invalidates the hard answer.
`workspace/quick_tests/replay_turn_pause_049_coverage_reveal_absorber_smogtours-gen2ou-924921_2026-05-14.md`
tests that re-solve. Snorlax revealing Fire Blast into Cloyster invalidated the
old clean-answer map, but it did not mean Snorlax should keep attacking. After
Cloyster survived and could threaten Explosion, the Snorlax side pivoted
sleeping Moltres into the support piece, accepting Spikes while preserving the
Fire Blast Snorlax route.
`workspace/quick_tests/coverage_reveal_absorber_probe_001_2026-05-14.md` turns this into
three checks: coverage reveal invalidates the clean answer, the invalidated
answer may still deliver support before cash-out, and a sleeping absorber can
protect the revealed coverage user from Explosion.
`workspace/quick_tests/replay_turn_pause_052_lovely_kiss_snorlax_sleep_pivot_smogtours-gen2ou-923076_2026-05-14.md`
adds damage-and-recoil pricing into the pivot ladder. If the active Pokemon
survives the hit and its damage plus the opponent's recoil materially improves
the route, staying can beat an immediate nominal-answer switch. Re-solve after
that trade: once the active falls into KO range, choose the absorber that
covers the most likely coverage branch, not merely the one that covers the
obvious STAB.
`workspace/quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
adds the RestTalk inference boundary. Rest reveals recovery, not Sleep Talk.
If a sleeping Snorlax has not revealed Sleep Talk and a lower-value teammate
can absorb the immediate hit while preserving the anchor, switching can be
better than assuming Sleep Talk is the active route.

Exceptions: when behind with no slow route left, a high-risk line can become
the only real winning route.

Worst branch: an unnecessary read gives the opponent a free route when the
simple move already kept control.

Local status: fully transferable as an abstract principle, but exact branch
severity depends on local damage and boss AI incentives.

## STP-005: Spikes Need Support If They Are The Plan

Source: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes)

Trigger: the battle plan depends on keeping hazards up over multiple turns.

Policy: if hazards are central, also plan how to stop or punish removal:
spinblock, pressure the spinner, trap or weaken support, or use the hazard turn
to force progress elsewhere.

Exceptions: short offensive route where a temporary layer already creates the
needed breakpoint, or no relevant grounded switching remains.

Worst branch: spending repeated turns setting hazards while the opponent spins
freely or uses those turns to set up.

Local status: transfer cautiously because romhack three-layer Spikes increases
the upside and the punishment for losing hazard tempo.

Replay update:
`workspace/quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`
adds the predicted-cash-out Spin window. When low Cloyster threatens Explosion
and the opponent is likely to switch a lower-value absorber into the cash-out,
Rapid Spin can be the better route move than booming. After the Spin, re-solve:
the opponent may reset Spikes immediately, and the next support move may be
Surf chip, Toxic into the handoff, another Spin, or Explosion depending on
which branch keeps the hazard loop favorable.

## STP-006: Save The Converter Until Its Blockers Are Priced

Source: Smogon, [Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking)

Trigger: a sweeper, setup user, cleaner, or boss-answer piece can win later.

Policy: keep the converter healthy until its blockers are revealed, weakened,
removed, or forced into a predictable recovery/status turn.

Exceptions: the converter must enter now to prevent an irreversible route, or
all safer routes are already losing.

Worst branch: the converter enters early, exposes its set, takes status/chip,
or is forced out before the board is prepared.

Local status: highly transferable; local damage, boss roster, and AI incentives
decide which blocker must be prepared first.

## STP-007: Sacrifice Only When The Lost Role Is Accounted For

Source: Smogon, [Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking)

Trigger: a sack, Explosion, or low-HP cash-out looks attractive.

Policy: before sacrificing, name what route the sacrifice opens and what answer
or support job disappears afterward.

Exceptions: the sacrificed piece has no live role, or the sacrifice creates the
only realistic route from a losing board.

Worst branch: the sacrifice wins one exchange but removes the only answer to a
later threat.

Local status: fully transferable, but role accounting must use the romhack boss
roster rather than competitive species assumptions.

## STP-008: Setup Is Good Only If The Boost Changes The Next Board

Source: Smogon, [An Introduction to Setup Moves](https://www.smogon.com/smog/issue26/setting_up)

Trigger: a boost move is available instead of attacking, switching, recovering,
or denying support.

Policy: set up when the next boost changes a named blocker, KO range, speed
relation, defensive survival point, or forced response and the opponent cannot
immediately erase or punish it. After a boost lands, re-score the marginal next
boost. If the current boost is already sufficient to convert, attack, pivot, or
recover instead of boosting again.

Replay update: `workspace/quick_tests/replay_turn_pause_047_special_wall_pivot_ladder_transfer_smogtours-gen2ou-925686_2026-05-14.md`
adds the forced-switch boundary. A forced switch is only a setup turn if the
incoming pivot cannot immediately punish the boost. If the likely pivot can
spread status, Explode, recover, phaze, or force the booster out, direct damage
into the pivot may be the better route move.
`workspace/quick_tests/forced_switch_pivot_damage_probe_001_2026-05-14.md` makes this a
regression: do not Swords Dance on a forced exit if Exeggutor or another
punishing pivot can enter and take control immediately.

Exceptions: direct attack already removes the blocker, or the setup turn gives
the opponent phazing, Haze, Encore, status, Explosion, recovery reset, or a
lethal hit.

Worst branch: the boost looks productive but the opponent's next action makes
it irrelevant; or the first boost was correct, but a greedy second boost gives
the opponent the turn that erases the route.

Local status: transferable as route logic; exact stat stages and anti-setup
tools must be checked against GSC/romhack mechanics. The romhack uses Gen 2
stage multipliers over computed battle stats, and Dragon Dance is not plain
`+Atk`: local docs say it raises the user's current higher offensive stat, then
Speed. Exact setup advice must cite `docs/agent_navigation/hack_mechanics_reference.md`,
`docs/agent_navigation/gen2_vs_modern_mechanics.md`, and `data/moves/moves.asm`
when the affected stat changes the move choice.

## STP-009: An Answer Is Only As Good As Its Entry

Sources: Smogon, [What are Checks and Counters?](https://www.smogon.com/smog/issue32/checks-and-counters),
[Pivots in SM OU](https://www.smogon.com/articles/pivots-sm-ou), and
[Teambuilding Guide](https://www.smogon.com/forums/threads/teambuilding-guide.3552468/)

Trigger: we are relying on a Pokemon to answer a threat.

Policy: label the answer precisely: counter, hard-switch answer, free-entry
check, revenge check, one-time emergency, or not an answer after hazards/status.
If the label is not "hard-switch answer," name the entry method before making
the move: KO, pivot, forced recovery, lock, phazing/Haze turn, controlled sack,
or abandoning the long route for a shorter one.

Exceptions: if no true entry exists, create one through a KO, pivot, forced
recovery, lock, sack, or phazing turn.

Worst branch: treating a revenge check as a counter and losing it on entry.

Local status: strongly transferable; local hazard layers, passive abilities,
and type-chart deltas decide whether entry is real.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/check_durability_boss_examples.md`,
`worked_examples/entry_creation_ladder_boss_examples.md`, and
`worked_examples/controlled_sack_for_clean_entry_boss_examples.md`.

## STP-010: Lead Choice Must Preserve The Team's Later Jobs

Sources: Smogon, [Your Lead Pokemon](https://www.smogon.com/rs/articles/your_starter_pokemon),
[Creating / Selecting a Lead](https://www.smogon.com/smog/issue10/leads), and
[An Analysis of Leads in GSC OU](https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/)

Trigger: choosing a lead or judging whether the active should spend HP/status
on the opening exchange.

Policy: lead with a piece whose opening job fits the route without wasting the
piece's best later function. When multiple openers are plausible, judge the
lead by the opener set and by full-fight usability after turns 1-2, not by its
best single matchup. In no-preview GSC-style formats, the lead should create
useful contact value against the likely opener field: information, status,
hazards, forced switch, item removal, phazing, or safe pivot tempo.

Exceptions: an early denial job is more valuable than the later job, or the
later job is duplicated elsewhere.

Worst branch: a flashy opening turn burns the one Pokemon needed for the boss's
real route, or a lead wins one possible opener while losing to the adaptive
opener set.

Local status: highly relevant to boss planning because known boss rosters and
no-preview player information make lead role fit more important than
competitive lead fashion. Use `boss_route_maps/adaptive_lead_audit_2026-05-13.md`
before assuming the first listed boss Pokemon is guaranteed to lead, and keep
boss AI lead/move logic tied to public player information rather than the
unrevealed player team.

## STP-011: Core Synergy Means Removing Each Other's Blockers

Source: Smogon, [Synergy and Cores](https://www.smogon.com/resources/beginner/synergy)

Trigger: choosing between damage, status, trap, hazard, setup, pivot, or
sacrifice when multiple teammates could become the route.

Policy: prefer actions that remove or weaken the blocker to a teammate's live
route, not just actions with good type matchup into the active Pokemon.

Exceptions: immediate defensive catastrophe, forced survival, or a route that
does not need teammate support.

Worst branch: winning the visible exchange while leaving the real blocker
untouched.

Local status: transferable, but romhack passives and boss movesets can change
which blocker matters.

## STP-012: Known Boss Roster Starts The Route Ledger

Sources: Smogon, [Taking Advantage of Team Preview](https://www.smogon.com/tiers/ou/advantage_team_preview) and
[Preview Analysis](https://www.smogon.com/forums/threads/preview-analysis-a-guide-to-starting-the-game-right.3664910/)

Trigger: boss roster or likely adaptive opener set is known before turn 1.

Policy: identify the boss's routes, our blockers, the pieces to preserve, and
the source-supported opener subset before choosing the lead or first move.
Known-roster planning is useful only if it changes the opening plan and
continues to dictate strategy after turn 1. This is not a Team Preview
mechanic: the player-side advisor may inspect boss data before a planned fight,
but boss AI must not know the unrevealed player team.

Exceptions: if the boss has a fixed opener, route planning still matters but
lead-probability work narrows.

Worst branch: choosing a lead to beat one opener while losing to the route the
roster actually enables, or letting later-generation preview assumptions hide
the fact that Gen 2/Gym Leader Lab information arrives through leads, source
data, and reveals over time.

Local status: directly applicable for player-side boss preparation because
boss rosters are visible in source; opening policy still needs the local
fixed/adaptive map. For boss AI, the same policy must be rewritten around
public state and revealed player information only.

## STP-013: Forcing A Pivot Is Progress Only With A Follow-Up

Sources: Smogon, [Fundamental Tactic: The Double Switch](https://www.smogon.com/forums/threads/fundamental-tactic-the-double-switch.3495451/) and
[Pivots in SM OU](https://www.smogon.com/articles/pivots-sm-ou)

Trigger: our attack threatens the active, but the opponent has an obvious
switch or pivot response.

Policy: use the forcing move when it KOs or pressures the active and the pivot
branch is survivable or punishable next turn.

Exceptions: double-switch or coverage rises when the pivot is highly
incentivized, the current hit gains little, and the wrong branch is tolerable.

Worst branch: calling a move good because it wins the stay-in branch, then
having no plan for the obvious pivot.

Local status: transferable, but boss AI incentives and local type/passive
damage decide whether the pivot branch is real.

## STP-014: Reveal The Hidden Resource Only When It Hits The Route Blocker

Sources: Smogon, [How To Effectively Surprise Your Opponent](https://www.smogon.com/articles/surprise-your-opponent),
[The Concept of Lures](https://www.smogon.com/smog/issue1/concept_of_lures), and
[Effective Lures in OU](https://www.smogon.com/smog/issue37/effective-lures-in-ou)

Trigger: we have a hidden move, one-time item, unexpected coverage, unusual
speed, or reveal-dependent line that could punish an expected answer.

Policy: reveal it only when the target is the blocker to a named route, the
reveal removes or cripples that blocker, and spending the surprise now is more
valuable than holding it for a later blocker.

Exceptions: reveal earlier if waiting lets the blocker become unremovable, if
the current target is the only realistic route blocker, or if hiding the
resource creates a worse immediate catastrophe.

Worst branch: the reveal wins the visible exchange but fails to touch the
actual route blocker, so the opponent or boss preserves the piece that still
invalidates our endgame.

Local status: strongly transferable as route logic. Human expectation
management does not automatically transfer to boss AI, but the narrower rule
does: spend route-specific resources on route-specific blockers, not on the
first target that makes the move look clever.

Local drills: `worked_examples/reveal_timing_lure_boss_examples.md` and
`worked_examples/clair_dragonair_suicune_hidden_coverage.md`.

## STP-015: Scouting Is Progress Only If The Protected Turn Has A Job

Sources: Smogon, [Safe Battling: How to use Protection](https://www.smogon.com/smog/issue22/safe_battling) and
[Substitute Analysis](https://www.smogon.com/rs/articles/substitute)

Trigger: Protect, Detect, Substitute, Endure, Focus Band, or another block /
survival branch can scout, absorb, or delay the intended move.

Policy: use or respect the protection state when the protected turn changes a
route: confirms decisive information, blocks status, enables setup or Focus
Punch, gains needed recovery, stalls a clock, preserves a key answer, or
punishes the opponent's locked / forced move.

Exceptions: attack or pivot instead when protection only donates a free setup,
hazard, recovery, switch, or scouting turn to the opponent, or when the move
being scouted is already priced well enough to choose.

Worst branch: we call the protected turn safe, but it gives the opponent the
exact free turn needed for setup, hazards, recovery, trapping, or entry into a
harder route.

Local status: transferable, but local move data decides priority, PP, failure
rules, Focus Band behavior, and whether the protected branch is legal in the
romhack.

Local drills: `worked_examples/protection_state_boss_examples.md`,
`boss_route_maps/brock_turn1_route_sheet.md`, and
`boss_route_maps/will_turn1_route_sheet.md`.

## STP-016: A Lock Is A Route Commitment

Sources: Smogon, [Move Restriction Guide](https://www.smogon.com/dp/articles/move_restrictions) and
[Risk/Reward](https://www.smogon.com/resources/beginner/bw_risk_reward)

Trigger: a move or effect commits future turns or restricts move choice:
Choice item lock, Encore, Disable, Taunt, Rollout / Ice Ball, Outrage /
Thrash / Petal Dance, charge moves, recharge moves, or similar local effects.

Policy: commit to the lock only when the first committed turn changes the
route, the opponent's punish branches are reduced, and the board after the
forced sequence is favorable or forced. Against a locked opponent, stop the old
plan and ask what the lock now lets us enter, set up, heal, phaze, status, or
KO safely. Before using a lock claim, separate move selection, execution,
success, and PP loss; the correct punish can change if a move was selected but
not executed, executed but failed, executed over multiple turns from one
selection, or followed by a recharge turn that is not itself a move execution.

Exceptions: delay the lock when the first hit is only chip, the user still
needs flexible recovery/status/switch options, the opponent can pivot to a
punish, or the lock exposes an irreplaceable piece. Use a control lock such as
Encore only when the last move, speed, PP, and follow-up are known enough to
make the forced turns valuable.

Worst branch: the move looks decisive, but the forced sequence gives the
opponent a predictable punish turn or removes the user's ability to recover,
switch, status, or answer the next route.

Local status: transferable as route logic. Exact behavior must use the romhack
source for lock duration, PP, recharge, Rollout / Outrage handling, Choice Band,
Encore, Disable, Taunt, AI scoring, and boss-specific move legality.

Local drills: `worked_examples/whitney_miltank_rollout_commitment.md`,
`worked_examples/whitney_miltank_geodude_player_turn_drill.md`,
`worked_examples/blue_pre_battle_route_sheet.md`, and
`worked_examples/clair_dragonair_suicune_hidden_coverage.md`.

## STP-017: Recovery Is A Route Reset Unless It Is Forced Or Denied

Sources: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
[Stallbreakers in ORAS OU](https://www.smogon.com/articles/ou-stallbreakers), and
[A Guide to Stallbreakers](https://www.smogon.com/smog/issue18/stallbreakers)

Trigger: Recover, Rest, Milk Drink, Morning Sun, Synthesis, Moonlight,
Soft-Boiled, Wish-like timing, or item recovery can erase the current damage
race.

Policy: attack a recovery user when the hit KOs, forces recovery at a
punishable time, crosses a future threshold, or denies the recovery move by
status, Taunt-like control, Encore timing, PP pressure, trapping, weather,
Explosion / sacrifice, or safe entry for the real breaker.

Exceptions: heal or pivot instead when the recovered piece remains an
irreplaceable answer and healing preserves the route, or when attacking only
feeds a recovery loop that the opponent owns.

Worst branch: we trade harmless chip into repeated recovery, letting the
opponent reset HP while gaining hazards, status, setup, PP advantage, or safe
entry for a later route.

Local status: directly relevant to boss fights. Exact advice must verify local
recovery amounts, PP, weather effects, Rest sleep behavior, items, and whether
the current damage range actually beats the recovery window.

Local drills: `worked_examples/misty_starmie_meganium_player_turn_drill.md`,
`worked_examples/standard_function_denial_boss_examples.md`,
`worked_examples/brock_pre_battle_route_sheet.md`, and
`worked_examples/blue_pre_battle_route_sheet.md`.

## STP-018: Weather Ownership Is A Five-Turn Route Clock

Sources: Smogon, [A Guide to Common Battle Conditions](https://www.smogon.com/resources/beginner/battle_conditions) and
[Rain Offense Guide](https://www.smogon.com/dp/articles/rain_offense)

Trigger: Rain Dance, Sunny Day, Sandstorm, weather-dependent recovery, Thunder,
SolarBeam, Fire / Water damage changes, or weather chip can affect the next
several turns.

Policy: treat weather as a finite route clock. Set or preserve weather only
when the team can convert the turns into KOs, forced recovery, safe entry,
accuracy, charge-turn removal, recovery math, or endgame cleanup. Defend
against weather by punishing the setup turn, forcing the weather owner to spend
turns switching / recovering / using weak coverage, changing the weather, or
preserving the one piece that still answers the payoff.

Exceptions: do not spend a weather turn when the payoff piece is blocked,
statused, too low, outsped by priority, or when the opponent can stall the
clock while improving a stronger route. Do not use clear-weather answer labels
after weather changes damage or recovery math.

Worst branch: the weather setter gets a free turn, the player keeps following
the clear-weather plan, and the boss converts the limited window into a KO,
sleep/status bridge, SolarBeam punish, boosted Fire / Water damage, or recovery
reset.

Local status: directly applicable, but every weather claim must use romhack
mechanics for turn count, Thunder accuracy, SolarBeam, Fire / Water modifiers,
Synthesis / Morning Sun / Moonlight, passive type abilities, and local boss AI
weather scoring.

Local drills: `worked_examples/weather_clock_boss_examples.md`,
`worked_examples/misty_pre_battle_route_sheet.md`,
`worked_examples/blaine_pre_battle_route_sheet.md`,
`worked_examples/erika_pre_battle_route_sheet.md`, and
`worked_examples/red_30_turn_final_boss_ledger_drill.md`.

## STP-019: Screens Are A Finite Route Window

Sources: Smogon, [A Guide to Common Battle Conditions](https://www.smogon.com/resources/beginner/battle_conditions) and
[Dual Screens discussion](https://www.smogon.com/forums/threads/dual-screens-reflect-and-light-screen.3491571/)

Trigger: Light Screen or Reflect is active, can be set, or changes the damage
category that decides the current route.

Policy: set a screen only when the protected turns let a specific teammate
enter, set up, survive a threshold, force recovery, deny priority range, or
preserve an irreplaceable answer. When the opponent sets a screen, start a turn
counter and re-rank move categories: attack through the unprotected category,
force progress that ignores the screen, stall only if stalling does not give
the opponent a stronger route, or remove / deny the screen setter before the
receiver appears.

Exceptions: do not set a screen if the setup turn gives the opponent a KO,
Encore, phaze, Haze, trap, hazard, recovery reset, or setup route that matters
more than the reduced damage. Do not keep attacking into the blocked category
unless the damage still crosses a route threshold.

Worst branch: the screen turn looks defensive, but it delivers the real
converter safely, or we keep using the wrong damage category while the screen
clock becomes the opponent's setup window.

Local status: directly applicable. Use romhack evidence for screen duration,
damage category, critical-hit behavior through screens, Encore timing, AI
screen scoring, and whether the target route is physical, special, mixed, or
non-damage.

Local drills: `worked_examples/bugsy_scyther_answer_thresholds.md`,
`worked_examples/lt_surge_pre_battle_route_sheet.md`,
`worked_examples/sabrina_30_turn_ledger_drill.md`,
`worked_examples/sabrina_low_hp_support_job_stress_test.md`, and
`worked_examples/red_30_turn_final_boss_ledger_drill.md`.

## STP-020: Speed Control Ends At The Real Move-Order Exception

Sources: Smogon, [Get Your Priorities Straight](https://www.smogon.com/bw/articles/ou_priority_guide),
[Priority Analysis Across All Generations](https://www.smogon.com/articles/priority-through-generations), and
[GSC Move Priority](https://www.smogon.com/gs/articles/move_priority)

Trigger: a faster Pokemon, boosted Pokemon, Choice Scarf user, or revenge
piece is being treated as a cleaner while the opponent has priority, Quick
Claw, Protect / Endure, Focus Band, lock-in, recharge, paralysis, or another
turn-order / survival branch.

Policy: before calling the route a clean revenge or sweep, write the real
move-order ledger: priority bracket, Speed within bracket, item branches,
entry-hazard HP, and whether the priority or survival branch KOs, only chips,
or puts the cleaner into the next threat's range. If priority is lethal or
spends an irreplaceable cleaner, use a bulkier answer, preserve the cleaner,
force recoil / lock / PP first, or create a controlled sack entry. If priority
does not change the route, do not over-preserve; finish the forced line.

Exceptions: a priority move can be exploitable when it is weak, resisted by the
current entry, forced by lock or range, low on PP, or fails to stop the next
job. In that case, the priority user may be the one donating setup, recovery,
hazard, recoil, or safe-entry value.

Worst branch: the advice says "we are faster" and ignores that the boss acts
first through priority or Quick Claw, or that Focus Band / Endure leaves the
target alive for one more route-changing action.

Local status: directly applicable. In the romhack, `docs/agent_navigation`
records Quick Attack, Mach Punch, and ExtremeSpeed as the same
`EFFECT_PRIORITY_HIT` tier; Protect / Endure are higher; Quick Claw is a
separate 60/256 turn-order branch. Exact advice still needs local damage,
type/passive, item, lock, recharge, and AI evidence.

Local drills: `worked_examples/priority_revenge_range_boss_examples.md`,
`worked_examples/blaine_pre_battle_route_sheet.md`,
`worked_examples/bruno_pre_battle_route_sheet.md`,
`worked_examples/red_30_turn_final_boss_ledger_drill.md`, and
`worked_examples/endgame_forced_line_boss_examples.md`.

## STP-021: Status Is Assignment Plus Reset Map

Sources: Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
[Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes), and
[Status in DP](https://www.smogon.com/dp/articles/status)

Trigger: sleep, paralysis, poison, burn, confusion, trap status, Heal Bell,
Rest, Safeguard, Full Heal, Full Restore, or item cure can decide whether the
current route survives.

Policy: before using, accepting, or ignoring status, assign the status to a
specific route job. On offense, status is progress only if it changes Speed,
recovery pressure, hazard damage, setup safety, forced Rest, cure timing, or an
endgame clock before it is reset. On defense, the absorber is the Pokemon whose
remaining jobs still work with that exact status, not automatically the lowest
HP or least flashy piece. If no such absorber exists, deny the status user or
shorten the route instead of treating status as harmless.

Exceptions: status falls when the target is already statused, immune, protected
by Safeguard or clause, likely RestTalk / cleric-supported, or when the boss
can cure without losing a useful turn. Status rises again after the cure item,
Heal Bell, or Rest route is spent, or when forcing the reset creates safe
entry, setup, phazing, hazard damage, or a KO threshold.

Worst branch: we land status but only trigger a cheap reset, or we "absorb"
status with the only piece that still answers the boss's next converter.

Local status: directly applicable. Local advice must verify Sleep Clause,
status immunities, Safeguard timing, Rest / Sleep Talk, item cures, Full Heal /
Full Restore rosters, type passives, and whether the boss uses the status turn
to enable rain, screens, trapping, recovery, setup, or priority cleanup.

Local drills: `worked_examples/status_absorber_assignment_boss_examples.md`,
`worked_examples/status_reset_map_boss_examples.md`,
`worked_examples/misty_pre_battle_route_sheet.md`,
`worked_examples/sabrina_pre_battle_route_sheet.md`, and
`worked_examples/koga_pre_battle_route_sheet.md`.

## STP-022: Support Chains Are Judged At The Receiver

Sources: Smogon, [DPP Baton Pass Guide](https://www.smogon.com/dp/articles/baton_pass_chains) and
[ADV Baton Pass Chain](https://www.smogon.com/resources/competitive/rs/baton_pass)

Trigger: the opponent can combine Baton Pass, screens, stat boosts, trapping,
Substitute, sleep, Encore, recovery, or sacrifice to deliver a later receiver.

Policy: do not grade the support Pokemon by immediate damage. Name the
receiver, the support being delivered, the stop turn, and the piece that still
answers the receiver after support lands. If the chain is one turn from making
the receiver unanswerable, denial outranks slow value such as hazards, status,
or chip. If the receiver answer is still healthy and the pass is not yet live,
preserve that answer instead of spending it to win the support one-on-one.

Exceptions: attacking the support user rises when it removes the pass before
the receiver can enter, forces a bad receiver entry, or makes the passed board
still answerable. Preserving or pivoting rises when the current active is the
only receiver answer and the support user is trying to tax it before the pass.

Worst branch: we ignore a low-damage support Pokemon until it passes the exact
boost, screen, trap, or safe entry that makes the real converter win, or we
spend the only receiver answer beating the support user.

Local status: directly applicable to Bugsy and any boss with Baton Pass or
multi-turn support. Verify local Baton Pass behavior, screen turns, passed
boosts, phazing / Haze / Encore timing, item thresholds, and whether the boss
AI can or will pass into the named receiver.

Local drills: `worked_examples/bugsy_pre_battle_route_sheet.md`,
`worked_examples/bugsy_scyther_answer_thresholds.md`,
`worked_examples/smogtours_604744_support_delivery_cascade.md`, and
`worked_examples/boss_live_turn_prompt_cards.md`.

## STP-023: Degraded Pieces Need New Job Labels

Sources: Pokemon Showdown replay, [smogtours-gen2ou-908690](https://replay.pokemonshowdown.com/smogtours-gen2ou-908690),
Smogon forum source, [SPL XVII Week 5](https://www.smogon.com/forums/threads/smogon-premier-league-xvii-week-5.3777540/), and
local review `reviews/2026-05-13_smogtours-gen2ou-908690.md`

Trigger: a Pokemon misses a key move, is slept, paralyzed, heavily chipped,
forced out, loses its first target, or otherwise no longer performs its
original broad role.

Policy: immediately relabel the piece by remaining real jobs before deciding
whether to preserve, spend, or sacrifice it. A damaged sleep user may still be
an Explosion converter; a sleeping RestTalk attacker may still be the planned
endgame; a low-HP support piece may still have one pass, phaze, status, spin,
screen, or sack-entry job. Preserve only if that narrow job has a live trigger;
spend it when the target or route is now present; sacrifice only after proving
no remaining job changes the route.

Exceptions: do not preserve a degraded piece by inertia. If its remaining job
has no receiver, no target, no legal timing, no survival path, or no route
impact after local mechanics are checked, it can become sack material.

Worst branch: bad luck invalidates the original plan, and the advisor either
keeps following the dead script or throws away a piece that still has the one
action needed to convert the new route.

Local status: directly applicable. Boss advice should track degraded jobs
after sleep, paralysis, poison, accuracy drops, Focus Band, Quick Claw, failed
status, item loss, hazard chip, and changed boss roster state. Use local
mechanics for RestTalk, items, passives, hazards, Speed, and whether the narrow
job still works.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/sabrina_low_hp_support_job_stress_test.md`,
`worked_examples/red_late_weather_support_job_stress_test.md`, and
`worked_examples/primary_to_backup_route_handoff_boss_examples.md`.

## STP-024: Temporary Disable Must Be Cashed Out Before Reset

Sources: Pokemon Showdown replay, [smogtours-gen2ou-905952](https://replay.pokemonshowdown.com/smogtours-gen2ou-905952),
Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status), and
local review `reviews/2026-05-13_smogtours-gen2ou-905952.md`

Trigger: freeze, sleep, confusion, recharge, lock-in, trapping, Destiny Bond,
Perish Song, Curse, Pain Split, or another temporary agency change creates an
apparent opening.

Policy: treat temporary control as a route discount, not ownership. Name the
converter, the cash-out move, the reset route, and the material that must be
preserved until the position is actually closed. If the disabled target can
Rest, wake, switch, stall, cure, use Sleep Talk, or force a trade before the
cash-out happens, the advisor must either deny that reset or preserve the piece
that still converts after the reset.

Exceptions: if the control state already creates a forced win, immediate KO, or
unavoidable endgame clock, cash out now rather than over-preserving. If no
converter can reach the target before the reset, abandon the old route and
build the backup plan instead of pretending the disable solved the battle.

Worst branch: the target is frozen, asleep, confused, locked, or recharging,
so the advisor declares the route won, spends the converter, and then the boss
Rests, wakes, switches, cures, or trades into a board where the remaining team
cannot finish.

Local status: directly applicable. Boss fights can create false solved states
through freeze, sleep, confusion, recharge, Focus Band, Quick Claw, lock-in,
Encore, Rest, item cures, and AI switch incentives. Exact advice must verify
local status duration, Rest / Sleep Talk, cure items, switch rules, and whether
the converter still survives the reset branch.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/status_reset_map_boss_examples.md`,
`worked_examples/endgame_forced_line_boss_examples.md`, and
`worked_examples/red_sequential_converter_pressure_stress_test.md`.

## STP-025: Rebuild The Route Map After Every One-Time Trade

Sources: Pokemon Showdown replay, [smogtours-gen2ou-930772](https://replay.pokemonshowdown.com/smogtours-gen2ou-930772),
Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion), and
local review `reviews/2026-05-13_smogtours-gen2ou-930772.md`

Trigger: Explosion, Self-Destruct, Destiny Bond, Perish Song, Focus Band,
Endure, a forced sack, a lure, a trap, or another one-time resource removes or
spends a piece.

Policy: after the trade resolves, stop and rebuild both route maps before
choosing the next one-time action. The next trade is good only if it removes
the new live converter, preserves the current winning route, or simplifies into
a known winning endgame. Do not let a previous good trade justify a second
trade by momentum; prove the target, lost role, next entry, and remaining boss
route from the new board.

Exceptions: if the game has already simplified into a forced endgame, the next
trade can be immediate. If the first trade exposes an urgent opposing converter,
defensive trading can dominate slower value. If the remaining route map is
unclear, preserve one-time resources until the target and beneficiary are
named.

Worst branch: the first trade was correct, but the advisor spends the next
Explosion, sack, Focus Band, phazer, or status absorber without recalculating,
leaving only a paralyzed anchor, uncovered ace, weather payoff, spinner,
recovery loop, or setup sweeper to win for the opponent.

Local status: directly applicable. In Gym Leader Lab, one-time resources
include Explosion, Destiny Bond, Perish-style clocks, Focus Band survival,
limited phazing / Haze / status windows, item cures, and sacrificing a unique
answer. Exact advice must use local rosters, AI incentives, damage, type
passives, item behavior, and remaining boss route priority.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/risk_posture_boss_examples.md`,
`worked_examples/endgame_forced_line_boss_examples.md`,
`worked_examples/controlled_sack_for_clean_entry_boss_examples.md`,
`worked_examples/smogtours_902742_staged_one_time_trades.md`, and
`worked_examples/boss_route_triage_examples.md`.

## STP-026: PP Is Route Material Only When A Scarce Move Gates The Route

Sources: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
local reviews `reviews/2026-05-13_smogtours-gen2ou-933547.md` and
`reviews/2026-05-13_smogtours-gen2ou-909431.md`

Trigger: a long loop, recovery war, hazard war, phazing / Haze sequence, spin
contest, Rest cycle, low-PP attack, or stalled endgame may make PP decide the
route.

Policy: count PP only for moves that gate a concrete route. Before spending or
trying to exhaust PP, name the scarce move, owner, remaining PP, route it
protects, route it attacks, what forces it, what conserves it, and what changes
when it reaches zero. If zero PP does not change the win route, this is not a
PP plan; look for HP, status, hazard, setup, recovery, or entry progress
instead.

Exceptions: do not chase high-PP exhaustion, such as Rapid Spin, when HP,
entry access, spinner survival, spinblock timing, or the setter's survival will
fail first. Spending scarce phazing, Haze, recovery, or coverage PP is correct
when it denies a live route or preserves the endgame; wasting it into a
contained board can lose the real clock.

Worst branch: the advisor calls the fight a PP war and spends the only
recovery, phaze, Haze, Spin, or coverage PP that still keeps the route alive,
or keeps attacking into a larger reset budget without creating entry, setup,
status, hazard, or KO progress.

Local status: directly applicable. Use local `data/moves/moves.asm` PP,
romhack recovery/weather behavior, three-layer Spikes, Rapid Spin clearing,
Rest / Sleep Talk behavior, boss items, and AI incentives before making exact
PP claims.

Local drills: `worked_examples/pp_budget_ledger_boss_examples.md`,
`worked_examples/smogtours_909431_contained_waiting_loop.md`,
`worked_examples/endgame_forced_line_boss_examples.md`,
`worked_examples/will_hazard_retention_stress_test.md`, and
`worked_examples/karen_hazard_retention_stress_test.md`.

## STP-027: Waiting Is Legal Only Inside A Contained Winning Loop

Sources: Pokemon Showdown replay, [smogtours-gen2ou-909431](https://replay.pokemonshowdown.com/smogtours-gen2ou-909431),
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes), and
local review `reviews/2026-05-13_smogtours-gen2ou-909431.md`

Trigger: a low-effect, no-effect, defensive, recovery, failed-hazard,
repeated pivot, or waiting move looks passive while an external clock may
already be doing the work.

Policy: waiting is correct only when the position is contained: the opponent's
live punish branches are covered, the irreplaceable answer remains healthy
enough, and an external clock continues to improve the route. Name the clock,
the containment piece, and the covered punish before choosing the low-effect
move. If the opponent can set up, heal, spin, remove an answer, pass support,
or force a new route, waiting becomes passivity.

Exceptions: a no-effect move can be acceptable when it preserves a winning
loop, burns finite weather / screen / Safeguard turns, lets poison / hazards /
recoil / Rest sleep finish the job, or avoids opening the only answer. It is
catastrophic when the same move gives an uncontained boss route a free turn.

Worst branch: the advisor calls a passive turn "patience," but the opponent
uses it to create a live setup, recovery, spin, weather, screen, status, or
trade route, while the external clock was not actually winning.

Local status: directly applicable. In Gym Leader Lab, waiting can be correct
during poison, recoil, weather, Safeguard, screen, Rest sleep, Perish, trap, or
hazard clocks only after verifying local turn counts, AI incentives, recovery
/ items, and whether the answer can still enter after hazards / status /
priority.

Local drills: `worked_examples/smogtours_909431_contained_waiting_loop.md`,
`worked_examples/live_turn_drills.md`,
`worked_examples/pp_budget_ledger_boss_examples.md`,
`worked_examples/weather_clock_boss_examples.md`, and
`worked_examples/endgame_forced_line_boss_examples.md`.

## STP-028: Hazard Plans Need Set, Retain, And Convert

Sources: Smogon, [Opening the Door - A Guide to Entry Hazards](https://www.smogon.com/dp/articles/entry_hazards),
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes), and
local review `reviews/2026-05-13_smogtours-gen4ou-878566.md`

Trigger: a plan depends on Spikes, Toxic Spikes, Stealth Rock, Rapid Spin,
spinblocking, phazing, forced switching, or repeated hazard resets.

Policy: split the hazard route into three jobs before choosing the move:
set, retain, and convert. Set asks who creates the layer and what turn it
costs. Retain asks who stops, punishes, or outpaces removal. Convert asks what
KO range, forced switch, recovery turn, phaze cycle, or cleaner route improves
before the layer disappears. If retain collapses, either convert immediately
or stop treating the layer as the main plan.

Exceptions: a temporary hazard can still be correct when it immediately forces
a key range, denies Focus Sash / Endure-style survival, taxes the next forced
entry, or creates a one-turn trade before the spinner acts. A long hazard war
is bad when the spinner, Haze user, healer, or phazer removes the route at
lower cost than the setter spends creating it.

Worst branch: the advisor keeps stacking or preserving hazards because hazards
are generally strong, while the opponent removes them on the conversion turn
or uses the setter / spinblocker slot collapse to open a cleaner, setup,
recovery, or attrition route.

Local status: directly applicable but mechanics-profile-specific. Gym Leader
Lab has three-layer Spikes and Rapid Spin clearing behavior that must stay
separate from DPP or vanilla GSC. Use local layer count, groundedness, spin
timing, type passives, damage thresholds, and boss AI incentives before calling
a hazard move progress.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/koga_first_three_turn_clock_ownership_drill.md`,
`worked_examples/pryce_30_turn_ledger_drill.md`,
`worked_examples/will_hazard_retention_stress_test.md`, and
`worked_examples/smogtours_878566_hazard_contract.md`.

## STP-029: After Stopping One Route, Name The Board Inheritor

Sources: Smogon, [Prediction and Planning](https://www.smogon.com/smog/issue20/prediction_ubers),
Smogon, [Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking), and
local review `reviews/2026-05-13_smogtours-gen4ou-670049.md`. See also
Smogon, [Mastering the Maison Part 1](https://www.smogon.com/ingame/bc/maison_part1)
for the in-game AI lesson that post-KO replacement may follow policy-shaped
sendout logic rather than human matchup intuition.

Trigger: we just stopped, checked, statused, phazed, traded with, or forced out
the opponent's visible converter or setup route.

Policy: before taking the next move, name who inherits the board. Record the
first route stopped, the answer used, the cost paid by that answer, the
opponent piece or route that benefits from the residue, and our remaining
answer to that next route. If the same answer is now too chipped, statused,
PP-poor, trapped, or exposed to cover the next route, hand off immediately
instead of continuing the old plan.

Exceptions: if the first denial also removes the only remaining converter, the
game may simplify into cleanup or contained waiting. If the opponent's next
route is impossible under public state or already covered by a healthy backup,
the original plan can continue, but the backup must be named.

Worst branch: the advisor celebrates stopping the active threat, then gives the
opponent a free handoff into the next boss ace, weather user, anchor, breaker,
or cleaner because the answer spent to stop route one was also needed for route
two.

Local status: directly applicable. Gym Leader Lab bosses often use staged
pressure: Bugsy support into Scyther, Koga clocks into Crobat / Nidoking,
Lance waves of Dragon setup, Blue adaptive pressure into multiple breakers,
and Red Pikachu / Espeon / Snorlax / weather / Blastoise handoffs. Use local
rosters, AI incentives, damage, and mechanics before deciding whether the
current answer still covers the inheritor. If advising after a KO, do not
assume human-style replacement order; check current boss AI source, trace, or
route-sheet evidence where the replacement choice matters.

Local drills: `worked_examples/smogtours_gen4ou_670049_sequential_converter_pressure.md`,
`worked_examples/primary_to_backup_route_handoff_boss_examples.md`,
`boss_route_maps/misty_turn1_route_sheet.md`,
`worked_examples/red_sequential_converter_pressure_stress_test.md`,
`worked_examples/lance_sequential_setup_wave_stress_test.md`, and
`worked_examples/live_turn_drills.md`.

## STP-030: Shared-Answer Overload Is A Route, Not An Accident

Sources: Smogon, [Synergies and Cores](https://www.smogon.com/resources/beginner/synergy),
Smogon, [Identifying and Eliminating Threats](https://www.smogon.com/smog/issue40/identifying-threats), and
Smogon RMT archive, [Optical Overload](https://www.smogon.com/rmt/archive/optical_overload)

Trigger: two or more opposing threats, boss routes, or staged converters are
answered by the same player Pokemon, item, phazer, Haze user, revenge killer,
spinner, weather answer, or status absorber.

Policy: treat the shared answer's entry budget as the route resource. Before
using that answer, list every live route it still covers, how many entries or
actions it has left after hazards/status/weather/PP, and which route becomes
uncovered if it takes damage or status now. If the opponent can intentionally
weaken one shared answer so a partner sweeps, preserve it, create a second
answer, or shorten the game before the overload resolves.

Exceptions: spending the shared answer is correct when the route it denies now
is more urgent than all later routes, when a backup answer has become real, or
when the sacrifice opens an immediate forced win. If the answer has already
completed its unique jobs, relabel it as expendable instead of over-preserving
it by old role memory.

Worst branch: the advisor handles each matchup separately, saying "we have an
answer" every time, while hazards, poison, status, PP, or chip make the same
answer unable to cover the final boss route.

Local status: directly applicable. Gym Leader Lab frequently creates shared
answer pressure: Koga can poison the Nidoking / Crobat answer, Lance can force
multiple anti-Dragon entries, Misty can stress one Water answer across sleep,
rain, recovery, and Curse, and Red can tax the same physical or special anchor
before Snorlax, Espeon, sun, or Blastoise inherits the board.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/boss_route_triage_examples.md`,
`worked_examples/misty_30_turn_weather_ledger_drill.md`,
`worked_examples/lance_30_turn_serial_setup_ledger_drill.md`,
`worked_examples/red_30_turn_final_boss_ledger_drill.md`, and
`worked_examples/elite_four_gauntlet_resource_carryover_drill.md`.

## STP-031: Target The Route Switch-In When The Active Is Already Priced

Sources: Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status) and
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes)

Trigger: our current move threatens the active Pokemon enough that a switch,
absorber, spinner, phazer, wall, or status sponge is highly incentivized.

Policy: if the stay-in branch is already covered, aim the move at the route
switch-in, not the active. That can mean using Toxic, paralysis, sleep,
coverage, phazing, a double switch, or a hazard/pivot line that punishes the
piece that normally absorbs the obvious move. Name the expected switch-in, why
it is incentivized, what route it blocks, and what happens if the active stays.

Exceptions: attack the active when its stay branch can KO, set up, heal, trap,
spin, phaze, or otherwise create the larger route. Do not target a switch-in
when the opponent has no incentive or no AI tendency to switch, when the
switch-in is already statused / irrelevant, or when the wrong branch loses an
irreplaceable answer.

Worst branch: the advisor uses status or coverage into the predicted switch,
but the active stays and converts; or the advisor keeps hitting the active with
safe-looking moves while the real blocker keeps entering for free.

Local status: transferable as route logic, but human switch incentives cannot
be assumed for Gym Leader Lab. Use boss roster, local AI switch evidence,
trapping state, HP, public move pressure, and type/passive/damage evidence
before calling a switch-in likely. Against fixed-stay AI states, this rule
becomes "target the route blocker when it is active," not a prediction rule.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/status_absorber_assignment_boss_examples.md`,
`worked_examples/boss_ai_opponent_model_examples.md`,
`worked_examples/proactive_switch_discipline_boss_examples.md`, and
`worked_examples/koga_first_three_turn_clock_ownership_drill.md`.

## STP-032: Variance Budget Follows Route Posture

Sources: Smogon, [Playing with Loaded Dice: How to Control Luck](https://www.smogon.com/smog/issue20/control_luck),
[Risk/Reward](https://www.smogon.com/resources/beginner/bw_risk_reward), and
[Minimizing the Effects of Luck](https://www.smogon.com/smog/issue2/minimizing_luck2)

Trigger: a move choice depends on miss chance, critical hits, full paralysis,
confusion, sleep turns, secondary effects, Quick Claw, Focus Band, damage
rolls, or a prediction coinflip.

Policy: price the variance by route posture. When ahead or stable, choose the
line that keeps the route alive through avoidable miss, crit, status, item, or
coinflip branches. When every non-variance line loses, choose the highest-real
chance branch that creates a named route, and label it forced risk.

Exceptions: accept extra variance when the safer move only preserves a losing
loop, when the inaccurate or secondary-effect move is the only way to deny an
immediate route, or when the exposed piece no longer has a unique future job.

Worst branch: calling a lucky comeback line "clean" after it works, or blaming
bad luck after choosing a line that unnecessarily exposed an irreplaceable
answer to avoidable variance.

Local status: strongly transferable as decision posture. Exact advice needs
local move accuracy, crit behavior, Quick Claw, Focus Band, sleep, status,
damage ranges, and boss AI incentives.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/variance_budget_boss_examples.md`, and
`worked_examples/risk_posture_boss_examples.md`.

## STP-033: Delayed Effects Must Own The Resolution Turn

Sources: Smogon, [Future Sight & Doom Desire](https://www.smogon.com/forums/threads/future-sight-doom-desire.3490776/),
[Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
[GSC Jynx](https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/), and
[GSC Gengar](https://www.smogon.com/forums/threads/gsc-ou-gengar.3696769/)

Trigger: Future Sight, Doom Desire, Bide, Perish Song, Leech Seed, trapping
damage, stored damage, or another delayed effect has been started or can be
started.

Policy: judge the move by the resolution turn, not the setup turn. Before
calling the delayed effect progress, name its landing/countdown turn, likely
active Pokemon then, whether it stacks with current pressure, what escape or
reset options exist, what resource was spent to start it, and which route gets
better when it resolves.

Exceptions: immediate pressure rises when the setup turn lets the opponent
heal, boost, spin, trap, remove the user, or pivot the delayed effect into an
expendable piece. Switching or sacrificing rises when the delayed hit plus the
current attack would land on an irreplaceable answer.

Worst branch: the advisor treats the delayed effect as background text, then
the landing turn forces the only answer into damage, a bad switch, Pursuit,
Perish count, Leech Seed drain, or a boss converter's clean entry.

Local status: directly relevant. Gym Leader Lab contains Will Xatu with Future
Sight, Sabrina Jynx with Perish Song, Morty-style Perish routes, Erika Leech
Seed routes, and Koga Spider Web / Toxic clocks. Exact advice needs local
move data from `data/moves/moves.asm`, local mechanics in `engine/battle/core.asm`
and the relevant move-effect files, plus boss AI switching evidence.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/will_pre_battle_route_sheet.md`,
`worked_examples/sabrina_30_turn_ledger_drill.md`,
`worked_examples/morty_misdreavus_vs_typhlosion_perish_route.md`, and
`worked_examples/erika_pre_battle_route_sheet.md`.

## STP-034: Boss AI Prediction Is Evidence Plus Route Map

Sources: Smogon, [An Introduction to Prediction](https://www.smogon.com/smog/issue1/introduction_to_prediction),
[Risk/Reward](https://www.smogon.com/resources/beginner/bw_risk_reward),
[Getting Started with Competitive Battling](https://www.smogon.com/articles/getting-started), and
[Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking)

Trigger: advising a Gym Leader Lab boss turn where local AI traces, boss roster
data, scoring source, or adaptive/fixed opening behavior may change the
opponent model.

Policy: separate three claims before choosing: roster route, likely AI move,
and worst route move. Use validated traces and source to weight the likely AI
move, but never let a first-decision trace erase the boss's remaining legal
moves, the route it is built to pursue, or the user's irreplaceable pieces.
Choose the move that covers the route, not merely the predicted click.

Exceptions: a trace can dominate when it is current, state-matched, and the
wrong-branch cost is tolerable or already covered. Human-style doubles,
bluffs, and switch incentives require local AI evidence before they are treated
as likely.

Worst branch: saying "the AI will click X" from an old trace or human
prediction habit, then losing to the boss's legal route move, alternate scorer
choice, weighted near-tie, or preserved endgame piece.

Local status: directly applicable. Current local AI design promises public-info
reasoning from visible species, HP/status/field state, revealed moves, public
type chart, learnability priors, boss roster, and observed player patterns.
Exact claims need current trace artifacts, source references such as
`engine/battle/ai/POLICY_DESIGN.md` and
`docs/agent_navigation/subsystems/boss_ai_logic.md`, and ROM/symbol hash
alignment when relying on captured traces.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/boss_ai_opponent_model_examples.md`,
`worked_examples/proactive_switch_discipline_boss_examples.md`,
`worked_examples/misty_30_turn_weather_ledger_drill.md`, and
`worked_examples/boss_live_turn_practice_run_2026-05-13.md`.

## STP-035: Item Removal Is A Route Discount, Not Progress

Sources: Smogon, [GSC Jynx](https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/),
[GSC Thief Discussion](https://www.smogon.com/forums/threads/thief.3543261/), and
[GSC Nidoking](https://www.smogon.com/forums/threads/gsc-nidoking.3681149/)

Trigger: Thief is available, a consumable item can be baited, or a held item
is central to a recovery, status, damage, lock, survival, or setup route.

Policy: remove, consume, or play around the item only when the item supports a
live route and the next state uses that discount. Name the item, the route it
supports, the item-control user's lost job, and the follow-up that converts:
sleep, hazards, phazing, direct damage, forced Rest, PP pressure, setup, lock
exploitation, or survival-branch coverage.

Exceptions: attack, switch, preserve, or target another Pokemon when the item
belongs to a spent target, the removed item does not change a threshold, the
item-control user is still an irreplaceable answer, the user already holds a
needed item, or local AI evidence does not support the boss using item-control
in this state.

Worst branch: the advisor says "steal/remove the item" without naming the
route that changes, spends a key answer for a cosmetic item, or removes a
soon-to-faint target's item while a later anchor keeps the item that matters.

Local status: directly applicable. Local Thief exists as `EFFECT_THIEF` in
`data/moves/moves.asm` and `engine/battle/move_effects/thief.asm`, but the
user must have no item and the target must have a non-mail item. Gym Leader
Lab item advice must verify local Leftovers, Mint Berry, Focus Band, Choice
item, Life Orb, and type-boost behavior in
`docs/agent_navigation/gen2_vs_modern_mechanics.md`,
`docs/agent_navigation/hack_mechanics_reference.md`, and
`engine/battle/late_gen_held_items.asm`.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/smogtours_891179_item_removal_anchor_pressure.md`,
`worked_examples/check_durability_boss_examples.md`,
`worked_examples/protection_state_boss_examples.md`, and
`worked_examples/boss_live_turn_prompt_cards.md`.

## STP-036: Retaliation Moves Price Damage By Route Cost

Sources: Smogon, [Risk/Reward](https://www.smogon.com/resources/beginner/bw_risk_reward),
[An Introduction to Prediction](https://www.smogon.com/smog/issue1/introduction_to_prediction),
[Priority Analysis Across All Generations](https://www.smogon.com/articles/priority-through-generations),
[A Guide to Stallbreakers](https://www.smogon.com/smog/issue18/stallbreakers),
and local Red / Mirror Coat source evidence.

Trigger: Counter, Mirror Coat, Bide, Destiny Bond, or another punishment move
can turn a strong-looking attack into the loss of an irreplaceable route piece.

Policy: before recommending direct damage, price the retaliation branch by
category, timing, legality, KO range, speed/order, and route cost. The attack
is good when it KOs before retaliation, when the punishment cannot legally
resolve, when the attacker is expendable and the trade opens a named route, or
when avoiding the punish gives the opponent an even stronger route.

Revealed setup update: if the opponent has revealed Focus Energy or another
crit-stage/setup move, do not price retaliation in isolation. Re-score the
combined branch: whether our active moves before being KOed, whether our
obvious attack triggers Counter-like punishment, whether Hidden Power or
another odd-category move changes retaliation legality, whether coverage beats
the current target, and whether the low-HP boosted attacker is still valuable
enough to stay in.

Exceptions: do not avoid a severe-looking punish with a line that does not
change the state, loses to the opponent's ordinary coverage, or spends the
answer needed for the next route. Do not treat the punish as guaranteed unless
local AI/source/trace evidence supports that exact branch.

Worst branch: the advisor fires the obvious high-damage move, gets punished by
a legal retaliation move, and loses the piece needed for the remaining boss
route; or overcorrects by avoiding the punish while the boss uses ordinary
coverage, setup, weather, or recovery to inherit a better board.

Local status: directly applicable to Red Blastoise and any future boss with
Counter-like effects. Exact advice needs `data/moves/moves.asm`,
`engine/battle/move_effects/mirror_coat.asm`,
`docs/agent_navigation/gen2_vs_modern_mechanics.md`, speed/order evidence,
damage ranges, and current boss AI evidence. For late-tier bosses, current
source encourages Counter/Mirror Coat only from public revealed-move conditions:
matching revealed damaging category, no boss KO line, boss not publicly faster,
player public threat, and reflected move can hit the visible player type.
Do not transfer Wobbuffet-style CounterCoat certainty blindly: expert material
often pairs Counter/Mirror Coat with trapping, Encore, or forced category
information. Red's Blastoise has Mirror Coat but not that full lock.

Local drills: `worked_examples/red_blastoise_mirror_coat_arbitration.md`,
`worked_examples/boss_live_turn_prompt_cards.md`,
`worked_examples/red_30_turn_final_boss_ledger_drill.md`,
`workspace/quick_tests/focus_energy_counter_branch_regression_001_smogtours-gen2ou-935022_2026-05-14.md`,
and `paused_turn_atlas.md#pta-059-focus-energy-retaliation-branch`.

## STP-037: Known-Set Threatlists Gate Boss Plan Confidence

Sources: Smogon, [Mastering the Maison Part 1](https://www.smogon.com/ingame/bc/maison_part1),
[Mastering the Maison Part 2](https://www.smogon.com/ingame/bc/maison_part2), and
[Identifying and Eliminating Threats to Your Team](https://www.smogon.com/smog/issue40/identifying-threats)

Trigger: a Gym Leader Lab boss roster, trainer set list, route sheet, or
simulator validation plan is available before battle.

Policy: before calling a boss matchup favorable, audit the known or plausible
enemy sets that can beat the player team if the primary route fails. Each
high-severity threat needs a reasonable play line: answer, entry path, backup
if the answer is crippled, worst plausible variance branch, and the hidden
move/ability/item/passive/speed fact that would change the line. A threatlist
must include offensive threats, defensive anchors the team cannot break,
utility/status routes, hazard exposure, and boss cores that remove each
other's answers; type synergy alone is not enough evidence.

Exceptions: in a forced-risk matchup, the audit may conclude that no stable
answer exists. Then choose the route with the highest real survival chance and
record the risk explicitly instead of pretending the plan is covered.

Worst branch: the advisor plans around the lead or aggregate simulator win
rate, misses one known backline boss set, and loses because the team never had
a reasonable line into that threat. A second common failure is clearing a boss
Pokemon as "covered" by type while its actual moves, item, passive, recovery,
status, or partner support breaks the listed answer.

Local status: directly applicable. Gym Leader Lab has local boss roster data
and source-backed AI behavior, so pre-battle advice should use the actual boss
route sheets, not generic metagame memory. Exact coverage still needs local
mechanics evidence for type-chart edits, passive type abilities, items, speed,
damage, and AI move scoring.

Local drills: `pre_battle_route_sheet.md`,
`worked_examples/boss_route_triage_examples.md`,
`worked_examples/live_turn_drills.md`,
`boss_sim_validation_protocol.md`, and the boss route maps in
`boss_route_maps/`.

## STP-038: AI Move Bias Can Create PP Loops Only With Evidence

Sources: Smogon, [Mastering the Maison Part 1](https://www.smogon.com/ingame/bc/maison_part1)
and [Mastering the Maison Part 2](https://www.smogon.com/ingame/bc/maison_part2)

Trigger: a boss or in-game AI has a high-pressure move into the current active,
and the player has a teammate that is immune to or heavily resists that move.

Policy: consider a switch-stall or pivot loop only after separating three
claims: the AI is likely to choose the move, the switch-in survives the move
and follow-up coverage, and the loop converts into route progress such as PP
depletion, weather-turn burn, poison damage, safe setup, forced recovery, or
clean entry.

Exceptions: do not loop if the boss has a second plausible move that breaks the
cycle, if secondary effects or hazards make repeated entries unsafe, if the PP
being drained is not route-relevant, or if local AI evidence does not support
the predicted move.

Worst branch: the advisor imports generic AI KO-bias, switches repeatedly into
coverage, status, hazards, Pursuit, or a weighted second-best move, and loses
the answer that the route needed later.

Local status: use carefully. Gym Leader Lab boss AI has public-info KO
pressure, weighted move selection, switch heuristics, and plan bias documented
in `docs/boss_ai_spec.md` and
`docs/agent_navigation/subsystems/boss_ai_logic.md`. Exact loop advice needs
the boss's visible moves, local damage evidence, PP counts, hazard state,
secondary-effect risk, and current trace/source evidence for move likelihood.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/boss_ai_opponent_model_examples.md`,
`worked_examples/pp_budget_ledger_boss_examples.md`, and
`worked_examples/entry_creation_ladder_boss_examples.md`.

## STP-039: Foresight Turns Good Turns Into A Route Ladder

Source: Smogon, [Borat's Guide to GSC - Part 1](https://www.smogon.com/gs/articles/gsc_guide_part1)

Trigger: a move looks locally useful because it does damage, lands status,
sets a layer, scouts, preserves, or takes an extra attack.

Policy: before recommending the move, write the next route step it creates and
the route step after that. A move is strong when it improves position toward a
specific later opening: forced Rest, safe entry, blocker removal, phaze damage,
PP pressure, setup threshold, recovery denial, or endgame simplification. If
the answer to "so what?" is only "we did something useful," choose another
move or lower confidence.

Exceptions: immediate survival and irreversible denial can shorten the horizon.
If the opponent has a live setup, KO, status, or recovery route that must be
stopped now, the two-step plan can be "deny route now, rebuild next turn."

Worst branch: the advisor wins or improves the visible exchange, but the next
state gives the boss the same reset, a free setup turn, or entry for the real
threat because the move never had a route ladder.

Local status: fully transferable as planning discipline. Exact boss advice
still needs local mechanics, damage, AI, roster, and type/passive evidence for
the named route steps.

Local drills: `worked_examples/live_turn_drills.md`,
`worked_examples/boss_route_triage_examples.md`,
`worked_examples/endgame_forced_line_boss_examples.md`,
`boss_route_maps/pryce_turn1_route_sheet.md`, and
`worked_examples/boss_live_turn_prompt_cards.md`.

## STP-040: Encore Punishes The Last Executed Move

Sources: local `engine/battle/move_effects/encore.asm`,
`docs/agent_navigation/gen2_vs_modern_mechanics.md`, and Smogon,
[Move Restriction Guide](https://www.smogon.com/dp/articles/move_restrictions)

Trigger: either side can use Encore after a setup, recovery, hazard, status,
screen, scouting, or other low-immediate-value move.

Policy: price Encore from the exact last executed move, not from the move's
intention. Before recommending a passive move into an Encore user, ask whether
being locked into that move for the local 3-6 turn window gives the boss a free
receiver, spin, screen, setup, recovery, phaze, or KO route. When using Encore
ourselves, name the follow-up that makes the lock valuable; Encore is not
progress unless the locked move creates entry, setup, healing, hazard, or KO
value.

Exceptions: local Encore fails if the target has no last move, the last move is
Struggle, Encore, or Mirror Move, the target lacks that move with PP remaining,
the Encore attempt missed, or the target is already Encored. A lock can also be
tolerable when the locked move still improves the route, blocks the boss's best
line, or switching out would cost more than spending lock turns.

Worst branch: the advisor clicks hazards, setup, recovery, or screens because
the immediate board looks safe; the boss Encores the actual last move, then uses
the forced turns to spin hazards, set screens, enter a receiver, or start a
cleanup route while the player's original plan keeps being followed.

Local status: directly applicable. The romhack source sets Encore duration with
`BattleRandom & 3` plus three turns, and if the Encore user moves before the
target has acted this turn, the target's already-selected move can be replaced
by the last move immediately. Exact boss advice still needs speed order, PP,
last-move evidence, switch cost, and the boss's follow-up route.

Local drills: `worked_examples/live_turn_drills.md`,
`boss_route_maps/pryce_turn1_route_sheet.md`, and
`boss_route_maps/sabrina_turn1_route_sheet.md`.

## STP-041: Exit Setup When Phazing Owns The Clock

Sources: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
and replay review `reviews/2026-05-13_smogtours-gen2ou-902619.md`.

Trigger: a setup route is being reset by Roar, Whirlwind, Haze, Encore,
Perish timing, trapping escape, or another control move while hazards, passive
damage, recovery, or PP make each failed attempt favorable for the opponent.

Policy: after the first forced reset, re-score setup as a fresh move. Setup is
still correct only if the next attempt changes a route fact: the control user
is now KO-threatened, trapped, asleep, locked, low on relevant PP, denied by
mechanics, unable to survive, or no longer backed by hazards/passive damage.
If the next boost only recreates the same forced-out board, exit the loop by
removing hazards, pressuring the control user, trading, trapping, forcing
recovery, pivoting to a different converter, or accepting a sack for clean
entry.

Exceptions: a repeated setup attempt can be correct when it is baiting a finite
control PP, preserving a stronger backline route, forcing the control user into
Explosion/self-KO range, or when local mechanics make the control move fail in
the current speed/order/last-Pokemon state. Name that concrete change before
calling the loop good.

Worst branch: the advisor keeps boosting because the active Pokemon walls the
visible attack, while the opponent repeatedly phazes or resets it and hazards
chip the backline. The visible matchup looks safe, but the route ledger is
moving only for the opponent.

Local status: highly transferable as planning discipline. Gym Leader Lab has
three-layer Spikes and several local control effects, so exact advice needs
source or trace evidence for Roar/Whirlwind/Haze/Encore timing, Spikes damage,
Rapid Spin clearing, trapping behavior, Explosion damage, RestTalk, type and
passive immunities, and boss AI incentives. Boss AI must use only public player
information when deciding whether the setup route is real.

Local drills: `worked_examples/live_turn_drills.md`,
`paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-902619.md`.

## STP-042: Final Trade Targets Are Chosen By Remaining Material

Sources: Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion),
and replay review `reviews/2026-05-13_smogtours-gen2ou-902089.md`.

Trigger: a simplified endgame has one or more one-time resources available:
Explosion, Self-Destruct, Destiny Bond, Perish timing, Focus Band cash-out, a
forced sack, or a final phaze/Haze/status window.

Policy: before spending the one-time resource, write the final material after
the trade. The correct target is often the piece the remaining converter cannot
beat, not necessarily the active Pokemon or highest-HP Pokemon. A final trade
is good only when the target, lost role, next entry, and last opposing route
are all accounted for.

Exceptions: trade the active target when it can immediately KO, recover, set
up, phaze, trap, spin, or status into a worse route. Preserve the one-time
resource when the opponent still has a Ghost, Protect, immunity, survival item,
faster KO, hidden backline target, or when the trade user is still the only
answer to the next route.

Worst branch: the advisor spends the final trade on the most annoying visible
target, then discovers the remaining teammate cannot beat the actual blocker.
The trade looked valuable but failed the final-material proof.

Local status: directly applicable as endgame discipline. Gym Leader Lab exact
advice needs local damage, priority, Focus Band, Destiny Bond, Perish,
Explosion/Selfdestruct, type/passive immunity, switch, and boss AI evidence.
Boss AI must not select a final trade from hidden player-team knowledge.

Local drills: `worked_examples/live_turn_drills.md`,
`paused_turn_atlas.md`,
`workspace/quick_tests/route_trade_active_pressure_probe_001_smogtours-gen2ou-934329_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_024_route_trade_threshold_smogtours-gen2ou-934148_2026-05-14.md`, and
`reviews/2026-05-13_smogtours-gen2ou-902089.md`.

## STP-043: One-Time Trades Must Pass The Execution Gate

Sources: Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion),
local `engine/battle/move_effects/selfdestruct.asm`,
`data/moves/moves.asm`, `data/moves/effects_priorities.asm`,
`docs/agent_navigation/gen2_vs_modern_mechanics.md`, and
`worked_examples/brock_golem_explosion_turn_order_quarantine.md`.

Trigger: Explosion, Self-Destruct, Destiny Bond, Perish Song, Focus Band
cash-out, Protect scouting, or another one-time route trade is being valued as
if it will happen.

Policy: before scoring the trade's route value, prove that it can execute or
resolve under the current branch. Check priority, Speed, paralysis, Quick
Claw, sleep, full paralysis, flinch, accuracy, Protect/Detect, Ghost/immunity,
Substitute, KO before action, switch target, and local fail rules. If the user
is removed or blocked before the trade resolves, the route trade is not real.

Exceptions: a failed-looking trade can still be useful if it forces a switch,
burns Protect/Endure odds, creates clean entry, or preserves a more important
piece; name that separate route instead of pretending the original trade
landed.

Worst branch: the advisor says "Explosion removes the blocker" or "Destiny
Bond trades" while the faster opponent KOs first, Protect blocks, the target
switches immune, or the local effect cannot resolve. The plan sounds decisive
but fails before its route value begins.

Local status: directly applicable. Gym Leader Lab changes enough items,
priority, Protect behavior, type passives, and AI incentives that every
one-time trade needs local source, damage, Speed/order, and public-info AI
evidence before exact advice.

Local drills: `worked_examples/boss_live_turn_prompt_cards.md`,
`worked_examples/brock_golem_explosion_turn_order_quarantine.md`,
`worked_examples/brock_golem_vaporeon_execution_gate_turn_drill.md`, and
`worked_examples/live_turn_drills.md`.

## STP-044: Non-Damage Support Needs Receiver And Escape Map

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-904753](https://replay.pokemonshowdown.com/smogtours-gen2ou-904753),
Pokemon Showdown replay,
[smogtours-gen2ou-860894](https://replay.pokemonshowdown.com/smogtours-gen2ou-860894),
Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
Smogon, [Introduction to Competitive GSC](https://www.smogon.com/smog/issue28/gsc),
and reviews `reviews/2026-05-13_smogtours-gen2ou-904753.md` and
`reviews/2026-05-14_smogtours-gen2ou-860894.md`.

Trigger: a move creates little or no immediate damage but may change a later
route: Growl, Charm, Screech, Sand Attack, Mean Look, Spider Web, Toxic,
screens, Rapid Spin, Protect, phazing, Haze, scouting, or similar support.

Policy: before recommending or dismissing the support move, name the receiver,
the support being delivered, the escape branch, and the payoff turn. The move
is progress only if it changes a future state before the opponent erases it:
safe entry, setup threshold, forced Rest, hazard retention, damage reduction,
status clock, PP pressure, phaze denial, or final-material simplification.

Exceptions: support falls when immunity, phazing, Haze, curing, Rest,
Protect/scouting, faster KO, or switching removes the effect before the
receiver acts. Support can still be correct if the "failed" branch creates a
different concrete payoff, such as a safe layer, clean pivot, or forced
Explosion into a less important target.

Worst branch: the advisor calls a support turn progress because the move did
something visible, but the opponent Roars, cures, ignores the status, or KOs
the support user before any receiver benefits. The opposite failure is
dismissing support as passive when it quietly creates the later winning clock.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local trapping, phazing, stat-stage, status immunity, Rest, Rapid Spin,
Protect, item, type-passive, and boss AI public-info evidence.

Local drills: `worked_examples/live_turn_drills.md`,
`paused_turn_atlas.md`, `worked_examples/boss_live_turn_prompt_cards.md`, and
`reviews/2026-05-13_smogtours-gen2ou-904753.md` and
`reviews/2026-05-14_smogtours-gen2ou-860894.md`.

## STP-045: Contained Loops Need A Conversion Endpoint

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-905628](https://replay.pokemonshowdown.com/smogtours-gen2ou-905628),
Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
and review `reviews/2026-05-13_smogtours-gen2ou-905628.md`.

Trigger: a repeated defensive, support, recovery, debuff, Pursuit, pivot,
RestTalk, phaze, Haze, Protect, or waiting loop contains the visible threat
but may not actually end the game.

Policy: before calling a contained loop winning, name the conversion endpoint:
KO range, forced Rest, poison / hazard / weather / recoil clock, scarce PP,
trap, switch denial, final trade, or a preserved converter that can finish
after the loop. If the opponent can rotate targets, heal with Leftovers or
Rest, reset the clock, or spend the loop to drain the only converter, treat the
line as a hold rather than a win condition.

Exceptions: a hold can still be the best move when it bridges to a named
endpoint, preserves the only answer until a finite clock expires, or avoids a
worse immediate loss. Call it a hold, not a win, until the endpoint is visible
from public state.

Worst branch: the advisor sees that the current active cannot break through
and declares the route safe, while the opponent repeatedly resets chip and the
only remaining damage source loses HP, PP, sleep turns, or recoil budget.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local PP, Rest / Sleep Talk, Pursuit, stat-stage, hazard, weather, item,
recoil, switch, trapping, and boss AI public-information evidence. Boss AI must
not judge the endpoint from unrevealed player-team knowledge.

Local drills: `worked_examples/live_turn_drills.md`,
`paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-905628.md`.

## STP-046: Phazing Requires Timing And A Target Pool

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-904815](https://replay.pokemonshowdown.com/smogtours-gen2ou-904815),
Smogon, [GSC Move Priority](https://www.smogon.com/gs/articles/move_priority),
local `engine/battle/effect_commands.asm`, local
`engine/battle/ai/switch.asm`, and review
`reviews/2026-05-13_smogtours-gen2ou-904815.md`.

Trigger: Roar, Whirlwind, or another forced-switch effect is being treated as
setup denial, hazard conversion, reset, or emergency control.

Policy: before recommending phazing, prove three gates: the move can resolve
under local timing, the target has a living non-active Pokemon to drag, and the
forced target map improves the route. If the target is last Pokemon, or no
legal bench target is public, phazing is not route control; switch to damage,
status with a real reset map, PP conservation, recovery, setup, pivoting, or a
trade.

Exceptions: a failed-looking phazing move can still matter only if it creates a
separate named payoff, such as PP exhaustion, lock timing, scouting with
answer-changing information, or preserving an irreplaceable answer. Do not
count ordinary "but it failed" turns as progress.

Worst branch: the advisor clicks Roar or Whirlwind because hazards are up or a
setup route exists, but the move acts too early, has no legal target, or drags
the wrong target into a better route for the opponent.

Local status: directly applicable. Local `BattleCommand_ForceSwitch` calls
`FindAliveEnemyMons` or `CheckPlayerHasMonToSwitchTo` before a trainer-battle
forced switch and routes no-target states to failure; it also checks
`wEnemyGoesFirst` for the Gen 2 act-last gate. Boss AI must not use unrevealed
player-team knowledge to decide whether a hidden bench target exists.

Local drills: `worked_examples/smogtours_904815_last_mon_phazing_fail.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-904815.md`.

## STP-047: Post-Converter Handoff Needs A Fresh Blocker Map

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-861526](https://replay.pokemonshowdown.com/smogtours-gen2ou-861526),
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
and review `reviews/2026-05-13_smogtours-gen2ou-861526.md`.

Trigger: a planned converter, breaker, setup Pokemon, weather abuser,
RestTalk attacker, trapper, or one-time route piece has fainted or been forced
out after removing some blockers.

Policy: do not decide whether the route succeeded from the converter's
survival. First list what it removed, what blockers remain, and which teammate
now converts the opened board. If a new closer is live, the best next move may
be utility or trade: Rapid Spin to preserve entries, phazing to improve the
target map, status to stop the remaining answer, Explosion to remove a final
blocker, or a pivot that delivers the closer.

Exceptions: if the converter died without removing a required blocker, or if
the remaining closer lacks HP, PP, status state, entry access, or coverage,
handoff may be fake and the plan should shift to a backup route. Do not call
utility progress unless it serves the new closer.

Worst branch: the advisor either mourns the dead converter and abandons a live
route, or keeps clicking setup/damage for the old route while hazards, Rest,
phazing, or remaining blockers make the new closer harder to deliver.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local Rapid Spin, phazing, Explosion, Sleep Talk, Rest, status, hazards,
weather, item, and boss AI public-information evidence. Boss AI must not use
unrevealed player-team knowledge to decide whether the handoff has a hidden
answer or hidden blocker.

Local drills:
`worked_examples/smogtours_861526_converter_handoff_after_breakthrough.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-861526.md`.

## STP-048: Anti-Pass Control Needs Receiver Map And Endpoint

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-861549](https://replay.pokemonshowdown.com/smogtours-gen2ou-861549),
Smogon, [Baton Pass Chain](https://www.smogon.com/rs/articles/baton_pass),
local `engine/battle/move_effects/baton_pass.asm`, and review
`reviews/2026-05-13_smogtours-gen2ou-861549.md`.

Trigger: Baton Pass, screen passing, Quiver Dance support, setup handoff,
pivot-passing, or another chain route is being answered by phazing, Haze,
Encore, status, direct attack, or a sacrifice.

Policy: name the support source, every live receiver, and the receiver that
actually converts. Phazing or Haze is a bridge only if the control user has the
HP, PP, speed/timing, and target pool to keep resetting until a payoff appears.
When the receiver is in damage range and the control user survives the return
branch, attacking can outrank another reset.
`workspace/quick_tests/replay_turn_pause_023_receiver_phaze_counterplay_smogtours-gen2ou-933853_2026-05-14.md`
adds the post-phaze rebuild check: after a receiver is dragged, do not stop at
"the phazer's species walls this." Rebuild the receiver's route job and check
for route-specific coverage, re-pass, sacrifice, absorber switch, or immediate
attack before auto-switching.

Exceptions: immediate phazing or Haze remains best when a boosted receiver
would win before damage can land. Directly attacking the passer is best when it
prevents the pass before support compounds. Preserving the control user is best
when it is the only answer to multiple receivers and the current turn does not
yet have an endpoint.

Worst branch: the advisor says "Roar beats Baton Pass" while the passer keeps
restarting, the phazer loses HP/PP, or the wrong receiver enters. The opposite
failure is continuing to Roar after the exposed receiver is in KO range and
damage would end the route.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local Baton Pass, Quiver Dance, screens, phazing, Haze, Encore, status,
entry-hazard, damage, Speed/order, and boss AI public-information evidence.
Boss AI must not use unrevealed player-team knowledge to infer hidden phazers,
Haze users, or receiver answers.

Local drills:
`worked_examples/smogtours_861549_baton_pass_phaze_endpoint.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`,
`worked_examples/boss_live_turn_prompt_cards.md`,
`workspace/quick_tests/post_phaze_receiver_map_probe_001_2026-05-14.md`, and
`reviews/2026-05-13_smogtours-gen2ou-861549.md`.

## STP-049: Reset Hubs Win Only After Leak Closure

Sources: Pokemon Showdown replays,
[smogtours-gen2ou-861180](https://replay.pokemonshowdown.com/smogtours-gen2ou-861180)
and
[smogtours-gen2ou-741084](https://replay.pokemonshowdown.com/smogtours-gen2ou-741084),
Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats),
and reviews `reviews/2026-05-13_smogtours-gen2ou-861180.md` and
`reviews/2026-05-13_smogtours-gen2ou-741084.md`.

Trigger: a recovery, cleric, debuff, phaze, spin, screen, Protect, RestTalk, or
status-reset hub appears to contain the opponent but does little immediate
damage.

Policy: before calling the hub winning, list the leak branches that break it:
mixed damage, setup, Explosion, status, hazards, PP, phazing, trapping,
critical-hit exposure, forced switches, or a one-time trade. If leaks remain,
the hub is stabilization and must preserve or deliver the answer to those
leaks. If the leaks are removed or controlled, low-damage reset moves can
become endpoint moves because the opponent no longer has a route through the
loop.

Exceptions: even after leak closure, the hub can lose if PP, accuracy, crit
risk, entry hazards, or a newly revealed move changes the resource map. A
direct attack or trade can still outrank reset when it removes the last leak
or prevents the opponent from creating a new one.

Worst branch: the advisor calls a reset hub passive and abandons a winning
loop after the leaks are already gone, or calls it winning too early while a
breaker, spinner, phazer, status route, or one-time trade still breaks it.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local move sets, recovery, debuff, cure, status, phazing, Haze, Encore, Rapid
Spin, PP, item, contact/passive, damage, and boss AI public-information
evidence. Boss AI must not use unrevealed player-team knowledge to decide that
no leak exists.

Local drills:
`worked_examples/smogtours_861180_reset_hub_leak_audit.md`,
`worked_examples/smogtours_741084_reset_hub_leak_remains.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-861180.md` and
`reviews/2026-05-13_smogtours-gen2ou-741084.md`.

## STP-050: Revealed Function Beats Species Assumption

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-891177](https://replay.pokemonshowdown.com/smogtours-gen2ou-891177),
Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats),
Smogon, [GSC Mechanics](https://www.smogon.com/forums/threads/gsc-mechanics.3542417/),
local `engine/battle/move_effects/present.asm`,
local `data/moves/present_power.asm`, local
`engine/battle/move_effects/rollout.asm`, and review
`reviews/2026-05-13_smogtours-gen2ou-891177.md`.

Trigger: a Pokemon reveals a move, damage roll, screen, trap, spin, Haze,
phaze, recovery, PP pattern, or lock route that contradicts the role its
species label suggested.

Policy: immediately reclassify the Pokemon by the public function it now
performs. A wall with demonstrated damage is not free setup bait; a passive
boost that implies a lock route is a warning to preserve the answer; a support
piece that completes its job before fainting may already have converted value.
Continue using the old species assumption only if the revealed function does
not change the route map.
`workspace/quick_tests/replay_turn_pause_023_receiver_phaze_counterplay_smogtours-gen2ou-933853_2026-05-14.md`
adds the mirror check: a species label can also underrate the active side's
coverage. Marowak into Skarmory looked walled by species, but the route job of
an Agility/Baton Pass receiver made Fire Blast the coverage question that had
to be priced.

Exceptions: do not invent the unrevealed companion move. A move such as
Defense Curl can justify preserving the anti-Rollout answer, but it is not
proof of Rollout until Rollout is shown or a source-authorized roster makes it
known. Do not transfer exact simulator damage into Gym Leader Lab without local
mechanics and damage evidence.

Worst branch: the advisor calls Blissey, Skarmory, Snorlax, or another
familiar species by its usual role while the public battle has already shown a
different function that blocks the plan. The opposite failure is overreacting
to a legal-but-unrevealed surprise and changing the route because of hidden
team knowledge.

Local status: transferable as route logic. Exact Gym Leader Lab advice needs
local move effects, move tables, damage, PP, AI memory, and public-information
evidence. Boss AI must not use unrevealed player-team knowledge to decide that
a surprise function exists or is absent.

Local drills:
`worked_examples/smogtours_891177_surprise_function_reclassification.md`,
`romhack_deltas/present_rollout_function_reclassification.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`,
`workspace/quick_tests/post_phaze_receiver_map_probe_001_2026-05-14.md`, and
`reviews/2026-05-13_smogtours-gen2ou-891177.md`.

## STP-051: Accuracy Disruption Needs Endpoint And Hit-Reliability Re-Score

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-891112](https://replay.pokemonshowdown.com/smogtours-gen2ou-891112),
Smogon, [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status),
Smogon, [Introduction to Competitive GSC](https://www.smogon.com/smog/issue28/gsc),
local `data/moves/moves.asm`,
local `data/battle/accuracy_multipliers.asm`, and review
`reviews/2026-05-13_smogtours-gen2ou-891112.md`.

Trigger: Sand Attack, Smokescreen, Flash, accuracy drops from damaging moves,
evasion changes, repeated low-accuracy attacks, or any line where a hit or
miss now decides the route.

Policy: after an accuracy change, re-score hit reliability and name the
endpoint. The accuracy move is support, not the win condition, unless it buys
a concrete miss, receiver turn, poison / hazard / weather clock, PP route,
safe switch, setup turn, or KO threshold before the opponent can clear or route
around it. Also check whether switching clears the affected stages and whether
a less accuracy-dependent endpoint now dominates.

Exceptions: accuracy disruption can be the best move when direct damage does
not change the route, the threatened hit is severe, and the next miss or switch
forces a named payoff. A debuffed attacker can still attack when the hit wins
immediately or when switching loses the only route.

Worst branch: the advisor ignores an accuracy drop and keeps recommending the
old repeated-hit route, or overcorrects and calls Sand Attack, Flash, or
Smokescreen progress while the opponent poisons, phazes, switches, heals, or
sets up a more reliable endpoint.

Local status: directly applicable as a public-state rule. Exact Gym Leader Lab
advice needs local move accuracy, stage multipliers, stat-stage reset on
switch, phazing/Haze timing, PP, items, contact/passive behavior, damage, and
AI public-memory evidence. Boss AI must not use unrevealed player-team
knowledge to decide that an accuracy route is safe or that no hidden endpoint
exists.

Local drills:
`worked_examples/smogtours_891112_accuracy_disruption_endpoint.md`,
`worked_examples/falkner_pidgeotto_geodude_probe.md`,
`worked_examples/live_turn_drills.md`, `paused_turn_atlas.md`, and
`reviews/2026-05-13_smogtours-gen2ou-891112.md`.

## STP-052: No Revealed Spinner Is Evidence, Not Proof

Sources: Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
local `romhack_deltas/spikes_and_rapid_spin.md`, and local worked example
`worked_examples/janine_qwilfish_spikes_arbitration.md`.

Trigger: a Spikes line is attractive because Rapid Spin has not been revealed.

Policy: estimate the posterior chance of a live effective spinner before
spending another hazard turn. Absence of Rapid Spin lowers the spinner odds
only if the opponent had a clean, valuable spin opportunity and declined it.
Set or complete the stack when the layer's conversion value beats the best
direct move after pricing that posterior; otherwise pressure, block, status, or
trade with the likely spinner first.

Exceptions: if the layer creates an immediate KO, forced recovery, forced
switch, or endgame threshold before any spinner can act, it can be correct even
with spinner risk. If the side setting hazards has no Ghost, trap, faster KO,
status, Explosion, or other punish, the spin posterior needs to be much lower
before stacking is worth the tempo.

Worst branch: the advisor treats "no Rapid Spin revealed" as "no Rapid Spin
exists," spends multiple turns reaching a three-layer stack, then a live
spinner erases the route before any conversion.

Local status: directly applicable. Gym Leader Lab makes the error sharper than
vanilla GSC because Rapid Spin clears all local layers. Boss AI may use public
species, revealed moves, seen opportunities, and observed switch/spin history
as evidence, but must not read hidden player moves or hidden reserve sets.

Local drills: `worked_examples/janine_qwilfish_spikes_arbitration.md`,
`worked_examples/smogtours_912836_rapid_spin_as_progress.md`,
`worked_examples/smogtours_935507_post_spin_trade_audit.md`, and
`worked_examples/will_hazard_retention_stress_test.md`.

## STP-053: Hazard Retention Is An Entry Condition

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-912653](https://replay.pokemonshowdown.com/smogtours-gen2ou-912653),
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
and review `reviews/2026-05-14_smogtours-gen2ou-912653.md`.

Trigger: a hazard plan depends on a spinblocker, spinner punish, trapper, or
other removal answer.

Policy: before trusting the retention plan, prove that the answer can enter or
act on the actual removal turn and that the wrong branch is priced. A Ghost in
the party is not retention if it cannot switch into the spinner; damage into a
spinner is not retention unless it KOs, denies recovery, forces a worse reset,
or immediately hands off to a converter.

Spinblock transfer update:
`workspace/quick_tests/replay_turn_pause_026_hazard_spinblock_transfer_smogtours-gen2ou-934842_2026-05-14.md`
exposed the mirror mistake from the spinner's side: Rapid Spin is not clean
progress if a live Ghost can enter on the removal turn and we have not named
the punish. `workspace/quick_tests/spinblock_route_probe_001_2026-05-14.md` turns that
miss into a six-part check: clean Spin, expected Ghost punish, healthy
Misdreavus block, fragile Gengar not solving Starmie, route-stopper before
Spin, and accepting status to remove a meaningful layer.
`workspace/quick_tests/replay_turn_pause_027_spinblock_transfer_smogtours-gen2ou-934144_2026-05-14.md`
adds the second-stage handoff: after the spinner is poisoned or otherwise
pressured, do not automatically reset Spikes. Ask whether a pressure piece can
force the spinner to switch, Recover, take damage, or lose tempo before the
next hazard reset.
`workspace/quick_tests/replay_turn_pause_028_statused_spinner_handoff_smogtours-gen2ou-934149_2026-05-14.md`
showed this is still not automatic enough: after Toxic and Spikes, I missed
both players handing off from Cloyster mirror to Electric pressure. The payoff
from statusing support is the forced switch, recovery, re-entry tax, phaze, or
pressure sequence it enables, not the status itself.
`workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md` turns that miss
into a six-branch ladder: first layer before handoff, clean Spin before
handoff, Electric or Snorlax pressure, phazing conversion, direct attack, and
delayed reset after the support piece leaves.
`workspace/quick_tests/replay_turn_pause_029_spin_vs_setup_handoff_smogtours-gen2ou-935409_2026-05-14.md`
adds the overcorrection boundary: do not block Rapid Spin automatically when a
spinner enters. If letting Spin resolve gives a pressure piece a setup, attack,
Rest, phaze, sacrifice, or forced-switch route that matters more than the
current layer, the pressure handoff can be correct.
`workspace/quick_tests/spin_vs_setup_handoff_probe_001_2026-05-14.md` turns that boundary
into a six-branch check: let Spin resolve for Curse, block Spin when the layer
is the route, attack the spinner, Rest the converter, phaze immediately, or
sacrifice the support piece to remove the spinner.
`workspace/quick_tests/replay_turn_pause_030_spinblock_pressure_boundary_smogtours-gen2ou-934312_2026-05-14.md`
transferred the boundary and widened the pressure-action list: after a spin
threat, the payoff can be Surf or other direct damage, Growth or other setup,
Rest to preserve the converter, a phaze, a sacrifice, or the spinblock itself.
Before switching to the Ghost, ask whether the current active punishes the
spinner or its pivot immediately.
`workspace/quick_tests/hazard_pressure_move_taxonomy_probe_001_2026-05-14.md`
compresses this into a six-class prompt: direct damage, setup, Rest, phaze,
sacrifice, or spinblock. On hazard-control turns, classify the pressure move
before defaulting to Rapid Spin or a Ghost switch.
`workspace/quick_tests/replay_turn_pause_031_hazard_pressure_taxonomy_transfer_smogtours-gen2ou-866835_2026-05-14.md`
tests the taxonomy in a fresh GSC Cup XI replay and adds the anti-overcorrection
boundary: the taxonomy is a re-solve prompt, not an anti-Spin rule. A turn-11
Starmie position punished premature Rapid Spin with Thunder/direct damage, but
a later turn-25 Starmie position rewarded clean Rapid Spin into Blissey after
the Ghost branch was priced. Reclassify each hazard-control turn instead of
carrying the previous answer forward.
`workspace/quick_tests/spin_vs_damage_boundary_probe_001_2026-05-14.md` turns that miss
into a Starmie/Cloyster four-question check: whether direct damage disables the
spinner, phazer, or spinblocker; whether Rapid Spin is clean enough now;
whether status changes future spin timing even if the current Spin resolves;
and whether a Ghost can actually enter the Spin turn.
`workspace/quick_tests/replay_turn_pause_032_spin_vs_damage_boundary_transfer_smogtours-gen2ou-852072_2026-05-14.md`
tests the check in a fresh replay and adds the poison-clock loop boundary:
repeated Rapid Spin can be correct while poison is already removing Cloyster
and the opponent keeps resetting Spikes, but the answer flips to Surf or other
damage once it actually removes the setter/spinner before another reset.
`workspace/quick_tests/poison_clock_spin_loop_probe_001_2026-05-14.md` compresses the
loop into HP-band prompts: do not Spin when our side is clear; Spin while
damage fails to remove Cloyster and poison is already doing the removal work;
attack once damage removes Cloyster before another reset; preserve Starmie if
the loop spends its remaining spinner/check role.
`workspace/quick_tests/replay_turn_pause_033_pressure_handoff_after_spin_smogtours-gen2ou-934324_2026-05-14.md`
adds the post-Spin pressure boundary: do not defend the layer at all costs. If
letting Rapid Spin resolve gives Zapdos or another pressure piece a clean board
against Starmie, the handoff can be correct. Rebuild Spikes later when a
sleeping or Resting Snorlax gives Cloyster a real reset turn; after Cloyster
has reset the layer and is too low to keep supporting, price Explosion before
preservation.
`workspace/quick_tests/pressure_handoff_after_spin_probe_001_2026-05-14.md` turns that
boundary into six regression branches: allow Spin into Zapdos pressure, block
Spin when the layer is the route, reset Spikes on Resting Snorlax, cash out a
spent Cloyster, preserve Cloyster when its job is still live, and carry weather
or sleep-clock timing before repeating the prior move.
`workspace/quick_tests/replay_turn_pause_035_unlabeled_hazard_cashout_transfer_smogtours-gen2ou-933816_2026-05-14.md`
adds the resource-selection version: when Cloyster threatens Explosion after
Spikes are up, do not preserve a sleeping anchor by exposing the spinner or
hazard-control piece if that piece has the live removal/checking job. After the
trade, a resisted or low-pressure matchup can be the Rapid Spin window even if
direct damage looks active.
`workspace/quick_tests/replay_turn_pause_036_selfko_absorber_transfer_smogtours-gen2ou-932597_2026-05-14.md`
adds the poisoned-spinner loop: Toxic the spinner, hand off to pressure, reset
Spikes on RestTalk Snorlax, and preserve the Spiker while poison does the
removal work. Once a Ghost is available, rank the spinblock conditional before
another pressure handoff. A low support Pokemon may also preserve itself by
switching a sleeping anchor into pressure rather than forcing Rapid Spin or
Explosion.
`workspace/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`
adds Golem compression: a clean Rapid Spin on the forced switch can be correct
even from a Pokemon that also checks Electric-types, and Roar can be the
branch-covering move after the opponent resets Spikes. If Roar drags in the
spinblocker, stop trying to Spin and punish the Ghost directly.
`workspace/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md` compresses
that into a reusable support-order check: Spin when the switch is forced, reset
the layer before the support piece is spent, Roar when Spin would invite the
Ghost, then attack the Ghost rather than repeating Spin into immunity.

Exceptions: a temporary layer can still be correct when it converts before the
spinner acts, or when the final support turn creates a layer and immediately
hands off to a live spinblocker. If the removal answer cannot enter, abandon
the long hazard route unless the non-block punish has a concrete endpoint.

Worst branch: the advisor says "we have a spinblocker" while Rapid Spin
resolves into a non-Ghost, or says "we punish the spinner" while the spinner
removes the layer first and then Recovers through the damage.

Local status: transferable as route logic. Gym Leader Lab makes this stricter
because Rapid Spin clears all local layers, and local type/passive changes can
decide whether the supposed spinblocker or punish actually works.

Local drills: `reviews/2026-05-14_smogtours-gen2ou-912653.md`,
`worked_examples/smogtours_878566_hazard_contract.md`,
`worked_examples/smogtours_912836_rapid_spin_as_progress.md`, and
`worked_examples/will_hazard_retention_stress_test.md`,
`workspace/quick_tests/replay_turn_pause_026_hazard_spinblock_transfer_smogtours-gen2ou-934842_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`,
`workspace/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md`,
`workspace/quick_tests/spinblock_route_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_027_spinblock_transfer_smogtours-gen2ou-934144_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_028_statused_spinner_handoff_smogtours-gen2ou-934149_2026-05-14.md`,
`workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_029_spin_vs_setup_handoff_smogtours-gen2ou-935409_2026-05-14.md`,
`workspace/quick_tests/spin_vs_setup_handoff_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_030_spinblock_pressure_boundary_smogtours-gen2ou-934312_2026-05-14.md`,
`workspace/quick_tests/hazard_pressure_move_taxonomy_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_031_hazard_pressure_taxonomy_transfer_smogtours-gen2ou-866835_2026-05-14.md`,
`workspace/quick_tests/spin_vs_damage_boundary_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_032_spin_vs_damage_boundary_transfer_smogtours-gen2ou-852072_2026-05-14.md`,
`workspace/quick_tests/poison_clock_spin_loop_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_033_pressure_handoff_after_spin_smogtours-gen2ou-934324_2026-05-14.md`,
`workspace/quick_tests/pressure_handoff_after_spin_probe_001_2026-05-14.md`, and
`workspace/quick_tests/replay_turn_pause_035_unlabeled_hazard_cashout_transfer_smogtours-gen2ou-933816_2026-05-14.md`,
and `workspace/quick_tests/replay_turn_pause_036_selfko_absorber_transfer_smogtours-gen2ou-932597_2026-05-14.md`.

## STP-054: Base Speed Is A Public Prior, Not Move Order

Sources: local source `engine/battle/core.asm`, `engine/pokemon/move_mon.asm`,
`data/trainers/dvs.asm`, `engine/battle/ai/boss_policy_move.asm`,
`engine/battle/ai/boss_policy_switch.asm`, `docs/boss_ai_spec.md`, and
`romhack_deltas/speed_order_public_model.md`.

Trigger: a route says a Pokemon is faster, can revenge kill, can set up before
damage, or can ignore a threat because species base Speed is higher.

Policy: build a move-order ledger before trusting the route. Priority resolves
before ordinary Speed; Quick Claw can override Speed; Choice Scarf multiplies
turn-order Speed; ties are random; local Speed can be changed by level, DVs,
player Stat Exp, stages, paralysis, Electric passive, Agility, Dragon Dance,
and Quiver Dance. For player-side boss planning, use exact known player stats
and source-visible boss stats when available. For ordinary boss AI, use the
public species/base-Speed model and known boss items, not private player Speed
or hidden items.

Exceptions: the documented `AICompareSpeed` boss-AI exception is allowed only
for setup-speed headroom: if exact active battle Speed already says the boss
outspeeds the active player, extra Speed setup has no value. Do not generalize
that exception to hidden damage, hidden held items, hidden moves, reserves, or
current-turn input. Hidden player Choice Scarf can become evidence after an
impossible resolved turn order, but only after ruling out priority, Quick Claw,
stages, paralysis, passives, and speed ties.

Worst branch: the advisor says "base Speed is higher" and spends a turn that
loses to priority, Quick Claw, Scarf, paralysis math, an Electric passive, a
Speed stage, a speed tie, or an exact-stat edge that was visible to the player
but illegal for the boss AI to assume.

Local status: source-checked. Current boss AI's public speed predicate is the
right no-cheat default; the narrow exact-speed setup exception is documented.
A broader revealed-Scarf or observed-speed-anomaly memory would need explicit
public observations, trace fields, and fixtures before it should be coded.

Local drills: `paused_turn_atlas.md`,
`worked_examples/priority_revenge_range_boss_examples.md`, and
`romhack_deltas/speed_order_public_model.md`.

## STP-055: Support Compression Has An Order

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-740650](https://replay.pokemonshowdown.com/smogtours-gen2ou-740650),
Smogon, [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes),
Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion),
review `reviews/2026-05-14_smogtours-gen2ou-740650.md`, and turn-pause runs
`workspace/quick_tests/replay_turn_pause_007_electric_handoff_overcorrection_smogtours-gen2ou-907668_2026-05-14.md`
and
`workspace/quick_tests/replay_turn_pause_008_cashout_handoff_fresh_smogtours-gen2ou-907674_2026-05-14.md`
and
`workspace/quick_tests/replay_turn_pause_009_pta057_cashout_handoff_smogtours-gen2ou-928699_2026-05-14.md`
and
`workspace/quick_tests/replay_turn_pause_010_pta057_regression_smogtours-gen2ou-928703_2026-05-14.md`
and
`workspace/quick_tests/replay_turn_pause_011_support_choice_smogtours-gen2ou-928706_2026-05-14.md`.

Trigger: a support Pokemon is losing future value but can still deliver one
route-changing support action, such as Spikes, Rapid Spin, phazing, screens,
status, scouting, or a support pass, and may also have Explosion,
Self-Destruct, Destiny Bond, or a sacrifice pivot.

Policy: order the actions by the converter they serve. If the support action
changes a named teammate's endgame before the opponent resets, deliver support
first; then cash out only if preservation no longer protects a better route
and the trade improves the converter's range, entry, or blocker map. If the
trade target is the required blocker or the support will be erased before the
support matters, cash out first and abandon the support route.

Exceptions: preserve the support user when it still has a unique later job:
spinblock, Rapid Spin, phaze, check a cleaner, absorb Explosion, take sleep, or
reset hazards again. Skip support when Rapid Spin, Haze, phazing, Rest, cure,
Protect, immediate KO, or switch timing erases it before any receiver benefits.

Replay update: do not let "Explosion is plausible" short-circuit the support
order. The 907668 and 907674 turn-pause runs both showed the same miss: I
overcalled Explosion from Cloyster, Exeggutor, or Golem while the expert line
used Toxic, Roar, or a handoff to Zapdos/Raikou/Snorlax first. Before
predicting a support cash-out, ask whether status, phazing, or a recurring
teammate solves the current route while preserving the one-time trade. Cash out
only when the target is the actual route blocker, the support user cannot
deliver a better recurring job, or the handoff gives the opponent a stronger
route than the trade removes.

Second replay update: "support delivered" is not the same as "cash-out is now
forced." In 928699, I correctly predicted Forretress should set Spikes before
Explosion, then immediately overcalled Explosion on the next turn. The actual
line preserved Forretress and handed off to Jynx while Espeon kept boosting.
After support lands, re-rank preservation and handoff again before declaring
the one-time trade necessary.

Regression update: 928703 showed partial correction. I did not overcall
Forretress or Exeggutor Explosion in the tested support-cash-out spots, but I
overfit "do not boom" into "Rapid Spin first." The support order still has to
select the support action that changes the route now: Spikes, status, phazing,
Spin, handoff, or Explosion. Avoiding cash-out is not enough if the chosen
support move serves the wrong converter.

Support-choice update: 928706 showed the same point without an Explosion
temptation. In a Cloyster mirror, after both sides had Spikes, the expert line
handed off to Raikou rather than continuing the support mirror. Later,
Charizard's route value came from Roar and Toxic, not immediate Fire Blast, and
Starmie accepted Toxic to Rapid Spin. On support turns, name the receiver and
the next subgame before choosing between more support, handoff, or direct
damage.

Boundary update: 930765 showed the opposite error. The checklist improved early
Spikes/status/handoff choices, but I undercalled Steelix Explosion into
Exeggutor after Steelix had already phazed and absorbed the Snorlax route.
Avoiding premature Explosion must not become refusing a correct cash-out. Once
the support job is delivered, cash out if the active target is the route piece
and preserving, phazing, spinning, or handing off no longer improves the board.

Defense update: 933556 showed the next half of the same boundary. I correctly
called p2 Cloyster Explosion after both Cloysters had delivered Toxic/Spikes,
but I failed to preserve p1's healthy Snorlax by switching to p1's own poisoned
Cloyster. When predicting the opponent's cash-out, first name the piece we are
willing to lose. If the active piece is still a route piece and a lower-value
absorber exists, preserve before attacking.

Handoff-defense update: 935045 split the same rule in both directions. I
overcalled Exeggutor Explosion into a paralyzed Raikou, while the actual line
used Psychic chip to force Raikou Rest and then handed Marowak into the reset.
Later, after low Cloyster woke and set Spikes, I correctly wanted Marowak
preserved from the attack, and the actual line spent lower-value Smeargle,
which still set Spikes before dying. If support status makes Rest or a passive
reset likely, price the handoff before the one-time trade.

Support-status follow-up update: 935022 showed the same ordering after Toxic
landed on a boosting Snorlax. Cloyster's useful sequence was Toxic, then Spikes,
then Explosion. The defending side must choose between staying on roll-dependent
survival and preserving the boosted anchor with an absorber; either way, name
the roll or absorber before accepting the cash-out branch.

Low-support pressure update: 931699 split the same rule across two low-HP
support pieces. Cloyster at 31% used Surf instead of immediately Exploding
because direct chip into Tyranitar still served the route. Gengar at 13%
Exploded into sleeping Kingdra because the target was expendable and the
post-trade Zapdos route was clear. Order by route payoff, not by the support
Pokemon's HP bar.

Support-coverage update: 924499 adds a support-mirror branch. After both
hazard seats were established, Forretress used Giga Drain into opposing
Cloyster instead of a passive Toxic, Spin, switch, or Explosion line. In a
support mirror, classify direct coverage into the opposing support Pokemon as
a real route move when it weakens the spinner, setter, or Explosion threat.

Support-entry update: 923748 adds that the support piece can enter before the
obvious hard answer. Cloyster switched into Machamp instead of Exeggutor
because claiming Spikes and later threatening Explosion changed the route. Do
not reduce the opponent's response tree to hard answer only; price support
seat entry when the support action can resolve before the active threat
punishes it.

Curselax-phaze update: 922830 adds that Cloyster's second support move can be
Toxic into a hard-phazer handoff before Explosion. Against Curse Snorlax,
Toxic plus Steelix Roar may do more route work than immediate Explosion
because it forces Rest, switch, or Spikes-taxed re-entry while preserving
Cloyster's cash-out threat for later. After the same support piece later drops
too low to re-enter through Spikes, final-gate Explosion becomes correct.

Hazard-loop update: 922676 adds the opposite boundary. Low Cloyster threatening
Explosion does not mean Explosion is the only final-gate move if the opponent
is likely to cover the cash-out with a support absorber. The expected absorber
switch can create the clean Rapid Spin turn. After Spin, do not assume the loop
is over: the mirror can reset Spikes and then use Surf, Toxic, handoff, Spin,
or Explosion according to the next route job.

Low-support preservation update: 922579 adds an even earlier boundary. Cloyster
at 48% and then 23% was still not forced to Explode into Snorlax. The actual
line tried Toxic first, then preserved Cloyster by switching Gengar while the
opponent preserved Snorlax with Misdreavus. Low HP is only one input; before
booming, price Toxic, Spin, Surf, Ghost pivot, Thief progress, and whether both
sides can preserve the route pieces through a double switch.

Immediate-converter update: 922569 is the opposite boundary. Do not convert
"do not boom automatically" into "do not boom." Exeggutor immediately traded
into Zapdos, and Forretress used Spikes then Explosion into boosted Snorlax
because Machamp was the named converter. The cash-out is correct when the
support has been delivered, the target is the route piece, and the next board
has a concrete receiver.

Sleep-absorber handoff update: 922568 combines the set and support boundaries.
After Snorlax revealed Curse, it still used Lovely Kiss into Forretress.
Forretress immediately left as Sleep Clause and future support material.
Exeggutor then correctly Exploded into the boosted Snorlax route, but the
defending side preserved Snorlax by losing Zapdos. Later, Cloyster set Spikes
and handed off rather than spending HP on Surf. Preserve the sleeper, name the
absorber, and after support lands re-rank handoff before direct damage.

Worst branch: the advisor preserves a support Pokemon whose future role is
gone, Explodes before laying the support that would have made the closer win,
or sets support without naming the receiver and then loses the support user for
no conversion.

Local status: transferable as route logic. Gym Leader Lab's three-layer Spikes,
Rapid Spin clearing, Focus Band, Protect/Endure priority, type passives, and
custom boss AI can all flip exact ordering. Boss AI may use its own team plan
and public active state, but must not use hidden player reserves to decide that
a cash-out is guaranteed.

Local drills: `reviews/2026-05-14_smogtours-gen2ou-740650.md`,
`paused_turn_atlas.md`,
`workspace/quick_tests/replay_turn_pause_008_cashout_handoff_fresh_smogtours-gen2ou-907674_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_009_pta057_cashout_handoff_smogtours-gen2ou-928699_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_010_pta057_regression_smogtours-gen2ou-928703_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_011_support_choice_smogtours-gen2ou-928706_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_012_pta058_boundary_smogtours-gen2ou-930765_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_013_pta058_preserve_boundary_smogtours-gen2ou-933556_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_014_pta058_handoff_defense_smogtours-gen2ou-935045_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_015_support_status_followup_smogtours-gen2ou-935022_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`,
and
`worked_examples/controlled_sack_for_clean_entry_boss_examples.md`.

## STP-056: Spacer Sacks Are Endgame Material

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-890958](https://replay.pokemonshowdown.com/smogtours-gen2ou-890958),
Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion),
and Smogon, [Long Term Thinking](https://www.smogon.com/rs/articles/long_term_thinking).

Trigger: a low-HP, statused, phazed, nearly spent, or apparently dead piece can
switch in, faint, Explode, phaze, absorb a locked hit, absorb a wake-up hit,
force recoil, or create final entry before the converter acts.

Policy: treat the piece as material if the sacrifice removes a bad branch from
the route tree. Before spending it, write the final material after the sack:
who enters, what hit or status branch was absorbed, what variance or entry
problem disappeared, and whether the converter now has a forced line. A spacer
sack is correct when the lost piece has no higher-value remaining job and the
entry or branch removal changes the final route.

Replay update:
`workspace/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`
adds the hazard-entry check: a 14% support Pokemon with Spikes on its own side
may have no real future job because re-entry leaves it unable to act. In that
case, staying in to faint can be better than a preservation switch that forces
the converter to take both entry damage and the incoming attack.
`workspace/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md` adds the
regression wording: preserving the name of a Pokemon is not preserving a
resource if hazard entry leaves it unable to act. Count the action after
re-entry, not the species in reserve.

Exceptions: do not call a sacrifice a spacer when the entering converter still
lacks damage, HP, PP, status state, speed/order, or coverage to force the win;
when the sacrificed piece still answers another live route; or when direct
damage, recovery, phazing, Haze, status, or a safer pivot preserves more
winning branches.

Worst branch: the advisor throws away a low piece because it "does nothing,"
then the converter has to enter through recoil, paralysis, wake, priority,
hazard, or damage variance and loses. The opposite failure is making a stylish
sack that gives clean entry to a converter that still cannot win.

Local status: transferable as route logic. Gym Leader Lab makes this sharper
because Focus Band, Quick Claw, priority, Protect/Endure timing, local sleep
turns, phazing target pools, type passives, and three-layer Spikes can all make
or break the final-material map. Boss AI may use public active state and its
own remaining team, but must not use hidden player reserves to prove a spacer
sack has no downside.

Local drills: `reviews/2026-05-14_smogtours-gen2ou-890958.md`,
`paused_turn_atlas.md`,
`worked_examples/controlled_sack_for_clean_entry_boss_examples.md`, and
`workspace/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`,
and
`workspace/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md`.

## STP-057: Support Jobs Can Be Split Across The Team

Sources: Pokemon Showdown replay,
[smogtours-gen2ou-912131](https://replay.pokemonshowdown.com/smogtours-gen2ou-912131),
and local turn-pause run
`workspace/quick_tests/replay_turn_pause_001_smogtours-gen2ou-912131_2026-05-14.md`.

Trigger: the active support Pokemon has set hazards, used status, phazed, or
otherwise taken the visible support seat, and the advisor is about to assume
that the same active Pokemon must also remove hazards, absorb the punish, or
finish the support exchange.

Policy: map support jobs by team role, not by the active Pokemon. Ask who sets,
who removes, who poisons or paralyzes the opposing support, who phazes setup,
who absorbs the forced attack, and who re-enters after the forced switch. If
the setter's job is only to poison or create symmetric hazards, the correct
spinner may be a reserve that enters after the opponent is forced out. Pressure
the active setter only if that denies the actual support route; otherwise
target the next support entrant or preserve the piece that can meet it.

Exceptions: if the active support Pokemon is confirmed to be the only spinner,
phazer, setter, or status spreader left, then direct pressure can deny the
whole support route. If the reserve support piece cannot enter through hazards,
status, damage, or speed pressure, treat the active support job as the real one.

Worst branch: the advisor Surfs or attacks the visible setter because it "must
be the spinner," while the real spinner enters on the forced switch and clears
hazards for free. The mirror error is overcommitting to Spin when the active
Pokemon's better job is Toxic, Spikes, phazing, or forcing the support mirror
into a teammate's entry.

Local status: transferable as route logic. Gym Leader Lab makes this especially
important because several bosses compress Spikes, Rapid Spin, Haze, Toxic,
phazing, trapping, and sacrifice across multiple authored team members. Boss AI
may use its own team role map and public player reveals, but must not assume
hidden player reserve support roles as fact under no Team Preview.

Local drills: `workspace/quick_tests/replay_turn_pause_001_smogtours-gen2ou-912131_2026-05-14.md`,
`paused_turn_atlas.md`, and `worked_examples/will_hazard_retention_stress_test.md`.

## STP-058: Re-Solve The Local Subgame After Every Reveal

Sources: Moravcik et al.,
[DeepStack: Expert-Level Artificial Intelligence in No-Limit Poker](https://arxiv.org/abs/1701.01724);
Brown and Sandholm,
[Safe and Nested Subgame Solving for Imperfect-Information Games](https://arxiv.org/abs/1705.02955);
Brown, Sandholm, and Amos,
[Depth-Limited Solving for Imperfect-Information Games](https://arxiv.org/abs/1805.08195);
and local transfer policy `cross_domain_autonomy_policy.md`.

Transfer: poker AI work is not Pokemon strategy, but it directly addresses a
shared problem: decisions under hidden private state. DeepStack combines
recursive reasoning, local decomposition, and learned intuition for imperfect
information. Libratus-style subgame solving warns that a local subgame depends
on the whole-game strategy and can be re-solved as the game progresses.
Depth-limited imperfect-information solving handles search cutoffs by testing
against multiple opponent continuation strategies instead of one assumed line.

Trigger: a reveal, KO, Rest, Sleep Talk result, Rapid Spin, Explosion, phaze,
status, item clue, speed-order clue, or support-role reveal changes the local
position after the current plan was chosen.

Policy: stop carrying the old script and re-solve the local subgame. Rebuild
the public belief state, name the current route for each side, then judge the
candidate move against at least three opponent continuations: the obvious
punish, the route-preserving switch, and the greed/support line. Prefer the
move that keeps acceptable value against that bundle when stable or ahead. Take
the exploitative read only when the slow robust line is losing or when public
evidence makes the opponent's branch highly incentive-compatible.

Canary update: the branch bundle has to be good, not just present. After
`workspace/quick_tests/replay_turn_pause_003_resolve_canary_smogtours-gen2ou-917193_2026-05-14.md`,
add status-as-route-stopper, preservation of the punisher, and double re-solve
after both sides know the active damage interaction when those branches are
publicly plausible. Do not let "obvious punish exists" silently become
"obvious punish is best now."

Second canary update:
`workspace/quick_tests/replay_turn_pause_004_branch_quality_smogtours-gen2ou-917826_2026-05-14.md`
showed a better support-map score but added another required branch: when the
route-preserving switch is obvious, include coverage into that switch as a
serious opponent continuation. The best punish may be the move aimed at the
incoming answer, not the strongest move into the current active.

Third canary update:
`workspace/quick_tests/replay_turn_pause_005_status_route_smogtours-gen2ou-903666_2026-05-14.md`
showed the same status blind spot again. When a setup anchor is active, Toxic,
paralysis, phazing, Encore, or another route-stopper may outrank both hazard
economy and direct damage. Do not ask "Spikes or Rapid Spin?" before asking
whether the opponent's current setup route becomes permanent if it is not
stopped now.

Baton Pass update:
`workspace/quick_tests/replay_turn_pause_016_baton_pass_resolve_smogtours-gen2ou-934428_2026-05-14.md`
showed that a pass route is not a script. After Agility, Swords Dance, or a
revealed Baton Pass, re-rank adding another boost, attacking with the passer,
passing to the named receiver, using Baton Pass as a fast pivot into a sack, or
abandoning the chain. The correct move can be Hidden Power before passing, or
Baton Pass with no boost payload, if that changes the next board.

Receiver update:
`workspace/quick_tests/replay_turn_pause_017_sleep_route_marowak_continuation_smogtours-gen2ou-934428_2026-05-14.md`
showed the comeback version. When ordinary damage loses and a Baton Pass
archetype is public, search for the remaining receiver route even if the exact
receiver is not yet public. In spectator-public replay study, quarantine the
receiver as an inferred route rather than a known species. In player-side or
boss-own-team advice, use the known own-team receiver map directly.

Exceptions: in forced endgames, exact damage/range gates, or known locked
states, the continuation bundle can collapse to one or two branches. Do not use
this rule to avoid choosing; it is a pruning method, not a permission slip for
analysis paralysis.

Worst branch: the advisor correctly names one threat but still plays the old
route into the wrong local subgame: staying Snorlax into obvious Explosion,
attacking a setter while the reserve spinner enters, setting hazards after the
spinner map changed, or assuming a no-Team-Preview opponent cannot have a
route-flipping own-team answer.

Local status: transferable as decision discipline. Ordinary boss AI can use
this only with public player information plus its authored own-team map; it
must not import hidden player reserves or current-turn input. A cheap boss-AI
version would be a traceable re-score trigger after public events such as
revealed Rapid Spin, observed speed anomaly, Rest/Sleep Talk reveal, phaze,
Explosion, or a no-progress loop.

Local drills: `workspace/quick_tests/replay_turn_pause_001_smogtours-gen2ou-912131_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_002_smogtours-gen2ou-917186_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_005_status_route_smogtours-gen2ou-903666_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_016_baton_pass_resolve_smogtours-gen2ou-934428_2026-05-14.md`,
`workspace/quick_tests/replay_turn_pause_017_sleep_route_marowak_continuation_smogtours-gen2ou-934428_2026-05-14.md`,
and `paused_turn_atlas.md`.
