# Replay Turn-Pause 016 Baton Pass Re-Solve - smogtours-gen2ou-934428 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934428`.

Discovery source: Pokemon Showdown replay search API,
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`.

Mode: spectator public.

Purpose: fresh follow-up to the Focus Energy regression. The target question
was whether I would re-solve after a setup/pass reveal instead of following a
single script such as "boost, then pass immediately."

Contamination control:

- Local search found no prior `934428` quick test, review, or worked example.
- I downloaded the raw `.log` to `.local/pokemon_mastery/replay_logs/`.
- Turns 1-3 were revealed while identifying the opening and are treated as
  context only, not scored.
- Turns 4-11 were answered before each reveal. The helper does not model Baton
  Pass boosts after a pass, so the manual public state for turns 7-8 included
  Machamp's passed `atk+2` and `spe+2`.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/focus_energy_counter_branch_regression_001_smogtours-gen2ou-935022_2026-05-14.md`

Web sources checked:

- Smogon Baton Pass Chain article:
  `https://www.smogon.com/rs/articles/baton_pass`
- Smogon GSC Scizor forum revamp:
  `https://www.smogon.com/forums/threads/scizor-ou-revamp.3510707/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon GSC Spikes article:
  `https://www.smogon.com/gs/articles/gsc_spikes`

Source note: the web check reinforced that Baton Pass is a route-transfer move
whose timing matters, and that GSC Scizor's practical niche is not just passing
immediately; it can add Swords Dance, attack with Hidden Power, or pass to a
specific receiver once the board has been priced.

## Score Summary

Turns scored: 4-11.

Decisions scored: 15 side-decisions. p2 turn 7 was excluded because Snorlax
fainted before its selected move was logged; the non-switch is still noted as
context.

Top-match: 7 / 15.

Acceptable-match: 11 / 15.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 5.

Targeted result: partial correction. I tracked the passed boosts manually and
correctly called the Machamp cash-in sequence, but I underpriced the more
flexible Baton Pass route: Scizor could attack before passing, and Jolteon
could use Baton Pass as a fast pivot to spend Smeargle even without passing
boosts.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 4 | Scizor `spe+2` vs Curse Snorlax | p1 Baton Pass; p2 Double-Edge | p1 Swords Dance; p2 Double-Edge | p1 acceptable, p2 top | Passing was live, but the better route first added Attack because resisted Double-Edge did not force an immediate pass. |
| 5 | Scizor `atk+2/spe+2` at 61 vs Snorlax 100 | p1 Baton Pass; p2 Double-Edge | p1 Hidden Power; p2 Double-Edge | p1 miss, p2 top | Do not autopass: +2 Hidden Power Fighting changed Snorlax's HP map before the handoff. |
| 6 | Scizor 31 with boosts vs Snorlax 60 | p1 Baton Pass; p2 Double-Edge | p1 Baton Pass to Machamp; p2 Double-Edge | both top | Correct handoff point after Snorlax was chipped into Machamp range. |
| 7 | Passed `atk+2/spe+2` Machamp 23 vs Snorlax 52 | p1 Cross Chop; p2 switch to answer if available | p1 Cross Chop KO; p2 move unlogged | p1 top, p2 excluded | Passed boosts must remain in state even if the helper omits them. |
| 8 | Boosted Machamp 23 vs Zapdos 100 | p1 Rock Slide; p2 Thunder | p1 Rock Slide; p2 Thunder | both top | Correctly priced that +2 Rock Slide was route-progressing but not a guaranteed KO. |
| 9 | Jolteon 100 vs Zapdos 31 | p1 Electric attack; p2 switch to an answer | p1 Thunder into Exeggutor; p2 Exeggutor | both acceptable | Preserve the damaged Zapdos; Jolteon's attack choice must include the switch branch. |
| 10 | Jolteon vs Exeggutor 68 | p1 spend Smeargle; p2 Sleep Powder | p1 Baton Pass to Smeargle; p2 Psychic KO | p1 acceptable, p2 miss | Baton Pass can be a fast pivot with no boost payload. Psychic beat sleeping a nearly spent Smeargle. |
| 11 | Snorlax 100 vs Exeggutor 74 | p1 Body Slam / Double-Edge; p2 Sleep Powder | p1 Lovely Kiss into Cloyster switch | both miss | Re-solve after the pivot: p1 Snorlax had its own sleep route, and p2 preserved Exeggutor by switching to Cloyster. |

## Error Classes

- Baton Pass script error: I treated boost transfer as the default endpoint and
  missed attack-before-pass on turn 5.
- Fast-pivot underpricing: turn 10 showed Baton Pass used as a tempo-preserving
  switch to spend Smeargle, not as a boost handoff.
- Sleep-route undercall: turn 11 showed Snorlax can be the sleep initiator, not
  only the anchor being protected from Exeggutor sleep.
- Helper limitation caught manually: the local replay helper does not retain
  Baton Pass boosts after the switch. I corrected the public state manually for
  turns 7-8, so this did not become a scored state error.

## Policy Update

Add a paused-turn prompt for Baton Pass routes: after each reveal, rank add
boost, attack with the passer, pass to receiver, fast-pivot to a sack, or
abandon the chain. Do not compress the whole line to "pass now."

## Next Study Target

Run a short sleep-route drill where Snorlax, Exeggutor, and a low-value absorber
are all live, because turn 11 exposed that I over-assigned sleep initiative to
Exeggutor and missed Lovely Kiss plus absorber switching.
