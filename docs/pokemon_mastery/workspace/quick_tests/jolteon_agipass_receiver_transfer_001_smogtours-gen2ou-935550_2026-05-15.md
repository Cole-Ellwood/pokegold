# Jolteon AgiPass Receiver Transfer 001 - smogtours-gen2ou-935550 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935550`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935550.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=1`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-935550` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-935550.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 5 after repeated revealed Baton Pass package
  and counter-handoff misses.
- After stopping, a raw-log verification read exposed later turns. This replay
  is closed at turn 5 and must not be extended as fresh work.

Players: p1 `aminita`, p2 `The_App15`.

## Score Summary

Decisions: 10 scored, 0 unscored.

Top-match: 2/10.
Acceptable-match: 5/10.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 7/10.
Route-converting move chosen: 5/10.
Branch-punish chosen: 4/8.
Earliest meaningful error: turn 1.

Result: not progress. Severe, hidden-info, state, and mechanics gates stayed
clean, but this was an early stop with weak top-match, weak route conversion,
and a repeated public Baton Pass package miss. The core failure was not
"unsafe play"; it was choosing plausible safe/generic lines instead of
opening the Jolteon boost-plus-receiver route after Baton Pass was revealed.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Switch to a special/Electric answer such as Snorlax/Raikou/Jolteon class; Ice Beam/Icy Wind; Spikes only on switch read | Jolteon | top by class | P/R/B | Correct class: Cloyster left before Zapdos pressure. Exact Jolteon later mattered because it was not only an Electric answer. |
| 1 | p2 | Thunder/active Electric pressure; Thunderbolt/Hidden Power; counter-pivot if reading p1 switch | Tyranitar | miss | - | Missed the immediate branch-punish into the Electric answer. |
| 2 | p1 | Handoff to Cloyster as Tyranitar answer; Thunder Wave/status; Growth/Baton Pass possible if set | Baton Pass to Cloyster | acceptable | P/R/B | Correct target board, wrong framing: Baton Pass was a public package reveal, not just switch syntax. |
| 2 | p2 | Earthquake or Ground/Rock attack class; Rock Slide; Curse/Pursuit | Rock Slide | acceptable | P | Correct pressure class, exact move was secondary. |
| 3 | p1 | Surf/coverage into Tyranitar; Spikes if forcing switch; Explosion high-risk later | Spikes | acceptable | P/R | Spikes was ranked, but top underrated Cloyster's one guaranteed field job before dying. |
| 3 | p2 | Switch Zapdos/Water resist owner; Rock Slide if staying; other pressure | Thunderbolt | miss | P/R | Tyranitar had lure coverage for Cloyster. Before reveal this was not anchorable, but voluntary-entry intent should have kept stay-and-cover live. |
| 4 | p1 | Cross Chop/Fighting STAB; DynamicPunch if present; setup/coverage/counter-switch if switch expected | Jolteon | miss | - | Missed the counter-switch to the named Zapdos receiver. This was the branch-action failure independent of hidden info. |
| 4 | p2 | Switch Zapdos as Fighting receiver; attack if reading no Fighting | Zapdos | top | P/R/B | Correct receiver. |
| 5 | p1 | Baton Pass to Machamp to punish Tyranitar/Snorlax receiver; Thunder if Zapdos stays; Growth/Hidden Power/Agility possible but not top | Agility | miss | P/R | Public Baton Pass required opening the Agility ledger before the pass. I treated the pass as immediate handoff only. |
| 5 | p2 | Zapdos Thunder/attack or Whirlwind if available; Tyranitar switch; other counter-pivot | Snorlax | miss | P | Missed the normal-special route owner into Jolteon's package. Possible phaze was not revealed and should have had a fallback. |

## Reusable Lessons

- A dry Baton Pass reveal changes the next Jolteon sighting. The question is
  no longer only attack versus switch; it is boost, receiver, denial, and then
  the fallback if the opponent stays.
- Jolteon in GSC OU is a live Agility/Growth/Substitute passer once Baton Pass
  appears. Do not collapse Baton Pass into a fancy switch.
- If Machamp has already been revealed and Jolteon is in front of Zapdos or a
  normal-special route owner, rank Agility plus pass to Machamp beside direct
  Baton Pass and Electric attacks.
- Counter-switches are still positive moves. On turn 4, Machamp into
  Tyranitar was less important than the Zapdos receiver that both players
  could name.
- Hidden Tyranitar Thunderbolt was not a hidden-info error because it was not
  used to anchor the frozen choice. After reveal, the role must immediately be
  reclassified as lure coverage into Cloyster.
- Future work should ask "what route does this support move create next turn?"
  before scoring a line as positive. Safe pressure without receiver conversion
  is not enough.
