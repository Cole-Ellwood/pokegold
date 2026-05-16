# Low Cloyster/Ghost Guard Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/low_cloyster_ghost_guard_transfer_001_smogtours-gen2ou-933115_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and stopped early. It repeated the
early-cycle handoff miss, then exposed a sharper low-Cloyster boundary:
coverage/status, preservation, Explosion, and the opponent's Ghost guard must
be solved together.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/low_cloyster_cashout_review_001_2026-05-15.md`
- `workspace/quick_tests/low_cloyster_cashout_transfer_001_gen2ou-2605299310_2026-05-15.md`

Current web sources:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Forums, GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`

## Confirmed Source Lessons

Jynx lead pressure:
Smogon Jynx material supports Jynx threatening Nidoking and drawing bulky
sleep/special absorbers such as Snorlax. That makes both Lovely Kiss and Ice
Beam reasonable turn-1 candidates, but if the opponent shows the Snorlax
answer, the follow-up should name the physical/hazard owner rather than repeat
a generic Jynx script.

Cloyster is a mixed support/offense piece:
Smogon Cloyster and Spikes sources describe Cloyster as a Spikes setter that
also pressures with Surf, Toxic, and Explosion. This replay showed that order:
Cloyster entered on Snorlax, set Spikes, landed Toxic, then preserved rather
than immediately cashing out.

Explosion guard:
The Explosion guide and local cash-out cards already require naming Ghosts and
low-value guards before making boom top. p2's Gengar switch on turn 5 is the
defensive mirror: once low Cloyster has delivered support and can explode, the
opponent can move the Ghost guard before continuing active damage.

No-Team-Preview discipline:
Gengar was not public before turn 5, so it cannot be treated as fact in the
recommendation. It must be a plausible Ghost/immunity class with a fallback:
if no guard enters, cash-out or coverage may convert; if the guard is likely,
preserve or use pressure/handoff.

## Policy Correction

The existing cards mostly cover the boundary, but `cashout_boundary.md` should
make the low-Cloyster four-way solve explicit:

1. After support lands, ask whether status or coverage still changes the active
   target before leaving.
2. Compare preservation, coverage/status, Explosion, and defensive sack.
3. Before Explosion, name revealed Ghosts and plausible hidden Ghost/low-value
   guards with a fallback.
4. If preservation is chosen, name the pressure owner and Cloyster's later job.

## Measurement Note

Not progress. This packet was only 10 decisions, with clean severe/hidden/
state/mechanics gates but low top, acceptable, route, and branch scores.
