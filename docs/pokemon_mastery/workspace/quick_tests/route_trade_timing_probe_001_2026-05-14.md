# Route Trade Timing Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_024` misses into six compact prompts
that force the choice between Toxic first, Spikes first, absorber pivot,
immediate Explosion/Self-Destruct, preserving the exploder, and delayed
cash-out.

This is not final-exam evidence. The prompts were built after studying the
policy and prior replay, so the score is a regression/checklist result, not a
fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_024_route_trade_threshold_smogtours-gen2ou-934148_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/route_trade_active_pressure_probe_001_smogtours-gen2ou-934329_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: GSC Explosion is a route trade, but Cloyster and similar pieces
often have other route jobs first. The sources emphasize Snorlax as a key Toxic
target, Cloyster as a Spikes plus Explosion role-compressor, and the need to
pair Snorlax Self-Destruct with successors that inherit its defensive job.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenario 3 and scenario 6 need fresh replay
transfer. The live skill is not knowing the checklist, but recognizing when the
same Snorlax route has crossed from "status and pivot" into "trade now."

## Scenario 1 - Toxic First

Public state: vanilla GSC, player-side known set. Our Cloyster is 100% with
Toxic / Spikes / Surf / Explosion. Opposing Snorlax is 100% at `atk+1 def+1
spe-1`, has revealed Curse, and is not statused. Spikes are not up on the
opponent's side. Our Tyranitar and Zapdos are healthy enough to pivot into
Double-Edge and Earthquake branches after poison starts ticking.

Frozen answer: use Toxic. Confidence: high. The route is to put CurseLax on a
clock before spending Cloyster's one-time trade. Explosion is a serious
alternative only if Cloyster will be KOed before Toxic matters, Snorlax can
Rest freely, or no absorber path exists. Worst branch: Toxic misses or Snorlax
has Rest and starts a longer cycle, but even then the status reveal changes
the next route.

Policy key: when the route threat is boosting but not yet converting, status
can be the first answer before the trade.

Grade: complete.

## Scenario 2 - Spikes First After Status

Public state: vanilla GSC, player-side known set. Our Cloyster is 100% with
Toxic / Spikes / Surf / Explosion. Opposing Snorlax is at `atk+2 def+2 spe-2`,
100%, and badly poisoned. It has revealed Curse but no Rest. Spikes are not up
on the opponent's side. Our Tyranitar can take one Double-Edge after Cloyster
does its job.

Frozen answer: use Spikes. Confidence: medium-high. The route is to convert
the forced future switching and poison clock into whole-team pressure before
Cloyster is spent. Explosion is still serious if Double-Edge damage or Rest
would erase Cloyster's chance, but the clean route is status, then field, then
trade or pivot. Worst branch: Snorlax attacks immediately and Cloyster loses
too much HP to boom later.

Policy key: after Toxic lands, support can still outrank Explosion if the
support changes the next board and a lower-cost absorber is available.

Grade: complete.

## Scenario 3 - Absorber Pivot

Public state: vanilla GSC, player-side known team. Our Cloyster is 40% with
Toxic / Spikes / Surf / Explosion. Opposing Snorlax is 85%, badly poisoned,
at `atk+2 def+2 spe-2`, and has Double-Edge revealed. Spikes are up on the
opponent's side. Our Tyranitar is 100% and can resist Double-Edge; Zapdos is
healthy and immune to Earthquake.

Frozen answer: switch Tyranitar first, keeping Zapdos as the Earthquake pivot.
Confidence: medium-high. The route is to preserve Cloyster's possible later
Explosion while the poison/recoil clock advances through a cheaper absorber.
Explosion is acceptable only if the absorber line fails to contain Snorlax or
Snorlax is about to Rest. Worst branch: Snorlax predicts Tyranitar with
Earthquake, forcing the Zapdos layer of the plan.

Policy key: when a lower-cost absorber advances the same route, do not spend
the one-time trade yet.

Grade: complete.

## Scenario 4 - Immediate Explosion

Public state: vanilla GSC, player-side known set. Our Cloyster is 38% with
Surf / Toxic / Spikes / Explosion. Opposing Snorlax is 72%, at `atk+2 def+2
spe-2`, has Curse / Double-Edge / Rest revealed, and is not statused. Our
Tyranitar is fainted, Zapdos is at 44%, and Snorlax will Rest if given another
turn. Spikes are already up.

Frozen answer: use Explosion. Confidence: high. The route is to stop the
active Curselax before it either KOs Cloyster or resets with Rest; the support
jobs are already delivered and the absorber map is gone. Serious alternatives:
Surf only if it KOs or puts Snorlax into a guaranteed revenge range; switching
is too slow if it lets Rest happen. Worst branch: a Ghost/Normal resist catches
Explosion or Snorlax survives into Rest range.

Policy key: immediate cash-out is correct when support is delivered,
absorbers are insufficient, and delay gives the target a reset.

Grade: complete.

## Scenario 5 - Preserve The Exploder

Public state: vanilla GSC, spectator-public style. Our Exeggutor is 63% with
Psychic and Thief revealed; Explosion is possible but not public. Opposing
Raikou is 59% and has Hidden Power revealed. Our Snorlax is healthy and can
absorb Raikou while Exeggutor still has value into Water/Ground routes.

Frozen answer: switch Snorlax, not Explosion. Confidence: medium-high. The
route is to use the recurring absorber before spending an unrevealed one-time
trade into a target that has not yet become the exact blocker. Serious
alternative: Psychic if staying chips safely; Explosion only if Raikou is the
route blocker and Exeggutor's remaining jobs are covered. Worst branch:
Snorlax gives Raikou or a double switch too much tempo.

Policy key: possible Explosion is not a reason to ignore a safe recurring
answer.

Grade: complete.

## Scenario 6 - Delayed Self-Destruct Into Exact Target

Public state: vanilla GSC, player-side known set. Our Snorlax is 48%, badly
poisoned, at `atk+2 def+2 spe-2`, with Double-Edge / Earthquake /
Self-Destruct revealed. Opposing Zapdos is active at 100% and can pressure the
rest of the team. Spikes are up on the opponent's side. Our Exeggutor and
Vaporeon can inherit enough of Snorlax's remaining defensive job, but they do
not want Zapdos alive.

Frozen answer: use Self-Destruct. Confidence: high. The route is delayed
cash-out: Toxic, Spikes, recoil, and absorber cycling have already extracted
value, and Zapdos is now the exact active target. Serious alternatives:
Double-Edge only if Self-Destruct is needed for a bigger blocker; Rest if it is
available and safe, but poison and Zapdos pressure make that unlikely. Worst
branch: Zapdos switches to a low-value absorber or Snorlax's lost role was
underestimated.

Policy key: the same trade that was premature earlier can become correct once
the exact target is active and prior jobs are complete.

Grade: complete.

## Resulting Rule

Before choosing the trade, rank these in order:

1. Status first if it changes the active threat's clock.
2. Spikes first if status already forces movement and a later absorber exists.
3. Absorber pivot if the clock advances without spending the one-time resource.
4. Preserve the exploder if a recurring answer covers the target.
5. Explode immediately if delay gives Rest, setup, or route escape.
6. Cash out after setup support when the exact target finally appears.

## Next Study Target

Run a fresh unseen replay segment with Cloyster or Forretress against a
boosting Snorlax and score whether this timing ladder transfers under real
turn pressure.
