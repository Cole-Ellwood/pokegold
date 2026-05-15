# Low Self-KO Transfer 002 - smogtours-gen2ou-831951 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-831951`

Context source:
Smogon, `GSC OU Winter Seasonal #7: Round 10`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-7-round-10.3762830/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Transfer the self-KO route-defining gate from `831843` to a fresh replay. The
packet stopped early because turn 9 produced a severe adjacent failure before
Explosion appeared: I chose a low-HP attack line into a faster Rest branch
instead of preserving the route piece with Rest.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/reviews/low_self_ko_review_001_smogtours-gen2ou-831843_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #7 Round 10 thread above.
- Pokemon Showdown replay source above.
- Raw log: `https://replay.pokemonshowdown.com/smogtours-gen2ou-831951.log`

## Contamination Control

Local search found no prior `831951` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not inspected;
each prompt was generated with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen.

Stopped after turn 9 because the first severe miss was already diagnostic.

## Score Summary

Turns scored: 1-9.

Scorable side decisions: 18.

Top-match: 6 / 18.

Acceptable-match: 14 / 18.

Severe blunders: 1.

State errors: 1.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 12 / 18.

Route-converting move chosen: 5 / 11 target converter decisions.

Branch-punish chosen: 7 / 12 named-branch decisions.

Main result:
This was a regression for positive move selection. Severe-blunder control did
not hold, and the miss was not hidden-information abuse. The problem was route
pricing: I failed to see that the faster low Zapdos could Rest first, which
turns Snorlax's low-HP Double-Edge into a bad cash-out line.

## Focused Turn Table

| Turn | Side | Frozen top | Actual | Top | Accept | Positive | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss | Ice Beam | 0 | 1 | 0 | Over-scripted sleep; Ice Beam kept tempo into the switch. |
| 1 | p2 | Switch to Jynx/sleep answer | Vaporeon switch | 1 | 1 | 1 | Correct class: meet Jynx without handing over sleep pressure. |
| 2 | p1 | Lovely Kiss | Cloyster switch | 0 | 0 | 0 | Missed proactive Cloyster handoff and Spikes route. |
| 2 | p2 | Stay and pressure/absorb | Surf | 0 | 1 | 1 | Surf punished the switch, but I did not make it primary. |
| 3 | p1 | Spikes | Spikes | 1 | 1 | 1 | Correct hazard route. |
| 3 | p2 | Surf pressure | Zapdos switch | 0 | 0 | 0 | Missed immediate Zapdos handoff after Spikes. |
| 4 | p1 | Switch to Electric resist/owner | Exeggutor switch | 1 | 1 | 1 | Correct preserve-Cloyster handoff. |
| 4 | p2 | Thunder | Thunder | 1 | 1 | 1 | Correct active pressure into the handoff. |
| 5 | p1 | Sleep/status with Exeggutor | Snorlax switch | 0 | 1 | 0 | Top line risked hidden coverage; switch was only an alternative. |
| 5 | p2 | Coverage into Exeggutor | Hidden Power | 1 | 1 | 1 | Correct by class without claiming exact Hidden Power type. |
| 6 | p1 | STAB attack | Curse | 0 | 1 | 1 | Missed setup as top, but named active route pressure. |
| 6 | p2 | Switch to Snorlax answer | Thunder | 0 | 1 | 1 | Thunder pressure was acceptable but not my top. |
| 7 | p1 | Attack | Curse | 0 | 1 | 1 | Accepted setup branch, but did not choose it. |
| 7 | p2 | Switch to Snorlax answer | Thunder | 0 | 1 | 1 | Accepted Thunder branch, but did not choose it. |
| 8 | p1 | Attack | Double-Edge | 1 | 1 | 1 | Correct conversion after two Curses. |
| 8 | p2 | Switch to Snorlax answer | Thunder | 0 | 1 | 1 | Thunder hit the active branch but relied on a crit to stabilize. |
| 9 | p1 | Double-Edge | Rest | 0 | 0 | 0 | Severe: missed faster Zapdos Rest and Snorlax's matching Rest route. |
| 9 | p2 | Thunder | Rest | 0 | 0 | 0 | Missed preservation route for low Zapdos. |

## Severe Miss Detail - Turn 9

Public state:
p1 Snorlax was at 10%, paralyzed, at +2 Attack/+2 Defense with Curse and
Double-Edge revealed. p2 Zapdos was at 13% with Thunder and Hidden Power
revealed. Spikes were on p2's side, but Zapdos is not grounded.

Frozen top:
Snorlax should use Double-Edge; Zapdos should use Thunder.

Actual:
Zapdos used Rest first and healed to full. Snorlax then used Rest and also
healed to full.

Why this matters:
The correct question was not "can low Snorlax finish low Zapdos?" The question
was "what if the faster low Zapdos preserves itself before Snorlax attacks?"
If Snorlax attacks into that branch, Double-Edge likely spends Snorlax into a
healed Zapdos instead of converting the route. That is the same family as the
self-KO gate: before spending a low route piece, name speed/order, target HP
after opponent action, recoil/survival, and the route piece preserved by Rest.

## Lessons

1. The self-KO gate needs a Rest-race clause. A low target that can Rest before
   the hit is not the same target the attacker is trying to cash out on.
2. Sleep script resurfaced on turns 1-2. I overvalued immediate Lovely Kiss and
   missed the proactive Cloyster-to-Spikes route.
3. Branch-action remains mixed. Turn 4 was correct, but turn 3 missed the
   Zapdos handoff that immediately pressured Cloyster after Spikes.
4. Hidden-info discipline held. I named Zapdos coverage by class as a strong
   prior and did not claim Rest or Sleep Talk as revealed. The error was
   underpricing a strong-prior preservation branch, not pretending it was fact.

## Next Rep

Run one tiny correction probe before another fresh replay:

- low attacker with recoil versus faster low Rest user;
- low attacker with non-recoil finisher versus faster low Rest user;
- low Rest user mirror where both sides can heal;
- low target with no known or strong-prior recovery, where attacking is correct.

Require the answer to name speed/order, whether the target can heal before the
hit, recoil/survival, and the preserved route piece.
