# Paired Handoff Transfer 001 - smogtours-gen2ou-920763 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920763`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Transfer `paired_handoff_probe_001` to a fresh replay and score my handoff,
opponent counter-handoff, active pressure into receiver, and setup after
handoff-out separately.

Why this attacks the bottleneck:
The latest failed gate was paired handoff: I could name a receiver or support
branch, but did not consistently choose the next-board action. This replay
quickly produced Rest-sleeper handoff, Steelix hard-answer handoff, setup after
handoff-out, and a one-turn cleric-before-Explosion branch.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/paired_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`

Web/current sources:

- Smogon GSC forum current index, checked for active 2026 GSC sources.
- Smogon GSC OU Winter Seasonal #8 Round 8, used to select this replay.
- Smogon GSC OU Global Championship 2026 Round 1 Stage 2, checked but all
  visible replay candidates were already used locally.
- Smogon GSC OU statistics resource, checked as current source context and
  evidence that 2026 Smogtours GSC replays remain a high-value replay pool.

## Contamination Control

Local search found no prior `920763` artifact. While downloading, turns 1-5
were exposed, so scored sealed play starts at turn 6. No turns after turn 5
were inspected before answering turn 6. From turn 6 onward, each answer was
frozen before revealing that turn.

## Score Summary

Turns scored: 6-12.

Decisions: 14.

Top-match: 4 / 14.

Acceptable-match: 7 / 14.

Severe blunders: 1.

Mechanics errors: 1.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 6, over-switching a Rested Cloyster before
pricing the safe sleep-turn burn and Surf chip.

Earliest severe error: turn 12, choosing Growl with Miltank instead of Heal
Bell before Steelix's Explosion. If Miltank dies without Heal Bell, the route
loses the one support action that woke the saved Cloyster.

## Focused Handoff Scores

My handoff found: 0 / 2.

- Missed turn 9: Rested Cloyster should hand off to Raikou after one sleep turn
  instead of trying to burn all wake turns.
- Missed turn 11: Raikou should hand off to Miltank after Steelix answered
  Thunder instead of assuming active coverage was the route.

Opponent counter-handoff found: 1 / 1.

- Hit turn 10: Cloyster to Steelix versus Raikou's Thunder.

Active pressure into receiver: 0 / 1.

- Missed turn 11 boundary. I wanted active coverage into Steelix, but the
  actual route was support handoff to Miltank.

Setup after handoff-out: 0 / 1.

- Missed turn 11: Steelix used Curse as Raikou left for Miltank.

Support before cash-out: 0 / 1.

- Missed turn 12: Miltank used Heal Bell before dying to Explosion.

## Turn Notes

### Turn 6

Public state:
Rested p1 Cloyster at 78% asleep versus p2 Cloyster at 97%, Spikes on both
sides.

Frozen answer:
p1 switch the sleeping Cloyster to preserve it; p2 Toxic or Surf, with Toxic
as my top branch.

Actual:
p1 stayed asleep; p2 used Surf.

Grade:
0 top, 1 acceptable. Surf was the correct immediate pressure; my p1 switch was
early because Cloyster could safely burn a sleep turn.

### Turn 7

Public state:
p1 Cloyster at 60% asleep, p2 Cloyster at 100%.

Frozen answer:
p1 Rapid Spin on the wake turn; p2 Toxic to re-status after wake.

Actual:
p2 Surfed before p1 cured sleep; p1 woke and Rapid Spun.

Grade:
1 top for p1, 0 top but acceptable for p2. Mechanics error: a faster or
earlier-moving opponent cannot Toxic the Rest user before the cure occurs.

### Turn 8

Public state:
p1 Cloyster at 38% healthy with p1 Spikes removed; p2 Cloyster at 100%, p2 side
still has Spikes.

Frozen answer:
p1 Rest; p2 Spikes or Surf, with Spikes as my top.

Actual:
p1 Rested; p2 Surfed.

Grade:
p1 top, p2 acceptable. Surf keeps the Rest loop under pressure.

### Turn 9

Public state:
p1 Cloyster at 80% asleep after Rest; p2 Cloyster at 100%; no p1-side Spikes.

Frozen answer:
p1 stay to burn the sleep turn; p2 Surf.

Actual:
p1 switched to Raikou; p2 set Spikes.

Grade:
0 top, 0 acceptable. This is the main Rest-sleeper handoff miss: once Cloyster
had absorbed enough and p2 could keep Surfing, the saved sleeper had a later
job and Raikou had the entry.

### Turn 10

Public state:
p1 Raikou at 100% versus p2 Cloyster at 100%, Spikes on both sides.

Frozen answer:
p1 Thunder; p2 switch to a Ground or Steelix-style hard answer.

Actual:
p2 switched to Steelix; p1 used Thunder.

Grade:
2 top hits. This was the one paired-handoff branch I found.

### Turn 11

Public state:
p1 Raikou at 100% versus p2 Steelix at 94%, with Steelix now revealed as the
Raikou answer.

Frozen answer:
p1 use active coverage if available or stay pressure; p2 Earthquake or Roar.

Actual:
p1 switched to Miltank; p2 used Curse.

Grade:
0 top, 0 acceptable. I missed both sides of the paired handoff: Raikou's
handoff to Miltank and Steelix's setup because the handoff was expected.

### Turn 12

Public state:
p1 Miltank at 94% versus +1 Attack/+1 Defense Steelix at 100%, Spikes on both
sides.

Frozen answer:
p1 Growl; p2 Earthquake or Roar.

Actual:
p1 Heal Bell; p2 Explosion, KOing both.

Grade:
0 top, 0 acceptable, severe blunder for p1. Growl would try to manage Steelix
while ignoring the one-turn support job. Heal Bell converted Miltank's death
into value by waking the saved Cloyster before Explosion removed Miltank.

## Error Classes Found

- Rest-sleeper handoff miss: I over-burned wake turns instead of saving the
  sleeper once the next board had a clear handoff.
- Rest wake timing mechanics error: the opponent can act before the Rest cure
  event, so status into the still-sleeping target is not the right punish.
- Paired handoff miss: after Steelix answered Raikou, I priced active coverage
  before asking which teammate actually owns the Steelix board.
- Setup after handoff-out miss: Steelix could Curse on the expected handoff
  instead of attacking immediately.
- One-turn support before cash-out miss: when a support piece is about to be
  traded by Explosion, use the unique support action first if it changes the
  route.

## Reusable Lesson

Do not treat "save the sleeper" and "burn wake turns" as rival scripts. First
ask whether the sleeper has already done enough, whether the next handoff has a
clean entry, and whether a cleric or other support piece can convert before a
cash-out branch removes it.

## Next Rep

Build one compact regression probe with four scenarios:

1. Rested support piece should stay one turn to burn safe sleep.
2. Rested support piece should switch out and be saved after its job is done.
3. Hard-answer receiver invites a support handoff, not active coverage.
4. Cleric must use Heal Bell before the incoming Explosion trade.

Then transfer that probe to a fresh unused replay.
