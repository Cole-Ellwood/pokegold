# Clean Oracle Subset Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_036_gen2ou-2584483135_p2_2026-05-15.md`

## Diagnosis

Packet 036 improved route quality but still missed the raw exact top gate:
16/30 top, 30/30 acceptable, and 16/26 top on clean-oracle turns. The important
distinction is that the misses were not one repeated new policy failure.

The actionable misses were already represented in the compact cards:

- Turn 2: after Heracross absorbed Nidoking pressure, Seismic Toss should have
  outranked Earthquake because it also hit the natural Zapdos/Flying branch.
- Turn 19: active Starmie should usually convert a real Rapid Spin window
  instead of assuming the replay double is a better oracle.
- Turns 29-30: low support and low Snorlax cash-outs transferred correctly once
  move order and RestTalk action timing were named.

## Sources Read

Local:

- `live_core.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/role_package_ledger.md`
- `replay_turn_pause_protocol.md`

Web:

- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Zapdos Through the Ages:
  `https://www.smogon.com/articles/zapdos-through-ages`
- Smogon Forums, Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Lessons Kept

Heracross branch damage:
Heracross can check Nidoking and Machamp, but Zapdos is a hard answer that
Raikou normally covers. When Heracross lacks Megahorn in the reconstructed
side-known view and has Seismic Toss, the neutral branch-covering damage can be
the positive move over Earthquake into only the active Nidoking.

Spin window discipline:
Starmie is a premier Rapid Spin user because of Recover and speed, but Rapid
Spin still needs the immediate board to cooperate. In this packet, active
Starmie had a real spin window before the replay chose a double. That supports
the recent hazard-tempo patch rather than requiring a new rule.

Explosion/Self-Destruct timing:
The packet reinforced the existing rule. Spend low Forretress or Snorlax when
the user moves before the RestTalk action or slower target and the lost job is
already delivered. Do not spend into a faster revealed hit that removes the user
first unless explicitly taking a miss/switch read.

## Policy Outcome

No additional live-card edit. The correct response is to keep measuring with
`oracle_quality` and clean-oracle subset scores, not to bloat the compact docs
with Heracross/Zapdos-specific text.
