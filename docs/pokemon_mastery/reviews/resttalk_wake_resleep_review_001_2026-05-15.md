# RestTalk Wake Re-Sleep Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_025_gen2ou-2594757032_p1_2026-05-15.md`

Reason for study:
Packet 025 was close to the top-match gate and cash-out repaired behavior
improved, but turn 22 failed a mechanics/timing gate. I attacked with Jynx
while Raikou woke and used Thunder; the actual move was Lovely Kiss to re-sleep
Raikou before it could keep the RestTalk loop stable.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/rest_curse_tempo_window.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/rescore_after_reveal.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`

Current web sources:

- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Forums, GSC Mechanics:
  `https://www.smogon.com/forums/threads/gsc-mechanics.3542417/`
- Bulbapedia, Sleep Talk:
  `https://bulbapedia.bulbagarden.net/wiki/Sleep_Talk`

## Confirmed Lessons

GSC RestTalk can reset itself:
Smogon status material and the mechanics thread both state that Sleep Talk can
call Rest in GSC, healing the user and resetting sleep to Rest's normal clock.
Bulbapedia gives the same Generation II rule. The existing local sleep card
already had this, so the miss was not missing knowledge; it was failure to make
the clock mandatory in the live solve.

Wake-and-act changes the top move:
GSC sleepers can act on the turn they wake. On turn 22, Raikou's wake meant
Ice Beam was no longer just damage into a sleeping target; it allowed Thunder
before the route was denied. Lovely Kiss was the converter because it reset
Raikou before RestTalk pressure could continue.

Nightmare works only if sleep timing is owned:
Nightmare plus Ice Beam beat the loop after Jynx re-slept Raikou and stole
Leftovers. The route was not "always attack"; it was re-sleep on the wake turn,
then Nightmare and damage while the sleep window was real.

## Policy Correction

- `rest_curse_tempo_window.md`: added explicit Sleep Talk -> Rest -> fresh
  two-turn clock wording.
- `reset_loop_denial.md`: added wake-and-act denial before chip.
- `rescore_after_reveal.md`: added RestTalk-called Rest as a timing reveal.

## Measurement Note

This is limited positive transfer only. Cash-out and exact-removal behavior
improved compared with packets 023-024, but top-match was 15/28 and one
mechanics error remained. The next fresh packet should keep the cash-out prompt
and add an explicit RestTalk clock line whenever Sleep Talk calls Rest.

