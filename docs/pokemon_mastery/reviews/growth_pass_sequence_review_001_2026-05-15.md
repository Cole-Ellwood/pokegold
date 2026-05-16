# Growth Pass Sequence Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_021_gen2ou-2609820489_p1_2026-05-15.md`

Reason for study:
The fresh post-repair transfer showed that the low cash-out repair worked, but
the replay stayed flat on Growth/Baton Pass sequencing. I kept naming the pass
route without solving the timing: boost-now, attack-now, or pass-now.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/rescore_after_reveal.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`
- `policy_cards/branch_action_after_naming.md`
- `reviews/jolteon_agipass_receiver_review_001_2026-05-15.md`
- `reviews/pass_package_sleeper_handoff_review_001_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC OU Speed Tiers:
  `https://www.smogon.com/resources/competitive/gs/gsc_speedtiers`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums, Beginner's Guide to GSC:
  `https://www.smogon.com/forums/threads/beginners-guide-to-gsc.38663/`

## Confirmed Lessons

Jolteon can be both passer and receiver:
The threatlist frames Jolteon as a Baton Pass user that can pass Agility,
Growth, or Substitute, while also using boosted Thunderbolt and Hidden Power
itself. This means a pass route is not always "pass immediately"; sometimes the
current boosted attacker is the converter.

Vaporeon Growth is an endgame route, not flavor text:
The threatlist describes Growth Vaporeon as a major endgame sweeper and warns
that after a couple of boosts it becomes dangerous. The sample-team material
also says Vaporeon can soften opponents before passing boosts. Therefore the
live question is timing: attack with boosted coverage, keep boosting, or pass
to a receiver that survives the reply.

Receiver survival is part of the move choice:
Speed-tier and Baton Pass sources make Baton Pass a move-timed handoff, not a
normal switch. The receiving Pokemon still has to live the incoming hit or
immediately own the next board. In transfer 021, passing +2 from Vaporeon to
Jolteon was correct only after Vaporeon had absorbed the immediate Hydro Pump
turn; passing earlier could have fed Jolteon into that hit.

Phaze and Spikes are the counter-pressure:
The sample-team source describes GSC Baton Pass as dangerous but disruptable by
phazing and Spikes. In this replay, Spikes meant every pass recipient had a
real HP tax, so receiver selection had to include the incoming hit plus Spikes,
not just the final attacking matchup.

## Policy Correction

- `rescore_after_reveal.md`: Growth/Baton Pass now explicitly compares
  boost-now, attack-now, and pass-now by receiver survival and next-board
  conversion.
- `name_next_board_owner.md`: Baton Pass now requires naming the receiver, the
  hit that lands during the pass, and the owner after the receiver appears.
- `branch_punish_ranking.md`: boost/pass mirrors now require choosing which of
  attack, boost, or pass actually punishes the next board.

## Measurement Note

Not progress. The clean severe/hidden/state/mechanics gates are useful, and the
turn-13 cash-out repair transferred, but 10/20 top-match is flat. This should
trigger another fresh packet after a small nonblind GrowthPass drill; if exact
top stays flat over the next sizable sample, the training method needs a larger
rethink around multi-turn package sequencing, not more card text.

