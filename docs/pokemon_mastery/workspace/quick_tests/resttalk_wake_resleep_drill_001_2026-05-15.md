# RestTalk Wake Re-Sleep Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_025_gen2ou-2594757032`. This is not fresh progress proof.

Source basis:

- `reviews/resttalk_wake_resleep_review_001_2026-05-15.md`
- `heuristic_core/rest_curse_tempo_window.md`
- `heuristic_core/reset_loop_denial.md`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Forums, GSC Mechanics:
  `https://www.smogon.com/forums/threads/gsc-mechanics.3542417/`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Wake Turn Re-Sleep

Prompt:
Jynx faces Raikou. Raikou has revealed Rest, Sleep Talk, Thunder, and Hidden
Power. Sleep Talk called Rest two sleeping action turns ago, so this is the
wake-and-act turn even if a helper still displays sleep. Raikou is in Ice Beam
range only after another turn, and Lovely Kiss is available.

Frozen answer:
Top action: Lovely Kiss. Wake-and-act means Raikou can Thunder before generic
damage; re-sleep denies the RestTalk loop and creates the Nightmare window.

Answer key: hit.

## Scenario 2 - Sleeping Action Damage

Prompt:
Jynx faces the same Raikou one sleeping action turn after Sleep Talk called
Rest. Nightmare is already active and Raikou cannot wake this turn. Ice Beam
plus Nightmare puts Raikou into finishing range.

Frozen answer:
Top action: Ice Beam. This is a true sleeping action turn, so damage converts
before Raikou can wake.

Answer key: hit.

## Scenario 3 - Sleep Talk Rest Reset

Prompt:
Raikou was at 43% asleep and Sleep Talk called Rest this turn, healing to full.
Nightmare is active. Jynx is healthy enough to survive Hidden Power but not
Thunder.

Frozen answer:
Top action next turn: Ice Beam if Raikou remains on a sleeping action turn;
do not assume it is about to wake immediately, because Sleep Talk Rest started
a fresh Rest clock.

Answer key: hit.

## Scenario 4 - Attack Beats Re-Sleep

Prompt:
Raikou is asleep at 18%, no Rest PP remains, and Jynx's Ice Beam KOs before
Raikou can wake. Lovely Kiss is legal but would only add miss risk.

Frozen answer:
Top action: Ice Beam. Re-sleep is not a script; exact removal before wake/reset
beats status.

Answer key: hit.

## Next Use

In fresh replays, every time Sleep Talk calls Rest, mark:
`fresh Rest clock -> sleeping action 1 -> sleeping action 2 -> wake/act`.
On the wake/act turn, rank re-sleep/status/KO before generic chip.

