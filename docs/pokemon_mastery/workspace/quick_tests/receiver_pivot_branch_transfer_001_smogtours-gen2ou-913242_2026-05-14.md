# Receiver Pivot Branch Transfer 001 - smogtours-gen2ou-913242 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-913242`.

Context source: Smogon GSC OU Winter Seasonal #8 Round 4 replay post.

Mode: focused fresh replay transfer. This is a sealed turn-pause segment that
advanced from the public opener until the first obvious receiver-pivot branch.
It is not a 30-decision primary gate.

Contamination control:

- Local docs were searched for `913242`; no prior local use was found.
- Web search confirmed the replay link in the Smogon Winter Seasonal Round 4
  thread.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Turns were revealed sequentially from the public opener until the first
  receiver-pivot branch appeared.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/baton_pass_receiver_branch_probe_001_2026-05-14.md`

## Score Summary

Target decisions: 1.

Top-match: 1 / 1.

Acceptable-match: 1 / 1.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Measurement status: focused fresh transfer only. This checks the same
branch-action habit as the Baton Pass probe, but on a simple receiver pivot
rather than a Baton Pass chain.

## Lead-Up

Public sequence before the target:

- p1 Snorlax and p2 Snorlax led and traded Double-Edge on turn 1, leaving p1 at
  57% and p2 at 59% after Leftovers.
- On turn 2, both sides left the Snorlax mirror: p1 switched Skarmory and p2
  switched Umbreon.

## Target Turn - Turn 3

Public state:

```text
Vanilla GSC spectator-public state. p1 Skarmory is active at 100% against p2
Umbreon at 100%. p1 has Snorlax at 57% with Double-Edge revealed and Skarmory
revealed. p2 has Snorlax at 59% with Double-Edge revealed and Umbreon revealed.
No Spikes or status are up.
```

Frozen answer:

- p1: Toxic. Umbreon is a passive target, and Toxic also punishes the likely
  Electric or special-pressure receiver.
- p2: switch Raikou, Zapdos, or another Skarmory pressure piece rather than let
  Umbreon be poisoned or phazed.

Actual choices: p2 switched Raikou. p1 used Toxic and poisoned Raikou.

Grade: p1 top-match. This is the branch-action transfer: after naming the
receiver class, the move chosen beat the receiver instead of only damaging the
Pokemon currently on screen.

## Error Classes

- No severe miss.
- Remaining risk: this was a single receiver-pivot target, not a Baton Pass
  chain and not a 30-decision packet. It does not prove stable transfer after
  replay 071's Whirlwind miss.

## Policy Extraction

Trigger:
  A passive or defensive active Pokemon invites a receiver that wants to take
  over the next board.

Default:
  Choose the utility move, coverage move, phaze, or counter-switch that beats
  the receiver when it also makes progress into the active Pokemon.

Exceptions:
  Keep attacking the active Pokemon when the receiver is speculative, the active
  target is route-critical, or the receiver takes enough damage from the active
  attack to remain punished.

Worst branch:
  You identify the receiver, click an active-only move, and let the receiver
  enter without losing HP, status, tempo, or route position.

Local status:
  Vanilla GSC replay evidence. Local romhack type, status, AI, and switch
  behavior require local verification when decision-relevant.

Drill:
  In the next full replay packet, require every receiver read to name both the
  active-only move and the branch-beating action before choosing.
