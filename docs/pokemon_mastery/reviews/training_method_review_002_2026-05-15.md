# Training Method Review 002 - 2026-05-15

Trigger:
`workspace/quick_tests/side_known_transfer_030_gen2ou-2586857838_p1_2026-05-15.md`

## Diagnosis

The simplified docs helped retrieval but did not solve the wall by themselves.
Packet 030 used ranked top-three candidates and still produced a severe error:
on turn 30 I clicked the sleep script into a Rest wake/action turn, letting a
passed Marowak survive at 47%, use Swords Dance, and sweep.

This is not mainly a missing GSC theory problem. The relevant theory already
existed locally in `rest_curse_tempo_window.md` and was supported by current
GSC sources:

- GSC sleep can act on the wake turn.
- Rest creates a two-action sleep clock.
- Sleep Talk can call Rest in GSC and reset the Rest clock.
- Baton Pass Speed changes the receiver's immediate lethal branch.

The failure was that the replay prompt did not make that state impossible to
ignore. I reasoned from a stale "sleeping Snorlax" label instead of a mandatory
critical ledger: Rest sleep actions = 2, wake/act now, Marowak at 47%, passed
Speed, Swords Dance lethal branch.

## Source Check

Current source support:

- Smogon status guide: GSC sleep allows the Pokemon to act on the turn it wakes
  and Sleep Talk + Rest is a special Gen 2 interaction.
- Smogon GSC mechanics resource: Sleep Talk can pick Rest and reset the sleep
  count to the regular Rest clock.
- Rest reference: from Generation II onward, Rest wakes on the third turn and
  the user can act then.

Sources:

- https://www.smogon.com/resources/competitive/gs/status
- https://www.smogon.com/forums/threads/gsc-mechanics.3542417/
- https://pokemon.fandom.com/wiki/Rest

## Structural Repair

Implemented:

1. `replay_turn_pause.py` now tracks Rest sleep actions from logs and prints
   `Rest sleep actions 2; wake/act next in GSC` in prompts.
2. Replay prompts now require a critical ledger before candidates:
   sleep/wake counter, passed boosts/speed, self-KO or cash-out branch, and
   immediate lethal/miss/crit risk.
3. `replay_turn_pause_protocol.md` now scores
   `critical_state_ledger_obeyed`.
4. `live_core.md` now places critical counters before next-owner ranking.
5. `rest_curse_tempo_window.md` now says not to choose Sleep Talk when the
   helper marks `Rest sleep actions 2` / wake-act next.

## Training Loop Change

Do not fix this by adding more general notes. The next loop must be:

1. Run one small nonblind regression drill on wake/act + AgilityPass lethal.
2. Run the next fresh replay packet only with the helper's critical ledger in
   the prompt.
3. Stop immediately if either error repeats:
   - cash-out guard under-ranked after support job is complete;
   - Rest wake/action turn treated as a Sleep Talk turn.

Progress remains unproven until a fresh packet clears severe/hidden/mechanics
gates while keeping top, acceptable, route conversion, and branch punish above
the post-repair targets.
