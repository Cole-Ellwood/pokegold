# Utility Screen/Screech Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/utility_screen_screech_transfer_001_gen2ou-2592987202_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. Top-match was 11 / 30 and the main misses
were positive-selection failures: Gengar Dynamic Punch, Zapdos Reflect, and
Tyranitar Screech were not ranked as route-improving utility moves before
reveal.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/active_pressure_before_status.md`
- `workspace/quick_tests/support_action_branch_probe_001_2026-05-14.md`
- `workspace/quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`
- `workspace/quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`
- `workspace/quick_tests/branch_absorber_transfer_001_smogtours-gen2ou-912287_2026-05-14.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Tyranitar OU Revamp:
  `https://www.smogon.com/forums/threads/tyranitar-ou-revamp-done.3658517/`
- Smogon Gengar WIP:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon Zapdos QC:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Move Analysis: Light Screen / Reflect:
  `https://www.smogon.com/forums/threads/move-analysis-light-screen-reflect.6235/`

## Confirmed Source Lessons

Gengar:
Smogon describes Gengar as a Spikes-preserving spinblocker with offensive
pressure, not only as a sleep or Explosion button. Its GSC offensive options
include Thunderbolt/Thunder, Ice Punch, Explosion, and a flexible fourth slot.
Dynamic Punch specifically improves damage into Snorlax, Tyranitar, and
Umbreon while helping put them into Explosion range. That maps directly to the
turn-9 miss: after Snorlax entered, Dynamic Punch was the route-preserving
middle line.

Tyranitar:
Smogon's Tyranitar analysis emphasizes role compression: Rock Slide pressures
Zapdos, Pursuit punishes Ghost/Psychic exits, Roar is important phazing
support, and Fire Blast hits Steel-types such as Skarmory and Forretress.
Screech is described as an alternative to Roar that forces switches by dropping
Defense and pairs with Pursuit because the target fears Rock Slide after the
drop. That directly explains turn 14: Screech into Starmie was not random
utility; it attacked the receiver map.

Zapdos and screens:
Smogon sources describe Zapdos as a dominant Spikes-supported threat that can
also run Reflect or Light Screen for team support. Reflect/Light Screen are
team screens that last five turns including the setup turn and halve the
corresponding damage class. In the replay, Zapdos using Reflect into
Tyranitar's Rock Slide changed the board before any HP Water or switch line
needed to be chosen.

Spikes context:
The GSC Spikes article warns that Spikes are not a win condition by themselves;
they need pressure, phazing, trapping, status, spinblock support, or mixed
attackers. It also identifies Zapdos as a major Spikes-loop problem because it
is immune to Spikes. That supports the transfer lesson: the right move is often
the utility action that lets Spikes pressure keep converting, not just the move
that wins the visible matchup.

## Policy Correction

Previous local docs already knew "support moves can beat the branch" in a
constructed probe. The failure was transfer under time pressure. The practical
fix is to insert utility moves into the ranked top-three before damage/switch
scripts when one of these conditions is true:

1. The opponent's named receiver is physically punished by a Defense drop.
2. A screen lets the current side stay for the follow-up or bring in a physical
   owner without losing the route.
3. Gengar has a unique spinblock or pressure job and can use Dynamic Punch to
   tax a Normal/Dark owner without spending Explosion.
4. A public Ghost makes Rapid Spin fail or lose tempo, so the spinner must
   pressure the Ghost branch first.

## Decision Checklist

Before choosing in this pattern:

1. Name the receiver, not just the active target.
2. Ask whether Reflect, Screech, Dynamic Punch, Toxic, or another utility move
   is the move that beats that receiver.
3. If using a support move, name the follow-up that converts it: phaze, Pursuit,
   Rock Slide, Explosion, switch, Surf, or Spin after the Ghost is covered.
4. If the utility move is only possible-only, keep the fallback line explicit.
5. Do not count a hidden utility move as proven until it is revealed.

## Measurement Note

No broad progress claim. This review fixes the interpretation of the miss, but
the only proof that the correction transferred will be another fresh unseen
replay or a later sealed prompt set. Existing constructed Screech/screen probes
remain regression evidence only.
