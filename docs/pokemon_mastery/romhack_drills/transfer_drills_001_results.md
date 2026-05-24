# Transfer Drills 001 Results

Status: practice-source-derived self-check, not validation.
Date: 2026-05-17.

Packet: `transfer_drills_001.jsonl`
Scores: `transfer_drills_001_scores.jsonl`

## Summary

This packet was used to check whether the romhack transfer layer can preserve
the right candidate classes and mechanics gates across source-derived boss
states.

Metrics:

| Metric | Result |
| --- | ---: |
| Decisions answered | 12 |
| Distinct bosses covered | 10 |
| `local_mechanic_checked` | 12/12 |
| `boss_route_named` | 12/12 |
| `player_route_named` | 12/12 |
| `top_three_cover_roles` | 12/12 |
| `route_budget_top1` | 12/12 |
| `hidden_info_clean` | 12/12 |
| `damage_or_fixture_needed_named` | 12/12 |

Interpretation: promising as a coverage check, not proof of live romhack play mastery.
The packet is open-book and source-derived, so it mostly verifies that the
bridge and workbench can force the right mechanics/candidate vocabulary.

## Main Lesson

The current bottleneck is no longer "does the note mention the romhack
mechanic?" The repeated constraint is that several route-important mechanics
still need runtime or tool support before becoming hard boss-AI policy:

- Air Balloon is now covered for Ground immunity and after-hit active/party
  item clear; the next test is decision use, not another fixture.
- Explosion timing and Ghost interactions.
- Rest/Sleep Talk details.
- Protect/phazing timing.
- Contact/passive edge cases when Rocky Helmet or Poison retaliation is
  decision-critical.

## Drill-Level Outcomes

| ID | Top action class | Main gate | Failure tag if missed |
| --- | --- | --- | --- |
| RMT-001 | Pop or pressure Air Balloon before relying on Ground. | Air Balloon verified; test decision use next. | mechanics |
| RMT-002 | Pressure Gligar while preserving Dragon answers. | Quick Claw, Toxic, 3-layer Spikes. | resource_identity |
| RMT-003 | Force Ariados before setup unless setup converts first. | Trap/status/hazard clock. | script_too_slow |
| RMT-004 | Exploit or respect Choice Specs Psychic lock. | Choice lock and damage range. | item_commitment |
| RMT-005 | Scout/absorb Choice Band before spending later answers. | First-lock next-board owner. | next_board_owner |
| RMT-006 | Make Cloyster choose survival over Spikes/cash-out. | Explosion plus Dewgong Spin. | cash_out |
| RMT-007 | Avoid fake contact progress into Muk. | Rocky Helmet, Poison, RestTalk. | mechanics |
| RMT-008 | Deny Dragon Dance or name the fallback controller. | `bestattackup`, Outrage, Speed. | setup_timing |
| RMT-009 | Price sleep, Life Orb, Giga Drain, and Explosion together. | Sleep/Explosion pending. | status_allocation |
| RMT-010 | Pressure Forretress and account for Starmie Spin. | Spikes, Toxic, Protect, Explosion. | candidate_generation |
| RMT-011 | Control Curse/RestTalk before generic damage. | RestTalk pending. | reset_loop |
| RMT-012 | Use local Steel/Dragon matchup and anti-Roar logic. | Type chart, Outrage, phazing. | mechanics |

## Decision

Keep the transfer method, but do not promote it to "romhack meta mastered."
Next validation needs fresh or semi-blind boss states, not more source-derived
drill prose.

Next packet should test:

1. Fresh or semi-blind Air Balloon decision use, not another mechanics fixture.
2. Rest/Sleep Talk anchors from Red, Koga, Misty, and Will.
3. Explosion/cash-out branches from Pryce, Lt. Surge, Janine, Will, and Erika.
4. A scored boss-state packet where exact damage ranges can flip candidate
   promotion.
