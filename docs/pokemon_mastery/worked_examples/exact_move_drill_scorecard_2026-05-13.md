# Exact Move Drill Scorecard: 2026-05-13

Purpose: practice the live-turn standard on concrete player-side positions.
These are not sealed benchmarks; they are a calibration pass over existing
drills with real public state, damage anchors, and one recommended move.

Scoring rule:

```text
pass:
  recommends one move or one ranked move class;
  names the route gained;
  names the worst plausible branch;
  names the piece being preserved or spent;
  states what information would flip the answer.

cap confidence:
  user bench unknown;
  exact HP, PP, speed, item, or damage source stale;
  local type/passive evidence missing for a decision-relevant claim.
```

## Drill 1: Misty Starmie vs Meganium

Source: `misty_starmie_meganium_player_turn_drill.md`

Recommendation checked: `Razor Leaf`.

Why it passes:

- The move removes Starmie from the shown 46% HP before Recover can reset the
  position.
- The route gained is not "Grass beats Water"; it is denying Starmie as a fast
  Recover bridge.
- The worst branch is Psychic chip into Lapras or another follow-up route.
- Meganium is not labeled expendable after the KO; it may still be needed for
  Quagsire or the Water-route map.

Confidence cap: if Meganium's actual HP, moves, PP, or the damage self-test is
stale, the recommendation must be recalculated.

## Drill 2: Jasmine Steelix vs Quilava

Source: `jasmine_steelix_quilava_player_turn_drill.md`

Recommendation checked: `Fire Blast if available; otherwise Flame Wheel`.

Why it passes:

- Fire Blast is route-ending damage from the shown Steelix HP, while Flame
  Wheel is the best revealed fallback.
- The answer separates exact move availability from move class: stronger Fire
  coverage changes the move, but weak Dig or Quick Attack does not.
- The worst branch is a Fire Blast miss or unavailable coverage into Rock
  Slide, leaving Quilava too low for later Steel routes.
- Quilava's later job against Forretress, Scizor, or Skarmory is kept visible.

Confidence cap: if Quilava lacks Fire Blast, is lower than public HP, or a
safer teammate handles Steelix while Quilava is required later, switch or
Flame Wheel may replace the top line.

## Drill 3: Koga Crobat vs Alakazam

Source: `koga_crobat_vs_alakazam_immediate_ko.md`

Recommendation checked: `Wing Attack`.

Why it passes:

- Public damage says Wing Attack KOs Alakazam from 51%, removing Psychic and
  Recover branches immediately.
- Toxic and Confuse Ray are correctly rejected because they leave the active
  route alive.
- The fallback answer, Umbreon, is named only if the KO threshold disappears.
- This is a clean example that direct damage is strategic when it removes a
  recovery or retaliation route.

Confidence cap: if Wing Attack no longer KOs, Crobat is slower, or Alakazam has
a new survival/status state, the move must be re-ranked.

## Drill 4: Karen Crobat vs Dragonite

Source: `karen_crobat_vs_dragonite_toxic_clock.md`

Recommendation checked: `Toxic`.

Why it passes:

- Public damage says Wing Attack chip is not decisive, while Crobat survives
  the immediate Outrage branch.
- Toxic creates a real clock before pivoting to Tyranitar; it is not generic
  status.
- The worst branch is staying in too long after landing Toxic and losing
  Crobat to repeated Outrage or coverage.
- The drill names Tyranitar as the follow-up, so the status user is not asked
  to solo the route.

Confidence cap: if Crobat no longer survives, Dragonite is already statused, or
hidden coverage invalidates Tyranitar, switch or another control line can rise.

## Drill 5: Jasmine Skarmory vs Quilava Last-Mon

Source: `jasmine_skarmory_quilava_last_mon_phaze_gate.md`

Recommendation checked: `Fire Blast if available; otherwise Flame Wheel`.

Why it passes:

- The answer rejects stale Whirlwind fear because the player has no living
  bench target; phazing is no longer route control.
- Fire Blast is a non-contact guaranteed KO from full, while Flame Wheel is the
  best revealed two-hit route.
- Rocky Helmet is priced correctly: Flame Wheel is contact and costs Quilava
  max HP / 6 after the hit, while Fire Blast avoids that contact recoil.
- The worst branch is Fire Blast miss or Flame Wheel contact/recoil plus Toxic
  or Steel Wing, not a nonexistent forced switch.

Confidence cap: if the player still has a bench target, Whirlwind and Spikes
become live again. If Quilava lacks Fire Blast or is too low for the two-turn
Flame Wheel route, re-rank by current HP and move availability.

## Drill 6: Pryce Dewgong vs Ampharos

Source: `pryce_dewgong_ampharos_encore_spin_gate.md`

Recommendation checked: `ThunderPunch`.

Why it passes:

- ThunderPunch removes Dewgong from the shown 41% HP, denying Rapid Spin and
  Encore instead of merely "playing around" them.
- The answer rejects Thunder Wave, weak chip, hazards, and passive scouting
  because they let Dewgong use the exact spin/Encore route the Pryce map warns
  about.
- The worst branch is Pryce pivoting Piloswine into ThunderPunch, then the
  player staying in by inertia and losing Ampharos to Earthquake pressure.
- Ampharos is treated as the current Dewgong remover, not as a permanent answer
  to Pryce's remaining route map.

Confidence cap: if Ampharos is slower, statused, out of ThunderPunch PP, or
Dewgong is above the KO threshold, re-score before attacking. If the player has
a verified Piloswine punish and Pryce's switch is strongly expected, a
double-switch can compete with the active-target KO.

## Drill 7: Whitney Miltank vs Geodude

Source: `whitney_miltank_rollout_commitment.md`

Recommendation checked: `Body Slam`.

Why it passes:

- Body Slam is the one move that creates pressure while preserving Miltank's
  flexible route.
- The answer rejects first-turn Rollout because local damage says the opening
  hit is only 2-3 damage into healthy, unstatused Geodude.
- The worst branch is a high Magnitude line or no paralysis, which makes Milk
  Drink a next-turn preservation question rather than retroactively justifying
  turn-1 Rollout.
- Miltank is correctly treated as the ace to preserve; the point is to unlock
  later Rollout, not spend the lock before the board is ready.

Confidence cap: if Geodude is already paralyzed, lower, confirmed without
Magnitude, or Miltank is near a real danger threshold, Rollout or Milk Drink
can overtake Body Slam.

## Cross-Drill Lesson

Exact move advice improves when it chooses the move whose next state is best,
not the move with the best-looking label:

```text
Misty: take the KO because it denies Recover.
Jasmine: use the stronger Fire move only if it is actually available.
Koga: direct damage is best because it removes Psychic/Recover.
Karen: status is best because damage does not change the route yet.
Jasmine Skarmory: attack because phazing has lost its target pool.
Pryce Dewgong: attack because spin/Encore disappears if Dewgong faints.
Whitney: Body Slam because Rollout needs status, HP, and punish branches to be
favorable before commitment.
```

The common rule is decision compression:

```text
Pick one move, name the route, name the punish, name the preserved piece, then
state the flip condition.
```

## Chained Drill 1: Misty Starmie Follow-Up

Source: `misty_starmie_meganium_followup_chain.md`

Root recommendation checked: `Razor Leaf`.

Follow-up standard checked: after Razor Leaf resolves, choose the next
recommendation from Misty's replacement route instead of continuing the same
move script.

Why it passes:

- Branch A, Starmie faints after Psychic: the next answer preserves Meganium by
  default unless the replacement can be removed immediately or Meganium is no
  longer needed for Quagsire, Lapras, Lanturn, or Politoed.
- Branch B, Starmie Recovers first: Razor Leaf remains the likely follow-up
  because Recover did not escape the damage cycle; switching to a slower plan
  would be fake caution unless exact HP/damage changed.
- Branch C, Misty switches: the answer re-scores by incoming route. Lapras
  asks rain-extension and Ice Beam questions, Quagsire asks Curse/Rest denial,
  Lanturn asks Thunder Wave preservation, and Politoed asks sleep/rain
  arbitration.
- Meganium is treated as a current-role object, not as "the Grass type that
  always stays in." Its job changes with replacement, rain turns, HP, status,
  and whether the team still needs it later.

Confidence cap: the chain is abstract until exact user party, Meganium HP after
Psychic, rain turns, PP, Sleep Clause, and replacement order are known.

New habit trained:

```text
Correct first move -> new state -> new route owner.
```

The first move being correct is not permission to keep clicking the same move.
It creates a sharper follow-up question.

## Next Practice Gap

Current status: `blocked_no_real_team`.

The next improvement is to use one actual player team or recorded attempt and
score a multi-turn sequence, not just a constructed branch tree. The advice
should recommend exact moves for at least three consecutive public states and
grade whether each move preserved the declared route.

Use `../battle_captures/README.md` as the evidence gate. If no real player
team, save state, video, screenshots, or turn log is available, do not fill the
gap with another constructed prompt. Keep the gap explicit until a public battle
state can be scored.
