# Boss AI Teaching Heuristics

Purpose: preserve the user's boss-battle judgment as readable rules before
turning it into synthetic examples, debugger weights, or ROM scoring changes.

This file is the working sheet for the hybrid teaching loop. A rule should not
be promoted into ROM behavior just because it appears here; it needs matching
fixtures, passing audits, and a clear implementation target.

## Workflow

1. Ask the user a concrete public-info boss state from the training lab.
2. Record the answer as a rule, exception, or open question here.
3. Save the matching preference or trajectory row in the lab data.
4. Re-run reports to check for conflicts, stale source rows, and coverage gaps.
5. Generate synthetic examples only from stable, high-confidence rules.
6. Keep user-authored examples weighted above synthetic examples.
7. Promote a rule to ROM scoring only when the behavior is clear and testable.

## Synthetic Data Rules

- Synthetic examples are allowed for obvious cases, not taste calls.
- Synthetic rows must stay marked as synthetic when generated.
- Do not generate synthetic labels from a rule with unresolved exceptions.
- Do not use synthetic data to override a direct user answer.
- Prefer small batches that can be spot-checked before larger batches.

## Pokemon Singles Study Notebook

Status: active learning. Do not treat this section as mastery proof yet. It is
the working notebook for learning the game well enough to answer Gym Leader Lab
questions without sounding like a generic policy summary.

### Research Autonomy Contract

The user explicitly granted autonomy to spend long work blocks on fuzzy expert
study, web research, and battle review even when the immediate output is not
code. The primary curriculum is how strong players actually play Pokemon,
especially Smogon GSC articles, analyses, forum discussions, tournament
replays, and battle logs.

GPT-5.5 Pro's saved guidance has been read and organized under
`docs/pokemon_mastery/workspace/pro_notes/`. Treat those files as method guidance for
study, review, and evidence discipline, not as a replacement for expert-source
study.

Weighting rule:

- Expert play sources and long battle reviews are the main training signal.
- Romhack source/docs/debugger evidence is the transfer and verification layer.
- User-provided RLHF cards are calibration examples, not the curriculum; weight
  them lightly unless they expose a concrete mechanic, answer flip, or repeated
  decision error.

Preferred work-block shape:

1. Read and synthesize expert sources first.
2. Review full games or long constructed positions for win-condition,
   preservation, Spikes, status, Rest-cycle, Explosion, phazing, PP, and
   hidden-information decisions.
3. Convert only the best learned principles into policy notes, benchmark cards,
   or tests.
4. Avoid spending most of a block expanding local preference cards unless the
   user explicitly asks for that.
5. Never delete ROM artifacts or spend real money.

### Operational Mastery Target

I am not "done" when I can name a good move in a vacuum. The target is to play
or analyze a long singles battle by tracking:

- the current damage race;
- both players' likely win conditions;
- which Pokemon must be preserved for later;
- which opposing answers have been revealed, weakened, slept, paralyzed, or
  removed;
- what happens after taking a KO;
- what happens if a setup, sleep, recovery, or switch line fails;
- PP, recovery, hazards, status, and forced-switch consequences over many
  turns.

Before choosing a move, ask these questions in order:

1. Can I win or prevent losing immediately?
2. Does a direct KO create a worse board for me on the next forced switch?
3. Which side improves if both players make the obvious safe play?
4. What is the worst plausible punish, and can my team absorb it?
5. Does setup change the number of turns needed to win, or is it just greed?
6. Is status buying a concrete future turn, denying recovery, or preserving a
   resource?
7. Is switching preserving something that matters, or just giving away tempo?
8. After this exchange, what is my remaining route to win?

### Research Anchors

Current web research agrees with the user-taught direction:

- Smogon's beginner guide frames good play as minimizing risk while maximizing
  reward each turn, then checking the long-term effect of a move: what comes in
  after a KO, and how a sweeper gets a setup opportunity.
- Smogon's risk/reward guide separates the likely opposing move from the
  worst-case move, and says conservative play is strongest when the matchup is
  already favorable while riskier play may be needed from a bad matchup.
- Smogon's long-term thinking guide emphasizes that battles are not one-turn
  puzzles; preserve sweepers until counters are known or weakened, track PP,
  and use recovery turns as chances to create pressure.
- GSC Spikes writing treats status as long-term pressure, not just immediate
  disruption: status can deny spin, force recovery, and support future entry or
  setup lines, but it needs patience and a plan against cleric/recovery answers.
- GSC-specific writing emphasizes that normal GSC is not won by autopilot
  switching. You need a plan and backup plan, look many turns ahead, exploit
  switching patterns, and avoid relying on Snorlax as the only win condition.
- Win-condition writing frames a win condition as an endgame route, not just a
  strong Pokemon: identify what threatens you, remove or weaken those answers,
  and update the plan as information changes.
- GSC mechanics notes matter for this hack's base: one-layer Spikes, Sleep Talk
  can call Rest, and GSC Roar/Whirlwind have generation-specific behavior.
- Borat's GSC guide is a useful warning against shallow one-turn thinking:
  kills are worked for, switches must be punished, and useful planning can run
  many turns ahead rather than only predicting the next click.
- GSC threat writing treats Snorlax as the central threat and warns that no
  single answer covers all sets. Preserve multiple Snorlax answers or a real
  emergency route instead of assuming one check solves the matchup.
- GSC Explosion writing treats Explosion as wallbreaking, emergency defense,
  free-turn creation, or endgame simplification depending on context. It is a
  future-route trade, not just a high-damage move.
- GSC Misdreavus analysis supports the trap-clock lesson from the scratch
  battles: Ghost typing, spinblocking, Snorlax checking, Mean Look, Perish
  Song, and Pursuit vulnerability form a whole route map. The answer is not
  "attack the Ghost"; the answer is to know whether phazing, Pursuit, sleep
  state, or immediate KO pressure can change the countdown.
- GSC SleepTrap discussion reinforces that sleep plus trapping can bypass the
  normal "fodder something to sleep, then answer it" pattern. Any sleep/trap
  line in the romhack must therefore be treated as a mechanics and ruleset
  question, not just a standard status heuristic.

Sources:

- https://www.smogon.com/articles/getting-started
- https://www.smogon.com/resources/beginner/bw_risk_reward
- https://www.smogon.com/rs/articles/long_term_thinking
- https://www.smogon.com/gs/articles/gsc_spikes
- https://www.smogon.com/smog/issue28/gsc
- https://www.smogon.com/gs/articles/gsc_guide_part1
- https://www.smogon.com/gs/articles/gsc_threats
- https://www.smogon.com/gs/articles/guide_to_explosion
- https://www.smogon.com/forums/threads/misdreavus-ou-revamp-done.3643258/
- https://www.smogon.com/forums/threads/sleep-trapping.3617871/
- https://www.smogon.com/forums/threads/knowing-how-to-find-your-win-condition.3474271/
- https://www.smogon.com/forums/threads/gsc-mechanics.3542417/
- https://github.com/smogon/pokemon-showdown
- https://www.npmjs.com/package/%40pkmn/sim

### Evidence Tiers

Keep these separate:

- General strategy source: Smogon articles, Showdown-style simulations, and
  human review. Use this to learn concepts like tempo, win conditions, status
  pressure, setup windows, and long-term planning.
- Romhack source evidence: source-derived fixtures, trainer rosters, move data,
  type charts, and threat availability reports. Use this before answering a
  Gym Leader Lab state.
- Romhack runtime evidence: damage debugger, PyBoy, trace ROM captures, and
  live battle states. Use this before claiming exact damage, exact legality, AI
  behavior, or source-level correctness.

Do not promote a Showdown-sim result to a boss heuristic unless the same idea
still makes sense against the romhack fixture data and known mechanics.

### Romhack-Specific Simulation Path

Easiest useful path for Gym Leader Lab work:

1. Start from `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
   so teams, known moves, public priors, boss rosters, and field context come
   from this repo instead of a generic simulator.
2. Use `tools.damage_debugger.matchup` or the preference lab's damage-estimate
   helpers for concrete damage questions before trusting type or KO intuition.
3. Build a small branch evaluator for lab-shaped questions:
   sleep/setup/attack, switch/preserve, recover/attack, scout/commit, and
   lock-in/cash-out.
4. Use PyBoy or trace ROM only when exact battle-engine behavior matters.

Full Pokemon Showdown parity is possible but should be treated as a separate
project, not a quick prerequisite. Do not edit installed `node_modules`
directly. If a playable sandbox becomes worth it, make a local Showdown mod or
fork and port mechanics incrementally from the repo docs and data. The first
version should cover only the mechanics the current lab questions need.

### Transfer Model

Learning normal GSC is still worthwhile. Treat it as the base language for:

- long-term win-condition planning;
- Rest, Sleep Talk, status, and recovery cycles;
- using sleep or paralysis to create setup turns;
- preserving key Pokemon instead of winning only the current turn;
- switching, double-switching, phazing, and punishing predictable patterns;
- turning Spikes/status chip into future KO ranges.

The romhack is the dialect layer. Before answering a lab question, check the
local differences that can change the conclusion. The largest current caution
is three-layer Spikes, because it makes repeated switching much more expensive
than vanilla GSC. Type passives, late-gen item behavior, and trainer-specific
rosters are also enough to change damage races and switch value.

### GSC Role Map Seed

Use roles to decide what can be spent. A Pokemon is "low HP" only after its
job is no longer needed; otherwise it may still be the piece holding the game
together.

| Role | Common GSC examples | Why it matters | Preservation question |
| --- | --- | --- | --- |
| Central win route / defensive hub | Snorlax | Snorlax can attack, absorb special pressure, Rest, Curse, spread paralysis, or boom depending on set. No one answer covers every set. | What stops opposing Snorlax if this is damaged, slept, boomed, or forced to Rest? |
| Spiker | Cloyster, Forretress | Spikes turn switching, phazing, Rest cycles, and doubles into progress. In this romhack, 3 layers can make the role even more defining. | Can the setter place and keep hazards, or is it being spent before the hazard game starts? |
| Spinner / hazard control | Starmie, Forretress, Cloyster | Removing Spikes changes every future switch and can rescue a defensive gameplan. | If this dies or is statused, can the team still tolerate hazard pressure? |
| Spinblocker / anti-removal | Misdreavus, Gengar | Keeps Spikes down and can force awkward Normal/Ghost coverage decisions. | Is blocking spin worth the HP/status risk in this specific hazard state? |
| Phazer / anti-setup | Skarmory, Steelix, Raikou, Suicune | Roar/Whirlwind stops setup and turns Spikes into repeated damage. Gen 2 phazing has special priority behavior, so speed order matters. | If this phazer is lost, what stops Curse, Belly Drum, Growth, or Baton Pass routes? |
| Electric pressure / bulky special check | Raikou, Zapdos | Forces Water/Flying pressure, absorbs some special routes, and often participates in RestTalk cycles. | Can this afford Rest now, or will sleep turns donate tempo? |
| Explosion / sacrifice route | Cloyster, Exeggutor, Gengar, Steelix, Forretress, Snorlax | Explosion can remove counters, stop a sweep, create a free entry, or simplify a won endgame. | What future route does the trade buy, and what defensive job disappears? |
| Sleep or paralysis creator | Exeggutor, Gengar, Jynx, Nidoking, Lovely Kiss Snorlax | Status creates turns, denies recovery, and shapes switch patterns. | What exact turn does status buy, and what happens after miss, wake, or status block? |
| Physical breaker | Machamp, Marowak, Belly Drum or Curse Snorlax | Converts chip/status into forced damage and punishes passive teams. | Which opposing answer must be weakened, slept, trapped, boomed, or phazed first? |
| Recovery wall / Rest-cycle piece | Suicune, Miltank, Umbreon, Starmie, Blissey | Can stretch games, force PP/resource questions, or stall without progress if unsupported. | Is recovery preserving a route, or giving the opponent a free setup/hazard turn? |

Romhack transfer rule: map the role first, then re-check the mechanics. A local
species may fill a familiar role with unfamiliar stats, moves, passive type
effects, items, or hazard economics.

### Romhack Mechanics Checkpoints

Use these local facts when translating general singles ideas into this hack:

- Sleep duration matches vanilla Gen 2: sleep is rolled at application, stores
  a `2..7` counter, and produces 1..6 asleep turns before the wake-up turn.
  Sleep Talk and Snore exist; Rest uses the stock Rest sleep counter.
- Spikes is not vanilla GSC. This hack has 3 layers:
  1 layer is max HP / 8, 2 layers is max HP / 6, and 3 layers is max HP / 4.
  Flying-types are unaffected, Rapid Spin clears all layers, and a fourth
  Spikes click fails instead of adding value.
- Type passives and late-gen item changes mean type-chart and damage intuition
  must be checked against local docs or the damage debugger before being used
  as a firm lab answer.

Local references:

- `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- `docs/mechanics_changes_from_base.md`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/core.asm`
- `tools/boss_ai_preference/README.md`

### Romhack Delta Register Seed

Do not transfer vanilla GSC conclusions through these mechanics without a local
check:

| Delta | Local fact | Strategic implication |
| --- | --- | --- |
| Spikes | 3 layers: max HP / 8, / 6, / 4; Flying-types ignore them; Rapid Spin clears all layers; extra layers fail after 3. | Hazard turns can be much more decisive than vanilla, but only if the setter survives long enough or the spinner is controlled. The third layer can be worth more than ordinary chip; a fourth click is a state error. |
| Type passives | Type-based effects apply to every mon of that type; they are not optional abilities. | Damage and status plans need local verification even when the type chart looks familiar. |
| Dark status shield | Full Dark blocks the first eligible incoming status; half Dark has a 50% block chance. | Do not treat sleep, Toxic, or paralysis into Dark targets as reliable one-turn control unless the shield is already consumed or the branch tolerates failure. |
| Dragon defender | Non-super-effective hits into Dragon are reduced by Imperial Scales. | Neutral chip into Dragon-types may be far weaker than normal; KO math must be checked before assuming a speed advantage is enough. |
| Dragon attacker | Dragon damaging moves can treat immunities as resistances; Dragon Outrage may use physical category when Attack exceeds Special Attack. | "Immune pivot" and Counter/Mirror Coat logic can change for Dragon routes. |
| Electric speed | Electric types get a small speed multiplier. | Close speed races involving Electric pivots need local speed evidence, not base-stat slogans. |
| Grass regrowth | Grass types heal between turns if not statused and not full HP. | Poison/paralysis can be a resource denial tool, not merely chip or speed control. |
| Poison contact retaliation | Contact into Poison defenders can poison the attacker unless immunity/status/item rules block it. | Contact chip can carry hidden future cost; non-contact alternatives may preserve long-game resources. |
| Psychic mind shield | Psychic defenders have a small chance to take 0 damage while still registering a hit. | Low-probability defensive branches should be separated from decision quality; do not overfit to the null-damage outcome. |
| Steel recoil mitigation | Steel users reduce or remove recoil from recoil moves. | Recoil-based trade math is different for Steel attackers. |

Resolved mismatch ledger:

- `mismatch_ground_flying_damage_001`: resolved as a Dragon's Majesty / fixture
  note issue, not a debugger issue. `data/types/type_matchups.asm` correctly
  lists Ground into Flying as `NO_EFFECT`, and non-Dragon Ground users such as
  Onix, Donphan, and Golem return 0 damage into Flying targets. Dragon-typed
  attackers such as Dragonite, Steelix, Gyarados, and Kingdra can still hit
  type-chart immunities as resistances because Dragon's Majesty applies to
  damaging non-fixed moves. The Lance Aerodactyl fixture note "Earthquake
  cannot hit a Flying target" is therefore too broad for Dragonite.

Extracted delta rule: when the attacker has Dragon typing, re-check any line
that relies on a type immunity. The base chart row may still say `NO_EFFECT`,
but Dragon's Majesty can make the damaging move connect as resisted damage.

### Simulation Notes

Scratch simulator: `.local/tmp/pokemon_singles_sim`, using canonical
Pokemon Showdown-style Gen 2 mechanics through `@pkmn/sim`, installed outside
tracked repo files. This is for learning general singles concepts and sanity
checking strategic branches only. It does not simulate this romhack's custom
moves, type passives, item changes, stat changes, trainer rosters, or boss AI.
Use the repo's damage debugger, source-derived fixtures, and PyBoy/trace ROM
runs before treating any result as romhack behavior or turning it into ROM
scoring.

Important limitation: the current sleep/setup sims are controlled policy tests,
not proof of optimal play. I picked both sides' policies: Victreebel followed
the tested line and Snorlax mostly used steady Body Slam pressure. These runs
show whether a line is robust against that pressure under RNG, but they do not
model a strong opponent that switches, preserves counters, uses Rest
strategically, or changes plans.

First sleep/setup test, 200 deterministic seeds, Gen 2 custom battle:
Victreebel with Sleep Powder / Swords Dance / Sludge Bomb / Giga Drain into
Snorlax using Body Slam pressure.

Observed outcomes, shown as Victreebel wins and losses across 200 simulator
runs with different deterministic RNG seeds:

| Line | Wins | Losses | Note |
| --- | ---: | ---: | --- |
| Sludge Bomb immediately | 30 | 170 | Direct damage was too slow. |
| Swords Dance raw, then attack | 91 | 109 | Setup helped but often ate the punish. |
| Sleep Powder, one Swords Dance, then attack | 133 | 67 | Best result; sleep bought the setup turn. |
| Sleep Powder, two Swords Dances, then attack | 111 | 89 | Worse than one boost; extra greed gave wake/miss/punish chances back. |

Follow-up conditional test, shown as Victreebel wins and losses across 500
deterministic RNG seeds:

| Policy | Wins | Losses | Note |
| --- | ---: | ---: | --- |
| Fixed script: Sleep Powder, Swords Dance, attack | 334 | 166 | Still strong, but it boosts even after a miss. |
| Conditional script: if sleep misses, re-score and retry only while healthy | 393 | 107 | Better; the status branch matters. |

Interpretation: the user's lesson is right, and the boundary matters. Sleep is
not the payoff. Sleep is a way to buy the turn that makes the payoff possible.
After sleep lands, one boost can be correct if it changes the damage race; a
second boost needs fresh evidence that the target cannot wake, punish, switch,
or otherwise make the extra turn bad. If sleep misses, the plan has already
changed; do not blindly spend the next turn on setup.

Long-battle drill, 40-turn canonical Gen 2 scratch simulation:

This was not a good-player-vs-good-player proof. It was a long-game review
surface using bulky GSC-like teams. The value is in spotting strategic errors:

- Turns 1-2: Cloyster poisoned and Exploded on Starmie before setting Spikes.
  Removing Starmie has value because Starmie spins and checks several threats,
  but sacrificing the only Spiker before hazards means the rest of the game no
  longer has passive switch pressure. In this romhack the cost is even higher
  because 3-layer Spikes can define switch economics.
- Turns 3-4: Steelix traded itself for Machamp. This removed a dangerous
  breaker, but also spent the team's phazer/normal-resistant physical answer.
  Explosion is not just damage; it changes the future defensive map.
- Turns 5-8: Raikou used Rest while healthy and without Sleep Talk, then died
  to Tyranitar while asleep. Rest is a resource cycle, not a heal button. If
  the sleeping turns cannot be protected or used, Rest can donate tempo.
- Turns 9-13: Exeggutor and Misdreavus combined Explosion/Perish pressure to
  remove Tyranitar, but by then the team had spent Cloyster, Steelix, Raikou,
  and Exeggutor. Trading can be correct only if the remaining endgame is still
  playable.
- Turns 14-40: the game collapsed into a Snorlax mirror. Paralysis, Curse
  count, Rest timing, Sleep Talk, and PP became the whole game. This is the
  warning: if early trades do not preserve a second route to win, Snorlax is
  forced to solve everything.

Extracted long-game rule: every sacrifice must name the future it buys. "I
removed Starmie" is incomplete unless the next sentence is "therefore my
hazard, Machamp, Marowak, Raikou, or Snorlax route is now live." If the trade
only makes the current turn look good while deleting the support for the
endgame, it is probably bad.

Second long-battle drill, 21-turn canonical Gen 2 scratch simulation:

Team A used Cloyster / Raikou / Snorlax / Steelix / Exeggutor / Starmie into
Forretress / Zapdos / Snorlax / Skarmory / Machamp / Misdreavus. The script
uses seeded `RandomPlayerAI` policies, so it is reproducible, but still only a
mistake-finding surface rather than expert proof.

Critical findings:

- Turns 1-3: both sides committed early to Spikes plus Explosion. Forretress
  set Spikes and blew up; Cloyster set Spikes and blew up on Machamp. This was
  not automatically bad because Team A's Spikes immediately taxed Machamp,
  Snorlax, and Misdreavus. The question is whether the trade names its future:
  "I am spending the Spiker because the hazard is already down and removing
  Machamp opens the Snorlax/Raikou route."
- Turn 4 and turn 20: Zapdos and Raikou clicked Rest while Rest could not
  produce useful recovery. This is a state-precondition error. Recovery has to
  preserve a route or change a damage threshold; otherwise it is just a donated
  turn.
- Turns 5-9: Steelix used Toxic plus Explosion to put Snorlax into a forced
  collapse sequence. Spikes, poison, Explosion chip, Rapid Spin tempo, Starmie
  damage, and Exeggutor damage together removed the central threat. This is a
  good example of a cash-out line: no single move solved Snorlax, but each move
  converted the previous resource into the next one.
- Turn 10: Exeggutor Exploded into Misdreavus Protect and got nothing. This is
  the opposite of the Steelix line. Explosion is only a cash-out when the target
  is forced, trapped, sufficiently punished for switching, or the free entry is
  itself the named payoff.
- Turns 11-16: Snorlax was trapped by Mean Look and then lost to the Perish
  Song clock. Once the trap route starts, normal Rest/Curse logic is no longer
  the main game. The position becomes a clock problem: switch before the trap if
  possible, KO or phaze before the count expires, or accept the trade only if
  the remaining endgame is winning.

Extracted long-game rule: a status move is only progress if it changes the next
resource exchange. Sleep, poison, and hazards all need a follow-up route. If
the next turns do not cash the created opening, the opponent can convert the
"control" turn back into Rest, setup, or a favorable trade.

Third long-battle drill, 81-turn canonical Gen 2 scratch simulation:

Batch run: `node .local/tmp/pokemon_singles_sim/long_gsc_drill.js batch 60`.
Seed offset 36 reached 81 turns and ended with Ledger B winning.

Critical findings:

- Turns 1-3: Cloyster clicked Toxic twice into Forretress, then Exploded into a
  Steel-type that survived. This is two mistakes chained together: status into
  an immune target, then Explosion without a forced or sufficiently valuable
  target. Cloyster died without setting Spikes, so Team A lost its Spiker and
  got no hazard economy in return.
- Turns 5-6: Raikou used Sleep Talk while awake, then stayed in and died to
  Snorlax Earthquake after Thunder missed. The miss was bad luck; staying in
  with no protection against the obvious Ground punish was the decision issue.
- Turns 11-12: Starmie used Rapid Spin when there were no Spikes to remove,
  then died to Machamp. Rapid Spin can be valid chip only if the chip matters;
  otherwise it is another state-precondition failure.
- Turns 25-77: Snorlax eventually beat Skarmory, but it took more than 50
  turns of Curse, Toxic, Rest, Whirlwind, and Body Slam pressure. This was not
  clean progress; it was a single-route endgame grinding through a dedicated
  phazer.
- Turn 49: Exeggutor Exploded into sleeping Skarmory for partial damage. That
  helped Snorlax eventually remove Skarmory, but it also deleted Team A's last
  non-Snorlax piece.
- Turns 78-81: preserved Misdreavus used Perish Song to force the final trade
  and win. The final error was prepared earlier: Team A reduced itself to one
  Snorlax route before checking whether the opponent still had a Ghost/Perish
  endgame.

Extracted long-game rule: before spending the second-to-last route, name the
opponent's preserved anti-route. A sacrifice that helps win the current wall
war can still lose the match if it leaves one Pokemon against an unrevealed or
preserved endgame answer.

Fourth long-battle drill, filtered-policy seed 15, 76-turn canonical Gen 2
scratch simulation:

This game used the filtered random policy, so the obvious state-invalid moves
were already removed. The remaining lessons are higher order:

- Turns 1-5: Cloyster set Spikes and then Exploded into Forretress, but
  Forretress survived, spun the Spikes away, and then Exploded on Raikou. This
  is a sharper version of the sacrifice rule: even after a hazard is placed,
  spending the Spiker is bad if the opponent's hazard-control piece survives
  and removes the hazard anyway.
- Turns 9-13: Misdreavus trapped Starmie and used Perish Song. Starmie removed
  Misdreavus before the clock expired, but still fainted to the Perish count.
  This was a trade, not a clean win. When a trap clock starts, the question is
  not just "can I KO the trapper?" but "what does the forced trade leave me
  against?"
- Turns 17-20: Exeggutor landed Sleep Powder on Skarmory, then used Giga Drain
  twice before Explosion. This is the corrected version of the earlier sleep
  mistake: once sleep lands, use the created turns for damage, switch, setup,
  or a forced trade; do not keep clicking sleep into a sleeping target.
- Turns 21-76: the game became a Snorlax mirror into Zapdos and Machamp. Team A
  eventually won because the opponent's Misdreavus was gone, so collapsing to
  a Snorlax route was not punished the way it was in drill 3. This is the
  important comparison: one-route endgames are bad only when the opponent still
  has the anti-route.

Extracted long-game rule: a sacrifice can be correct in one battle and losing
in another with the same Pokemon if the preserved anti-route differs. The
ledger must ask "what remains after this trade?" before judging the trade.

Fifth long-battle drill, canonical Gen 2 scratch simulation, seed 0, filtered
policy:

- The hard state gates were clean: no awake Sleep Talk, no status into public
  immunity/status, no Rapid Spin with no hazards, no full-HP Rest, and no
  Explosion into a known Ghost.
- Turns 1-4: Cloyster set Spikes, then Exploded into Forretress. This time the
  trade was converted because Raikou immediately removed Forretress before it
  could spin. The same Spiker cashout that was bad in drill 4 became playable
  because hazard control did not survive.
- Turns 6-34: Exeggutor traded Explosion for Machamp, then Snorlax used
  Body Slam / Curse / RestTalk to remove Zapdos and win the Snorlax mirror.
  That is a real route, but it also reduced the game toward one main route.
- Turns 36-52: Skarmory phazed Snorlax repeatedly while Spikes punished the
  dragged bench. Starmie eventually used Rapid Spin with a real hazard-control
  job, clearing Ledger A's side before dying later.
- Turns 64-74: Snorlax converted through Skarmory only after forcing repeated
  Rest cycles. This was not a simple "boost and attack" line; it depended on
  Rest timing, paralysis, Whirlwind turns, and keeping enough HP to survive
  until the phazer was gone.
- Turns 76-79: Misdreavus entered last and used Perish Song / Protect /
  Mean Look. The simulator ended with both final Pokemon fainting and no
  winner line. Strategically, the lesson is still clear: a last-route Snorlax
  that cannot hit Ghosts cannot treat a preserved Misdreavus as a normal damage
  endgame.

Extracted long-game rule: a route is not complete just because it beats the
current wall. Before committing to a last-Pokemon Snorlax line, check whether
the opponent's preserved Ghost, trap clock, phazer, or Explosion route can still
invalidate it after the apparent wall is removed.

Local Rest source check:

- `engine/battle/effect_commands.asm` compares current HP to max HP and jumps
  to the `.hp_full` failed-move path before the Rest-specific status cure and
  sleep-counter code.
- Therefore, in the local engine, Rest at exactly full HP fails even when the
  user is statused. Status-cure Rest requires the user to be below full HP, and
  the resulting sleep turns still need to be playable.

Measured state-error regression, same scratch simulator:

Command:

```text
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 200 random
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 200 filtered
```

The `filtered` policy is still random after applying only hard precondition
gates: no awake Sleep Talk, no direct Rest at exactly full HP, no direct Rest
at high HP with no status, no Rapid Spin with no own Spikes, no Toxic or sleep
move into a target that was immune or already statused at turn start, and no
Explosion into a known Ghost / Misdreavus denial target. It is not a strong
player. It is a test of whether the notebook's hard gates remove obvious state
errors.

| Metric across 200 games | Random policy | Filtered policy | Interpretation |
| --- | ---: | ---: | --- |
| Total turns | 8292 | 6612 | Different games, so compare error classes, not win rate. |
| Awake Sleep Talk | 668 | 0 | Hard state gate works. |
| Rapid Spin with no hazards to remove | 412 | 0 | Hazard-state gate works. |
| Toxic into immune/statused target | 360 | 0 | Status target gate works. |
| Sleep move into already-statused target | 64 | 0 | Sleep gate works when judged by turn-start state. |
| Direct Rest at exactly full HP | 798 | 0 | Local source-backed hard gate works. |
| Direct Rest at exactly full HP while statused | 350 | 0 | Status does not rescue full-HP Rest because the full-HP failure path comes first. |
| Direct Rest at high/full HP with no status | 545 | 0 | Hard recovery gate works. |
| Direct Rest at high/full HP while statused | 501 | 33 | Remaining cases are below full HP; they need Rest-cycle review, not a hard ban. |
| Explosion denied without target damage | 52 | 0 | Ghost / known denial target gate works; broader Explosion timing still needs judgment. |

Extracted measurable target: the next policy layer should keep the hard state
metrics at zero while learning when below-full status-cure Rest, hazard
sacrifice, and one-route endgames are actually worth the tempo.

Review of the remaining below-full, high-HP status Rest cases:

- Seed 58 turn 11: Snorlax used Rest at 432/460 while toxic, facing a sleeping
  Skarmory. This is a plausible status-cure Rest because the move succeeds,
  removes a worsening poison clock, and Sleep Talk gives the sleeping turns a
  job.
- Seed 1 turn 12: Raikou used Rest at 276/320 while toxic, but opposing
  Snorlax immediately used Double-Edge and KOed it. This is not a Rest-cycle
  success; the status cure never matters if the public damage branch removes
  the user first.
- Seed 16 turn 16: Snorlax used Rest at 431/460 while toxic, then Skarmory
  Whirlwinded it into a Spikes-taxed Raikou. The Rest clears status, but the
  phaze branch changes the resource exchange. Status-cure Rest must check
  phazing and forced-entry consequences, not only HP and status.

Extracted Rest rule: below-full status-cure Rest is allowed, but only after
checking three branches: immediate damage before recovery, phazing/trapping
after recovery, and whether the sleep turns have Sleep Talk or safe board
support.

Follow-up filtered-policy regression:

```text
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 300 filtered
```

Across 300 filtered games, the hard-invalid counters stayed at zero: awake
Sleep Talk, Rapid Spin with no hazards, Toxic into immune/statused targets,
sleep into already-statused targets, full-HP Rest, high-HP no-status Rest, and
Explosion into known Ghost denial. The only remaining flagged class was 53
below-full, high-HP status Rest events. That supports the split now used in
this notebook: full-HP Rest is a mechanics/state gate; below-full status-cure
Rest is a tactical judgment that must be reviewed through immediate damage,
phazing/trapping, and playable sleep turns.

Large-sample correction:

```text
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 1000 random
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 1000 filtered
```

The 1000-game random baseline produced 3320 awake Sleep Talk attempts, 2046
Rapid Spins with no hazards, 1818 Toxic attempts into immune/statused targets,
3839 full-HP Rest attempts, and 238 Explosion denial events. The 1000-game
filtered policy still held most hard-invalid classes at zero, but exposed 4
full-HP Rest attempts in very long games and 177 below-full high-HP status Rest
events. Manual inspection of seeds 759 and 577 showed these rare full-HP Rest
cases around long RestTalk, phazing, trap-clock, PP, or failed-move endgames.

Correction to the target: do not claim full-HP Rest is completely solved by the
current scratch policy. The rule is still mechanically true, but the simulator
policy needs a PP-aware fallback and failed-move context so it does not choose a
known failed recovery move when every attractive line has collapsed.

Follow-up simulator parser correction:

```text
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 500 random
node .local/tmp/pokemon_singles_sim/long_gsc_drill.js analyze 500 filtered
```

The scratch ledger was over-counting some sleep errors because it kept old
status when a later HP condition had no status suffix. The parser now treats
statusless HP conditions as public status clears and treats successful
non-Sleep Talk moves as wake evidence. This matters because stale `slp` state
can make the policy think Sleep Talk or sleep immunity is legal when the
Pokemon has already woken.

After the parser/status correction, the 500-game comparison was:

| Metric across 500 games | Random policy | Filtered policy | Interpretation |
| --- | ---: | ---: | --- |
| Total turns | 20443 | 16468 | Different games; compare error classes only. |
| Awake Sleep Talk | 2447 | 1 | Hard gate is almost complete; one residual long-game fallback remains to audit. |
| Rapid Spin with no hazards to remove | 1018 | 0 | Hazard-state gate held. |
| Toxic into immune/statused target | 780 | 0 | Status target gate held. |
| Sleep move into already-statused target | 123 | 0 | Sleep target gate held after wake-state cleanup. |
| Direct Rest at exactly full HP | 1942 | 2 | Still not fully solved in rare fallback states. |
| Direct Rest at high/full HP with no status | 2387 | 2 | No-status Rest is nearly eliminated but not proven gone. |
| Direct Rest at high/full HP while statused | 222 | 63 | These need branch review, not a blanket ban. |
| High/full HP Rest while toxic | 171 | 39 | Often a plausible cure line if the sleep turns are playable. |
| High/full HP Rest while paralyzed | 44 | 15 | More suspect than Toxic; must justify speed/status cure value. |
| Manual Rest while already asleep | 0 | 0 | The previous nonzero count was stale ledger state, not confirmed play. |
| Explosion denied without target damage | 129 | 0 | Known Ghost denial gate held. |

Extracted simulator rule: state cleanup is a first-class mechanic. When a
Showdown HP condition loses its status suffix or a sleeping Pokemon
successfully uses a non-Sleep Talk move, clear the old status in the ledger.
Then evaluate Rest by status class: full-HP Rest is a mechanics failure,
high-HP no-status Rest is usually wasted tempo, Toxic-cure Rest can be correct,
paralysis-cure Rest needs a stronger speed or endgame reason, and every
below-full Rest must still price immediate damage, phazing/trapping, and
playable sleep turns.

Follow-up implementation check: splitting the scratch policy into hard-invalid
and soft-avoid move classes, then reading the active slot more carefully, did
not change the 1000-game counts. Inspecting seed 759's ending explains why.
Snorlax was trapped by Misdreavus, Body Slam could not affect the Ghost, sleep
ended at full HP, the Perish count was already running, and the remaining move
choices were failed or exhausted endgame actions. Future reports must separate
avoidable full-HP Rest from no-exit failed-move endgames where the real mistake
was earlier: preserving no answer to the trap clock.

Sixth long-battle drill, filtered-policy seed 264, 79-turn canonical Gen 2
scratch simulation:

- Turns 1-7: Cloyster set Spikes and Exploded into Forretress. Starmie then
  spun away Forretress's Spikes and was removed by Forretress Explosion. This
  was a trade chain, not a simple hazard win: both sides spent hazard-control
  pieces, and the resulting game no longer had easy long-term Spikes pressure.
- Turns 8-29: Steelix and Exeggutor were spent into Skarmory, then Snorlax and
  Raikou finally removed Skarmory. The route worked only because Raikou could
  cash the phazer after Snorlax forced damage and Rest cycles. The review
  question is whether each earlier Explosion made that route easier or merely
  narrowed the game to one route.
- Turns 30-52: Raikou versus Zapdos became a RestTalk and PP/damage-range
  cycle. Rest was playable when the sleeping turns either had Sleep Talk or the
  opponent was also forced into recovery. Rest is bad when it donates tempo; it
  is acceptable when it preserves the only Electric route through a mirrored
  recovery cycle.
- Turns 60-64: low-HP Raikou was caught by Misdreavus's Perish Song / Mean
  Look line and traded down. This was acceptable only because Snorlax still had
  a real endgame into the opposing Snorlax afterward. If the remaining endgame
  were worse, the earlier choice to leave Misdreavus preserved would have been
  the irreversible error.
- Turns 65-79: Snorlax won the final mirror by combining Body Slam paralysis,
  Curse timing, and attacking through Rest turns. The game was decided by
  whether the final route survived all earlier trades, not by one flashy move.

Extracted seed-264 rule: before accepting a chain of sacrifice trades, name the
final route left after the chain. "I eventually win with Snorlax" is only
valid if the remaining opposing Ghost, phazer, Explosion, RestTalk, and PP
routes have been checked.

First external replay review, 46-turn GSC OU game:

- Source context: Smogon GSC Gyarados discussion, proof replay linked from a
  July 2025 post:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`
  and replay log
  `https://replay.pokemonshowdown.com/gen2ou-2404705604-gl00guvgmu8l6etle1dd06927fn0jlspw.log`.
- Opening, turns 1-4: Zapdos and Snorlax traded heavy damage, then both used
  Rest. The immediate damage race reset, but the sleep turns created a new
  positional phase instead of ending the exchange.
- First conversion attempt, turns 8-10: JackRG1 used Belly Drum Snorlax, but
  jouer no L preserved the correct answer by going Skarmory. The boosted Return
  did not break Skarmory, and Snorlax had to leave. Setup failed because the
  opponent's defensive answer was still available.
- Hazard phase, turns 11-14 and 21-23: Cloyster established Spikes, but the
  game still required hazard control. Forretress later set Spikes back against
  a sleeping Zapdos, showing how Rest can donate a hazard turn if the sleeping
  turns are not actively useful.
- Gyarados phase, turns 15-19 and 29-32: Gyarados used Surf and Toxic to force
  awkward pivots and chip Snorlax/Machamp, but it was not a solo breaker. Its
  value was role compression and forcing sequencing, not sweeping.
- Spin phase, turns 32 and 38: Golem removed one side's Spikes, then Forretress
  removed the other side's Spikes. A Spikes plan is not complete when the layer
  goes down; it is complete only if the player can keep the layer relevant or
  make the spin costly.
- Final conversion attempt, turns 39-46: JackRG1 tried Belly Drum Snorlax
  again after forcing Skarmory down. The line still failed because the opposing
  Snorlax was asleep on the bench, returned near full, and woke/acted in time
  to KO the Drummed Snorlax with Double-Edge.

Extracted external-review rule: sleep state is not a permanent disable and
bench sleep can still return as a wake-turn punish. Before setting up into a
sleeping or recently sleeping target, track whether the target can wake, switch
back in, phaze, trade, or attack before the setup route converts.

Replay review helper:

- Scratch tool: `.local/tmp/pokemon_singles_sim/replay_ledger.js`.
- Example:
  `node .local/tmp/pokemon_singles_sim/replay_ledger.js <showdown-log-url>`.
- Purpose: turn Showdown logs into a critical-turn ledger tagged for setup,
  Rest/recovery, Sleep Talk, hazards, spin, phazing, sacrifice, trap clocks,
  sleep punishment, switches, and faints. This does not judge the best move by
  itself; it makes long-game review less likely to skip important resource
  turns.

Second external replay review, 71-turn GSC OU game:

- Source context: Smogon GSC OU discussion replay list:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`
  and replay log
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-505883.log`.
- Turns 1-16: early Curse Snorlax forced Skarmory phazing, then both players
  established Spikes and traded hazard control. Golem spun, Cloyster Exploded,
  and Snorlax was removed. This is a clear route-trade sequence: hazard control
  and Explosion were used to change which late-game pieces mattered.
- Turns 19-30: Raikou Rested, Forretress used the sleeping/electric pressure
  window to re-enter the hazard game, Gengar landed sleep pressure into Zapdos,
  then Exploded into Raikou. The lesson is not simply "Explosion good"; it
  removed the RestTalk Electric and left the game to Snorlax/Skarmory/Golem
  structures.
- Turns 32-58: Skarmory, Snorlax, and Golem entered a long phazing and Rest
  cycle. Golem's Roar repeatedly denied Skarmory's Curse plan while Earthquake
  punished the forced Snorlax entries. This is the kind of 20+ turn sequence
  the notebook must learn: the good move is often the one that keeps the loop
  favorable, not the one that deals the most immediate damage.
- Turn 59: simultaneous phazing mattered. Golem's Roar failed while Skarmory's
  Whirlwind dragged Starmie in, creating the route that later ended the game.
- Turns 68-71: Golem Exploded into Skarmory, Starmie cleaned up with Surf, and
  Nightmare punished the sleeping Snorlax before the final KO.

Extracted external-review rule: when a long game becomes a phazing loop, track
which side benefits from every forced entry. The loop is progress only if it
changes HP, sleep turns, hazard state, PP, or final-entry access in favor of a
named endgame route.

Third external replay review, 54-turn GSC OU game:

- Source context: Smogon GSC OU Winter Seasonal #8 Round 4, leoperi vs
  DonMarto result post:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-4.3778203/`
  and replay log
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-912130.log`.
- Turns 1-5: don marto opened with Curse Snorlax, but leoperi immediately used
  Lovely Kiss, then both sides established Spikes. The early Curse did not
  become a sweep route because the Snorlax route was paused by sleep and then
  taxed by hazards for the rest of the game.
- Turns 6-18: Spikes converted ordinary pivots into real resource loss.
  Meganium repeatedly absorbed Hidden Power / Earthquake pressure and used
  Synthesis and Light Screen to keep the defensive route intact. Chip was only
  progress when it forced a non-recoverable state; otherwise Meganium turned it
  back into a tempo question.
- Turns 24-28: leoperi's Zapdos Rested, then Sleep Talk called Rest at 27% and
  reset the damage race to full. The important lesson is mechanical and
  strategic: attacking a sleeping RestTalk user is not a guaranteed conversion
  unless the Sleep Talk Rest branch has been priced in.
- Turns 33-41: Golem spun away don marto's Spikes, but leoperi preserved enough
  hazard access to re-layer with a poisoned Cloyster on turn 41. Rapid Spin was
  a temporary resource win, not permanent control, because the opposing Spiker
  still had a final job.
- Turns 42-43: leoperi's Cloyster completed a compact route trade. It set
  Spikes, Exploded into opposing Cloyster, then Houndoom cleaned that Cloyster.
  This was a sacrifice with two concrete jobs: restore switch tax and remove
  hazard control / Water counterplay.
- Turns 43-54: the early-slept Snorlax finally returned, still asleep, took
  Spikes and Leech Seed pressure, and woke only in time to Earthquake Rhydon
  before dying to boosted Earthquake. Rhydon then removed sleeping Zapdos before
  falling to Moltres, leaving leoperi's Zapdos to finish. The endgame was won
  because leoperi's final Zapdos route survived the Rhydon trade.

Extracted external-review rule: a preserved sleeping win condition is not the
same thing as an available win condition. Track how many turns it needs before
acting, what entry damage it must absorb, whether the opponent can set up while
it sleeps, and whether the wake turn actually arrives before the route is lost.

External source synthesis, GSC role compression:

- Source context:
  - Cloyster analysis thread:
    `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
  - Snorlax analysis thread:
    `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
  - Steelix analysis thread:
    `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Cloyster is not just "the Spikes Pokemon." The source frames Spikes as a way
  to make repeated grounded answers like Snorlax and Raikou stop entering for
  free, while Surf/Toxic/Explosion make spin attempts and Explosion pivots
  costly. Heuristic implication: after setting Spikes, ask what makes the
  opponent's removal or grounded pivot line expensive.
- Steelix turns the hazard layer into a repeated decision point through Roar.
  The source explicitly ties Roar, Spikes damage, and Cloyster partnership
  together. Heuristic implication: a phazing turn should be scored by the
  forced entry it creates, not by whether it looks passive.
- Snorlax's Curse + Double-Edge/Earthquake pressure can force phazing or win
  outright, but Rest without Sleep Talk creates a setup/phazing window and
  makes hazard control more important. Heuristic implication: Rest is not just
  healing; it changes who gets to spend the next two turns.
- Combined rule: in long GSC games, role compression matters more than species
  slogans. A Cloyster turn, Steelix turn, or Snorlax Rest turn must be judged
  by how it changes hazard relevance, phazing access, Explosion routes, and the
  remaining endgame pieces.

### Current Learning Rules

- Think in routes to win, not isolated best moves. A move is good when it keeps
  or improves the route.
- Prefer the line that wins against normal play and remains acceptable against
  the worst plausible punish.
- A KO is not automatically best if it gives the opponent a free setup entry
  that wins next turn.
- Setup needs a reason: it must change KO math, force a defensive response, or
  make a later sweep possible.
- Sleep is turn creation. Use it when the created turn has a clear job, such as
  one boost, one safe switch, or one recovery denial.
- Do not autopilot after a status move. If sleep misses, if the target wakes, or
  if Sleep Clause blocks another sleep, re-score the board.
- A preservation switch is good only when the saved Pokemon has real future
  value and the switch-in is actually safer.
- Long games are resource games. HP, PP, status slots, revealed moves,
  hazards, and future switch paths all matter.
- Reject state-invalid moves before taste scoring. Awake Sleep Talk, blocked
  sleep, repeated status into an already-statused target, and setup after the
  setup window has closed are not real plans.
- Treat full-HP Rest as state-invalid in the local engine. Rest can cure status
  only if the user is below full HP, and it is still bad if the sleep turns give
  away the position.

### Turn Ledger Template

Use this before reviewing or simulating a serious turn. If I cannot fill this
out, I do not know the position well enough to call the move "optimal".

```text
Battle / fixture:
Turn:
Format evidence: GSC / romhack source / romhack runtime / unknown

Own active:
Opponent active:
Own bench still relevant:
Opponent bench still relevant:

HP ranges:
Status:
Sleep or Rest counters:
Hazards:
Screens / weather / volatile state:
Stat stages:
Known moves:
Likely unrevealed moves:
PP pressure:
Speed order:
Damage ranges that matter:

Own current win routes:
Opponent current win routes:
Own irreplaceable pieces:
Opponent irreplaceable pieces:

Candidate 1:
Immediate result:
Opponent stay-in punish:
Opponent switch punish:
Opponent setup / Rest / status / Explosion punish:
Low-roll / miss / wake / full-para branch:
Resource gained:
Resource spent:
Next-turn plan:
Verdict:

Candidate 2:
Candidate 3:
```

The ledger should force concrete language. "Momentum" is not a resource unless
it names the follow-up: a safe Rest turn, a forced switch, a Spikes layer, a
phaze loop, a damage range, a preserved answer, or a revealed set.

### Decision Classifier

After ranking candidates, label the chosen move with one primary class:

| Class | Use when | Failure sign |
| --- | --- | --- |
| Force | The move wins now, prevents an immediate loss, or creates a forced sequence. | I ignore a reliable force to chase style points. |
| Convert | The move turns an existing edge into a clearer route: KO range, forced Rest, hazard loop, or endgame simplification. | I take chip that does not change any later turn. |
| Preserve | The move keeps an irreplaceable answer alive or avoids exposing a losing route. | I save a Pokemon without a named future job. |
| Scout | The move gathers information while keeping the dangerous branches covered. | I scout when the opponent already has a forced punish. |
| Deny | The move blocks setup, spin, recovery, sleep, phazing, or a free switch. | I deny something that was not actually threatening. |
| Cash out | The move spends a resource, including Explosion or sacrifice, to open a named route. | The trade removes my own last answer or leaves no route. |

If no class fits, the move is probably a vague "do something" click and needs
to be re-scored.

### Heuristic Card Template

Promote a rule only when it can choose moves in positions like the lab asks.

```markdown
# Heuristic: [short name]

Status: proposed / developing / stable / rejected
Format: GSC / romhack / both / unverified transfer
Evidence tier: source / fixture / runtime / simulation / user answer
Last reviewed:

Trigger:
- Exact board features that make the rule relevant.

Rule:
- The move preference or decision policy.

Why this should be true:
- Mechanics, damage ranges, role map, or long-term resource reason.

Candidate lines:
- Best line:
- Main alternative:
- Emergency line:

Exceptions:
- Conditions that flip the decision.

Worst plausible punish:
- The branch that would make this line bad.

Evidence:
- Source:
- Fixture:
- Damage check:
- Simulation:
- Battle review:

Counterexamples:
- Positions where the rule fails or becomes lower priority.

Benchmark tests:
- Scenario IDs that must keep passing.

Failure signs:
- GPT-shaped phrases, missing board facts, or known repeated mistakes.
```

Current stable example:

```markdown
# Heuristic: Re-score after sleep disruption

Status: stable
Format: both, with romhack legality checks
Evidence tier: user answer + simulation + fixture damage

Trigger:
- A sleep move misses, the target wakes, Sleep Clause blocks sleep, the target
  switches, Sleep Talk reveals a dangerous move, or new damage information
  changes the matchup.

Rule:
- Discard the prior sleep/setup script and recompute from the current board.
- Setup is still legal only if it changes KO math or creates a forced route
  after checking the new worst plausible punish.

Exceptions:
- Continue the prior plan only when the failed or changed branch still leaves
  no immediate KO, setup, phazing, or defensive-answer-loss punish.

Failure signs:
- Saying "continue the plan" without naming the changed state.
- Boosting after a miss because the original line wanted a boost.
```

### Battle Review Protocol

For 30+ turn games, review in phases instead of trying to explain every click
equally.

1. Reconstruct the ledger for every turn that changes resources: HP ranges,
   status, sleep or Rest counters, hazards, PP, revealed moves, boosts, and
   role obligations.
2. Split the game into opening, midgame, conversion, and endgame. The boundary
   is not the turn number; it is when the win routes or resource priorities
   change.
3. Mark critical turns where the player could set hazards, spin, sleep, wake,
   Rest, phaze, setup, sacrifice, explode, preserve an answer, or reveal
   coverage.
4. For each critical turn, compare at least three candidate lines with the turn
   ledger template.
5. Separate outcome from decision quality:
   - good decision / bad outcome;
   - bad decision / good outcome;
   - mechanics error;
   - state-tracking error;
   - damage-range error;
   - win-condition error;
   - sacrifice error;
   - script-following error;
   - romhack-transfer error.
6. Find the earliest irreversible error, not just the final losing move.
7. Extract exactly one or more notebook updates: a promoted heuristic, a
   narrowed exception, a rejected rule, or a new benchmark scenario.

### Mistake Loop

Every serious mistake should leave a regression trail:

```text
mistake observed
-> exact position captured
-> error class assigned
-> hypothesis written
-> controlled test or fixture chosen
-> result recorded
-> heuristic changed
-> benchmark scenario added
-> future reviews checked for recurrence
```

Acceptable mistake note:

- "After Sleep Powder missed, I kept the Swords Dance script and ignored that
  Body Slam now put Victreebel into range. Add `sleep_disruption_001` and
  require re-scoring after miss/wake/switch."

Unacceptable mistake note:

- "Be more careful with sleep."

### Mistake Ledger Seed

These are the first recurring error patterns to regress against.

| ID | Error class | Mistake pattern | Current regression |
| --- | --- | --- | --- |
| `mistake_sleep_script_001` | script-following error | After a sleep miss, wake, switch, or Sleep Clause block, continuing the old setup line as if sleep succeeded. | `bench_sleep_setup_erika_001` |
| `mistake_spiker_cashout_001` | sacrifice error | Spending the only Spiker before hazards are established without naming the future route bought by the trade. | Hazard war drills; long-battle drill turns 1-2 |
| `mistake_rest_tempo_001` | tempo error | Resting while healthy or unprotected, then donating sleep turns to a breaker or setup threat. | 30+ turn battle reviews; Rest timing drills |
| `mistake_rest_full_hp_status_001` | mechanics/state error | Treating full-HP Rest as a status cure even though the local engine fails the move before clearing status. | Local Rest source check; filtered-policy state gate |
| `mistake_setup_axis_001` | setup tempo error | Choosing a defensive setup move because it boosts the right stat, while ignoring that the user is slower and already in KO range. | `bench_setup_tempo_will_001` |
| `mistake_hazard_greed_001` | hazard tempo error | Clicking Spikes because hazards are valuable while ignoring a faster revealed KO on the setter. | `bench_hazard_tempo_koga_001` |
| `mistake_sacrifice_no_future_001` | sacrifice error | Exploding or sacrificing because the current turn improves, without naming the next entry and the route opened. | `bench_cashout_brock_001` |
| `mistake_species_slogan_001` | role-map error | Saying "this Pokemon walls/checks/sets hazards" without checking HP, speed, revealed moves, hazards, and whether that role is still needed. | Turn ledger and role map checks |
| `mistake_state_invalid_001` | state-tracking error | Considering a move whose current-state precondition is false, such as awake Sleep Talk or repeated status into an already-statused target. | Long-battle drill 2; state-invalid move checks |
| `mistake_status_no_payoff_001` | conversion error | Landing sleep, poison, or hazards without a named follow-up that converts the created turn or passive damage into progress. | Long-battle drill 2; sleep/status drills |
| `mistake_boom_unforced_001` | sacrifice error | Exploding into a target that can Protect, switch, resist, or ignore it without having made that branch costly. | Long-battle drill 2 turn 10; Explosion drills |
| `mistake_trap_clock_001` | endgame clock error | Treating Mean Look plus Perish Song as a normal damage race instead of a forced countdown that changes every priority. | Long-battle drill 2 turns 11-16; endgame drills |
| `mistake_no_exit_endgame_001` | win-condition error | Reaching a final state where all remaining choices are failed moves, immunities, or exhausted PP because the earlier route map did not preserve an exit from trap/Perish/Ghost endgames. | Filtered-policy seed 759 turns 93-108; endgame forced-line drills |
| `mistake_sleep_wake_setup_001` | setup / state-tracking error | Treating a sleeping bench target as permanently disabled and setting up into a wake-turn punish. | `bench_external_belly_drum_wake_001` |
| `mistake_phaze_loop_progress_001` | long-game planning error | Reviewing a phazing loop as repeated noise instead of tracking which side gains HP, sleep turns, PP, hazard control, and final-entry access. | `bench_external_phaze_loop_golem_skarm_001` |
| `mistake_status_immune_001` | mechanics error | Clicking Toxic or another status into a target publicly immune to that status. | Long-battle drill 3 turns 1-2; mechanics oracle |
| `mistake_sleep_statused_001` | state-tracking error | Clicking a sleep move into a target that was already statused at turn start. | Filtered-policy state gate; sleep/status drills |
| `mistake_spin_no_hazard_001` | state-tracking error | Clicking Rapid Spin as if hazard control is needed when there are no hazards to remove and the chip does not matter. | Long-battle drill 3 turn 11; hazard-control drills |
| `mistake_single_route_endgame_001` | win-condition error | Spending the second-to-last route before checking whether the opponent's preserved final piece beats the only remaining route. | Long-battle drill 3 turns 49 and 78-81 |
| `mistake_hazard_control_survives_001` | conversion error | Spending the Spiker after setting hazards while the opponent's spinner survives and can remove them before the hazard pressure matters. | Filtered-policy drill 4 turns 1-5 |
| `mistake_resttalk_rest_branch_001` | mechanics / conversion error | Treating attacks into a sleeping RestTalk user as guaranteed progress without pricing the Sleep Talk -> Rest branch that can reset the damage race. | `bench_external_resttalk_zapdos_001` |
| `mistake_spin_temporary_control_001` | hazard-control error | Treating Rapid Spin as final hazard control while the opposing Spiker is still alive or can trade itself to re-layer. | `bench_external_spin_relayer_cloyster_001` |
| `mistake_sleeping_wincon_available_001` | win-condition error | Counting a sleeping preserved Pokemon as an active endgame route without tracking entry damage, sleep turns, setup pressure, and whether the wake turn arrives in time. | `bench_external_sleeping_lax_endgame_001` |

### Benchmark Suite Backlog

Build these sets before claiming mastery. Each benchmark must have a held-out
side so the notebook does not merely memorize its own examples.

| Suite | Purpose | First evidence source |
| --- | --- | --- |
| Mechanics oracle | Verify sleep, Rest, Sleep Talk, phazing, Explosion, Spikes, speed, and romhack deltas. | Local mechanics docs and source. |
| Curated one-turn positions | Check whether the decision checklist picks the right move class. | Preference fixtures. |
| Three-turn branch positions | Test sleep/setup, switch/preserve, Rest timing, and punish branches. | Fixture variants plus damage debugger. |
| 30+ turn battle reviews | Practice long-game ledgers, turning-point analysis, and endgame planning. | Showdown GSC logs or scratch sims. |
| Hazard war drills | Compare no Spikes, vanilla one-layer Spikes, and romhack three-layer Spikes. | Local Spikes docs and custom fixtures. |
| Sacrifice / Explosion drills | Require naming what future a trade buys and what answer it deletes. | GSC Explosion guide plus fixture variants. |
| Snorlax route drills | Preserve multiple answers and avoid assuming one check covers all sets. | GSC threatlist plus local trainer data. |
| Romhack delta drills | Re-test any vanilla conclusion touched by type passives, items, hazards, learnsets, or AI constraints. | `docs/agent_navigation` and runtime checks. |

Initial pass gate:

- no critical mechanics mistake in the scenario explanation;
- best move class within the accepted answer set;
- at least two alternatives considered;
- worst plausible punish named;
- current win route and opponent win route named;
- no unverified Showdown result used as romhack proof.

### State-Transition Benchmark Policy

The active goal direction is now tested state-transition policy, not broad
notebook prose. Heuristics should be promoted only when they can survive a
hard position that forces move choice, arbitration, hidden-info reasoning, and
catastrophe analysis.

Machine-readable benchmarks are split so the policy cannot see the answer key:

- public cards:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
- hidden oracles:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`
- legacy combined source artifact:
  `tools/boss_ai_preference/benchmarks/state_transition_benchmarks.json`
- policy answer schema:
  `tools/boss_ai_preference/schemas/policy_answer.schema.json`

`tools/boss_ai_preference/benchmark_positions.py` validates the public cards,
hidden oracles, and structured policy answers. The deterministic baseline
consumes only public cards. The evaluator joins hidden oracle labels by
benchmark id when scoring the answer file.
Structured policy answers must carry non-empty route, preservation,
catastrophe, answer-changing information, and fired-rule fields. They must not
carry hidden oracle labels such as `best`, `acceptable`, `catastrophic`, or
oracle rationale.
Run `python -m tools.boss_ai_preference benchmark-policy` to write the current
deterministic baseline policy answers to
`audit/boss_ai_preference/state_transition_policy_answers.json`, then run
`python -m tools.boss_ai_preference benchmark-report --answers
audit/boss_ai_preference/state_transition_policy_answers.json` to write the
current benchmark contract and policy-answer evaluation to
`audit/boss_ai_preference/state_transition_benchmarks.md` and
`audit/boss_ai_preference/state_transition_benchmarks.json`.
Run `python -m tools.boss_ai_preference benchmark-mutations` to generate the
current boundary-mutation audit at
`audit/boss_ai_preference/state_transition_mutations.md` and
`audit/boss_ai_preference/state_transition_mutations.json`. These mutations are
not policy inputs; they are evaluator checks that a minimal public-state delta
flips the deterministic answer for sleep clause, target status, max Spikes,
public Rapid Spin, Explosion blocking, and unavailable preservation pivots.
Run `python -m tools.boss_ai_preference type-evidence` to generate the
type-effectiveness firewall report at
`audit/boss_ai_preference/type_effectiveness_evidence.md` and
`audit/boss_ai_preference/type_effectiveness_evidence.json`. This report parses
`data/types/type_matchups.asm`, checks the 15 documented romhack chart edits,
and scans benchmark/oracle/policy explanations for words like
`super-effective`, `resisted`, `immune`, and `neutral`. A claim must be tied to
the environment-specific source paths before it is allowed.
Run `python -m tools.boss_ai_preference long-battle-review` to generate the
current structured 30+ turn review at
`audit/boss_ai_preference/long_battle_review.md` and
`audit/boss_ai_preference/long_battle_review.json`. This is a constructed
vanilla-GSC review with 32 ledgered turns, critical-turn labels, earliest-error
classification, and benchmark extraction targets.
Run `python -m tools.boss_ai_preference benchmark-harvest` to inspect which
existing preference fixtures can already be promoted into benchmark cards and
which still lack a best / acceptable / catastrophic label piece.
Run `python -m tools.boss_ai_preference benchmark-label-queue` to turn those
partial harvested fixtures into concrete review requests instead of guessing
the missing labels.

Required public-card fields:

- `split`: one of `seed`, `holdout`, or `fixture_harvest`; held-out cards are
  for answer-changing variants that should not merely restate the seed case,
  while harvested cards are promoted from saved fixture preference feedback.
- `mechanics_profile`: either `vanilla_gsc` or `romhack_gym_leader_lab`; do
  not mix vanilla conclusions with romhack mechanics.
- `position_snapshot`: visible battle state only.
- `candidate_moves_public`: legal/effective candidate move IDs without labels
  or reasons.
- `required_answer_fields`: structured fields the policy answer must emit.
- `public_opponent_model`: the four required tiers are `immediate_punish`,
  `role_aware_preservation`, `incentive_compatible_response`, and
  `hidden_info_belief_state`.
- `hidden_info_visible_to_policy`: explicit public uncertainty, not oracle
  truth.

Required hidden-oracle fields:

- `best`, `acceptable`, and `catastrophic`: hidden move labels used only by the
  evaluator.
- `why_best`, `why_acceptable`, and `why_catastrophic`: expert rationale keyed
  by move ID.
- `catastrophe_branches`: exact trigger and consequence for losing lines.
- `answer_changing_information`: facts that would flip or change the answer.
- `heuristic_arbitration`: competing heuristics, dominant policy, and
  exceptions.
- `current_win_conditions` and `irreplaceable_pieces`: oracle route and
  preservation targets used for review.

Type-effectiveness firewall:

- Keep chart result, passive-adjusted result, final damage, and strategic move
  label as separate claims.
- Use `data/types/type_matchups.asm` for chart facts; this romhack already has
  15 known chart edits, including Dark -> Steel neutral and Ghost -> Steel no
  effect.
- Use `engine/battle/type_passive_damage_mods.asm` for Dragon's Majesty,
  Imperial Scales, Dark status shield, and other passive adjustments.
- Use validated debugger traces for exact battle-state damage, not as a blanket
  override of source. Source/debugger disagreement means source-version or
  tooling mismatch and must be investigated.
- Do not copy vanilla Steel/Ghost/Dark examples into romhack benchmarks unless
  the chart source is referenced and the romhack result is stated.

Initial hard snapshots:

| Benchmark | Split | Profile | Arbitration lesson |
| --- | --- | --- | --- |
| `vanilla_gsc_sleep_setup_disruption_001` | seed | vanilla GSC | After sleep misses, re-score before deciding whether sleep, chip, or setup dominates. |
| `romhack_spikes_third_layer_janine_001` | seed | romhack | Finish the third Spikes layer only when the current state makes the layer live and hard to remove. |
| `romhack_spikes_fourth_click_janine_001` | seed | romhack | A maxed Spikes state makes another Spikes click a failed move, regardless of the generic hazard heuristic. |
| `romhack_explosion_route_trade_brock_001` | seed | romhack | Explosion is correct only when the sacrifice buys a named next position and does not delete an irreplaceable answer. |
| `romhack_defensive_answer_preservation_pryce_001` | seed | romhack | Preserve the bulky pivot by moving through the resistant answer; do not trust type-slogan shortcuts. |
| `vanilla_gsc_sleep_clause_blocked_holdout_001` | holdout | vanilla GSC | Sleep/setup must collapse into a live move when Sleep Clause blocks the control route. |
| `romhack_spikes_public_spinner_holdout_001` | holdout | romhack | Public hazard control can dominate finishing the third layer. |
| `romhack_spikes_maxed_explosion_conversion_holdout_001` | holdout | romhack | At max layers, Explosion can dominate live chip if it removes the hazard absorber. |
| `romhack_explosion_blocked_by_protect_holdout_001` | holdout | romhack | Revealed Protect can override the Explosion-converts heuristic. |
| `romhack_defensive_answer_unavailable_holdout_001` | holdout | romhack | If the defensive pivot is gone, choose a live mitigation move instead of an impossible preservation line. |
| `long_battle_sleep_disruption_after_miss_001` | holdout | vanilla GSC | A missed sleep move forces re-scoring; raw setup is catastrophic while sleep remains live only if clause and target status still allow it. |
| `long_battle_rest_tempo_unforced_001` | holdout | vanilla GSC | Rest at high HP can be tempo loss when it is not yet forced by role survival. |
| `fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001` | fixture_harvest | romhack | A live preservation switch can dominate visible coverage when the active closer is still needed. |
| `fixture_janine_qwilfish_third_spikes_layer_001` | fixture_harvest | romhack | Fixture feedback confirms third-layer Spikes dominates chip while public spin and immediate KO routes are absent. |
| `fixture_mechanics_snorlax_full_hp_rest_status_fail_001` | fixture_harvest | romhack | Mechanics legality dominates role slogans: full-HP Rest and awake Sleep Talk are failed state transitions. |
| `fixture_brock_golem_vs_vaporeon_explosion_question_001` | fixture_harvest | romhack | Explosion can narrowly dominate a preservation switch when a low-future-value piece buys a clean next position. |
| `external_gsc_forretress_explosion_on_quagsire_001` | holdout | vanilla GSC | Replay 861526 converts a spent low-HP Forretress into a Quagsire-removal Explosion, then tests the blocked-Explosion boundary with a Protect mutation. |
| `external_gsc_vaporeon_vs_restdtalk_snorlax_001` | holdout | vanilla GSC | Replay 861526 tests the GSC RestTalk branch: sleeping Snorlax can still call Rest, so immediate Surf pressure dominates greedy Growth unless RestTalk is absent. |
| `external_gsc_golem_late_rapid_spin_001` | holdout | vanilla GSC | Replay 861526 tests late-game hazard removal: Rapid Spin preserves future switch/phaze routes while Snorlax is likely to Rest; no-hazards mutation flips to Earthquake. |
| `fixture_will_slowbro_vs_houndoom_fast_dark_001` | fixture_harvest | romhack | Existing Will feedback tests fast public Dark pressure: preserve Slowbro through the healthy Houndoom pivot; if the pivot is unavailable, the mutation flips to Surf as the best forced stay-in attack. |
| `fixture_koga_ariados_vs_typhlosion_fire_spikes_001` | fixture_harvest | romhack | Koga Ariados into revealed Typhlosion Flamethrower tests Spikes/status arbitration: preserve the hazard lead through Tentacruel; if Tentacruel is unavailable, the mutation flips to Umbreon. |
| `fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001` | fixture_harvest | romhack | Bugsy Scyther into Geodude tests the positive setup case: Swords Dance is correct while the worst plausible punish is survivable; if the punish becomes a KO, the mutation flips to Wing Attack. |
| `fixture_bugsy_scyther_vs_quilava_fire_setup_001` | fixture_harvest | romhack | Bugsy Scyther into Quilava tests setup under live Fire pressure: Swords Dance is correct while Scyther acts first and survives Ember; if Ember removes the setup route, the mutation flips to Wing Attack. |
| `fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001` | fixture_harvest | romhack | Chuck Poliwrath into faster Alakazam tests sleep-vs-preservation arbitration: verified Psychic immunity makes Umbreon best; if Umbreon is unavailable, the mutation flips to Hypnosis. |
| `fixture_morty_haunter_vs_noctowl_sleep_line_001` | fixture_harvest | romhack | Morty Haunter into Noctowl tests the positive sleep-control case: Hypnosis is best while Sleep Clause is free and the target is unstatused; if Sleep Clause is occupied, the mutation flips to Night Shade. |
| `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001` | fixture_harvest | romhack | Falkner Pidgeotto into Geodude tests one-probe policy: Sand Attack is best while Rock Throw is a live punish and Gust is tiny chip; if the punish branch is removed, the mutation flips to Gust. |
| `fixture_pryce_cloyster_vs_quilava_fire_pivot_001` | fixture_harvest | romhack | Pryce Cloyster into faster Quilava tests bad-matchup switching: preserve the low-HP Spikes/Explosion resource through Slowking while Flame Wheel KOs before progress; if Cloyster survives, the mutation flips to Surf. |
| `fixture_whitney_miltank_vs_geodude_rollout_lock_001` | fixture_harvest | romhack | Whitney Miltank into Geodude tests lock-move sequencing: Body Slam pressure comes before Rollout; if Geodude is paralyzed and the board is safe, the mutation flips to Rollout. |
| `fixture_karen_crobat_vs_dragonite_toxic_clock_001` | fixture_harvest | romhack | Karen Crobat into Dragonite tests Toxic-clock timing: start the clock while Crobat survives the public Outrage punish; if survival disappears, the mutation flips to Tyranitar. |
| `fixture_koga_crobat_vs_alakazam_immediate_ko_001` | fixture_harvest | romhack | Koga Crobat into Alakazam tests immediate-KO arbitration: Wing Attack beats Toxic while it removes Alakazam now; if the KO threshold disappears, the mutation flips to Umbreon. |
| `fixture_jasmine_skarmory_vs_machoke_focus_energy_001` | fixture_harvest | romhack | Jasmine Skarmory into Machoke tests phazing arbitration: Toxic beats reflexive Whirlwind while Focus Energy is low urgency; if a real attack-boost route appears, the mutation flips to Whirlwind. |
| `fixture_morty_misdreavus_vs_typhlosion_perish_route_001` | fixture_harvest | romhack | Morty Misdreavus into boosted Typhlosion tests forced-clock routing: Perish Song wins while Misdreavus survives Flame Wheel; if survival disappears, the mutation flips to Gengar. |
| `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001` | fixture_harvest | romhack | Whitney Clefairy into Bayleef tests Encore timing: Encore wins when Reflect was the visible last move and Clefairy is faster; if the trap is absent, the mutation flips to Double Team. |
| `fixture_jasmine_magneton_vs_quilava_speed_control_001` | fixture_harvest | romhack | Jasmine Magneton into Quilava tests speed-control status: Thunder Wave wins while Thunderbolt cannot remove the faster threat; if the damage threshold reaches direct removal, the mutation flips to Thunderbolt. |
| `fixture_misty_starmie_vs_meganium_recover_tempo_001` | fixture_harvest | romhack | Misty Starmie into Meganium tests recovery timing: Psychic wins while Recover lacks a real window and chip enables Lapras cleanup; if Meganium cannot punish and the chip threshold is gone, the mutation flips to Recover. |
| `fixture_clair_dragonair_vs_suicune_hidden_ice_001` | fixture_harvest | romhack | Clair Dragonair into Suicune tests hidden-info preservation: Kingdra wins while hidden Ice coverage is plausible; if that punish is no longer plausible, the mutation flips to Thunder. |
| `fixture_bugsy_ariados_vs_pidgey_status_clock_001` | fixture_harvest | romhack | Bugsy Ariados into Pidgey tests status-clock sequencing: Toxic wins while the target is unstatused and Ariados survives; if the clock already exists, the mutation flips to Scyther. |
| `fixture_morty_gengar_vs_kadabra_destiny_bond_001` | fixture_harvest | romhack | Morty Gengar into Kadabra tests sacrifice-trade arbitration: Shadow Ball wins while it directly removes the active threat; if that damage boundary disappears, the mutation flips to Destiny Bond. |

Key lesson: `set Spikes`, `preserve answers`, `use sleep`, and `Explosion
converts` can all be true. The policy has to decide which one dominates on the
exact turn, under the correct mechanics profile and opponent model.

Current fixture coverage audit:

- Latest generated reports:
  - `audit/boss_ai_preference/latest_report.md`
  - `audit/boss_ai_preference/lesson_report.md`
  - `audit/boss_ai_preference/active_queue.md`
  - `audit/boss_ai_preference/plan_queue.md`
  - `audit/boss_ai_preference/expert_play_research.md`
  - `audit/boss_ai_preference/feature_report.md`
- Current coverage is not close to mastery:
  - 57 total fixtures;
  - 0 direct action labels;
  - 52 pairwise preferences;
  - 27 / 57 fixtures with pairwise feedback;
  - 69 trajectory preferences and 3 plan demonstrations;
  - 43 machine-readable state-transition benchmarks: 5 seed, 15 holdout, and
    23 fixture-harvest cards promoted from saved feedback, fixture evidence, or
    targeted state-transition gaps.
  - 36 boundary mutation checks that force answer flips across sleep/setup,
    maxed Spikes, public spin pressure, Explosion blocking, opening
    double-switch pressure, RestTalk branch removal, late-game hazard removal,
    phazing order, PP conservation, damage survival, defensive preservation
    availability, fast public-punish pivot availability, and speed-control
    versus direct-removal thresholds, recovery-window timing, and hidden-info
    coverage plausibility, already-established status clocks, and sacrifice
    trades when direct removal stops converting.
  - 15 romhack type-chart deltas enforced by the type-effectiveness evidence
    report; current benchmark/oracle/policy text has 22 effectiveness claims
    and 0 unsupported claims.
  - 19 source-backed expert-play principles in
    `audit/boss_ai_preference/expert_play_research.md`, including the current
    type-slogan guard: effectiveness language must be tied to exact mechanics
    and a route-changing damage threshold, plus the Spikes guard that hazards
    are not a free passive turn under revealed lethal pressure, plus the setup
    guard that setup requires both a survivable punish branch and a route gain,
    plus the bad-matchup switching guard that a pivot can preserve future route
    resources when the active faints before progress.
  - 132 extracted feature names in
    `audit/boss_ai_preference/feature_report.md`; plan features now distinguish
    stay-in, setup, switch-preserve, and route-trade plans under public
    major/lethal active threats, with separate fast-threat markers.
  - 1 structured 32-turn constructed long-battle review with 4 critical turns,
    earliest irreversible error at turn 9, and 3 benchmark extraction targets.
  - 4 complete fixture-derived benchmark candidates and 23 partial candidates
    in `audit/boss_ai_preference/fixture_benchmark_harvest.md`; the complete
    candidates are now mirrored in the executable benchmark suite; the Will
    Slowbro/Houndoom fast-threat preservation case, the Koga Ariados/Typhlosion
    lethal Fire-pressure case, the Bugsy Scyther/Geodude safe-setup case, the
    Chuck Poliwrath/Alakazam Psychic-pivot case, and the Morty
    Haunter/Noctowl sleep-control case, and the Falkner Pidgeotto/Geodude
    scout-probe case are added as targeted coverage cards with answer-flip
    mutations.
  - 23 benchmark label-review requests in
    `audit/boss_ai_preference/benchmark_label_queue.md`; 11 can become complete
    benchmark candidates with one non-conflicting acceptable-label review.
- Current reports identify active gaps where the scorer is uncertain or
  lacks enough trajectory coverage. High-priority remaining gaps include
  `falkner_pidgeotto_vs_geodude_rock_risk`,
  `pryce_cloyster_vs_quilava_explosion_line`,
  `koga_crobat_vs_alakazam_toxic_or_attack`.
  The trajectory model still has only one strict holdout row, even though the
  latest fit now predicts that row correctly. More non-holdout fast-threat and
  hazard-vs-preservation coverage is still needed before trusting that model
  family.

Coverage rule: do not claim the notebook can answer the lab broadly while
direct labels are empty and most fixtures lack feedback. A benchmark card is
study evidence, not a replacement for a saved preference or trajectory row.

### Initial Benchmark Scenarios

Use these as the first regression checks. They are not a full mastery suite;
they are the seed positions that turn the current notebook into something that
can fail.

#### `bench_sleep_setup_erika_001`

- Fixture: `erika_victreebel_vs_snorlax_sleep_or_boost`
- Skill: sleep/setup branch control.
- Expected move class: Deny into Convert.
- Accepted line: Sleep Powder first, then one Swords Dance if sleep lands and
  the board remains safe, then Sludge Bomb.
- Required explanation:
  - raw Sludge Bomb is not a KO at current HP;
  - raw setup risks taking heavy Body Slam chip first;
  - sleep is useful because it creates the setup turn that changes KO math;
  - after a miss, wake, switch, or Sleep Clause block, re-score instead of
    continuing the script.
- Evidence:
  - damage debugger: unboosted Sludge Bomb into 84% Snorlax is 168-198 damage,
    51-60% max HP, not a guaranteed KO;
  - damage debugger: Snorlax Body Slam into 77% Victreebel is 116-137 damage,
    57-67% max HP;
  - damage debugger: +2 Sludge Bomb into Snorlax is 342-402 damage, 103-121%
    max HP, guaranteed from full;
  - scratch simulation: sleep plus one boost outperformed raw attack, raw
    setup, and sleep plus two boosts in the controlled Victreebel/Snorlax
    policy test.
- Failure signs:
  - choosing Swords Dance first without accounting for Body Slam;
  - choosing two boosts because sleep landed once;
  - continuing setup after a miss.

#### `bench_sleep_setup_lance_yanma_001`

- Fixture: `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Skill: sleep/setup branch control under lethal coverage.
- Expected move class: Deny into Convert.
- Accepted line: Sleep Powder first. If it lands and the board remains safe,
  use the created turn for Quiver Dance or immediate Giga Drain depending on
  wake/switch risk; if it misses or Sleep Clause blocks it, re-score before
  any setup.
- Required explanation:
  - raw Giga Drain is not meaningful damage into full Lapras;
  - raw Quiver Dance loses to the public Ice Beam branch;
  - Kingdra is the safer preservation pivot into Ice, but switching gives up
    Yanma's immediate disruption route;
  - Focus Band is not a plan, only a low-probability emergency branch.
- Evidence:
  - fixture: Yanma level 46 at full HP, Focus Band, with revealed Giga Drain
    into Lapras level 47 at full HP with revealed Surf and public Ice Beam;
  - damage debugger: Yanma Giga Drain into Lapras is 32-38 damage, 15-18% max
    HP;
  - damage debugger: Lapras Ice Beam into Yanma is 148-174 damage, guaranteed
    KO from full;
  - damage debugger: Lapras Surf into Yanma is 23-28 damage, 18-22% max HP;
  - damage debugger: Lapras Ice Beam into Kingdra is 39-46 damage, 26-31% max
    HP.
- Failure signs:
  - choosing Quiver Dance first because Yanma is a setup-style disruption mon;
  - choosing Giga Drain because it is super-effective without checking the
    tiny damage;
  - relying on Focus Band as if it were a stable defensive resource.

#### `bench_status_bugsy_ariados_001`

- Fixture: `bugsy_ariados_vs_pidgey_toxic_or_attack`
- Skill: status tempo, weak-chip recognition, and ace preservation.
- Expected move class: Deny or Convert.
- Accepted line: Toxic is the best listed opener if the boss is allowed to
  spend one turn creating a clock. Direct attacks are low-impact, and switching
  to Scyther exposes the ace before the board requires it.
- Required explanation:
  - Pidgey's public Flying pressure is real but not immediately lethal;
  - Ariados's direct damage into Pidgey is too small to win a damage race
    quickly;
  - Toxic changes future turns by forcing Pidgey to act under a clock or pivot;
  - Scyther should not be thrown in just because it is the ace.
- Evidence:
  - fixture: Ariados level 15 at full HP, Berry, into level 17 Pidgey with
    revealed Quick Attack and plausible Gust;
  - damage debugger: Pidgey Gust into Ariados is 16-19 damage, 27-32% max HP;
  - damage debugger: Pidgey Quick Attack into Ariados is 7-9 damage, 12-15%
    max HP;
  - damage debugger: Ariados Leech Life into Pidgey is 10-12 damage, 18-21%
    max HP;
  - damage debugger: Ariados Giga Drain into Pidgey is 10-12 damage, 18-21%
    max HP.
- Failure signs:
  - switching to Scyther only because Pidgey is Flying-type;
  - choosing weak chip and calling it tempo when it does not change the next
    turn;
  - using Toxic without naming what the poison clock buys.
- Benchmark artifact: `fixture_bugsy_ariados_vs_pidgey_status_clock_001`;
  mutation `mut_bugsy_status_clock_already_started_001` flips to Scyther when
  Pidgey is already toxic, because the status job is complete and the follow-up
  route must be re-scored.

#### `bench_switch_preserve_pryce_001`

- Fixture: `pryce_slowking_vs_ampharos_ground_pivot`
- Skill: switching, preservation, and public type pressure.
- Expected move class: Preserve or Deny.
- Accepted line: switch Slowking to Piloswine, then re-score from the new
  board.
- Required explanation:
  - Slowking is not supposed to sit in front of the known Electric pressure;
  - Thunder Wave is slower than solving the immediate survival problem;
  - Rest donates tempo and does not answer the public threat;
  - Piloswine is not just a "Ground type" slogan; it materially changes the
    damage race.
- Evidence:
  - damage debugger: Ampharos ThunderPunch into 68% Slowking is 75-89 damage,
    68-81% max HP and a guaranteed KO at current HP;
  - damage debugger: Ampharos ThunderPunch into Piloswine is 22-26 damage,
    16-19% max HP;
  - damage debugger: Piloswine Earthquake into 80% Ampharos is 76-90 damage,
    52-62% max HP;
  - damage debugger: Slowking Surf into 80% Ampharos is only 11-14 damage,
    8-10% max HP.
- Failure signs:
  - clicking Thunder Wave because status is generally useful;
  - resting at high risk;
  - calling the switch good without checking that Piloswine actually absorbs
    the public hit.

#### `bench_cashout_brock_001`

- Fixture: `brock_golem_vs_vaporeon_explosion_question`
- Skill: sacrifice and Explosion valuation.
- Expected move class: Cash out.
- Accepted line: Explosion is acceptable when the explanation names why Golem
  is being spent and what the next entry gains. The answer is not "Explosion is
  dramatic"; it is "Surf already removes Golem, while Explosion converts the
  doomed active into removal of the current Water threat."
- Required explanation:
  - Vaporeon Surf guarantees the KO on Golem even from full;
  - Earthquake is not enough to stop Vaporeon;
  - Curse is too slow under public Water pressure;
  - switching to Omastar is a candidate, but preserving Golem must be worth
    more than losing the chance to remove Vaporeon immediately.
- Evidence:
  - damage debugger: Vaporeon Surf into 42% Golem is 339-399 damage, 170-201%
    max HP, guaranteed KO even from full;
  - damage debugger: Golem Earthquake into 76% Vaporeon is 79-94 damage,
    29-34% max HP and not a KO;
  - damage debugger: Golem Explosion into 76% Vaporeon is 262-308 damage,
    95-112% max HP and guaranteed KO at current HP.
- Failure signs:
  - preserving Golem without naming its future job;
  - exploding without naming the follow-up route;
  - using Curse into a known immediate KO.

#### `bench_snorlax_tempo_red_001`

- Fixture: `red_snorlax_vs_alakazam_curse_or_body_slam`
- Skill: tempo before setup, Snorlax route discipline.
- Status: provisional. Keep this as a study benchmark, not a stable rule,
  until the rough threat report and direct damage debugger ranges are
  reconciled.
- Expected move class: Convert or Scout.
- Working accepted line: Body Slam before Curse, Rest, or awake Sleep Talk.
- Required explanation:
  - Curse may be strong later, but before paralysis or clearer pressure it can
    donate a Recover/Psychic turn;
  - Body Slam keeps tempo and can create paralysis, which may make later Curse
    or direct pressure more real;
  - Rest is too early at 84% HP;
  - Sleep Talk is a public fail while awake.
- Current evidence:
  - damage debugger: Snorlax Body Slam into 62% Alakazam is 43-51 damage,
    17-21% max HP and not a KO;
  - damage debugger: Alakazam Psychic into 84% Snorlax is 133-157 damage,
    39-47% max HP;
  - threat availability report has a rougher Psychic estimate around 34-39%,
    so do not promote the exact range until the mismatch is checked.
- Failure signs:
  - clicking Curse because Snorlax is a setup Pokemon;
  - using Rest or Sleep Talk without checking current state;
  - ignoring Alakazam's Recover and Psychic pressure.

#### `bench_setup_tempo_will_001`

- Fixture: `will_slowbro_vs_houndoom_amnesia_or_surf`
- Skill: setup tempo trap, speed-order awareness, and preservation.
- Expected move class: Preserve.
- Accepted line: switch Slowbro to Houndoom, then re-score.
- Required explanation:
  - Amnesia boosts the correct defensive side against Crunch, but Slowbro is
    already slower and cannot spend that turn if Crunch is selected;
  - Surf is the correct attacking lane into Houndoom only in branches where
    Slowbro actually moves;
  - Psychic is a public fail into Dark typing;
  - the mirror Houndoom pivot gives up immediate Surf pressure but is the only
    listed line that covers the revealed lethal Crunch branch.
- Evidence:
  - source fixture: Slowbro is level 41 at 78% HP with Leftovers; player
    Houndoom is level 44 at 100% HP with revealed Crunch;
  - local stat evidence: Houndoom's base Speed is 115 and Slowbro's is 30, so
    Houndoom should move first absent priority or speed modifiers;
  - damage debugger: Houndoom Crunch into 78% Slowbro is 170-200 damage,
    113-132% max HP, guaranteed KO even from full;
  - damage debugger: Slowbro Surf into Houndoom is 78-92 damage, 45-53% max HP,
    but this does not matter in the stay-in Crunch branch because Slowbro
    faints first;
  - damage debugger: Slowbro Psychic into Houndoom is 0 damage;
  - damage debugger: Houndoom Crunch into the boss Houndoom pivot is 43-51
    damage, 31-37% max HP.
- Failure signs:
  - choosing Amnesia because it boosts Special Defense without checking speed
    and current KO range;
  - choosing Surf as "clean direct damage" without naming the lethal faster
    Crunch branch;
  - switching only because of type matchup language, without checking that the
    pivot actually survives the public hit.

#### `bench_hazard_tempo_koga_001`

- Fixture: `koga_ariados_vs_typhlosion_spikes_or_toxic`
- Skill: hazard greed, preservation, and switch-punish awareness.
- Expected move class: Preserve or Scout.
- Accepted line: switch Ariados to Tentacruel over Spikes, Toxic, or Leech
  Life, then re-score immediately because Earthquake is a plausible punish.
- Required explanation:
  - three-layer Spikes are strategically powerful in this romhack, but the
    setter still needs a playable turn;
  - Ariados is slower than Typhlosion and cannot assume it gets to place
    Spikes or Toxic under revealed Flamethrower pressure;
  - Leech Life is resisted low-impact damage and does not solve the threat;
  - Tentacruel covers the revealed Flamethrower branch, but the line is not
    free because public notes say Earthquake is plausible.
- Evidence:
  - source fixture: Ariados level 40 at full HP, hazard lead; player Typhlosion
    level 45 at full HP with revealed Flamethrower and plausible Earthquake;
  - local stat evidence: Typhlosion's base Speed is 100 and Ariados's is 40,
    so Typhlosion should move first absent priority or speed modifiers;
  - damage debugger: Typhlosion Flamethrower into Ariados is 260-306 damage,
    181-213% max HP, guaranteed KO;
  - damage debugger: Ariados Leech Life into Typhlosion is 14-17 damage,
    9-11% max HP;
  - damage debugger: Typhlosion Flamethrower into Tentacruel is 34-40 damage,
    28-33% max HP;
  - damage debugger: Typhlosion Earthquake into Tentacruel is 141-166 damage,
    118-138% max HP, guaranteed KO.
- Failure signs:
  - clicking Spikes because hazards are generally important while ignoring the
    faster lethal revealed move;
  - switching to Tentacruel without naming Earthquake as the worst plausible
    punish;
  - treating Toxic or Leech Life as progress when the active matchup may end
    before Ariados moves.

#### `bench_romhack_spikes_third_layer_janine_001`

- Fixture: `janine_qwilfish_finish_third_spikes_layer`
- Skill: romhack hazard-layer valuation.
- Expected move class: Finish the hazard stack.
- Accepted line: use Spikes over ordinary Sludge Bomb, Surf, or switching when
  two player-side layers are already down, the seen player team is grounded, no
  Rapid Spin user has been revealed, and no immediate KO threat is public.
- Required explanation:
  - this is not vanilla GSC one-layer Spikes;
  - the third local layer changes grounded switch-ins from max HP / 6 to max
    HP / 4;
  - the value comes from future switches, Rest cycles, phazing, and forced
    re-entries, not from the Spikes turn dealing damage immediately;
  - Explosion remains a route-trade question, not a strict "always worse"
    alternative.
- Evidence:
  - source fixture: Janine Qwilfish level 60 with Spikes, Sludge Bomb, Surf,
    and Explosion;
  - local mechanics docs and source: three layers are supported, with damage at
    /8, /6, and /4;
  - strict labels prefer Spikes over Sludge Bomb, Surf, and switching, while
    the Explosion comparison is intentionally non-strict.
- Failure signs:
  - saying "Spikes are good" without naming current layer count;
  - treating the third layer like vanilla GSC chip;
  - cashing ordinary attack damage without explaining why the completed hazard
    stack is no longer needed.

#### `bench_romhack_spikes_maxed_janine_001`

- Fixture: `janine_qwilfish_spikes_already_maxed`
- Skill: hazard-state legality and redundancy.
- Expected move class: Use a live move; do not click Spikes.
- Accepted line: Sludge Bomb, Surf, Explosion, or a justified switch can all be
  live candidates, but Spikes itself is a failed fourth-layer attempt.
- Required explanation:
  - both local Spikes bits are already set for the player side;
  - the move-effect source fails placement at three layers;
  - once the stack is complete, Qwilfish should convert the hazard position
    through damage, preservation, or a later Explosion route.
- Evidence:
  - strict labels prefer Sludge Bomb and Surf over Spikes;
  - scorer feature `spikes_already_maxed` is present for the failed move.
- Failure signs:
  - treating Spikes as useful because hazards are generally valuable;
  - failing to check the current stack before choosing a hazard move.

#### `bench_two_turn_red_charizard_001`

- Fixture: `red_charizard_vs_starmie_sunny_day_or_switch`
- Skill: two-turn plan discipline and candidate-set skepticism.
- Status: unresolved. Do not promote the fixture baseline as correct until the
  candidate set is expanded or the opponent model explicitly says Starmie is
  unlikely to click revealed Surf.
- Expected move class: Preserve, but only if the switch actually survives the
  revealed punish.
- Working verdict: all listed stay-in moves fail against revealed Surf, and
  the listed Pikachu switch also fails if Starmie clicks Surf. The right review
  answer is "the shown candidates are incomplete or require a prediction
  assumption", not "Sunny Day is clever".
- Required explanation:
  - Starmie outspeeds Charizard;
  - Sunny Day plus SolarBeam is a two-turn package from neutral weather and
    does not solve the immediate Surf branch;
  - SolarBeam without sun charges and is therefore even slower;
  - Flamethrower and Wing Attack do not threaten enough damage;
  - Pikachu threatens Starmie if it gets in safely, but it does not absorb Surf
    at 64% HP.
- Evidence:
  - source fixture: Charizard level 77 at 92% HP, Charcoal, neutral weather;
    Starmie level 80 at 100% HP with revealed Surf;
  - local stat evidence: Starmie and Charizard both have 115 base Speed in this
    hack, but the fixture states Starmie outspeeds;
  - damage debugger: Starmie Surf into 92% Charizard is 262-308 damage,
    108-127% max HP, guaranteed KO even from full;
  - damage debugger: Charizard Flamethrower into Starmie is 39-46 damage,
    14-17% max HP;
  - damage debugger: Charizard Wing Attack into Starmie is 57-67 damage,
    21-24% max HP;
  - damage debugger: Starmie Surf into 64% level 81 Pikachu is 274-322 damage,
    136-160% max HP, guaranteed KO even from full;
  - damage debugger: Light Ball Pikachu Thunderbolt into Starmie is 145-171
    damage, 52-62% max HP, not a guaranteed KO from full.
- Failure signs:
  - recommending Sunny Day because it enables SolarBeam without checking the
    first turn;
  - recommending switch Pikachu as if threat alignment equals safe entry;
  - treating the listed action set as complete when every shown line loses to
    the public punish.

#### `bench_choice_lock_sabrina_001`

- Fixture: `sabrina_alakazam_choice_lock_vs_houndoom`
- Skill: choice-lock discipline, Dark immunity, and coverage triage.
- Expected move class: Coverage or Preserve.
- Working accepted line: do not lock Choice Specs Alakazam into Psychic
  against public Houndoom. ThunderPunch is the best listed direct coverage
  checked so far, but switching to Hypno remains a candidate if preserving the
  ace matters more than chip.
- Required explanation:
  - Psychic is a public fail into Dark typing, even with Choice Specs;
  - Houndoom's revealed Crunch threatens a guaranteed KO on the current
    Alakazam HP, so the boss is not free to throw a low-impact move;
  - coverage should be judged by concrete damage, not by "neutral is fine".
- Evidence:
  - fixture: Alakazam level 67 at 89% HP, Choice Specs, into Houndoom level 66
    at 72% HP with revealed Crunch and Flamethrower;
  - damage debugger: Choice Specs Psychic into Houndoom is 0 damage;
  - damage debugger: Choice Specs ThunderPunch into 72% Houndoom is 74-87
    damage, 40-47% current HP;
  - damage debugger: Choice Specs Ice Punch into 72% Houndoom is 36-43 damage,
    19-23% current HP;
  - damage debugger: Houndoom Crunch into 89% Alakazam is 158-186 damage,
    guaranteed KO at current HP.
- Failure signs:
  - choosing Psychic because it is Alakazam's identity move;
  - treating "coverage" as solved without comparing ThunderPunch and Ice Punch;
  - ignoring Choice lock when choosing a low-payoff neutral move.

#### `bench_priority_red_pikachu_001`

- Fixture: `red_pikachu_vs_dragonite_thunderbolt_or_extremespeed`
- Skill: priority discipline, Dragon passive transfer, and speed-value checks.
- Expected move class: Convert.
- Working accepted line: Thunderbolt is still the best listed first hit because
  Pikachu already outspeeds and ExtremeSpeed's priority does not add value.
- Required explanation:
  - priority is useful only when it changes move order or secures a range;
  - Light Ball special pressure is better than ExtremeSpeed here, but neither
    move comes close to a KO;
  - Dragonite's Outrage is lethal if Dragonite gets its attack turn, so the
    move must be understood as best available damage, not a complete answer.
- Evidence:
  - fixture: Red Pikachu level 81, Light Ball, full HP, into player Dragonite
    level 80, full HP, revealed Outrage;
  - fixture note: Pikachu outspeeds Dragonite;
  - damage debugger: Light Ball Thunderbolt into Dragonite is 44-52 damage,
    13-15% max HP;
  - damage debugger: Light Ball ExtremeSpeed into Dragonite is 25-30 damage,
    7-9% max HP;
  - damage debugger: Light Ball Surf into Dragonite is 14-17 damage, 4-5% max
    HP;
  - damage debugger: Dragonite Outrage into Pikachu is 381-448 damage,
    guaranteed KO from full.
- Failure signs:
  - clicking ExtremeSpeed because priority sounds safer when the boss already
    moves first;
  - claiming Thunderbolt "solves" Dragonite instead of saying it is merely the
    best listed damage;
  - ignoring Dragon-specific damage behavior and local damage ranges.

#### `bench_mirror_coat_red_blastoise_001`

- Fixture: `red_blastoise_vs_zapdos_mirror_coat_or_blizzard`
- Skill: reactive-counter survival checks and branch labeling.
- Status: provisional. Mirror Coat is a real high-upside line only on the
  branches where Blastoise survives the revealed Electric attack.
- Expected move class: Counterplay or Preserve, depending on risk tolerance and
  whether the battle state requires a swing.
- Working accepted line: Mirror Coat must be explained as a survival-roll trap,
  not as a guaranteed answer. If the line cannot tolerate being KOed by
  Thunderbolt, switch Snorlax or another special sponge must be considered.
- Required explanation:
  - Mirror Coat does nothing if Blastoise faints first;
  - Zapdos Thunderbolt is a possible KO at current HP, so this is not a safe
    baseline;
  - Blizzard hits Zapdos but is not enough damage to solve the matchup by
    itself.
- Evidence:
  - fixture: Blastoise level 77 at 88% HP, Mystic Water, into Zapdos level 78
    with revealed Thunderbolt;
  - damage debugger: Zapdos Thunderbolt into 88% Blastoise is 210-247 damage,
    98-115% current HP, possible KO;
  - damage debugger: Blastoise Blizzard into Zapdos is 112-132 damage, 37-44%
    max HP;
  - reactive implication: surviving Thunderbolt would let Mirror Coat return
    more than Zapdos's full HP, but the survival branch is not guaranteed.
- Failure signs:
  - recommending Mirror Coat without first checking survival;
  - recommending Surf or Earthquake as if they address Zapdos;
  - treating a possible-KO branch as safe because the counterplay is stylish.

#### `bench_prediction_karen_houndoom_001`

- Fixture: `karen_houndoom_vs_alakazam_pursuit_or_flamethrower`
- Skill: prediction discipline and stay/switch branch comparison.
- Expected move class: Predict or Convert.
- Working accepted line: Pursuit is fair only if the explanation names why
  Alakazam is likely to switch or why the switch branch is worth the weaker
  stay-in damage. If judging without that read, Crunch is the stronger direct
  pressure into a staying Alakazam.
- Required explanation:
  - Houndoom threatens Alakazam heavily, so a switch is plausible public
    information;
  - Pursuit has a high-payoff switch branch but is weak if Alakazam stays;
  - Crunch is better direct damage into the stay branch than Flamethrower or
    non-doubled Pursuit.
- Evidence:
  - fixture: Karen Houndoom level 47, Black Glasses, into player Alakazam
    level 47 at full HP with revealed Psychic;
  - damage debugger: Houndoom Pursuit into staying Alakazam is 42-50 damage,
    28-34% max HP;
  - damage debugger: Houndoom Flamethrower into Alakazam is 41-49 damage,
    28-33% max HP;
  - damage debugger: Houndoom Crunch into Alakazam is 91-108 damage, 61-72%
    max HP;
  - fixture note: Pursuit doubles damage on a switching target.
- Failure signs:
  - choosing Pursuit because it sounds advanced without naming the switch
    evidence;
  - choosing Flamethrower as "safe" while ignoring Crunch's much better stay
    branch;
  - switching away from Houndoom without naming the threat that forces it.

#### `bench_status_karen_crobat_001`

- Fixture: `karen_crobat_vs_dragonite_toxic_or_attack`
- Skill: status clock into lock-in, anti-Dragon pivot timing.
- Expected move class: Deny into Preserve.
- Working accepted line: Toxic is the best first listed move if Crobat can
  survive the initial Outrage branch, then the boss should re-score whether to
  pivot Tyranitar, use Confuse Ray, or preserve Crobat. Immediate Wing Attack
  is too small to matter.
- Required explanation:
  - Dragonite's Outrage lock makes a poison clock meaningful;
  - Crobat survives one non-critical Outrage from current HP but cannot ignore
    the follow-up turns;
  - Tyranitar is a real anti-Dragon pivot, but switching immediately spends the
    chance to start the clock;
  - Confuse Ray is swingy and should not replace the more deterministic Toxic
    clock without a reason.
- Evidence:
  - fixture: Karen Crobat level 45 at 92% HP, Leftovers, into player Dragonite
    level 48 at full HP with revealed Outrage;
  - damage debugger: Crobat Wing Attack into Dragonite is 25-30 damage, 12-14%
    max HP;
  - damage debugger: Dragonite Outrage into 92% Crobat is 87-103 damage,
    63-74% current HP;
  - damage debugger: Dragonite Outrage into Tyranitar is 84-99 damage, 55-65%
    max HP;
  - damage debugger: Tyranitar Rock Slide into Dragonite is 81-96 damage,
    39-46% max HP.
- Failure signs:
  - clicking Wing Attack because it is STAB without checking damage impact;
  - switching Tyranitar immediately without comparing the Toxic-first branch;
  - leaving Crobat in for repeated Outrage turns after the clock has been set.
- Benchmark artifact: `fixture_karen_crobat_vs_dragonite_toxic_clock_001`;
  mutation `mut_karen_toxic_clock_no_survival_001` flips to Tyranitar when
  Crobat no longer survives the immediate Outrage punish.

#### `bench_cashout_bruno_onix_001`

- Fixture: `bruno_onix_vs_typhlosion_sandstorm_or_explosion`
- Skill: low-HP cashout versus slow weather value.
- Expected move class: Cash out.
- Working accepted line: Explosion is the clean conversion if the boss accepts
  spending Onix. Sandstorm is too slow as the main line because Earthquake
  removes Onix immediately and the weather chip does not remove Typhlosion.
- Required explanation:
  - Onix is already in guaranteed Earthquake KO range;
  - Rock Slide does not KO Typhlosion from current HP;
  - Explosion does KO Typhlosion from current HP;
  - Sandstorm is only worth considering if the downstream team specifically
    benefits from the weather after Onix dies.
- Evidence:
  - fixture: Onix level 43 at 31% HP, Hard Stone, into Typhlosion level 45 at
    61% HP with revealed Flamethrower and Earthquake;
  - damage debugger: Typhlosion Earthquake into 31% Onix is 57-68 damage,
    guaranteed KO at current HP;
  - damage debugger: Onix Rock Slide into 61% Typhlosion is 66-78 damage,
    69-81% current HP and not a KO;
  - damage debugger: Onix Explosion into 61% Typhlosion is 120-142 damage,
    guaranteed KO at current HP.
- Failure signs:
  - choosing Sandstorm because it creates long-term chip without checking
    whether Onix survives or the chip changes the next turn;
  - choosing Rock Slide because it is super-effective while missing the
    non-KO into guaranteed Earthquake punish;
  - preserving Onix without naming a future job that beats removing
    Typhlosion now.

#### `bench_mirror_coat_negative_red_blastoise_001`

- Fixture: `red_blastoise_vs_tyranitar_surf_or_mirror_coat`
- Skill: reactive-counter negative example and simple pressure.
- Expected move class: Convert.
- Working accepted line: Surf is the right listed pressure. Mirror Coat is not
  a good default because the opponent has obvious physical branches and Surf
  already hits Tyranitar's weakness.
- Required explanation:
  - Mirror Coat only answers special damage, and Tyranitar's public profile
    includes Rock Slide plus plausible Earthquake;
  - Crunch is special, but it is not the only or most defining punish branch;
  - Surf is super-effective STAB and is stronger than Blastoise Earthquake.
- Evidence:
  - fixture: Red Blastoise level 77 at 76% HP, Mystic Water, into player
    Tyranitar level 78 at 82% HP with revealed Rock Slide and Crunch;
  - damage debugger: Blastoise Surf into 82% Tyranitar is 114-134 damage,
    46-54% current HP;
  - damage debugger: Blastoise Earthquake into 82% Tyranitar is 79-94 damage,
    32-38% current HP;
  - damage debugger: Tyranitar Rock Slide into 76% Blastoise is 91-108 damage,
    49-58% current HP;
  - damage debugger: Tyranitar Earthquake into 76% Blastoise is 80-95 damage,
    43-51% current HP;
  - damage debugger: Tyranitar Crunch into 76% Blastoise is 77-91 damage,
    42-49% current HP.
- Failure signs:
  - choosing Mirror Coat because it was good in the Zapdos fixture;
  - treating Crunch's special category as enough reason to ignore Rock Slide
    and Earthquake;
  - using Earthquake because Rock/Dark sounds physical while Surf is stronger.

#### `bench_delta_lance_dragonite_001`

- Fixture: `lance_dragonite_vs_aerodactyl_outrage_or_dragon_dance`
- Skill: mechanics-source conflict handling.
- Status: active benchmark with a fixture-note caveat.
- Working accepted line: Outrage is the clean listed pressure, but the answer
  must mention lock-in risk and the seen Vaporeon / Zapdos follow-ups. Dragon
  Dance is greedy under faster Rock Slide pressure unless the damage branch is
  explicitly acceptable.
- Evidence:
  - fixture note: Aerodactyl outspeeds Dragonite slightly and Outrage is clean
    pressure with lock-in risk;
  - source chart: `data/types/type_matchups.asm` has `GROUND, FLYING,
    NO_EFFECT`;
  - caveat: the fixture note "Earthquake cannot hit a Flying target" is too
    broad for Dragonite because Dragon's Majesty converts immunities into
    resistances for damaging non-fixed moves by Dragon-typed attackers;
  - control checks: non-Dragon Onix / Donphan / Golem Earthquake into Flying
    targets returned 0 damage;
  - damage debugger: Dragonite Outrage into Aerodactyl is 68-81 damage, 34-41%
    max HP;
  - damage debugger: Dragonite Earthquake into Aerodactyl is 45-54 damage,
    23-27% max HP, which is weaker than Outrage despite bypassing the usual
    immunity;
  - damage debugger: Aerodactyl Rock Slide into 92% Dragonite is 119-140
    damage, 69-81% current HP and not a KO.
- Failure signs:
  - repeating the broad "Ground cannot hit Flying" rule without checking
    Dragon's Majesty;
  - clicking Dragon Dance without checking faster Rock Slide pressure and
    lock-in alternatives;
  - ignoring seen Vaporeon and Zapdos when evaluating Outrage lock.

#### `bench_external_belly_drum_wake_001`

- Source: external GSC OU replay,
  `https://replay.pokemonshowdown.com/gen2ou-2404705604-gl00guvgmu8l6etle1dd06927fn0jlspw.log`.
- Turns: 44-46.
- Skill: sleep counter tracking, setup discipline, and preserved-answer checks.
- Expected move class: Reject Greedy Setup.
- Accepted answer: do not treat Belly Drum as safe merely because opposing
  Snorlax is currently asleep on the bench. The correct review must say that
  the opposing Snorlax can return near full, wake or act before the setup route
  converts, and KO the Drummed Snorlax after Belly Drum cuts HP.
- Required explanation:
  - p2 Snorlax re-entered at 88% after Spikes and healed to 99% while asleep;
  - p1 Snorlax re-entered at 63% and healed to 69%;
  - Belly Drum dropped p1 Snorlax to 19%;
  - p2 Snorlax then used Double-Edge and KOed it;
  - the earlier Skarmory answer had been weakened but not enough to make the
    Snorlax setup route automatically safe.
- Evidence:
  - replay ledger tags turn 46 as setup plus faint;
  - external review showed the same player tried Belly Drum twice, and both
    attempts failed because the opponent preserved or recovered the answer in
    time.
- Failure signs:
  - saying "Snorlax is asleep, so this is the setup window" without tracking
    wake or action timing;
  - ignoring the HP cost of Belly Drum;
  - reviewing only the final Double-Edge instead of the prior route map.

#### `bench_external_phaze_loop_golem_skarm_001`

- Source: external GSC OU replay,
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-505883.log`.
- Turns: 32-68, with key checkpoints at 36, 39, 49, 52, 59, and 68.
- Skill: phazing-loop review, forced-entry accounting, and endgame conversion.
- Expected move class: Long-game ledger, not one-turn move choice.
- Accepted answer: identify that Golem's Roar plus Earthquake was not random
  stalling. It repeatedly denied Skarmory's Curse plan, forced Snorlax entries,
  and controlled which endgame pieces could appear. Skarmory's Whirlwind on
  turn 59 mattered because it dragged Starmie in; Golem's Explosion on turn 68
  then removed or crippled Skarmory enough for Starmie to finish with Surf and
  Nightmare pressure into sleeping Snorlax.
- Required explanation:
  - name both sides' routes during the loop;
  - track which forced entries take damage or burn sleep turns;
  - distinguish Roar as progress from Roar as empty repetition;
  - explain why the final Golem Explosion was a route trade, not isolated
    damage;
  - note how Starmie's final entry converted the loop into a win.
- Evidence:
  - replay ledger tags repeated Golem Roar turns as phaze events;
  - turn 59: Golem's Roar failed while Skarmory's Whirlwind dragged Starmie;
  - turn 68: Golem Exploded into Skarmory;
  - turns 69-71: Starmie used Surf / Nightmare / Surf to end the game.
- Failure signs:
  - summarizing turns 32-68 as "they switched and phazed a lot";
  - claiming Skarmory was winning because it kept using Curse;
  - missing that the loop was setting up Starmie's final route.

#### `bench_external_resttalk_zapdos_001`

- Source: external GSC OU replay,
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-912130.log`.
- Turns: 24-28.
- Skill: RestTalk branch accounting and conversion review.
- Expected move class: Continue Pressure With Branch Awareness.
- Accepted answer: pressuring the sleeping Zapdos can be correct, but the
  explanation must not call the route converted while Sleep Talk can still call
  Rest. In the replay, Zapdos Rested on turn 24, was pushed to 27% on turn 25,
  then Sleep Talk called Rest and reset to full. The line only remains good if
  the attacking side can continue making progress after that reset.
- Required explanation:
  - p2 Zapdos used Rest on turn 24 and p1 Zapdos Thunder put it at 55%;
  - p1 Zapdos Hidden Power dropped it to 27% on turn 25;
  - p2 Zapdos Sleep Talk called Rest and restored to full;
  - Sleep Talk Rest is a legal branch to price, not a post-hoc excuse;
  - future Zapdos pressure must be re-scored after the reset.
- Evidence:
  - replay ledger tags turn 24 as recovery and turn 25 as Sleep Talk;
  - GSC mechanics allow Sleep Talk to call Rest and reset the Rest cycle.
- Failure signs:
  - saying "Zapdos is asleep, so finish it" without listing Sleep Talk
    branches;
  - treating Sleep Talk Rest as pure luck rather than a known legal branch;
  - ignoring that the HP reset changes later Thunder and Hidden Power trades.

#### `bench_external_spin_relayer_cloyster_001`

- Source: external GSC OU replay,
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-912130.log`.
- Turns: 33 and 40-43.
- Skill: hazard-control durability and sacrifice valuation.
- Expected move class: Temporary Control, Then Re-check Spiker Access.
- Accepted answer: Golem's Rapid Spin on turn 33 removed Spikes from don
  marto's side, but it did not permanently solve the hazard game because
  leoperi still had Cloyster. The poisoned Cloyster re-entered, set Spikes on
  turn 41, Exploded into the opposing Cloyster on turn 42, and let Houndoom
  remove it on turn 43. The sacrifice is good only because it restored switch
  tax and removed opposing hazard control / Water counterplay.
- Required explanation:
  - name the spinner, the remaining Spiker, and how the Spiker re-entered;
  - track Golem's HP after Spikes and Rhydon pressure;
  - explain why low-HP Cloyster still had one high-value job;
  - judge Explosion by the route it opened, not by immediate damage alone;
  - identify which future switches were taxed after Spikes returned.
- Evidence:
  - replay ledger tags turn 33 as Rapid Spin and turn 41 as Spikes;
  - turn 42 is a sacrifice event and turn 43 removes the opposing Cloyster.
- Failure signs:
  - saying "I spun, so hazards are solved";
  - ignoring the opponent's last chance to re-layer;
  - judging Explosion only by whether it immediately KOed the target.

#### `bench_external_sleeping_lax_endgame_001`

- Source: external GSC OU replay,
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-912130.log`.
- Turns: 1-2 and 43-51.
- Skill: sleeping win-condition tracking, wake timing, and endgame route audit.
- Expected move class: Preserve But Do Not Overcount Sleeping Route.
- Accepted answer: don marto preserved the Snorlax that opened with Curse and
  was put to sleep by Lovely Kiss, but preservation did not make it immediately
  available. When it returned late, it was still asleep, took Spikes and Leech
  Seed pressure, faced Curse Rhydon, woke on turn 51, and died after one
  Earthquake. The route had to be evaluated by wake timing and entry damage,
  not by the label "Snorlax saved for late game."
- Required explanation:
  - the early Curse did not matter until Snorlax could act again;
  - carry sleeping bench state forward instead of treating the switch-out as a
    reset;
  - hazards and Leech Seed changed the wake-turn math;
  - Rhydon's Curse on turn 49 converted the sleep window into an endgame route;
  - the final route belonged to leoperi's Zapdos after Rhydon traded through
    Snorlax and Zapdos.
- Evidence:
  - replay ledger shows Lovely Kiss on turn 2 and sleeping Snorlax returning on
    turns 43-51;
  - turn 49 is a setup event for Rhydon while Snorlax remains asleep;
  - turns 51-54 show the Rhydon trade opening Zapdos's final Thunder route.
- Failure signs:
  - saying "Snorlax was saved for late game" without sleep and wake timing;
  - ignoring that asleep Snorlax cannot stop Rhydon setup immediately;
  - reviewing only turn 51 instead of the early Lovely Kiss and hazard pressure.

### Romhack Fixture Check: Erika Sleep Setup

Fixture: `erika_victreebel_vs_snorlax_sleep_or_boost`.

Source state:

- Erika Victreebel level 64, 77% HP, Muscle Band, revealed Razor Leaf and
  Sludge Bomb.
- Player Snorlax level 65, 84% HP, revealed Body Slam and Rest, with Curse and
  Earthquake plausible.

Romhack damage debugger checks:

| Query | Result |
| --- | --- |
| Victreebel Sludge Bomb into 84% Snorlax | 168-198 damage, 51-60% max HP; not a guaranteed KO. |
| Snorlax Body Slam into 77% Victreebel | 116-137 damage, 57-67% max HP; not guaranteed, but leaves Victreebel badly chipped. |
| +2 Victreebel Sludge Bomb into Snorlax | 342-402 damage, 103-121% max HP; guaranteed KO even from full. |

Interpretation: raw Sludge Bomb is pressure but not closure, and raw Swords
Dance risks taking a huge Body Slam first. Sleep Powder is valuable because it
can create the one safe Swords Dance turn that converts Sludge Bomb from chip
into a guaranteed KO. The plan still branches: if Sleep Powder misses, do not
pretend the setup turn was earned.

## Current Heuristics

### Immediate KO Beats Slow Play

- Status: stable
- Type: weight hint
- Rule: If a move reliably KOs or nearly KOs the active target now, prefer it
  over slow status, passive recovery, weak chip, or greedy setup.
- Applies when: the boss can take the KO without exposing a more valuable plan.
- Does not apply when: the KO move creates a worse forced lock, misses a better
  safe switch, or the target has a known public countermeasure.
- Example fixtures:
  - `koga_crobat_vs_alakazam_toxic_or_attack`
  - `morty_gengar_vs_kadabra_destiny_bond`
  - `misty_starmie_vs_meganium_recover_or_attack`
- Benchmark artifact: `fixture_koga_crobat_vs_alakazam_immediate_ko_001`;
  mutation `mut_koga_ko_removed_preserve_umbreon_001` flips to Umbreon when
  Wing Attack no longer removes Alakazam before Psychic or Recover pressure.
- Implementation target: debugger scoring first; ROM move scoring after review.

### Phazing Needs A Live Setup Route

- Status: provisional
- Type: arbitration policy
- Rule: Whirlwind/Roar should dominate when the opponent has a real boost or
  forced-route threat that must be denied now. Do not spend phazing just
  because the opponent used a setup-looking move.
- Applies when: the setup changes damage, makes the target uncontainable, burns
  scarce defensive answers, or combines with hazards into progress.
- Does not apply when: the public setup signal is low urgency, the phazer has
  scarce PP, status creates a better clock, or phazing fails under Gen 2 move
  order.
- Benchmark artifact: `fixture_jasmine_skarmory_vs_machoke_focus_energy_001`;
  mutation `mut_jasmine_real_boost_requires_whirlwind_001` flips to Whirlwind
  when Machoke's setup route becomes a real attack-boost threat.
- Source note: Smogon's GSC phazing material supports phazing as route denial
  and hazard pressure, while the move-priority article keeps Gen 2 timing as a
  separate mechanics gate.

### Encore Needs A Public Trap Target

- Status: provisional
- Type: sequence policy
- Rule: Encore is a route move only when public last-move, speed, and fail-state
  evidence show it can lock the target into a low-value action. Without that
  evidence, treat it as speculative utility.
- Applies when: the target just used a support, recovery, Protect-style, or
  already-active screen move, the user acts first, and Encore is not already
  active or blocked by its local fail gates.
- Does not apply when: the last move is unknown, damaging, Struggle, Encore,
  Mirror Move, the user is slower, or the target can switch freely and the trap
  does not create a route.
- Benchmark artifact: `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001`;
  mutation `mut_whitney_encore_trap_absent_double_team_001` flips to Double
  Team when Bayleef's visible last move is no longer Reflect.
- Source note: local mechanics show Encore lasts 3-6 turns and fails without a
  valid last move; the play-policy lesson is to use that only when it changes
  the transition, not because Encore is generically clever.

### Speed Control Must Buy A Future Turn

- Status: provisional
- Type: arbitration policy
- Rule: paralysis or speed-control status is strongest when it changes who acts
  first on the next meaningful turn and the user survives the public punish.
  If direct damage already removes the active threat, attack instead.
- Applies when: the target is unstatused, the speed flip changes the next
  action, direct damage does not remove the target, and the status user survives
  the immediate branch.
- Does not apply when: the target is already statused, the direct attack reaches
  a removal threshold, the status user faints before the speed control matters,
  or the revealed/implied counterplay makes the next turn worse than attacking.
- Benchmark artifact: `fixture_jasmine_magneton_vs_quilava_speed_control_001`;
  mutation `mut_jasmine_speed_control_to_direct_ko_001` flips to Thunderbolt
  when the public damage threshold removes Quilava.
- Source note: Smogon's prediction and risk/reward guides frame play as public
  information plus branch cost. Here that means Thunder Wave is not a slogan;
  it is a state transition that must beat the direct-removal branch.

### Reliable Recovery Needs A Window

- Status: provisional
- Type: recovery / tempo policy
- Rule: Recover-style healing is correct only when it preserves a needed route
  and the opponent cannot immediately erase the healing turn or improve a
  stronger route. If attacking changes a cleanup threshold, attack first.
- Applies when: the user is needed later, the opponent cannot punish the
  recovery turn, and healing changes a future switch, KO, or endgame route.
- Does not apply when: recovery only loops the same losing damage exchange, a
  direct attack creates a cleanup threshold, or the opponent can use the free
  turn for recovery, setup, hazards, or a decisive switch.
- Benchmark artifact: `fixture_misty_starmie_vs_meganium_recover_tempo_001`;
  mutation `mut_misty_recovery_window_opens_001` flips to Recover when
  Meganium cannot punish and Psychic no longer changes the Lapras cleanup band.
- Source note: Smogon risk/reward framing and progress-oriented play both
  support evaluating recovery by branch cost and route change, not by HP alone.

### State-Invalid Moves Are Not Lines

- Status: stable
- Type: hard rule
- Rule: Reject moves whose current-state precondition is false before scoring
  taste, damage, setup, or style.
- Applies when: Sleep Talk is chosen while awake, a sleep move is blocked by
  Sleep Clause or existing status, status is repeated into an already-statused
  or immune target, Rapid Spin has no hazard-removal job and no meaningful chip
  target, a charge/setup package cannot survive its first turn, or recovery is
  unavailable or meaningless in the current state.
- Does not apply when: the move has a secondary legal purpose in the current
  state and that purpose is explicitly named.
- Example evidence:
  - long-battle drill 2: awake Sleep Talk wasted turns for Snorlax and Raikou.
  - long-battle drill 2: Steelix repeatedly clicked Toxic into an already badly
    poisoned Machamp.
  - long-battle drill 3: Cloyster clicked Toxic into Steel-type Forretress, and
    Starmie clicked Rapid Spin with no hazards to remove.
  - local Rest source check: Rest at exactly full HP jumps to the failed-move
    path before the local engine reaches status-cure or sleep-counter code.
  - `mechanics_snorlax_full_hp_rest_status_fail`: full-HP Rest and awake Sleep
    Talk are both saved as strict negative pairwise evidence.
- Implementation target: pre-scoring fail gates and state preconditions.

### Rest Needs A Real Recovery Window

- Status: stable
- Type: hard rule / resource policy
- Rule: Direct Rest is legal only if the user is below full HP. It is good only
  when the HP/status recovery is worth the donated sleep turns or Sleep Talk
  turns.
- Applies when: the user is damaged enough that Rest succeeds, the restored HP
  preserves an important route, and the opponent cannot convert the sleep turns
  into a decisive setup, phazing, trap, hazard, or Explosion branch.
- Does not apply when: the user is at exactly full HP, the user is healthy and
  unstatused, the opponent has an immediate punish that makes the sleep turns
  losing, or the Rest merely delays a bad route without changing it.
- Example evidence:
  - local source: `engine/battle/effect_commands.asm` fails Rest before status
    cure when HP is full.
  - 200-game state regression: random play clicked full-HP Rest 798 times,
    including 350 while statused; the filtered policy clicked it 0 times.
  - long-battle drill 5: below-full Rest was useful in the Snorlax routes, but
    only when the following sleep turns did not donate a decisive response.
  - filtered seed 1 turn 12: toxic Raikou used below-full Rest but was KOed by
    Snorlax Double-Edge before the recovery line could matter.
  - filtered seed 16 turn 16: toxic Snorlax used below-full Rest but Skarmory
    Whirlwinded it out, so the status cure had to be weighed against the forced
    Spikes entry.
  - `mechanics_snorlax_full_hp_rest_status_fail`: full-HP paralysis did not
    make Rest legal; the scorer and strict labels now treat it as a failed
    mechanics line.
  - `red_snorlax_vs_alakazam_curse_or_body_slam`: 84% unstatused Rest is too
    early into faster Recover/Psychic pressure; Body Slam is the live route.
- Implementation target: hard fail at exact full HP; separate scoring for
  below-full status-cure Rest, emergency healing Rest, and tempo-losing Rest.

### Setup Must Change The Damage Race

- Status: stable
- Type: sequence policy
- Rule: Setup is good when it changes the next-turn damage race, creates a KO
  window, or leaves the boss ahead after the expected punish. Do not click setup
  merely because the boss is a setup-style Pokemon.
- Applies when: the boss survives, the setup improves KO math, or the player is
  unlikely to punish immediately.
- Does not apply when: the player has revealed lethal pressure, setup does not
  change the number of turns to win, or the boss loses too much tempo.
- Example fixtures:
  - `bugsy_scyther_vs_quilava_fire_pressure`
  - `clair_kingdra_vs_lapras_dragon_dance_or_attack`
  - `whitney_clefairy_vs_bayleef_encore_window`
  - `erika_victreebel_vs_snorlax_sleep_or_boost`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
  - `will_slowbro_vs_houndoom_amnesia_or_surf`
  - `red_charizard_vs_starmie_sunny_day_or_switch`
- Implementation target: plan scoring, then ROM setup weights.

### Defensive Setup Still Needs Tempo

- Status: developing
- Type: sequence policy
- Rule: A defensive setup move is bad if the user is slower and already in
  lethal range before the boost applies, even when the move boosts the correct
  defensive stat.
- Applies when: the player has revealed or highly likely faster damage that
  KOs, and the setup move does not act before that damage.
- Does not apply when: the boss moves first, survives the public hit, has
  sleep/paralysis/protection support, or the setup turn is forced by the
  opponent's inability to punish.
- Example fixtures:
  - `will_slowbro_vs_houndoom_amnesia_or_surf`
  - `pryce_piloswine_vs_typhlosion_amnesia_or_attack`
- Implementation target: setup scoring should check speed order and current KO
  range before rewarding the stat-stage improvement.

### Two-Turn Packages Need A Safe First Turn

- Status: developing
- Type: sequence policy
- Rule: Do not choose a two-turn plan when the first turn loses to a revealed
  immediate punish, unless the plan's first turn itself prevents that punish.
- Applies when: a line needs setup weather, a charge move, lock-in ramping,
  recovery before attacking, or a switch before attacking, and the opponent has
  public damage or status that can stop the package before payoff.
- Does not apply when: the first turn changes the opponent's damage enough to
  survive, the opponent is forced out, the user moves first and creates a
  forced state, or the line is explicitly a prediction from a losing position.
- Example fixtures:
  - `red_charizard_vs_starmie_sunny_day_or_switch`
- Implementation target: plan scoring should evaluate the first-turn survival
  and the second-turn payoff as a linked branch, not as separate move scores.

### Explosion Needs A Forced Or Costly Target

- Status: developing
- Type: sacrifice policy
- Rule: Explosion is a cash-out only when the target cannot cheaply deny it, or
  when the denial branch is itself punished by the resulting position.
- Applies when: the opponent has Protect, Ghost typing, a Normal-resistant
  pivot, a low-value sacrifice, or a clear switch that makes the Explosion
  trade bad.
- Does not apply when: the target is trapped, asleep with no safe wake branch,
  forced to stay, too important to sacrifice, or the free entry after Explosion
  is itself the named route.
- Example evidence:
  - long-battle drill 2: Steelix Explosion into poisoned Snorlax was useful
    because Spikes and follow-up attackers converted the chip into removal of
    the central threat.
  - long-battle drill 2: Exeggutor Explosion into Misdreavus Protect did
    nothing because the target denied the trade for free.
- Implementation target: sacrifice scoring should consider Protect, Ghosts,
  Normal resists, forced-target evidence, and the next-entry plan.

### Trap Clocks Override Normal Plans

- Status: developing
- Type: endgame policy
- Rule: Once Mean Look / Spider Web plus Perish Song or a similar forced clock
  is active, evaluate the position as a countdown instead of a normal damage,
  Rest, or setup race.
- Applies when: the active Pokemon is trapped or likely to be trapped and a
  countdown, perish, lock, or forced-faint route is available.
- Does not apply when: the trapped Pokemon can immediately KO, phaze, pivot
  through Baton Pass-style mechanics, or accept the trade into a clearly winning
  endgame.
- Example evidence:
  - long-battle drill 2: Snorlax used Curse/Rest/Sleep Talk while Misdreavus
    executed Mean Look plus Perish Song, causing both to faint on the clock.
  - Smogon Misdreavus and SleepTrap resources describe Mean Look / Perish Song
    as route-ending pressure that makes phazing, Pursuit, and sleep state
    central counterplay rather than side details.
- Benchmark artifact: `fixture_morty_misdreavus_vs_typhlosion_perish_route_001`;
  mutation `mut_morty_perish_route_cannot_survive_001` flips to Gengar when
  Misdreavus no longer survives the public Flame Wheel branch long enough to
  start Perish Song.
- Implementation target: plan scoring should add a high-priority clock state
  that asks "how many turns remain, and what action changes the clock?"

### Do Not Collapse To One Route Blindly

- Status: developing
- Type: endgame policy
- Rule: Before sacrificing or exhausting the second-to-last useful route, name
  the opponent's preserved anti-route and verify the last route can beat it.
- Applies when: a sacrifice, Explosion, Rest loop, hazard trade, or wall-war
  commitment would leave only one realistic win condition.
- Does not apply when: the remaining route has a forced win, the opponent's
  anti-route is gone or disabled, or the sacrifice immediately ends the game.
- Example evidence:
  - long-battle drill 3: Exeggutor's Explosion helped Snorlax beat Skarmory,
    but left only Snorlax into a preserved Misdreavus Perish Song endgame.
- Implementation target: endgame scoring should count remaining independent
  routes, not only current matchup progress.

### Prediction Needs A Base Case

- Status: developing
- Type: prediction policy
- Rule: A prediction-only move is good only if its miss branch remains
  acceptable or the current board gives strong public evidence that the target
  will choose the predicted line.
- Applies when: Pursuit, double-switching, trap moves, immunities, Protect
  reads, or choice-lock reads gain large value only if the opponent switches or
  chooses one specific move.
- Does not apply when: the prediction move is also the best or near-best move
  if the opponent stays, or the board is losing unless the prediction succeeds.
- Example evidence:
  - Karen Houndoom into Alakazam: Pursuit is only superior if Alakazam
    switches; Crunch is much better if Alakazam stays.
- Implementation target: prediction scoring should compare stay and switch
  branches explicitly instead of rewarding "smart-looking" reads by default.

### Reactive Counters Need Survival And Category

- Status: developing
- Type: reactive policy
- Rule: Counter, Mirror Coat, Destiny Bond, and similar reactive moves must
  pass two checks before being scored as real answers: the user survives or
  otherwise acts in the right window, and the opponent's likely move belongs to
  the category or trigger the reactive move answers.
- Applies when: the move only pays off after taking a hit, after moving last,
  or after the opponent chooses a specific damage category.
- Does not apply when: the reactive move is being used from a forced-losing
  position where any normal move also fails and the gamble is the only route.
- Example evidence:
  - Red Blastoise into Zapdos: Mirror Coat is high-upside only if Blastoise
    survives the Electric special hit.
  - Red Blastoise into Tyranitar: Mirror Coat is poorly aligned because
    Tyranitar's public punish profile includes Rock Slide and Earthquake.
- Implementation target: reactive scoring should require survival ranges,
  category fit, and branch label before giving style or counterplay credit.

### Sleep Is Strong But Must Be Gated

- Status: stable
- Type: hard rule
- Rule: Sleep is legal and strong; do not avoid it just because it feels mean.
  Gate it only on real public fail states such as Sleep Clause, an already
  statused target, Substitute, Safeguard, or repeating sleep after it already
  landed. A landed sleep can justify one setup turn, then the boss should cash
  damage and only reapply sleep after the target wakes and Sleep Clause allows
  it.
- Applies when: target is awake, legal to sleep, and the miss risk is worth the
  control.
- Does not apply when: the boss can simply KO now, Sleep Clause blocks it, or
  missing loses a decisive race.
- Simulation note: in a Gen 2 Victreebel vs Snorlax scratch test, Sleep Powder
  into one Swords Dance beat both raw attacking and raw setup over 200 seeds.
  Sleep Powder into two Swords Dances was worse than one boost, so the rule is
  "sleep buys the needed setup turn", not "sleep means boost forever".
- Example fixtures:
  - `morty_haunter_vs_noctowl_sleep_line`
  - `erika_victreebel_vs_snorlax_sleep_or_boost`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Implementation target: sleep fail gates and status scoring.

### One Debuff Can Be Right, Repeating Debuffs Usually Is Not

- Status: stable
- Type: sequence policy
- Rule: One accuracy or control debuff can be good when direct damage is nearly
  worthless. Repeating debuffs is usually bad because the player can switch and
  clear them.
- Applies when: chip damage is negligible and one debuff materially improves
  survival or tempo.
- Does not apply when: useful damage is available, the target can freely switch,
  or the boss is spending multiple turns for no lasting gain.
- Example fixtures:
  - `falkner_pidgeotto_vs_geodude_rock_risk`
- Implementation target: sequence memory and repeat-utility penalties.

### Hazards Need A Playable Setter Turn

- Status: developing
- Type: hazard policy
- Rule: Spikes are high-value long-game pressure, especially with this
  romhack's three layers, but do not place hazards when the setter is slower
  and faces a revealed immediate KO unless the sacrifice creates a named route
  worth more than preserving the setter.
- Applies when: the active hazard setter is under public lethal pressure and
  the expected hazard turn is not protected by sleep, paralysis, forced switch,
  resistance, or a known opponent setup/recovery turn.
- Does not apply when: the setter survives the public hit, the opponent is
  likely forced out, the hazard layer creates an immediate forced route, or the
  setter is intentionally being spent as part of a cash-out plan.
- Example fixtures:
  - `koga_ariados_vs_typhlosion_spikes_or_toxic`
- Implementation target: hazard scoring should check speed order, public KO
  ranges, and whether the layer's future value is actually reachable.

### Local Spikes Must Be Layer-Aware

- Status: developing
- Type: romhack hazard policy
- Rule: Score Spikes from the current stack, not from a generic hazard slogan.
  The third layer can be a high-value conversion turn when the player is
  grounded and hazard control is not public; a fourth layer is a failed move.
- Applies when: the local field state records player-side Spikes layers and
  the boss is choosing whether to set Spikes, attack, switch, or sacrifice.
- Does not apply when: the setter faces immediate lethal pressure, the player
  has an available spinner that can remove the stack cheaply, the player team
  is mostly Flying, or Explosion removes a more important defensive answer than
  the hazard layer would pressure.
- Example fixtures:
  - `janine_qwilfish_finish_third_spikes_layer`
  - `janine_qwilfish_spikes_already_maxed`
- Implementation target: action scoring and features should expose
  `spikes_third_layer_available` and `spikes_already_maxed`, and the final
  decision should still review Explosion as a route trade.

### Hazard Sacrifice Must Beat Hazard Control

- Status: developing
- Type: hazard policy
- Rule: Do not spend the Spiker just because a layer is down if the opponent's
  spinner or remover survives and can clear it before the layer creates real
  pressure.
- Applies when: the Spiker is considering Explosion, sacrifice, or a low-value
  trade while the opposing spinner, Defog-equivalent, or romhack Rapid Spin
  user is still active or easily preserved.
- Does not apply when: the sacrifice removes the hazard-control piece, traps or
  punishes the remover, creates an immediate forced win, or the hazard has
  already produced the needed damage threshold.
- Example evidence:
  - filtered long-battle drill 4: Cloyster set Spikes, Exploded into
    Forretress, Forretress survived, spun the Spikes away, then traded for
    Raikou. The hazard plan did not survive the trade.
- Implementation target: hazard scoring should value "layer plus control" more
  than "layer placed once".

### Avoid Bad Lock-In Openers

- Status: stable
- Type: hard rule
- Rule: Do not begin a ramp or lock-in move like Rollout or Outrage when it is
  resisted, does not KO, and gives the player a clear punish or switch.
- Applies when: the lock-in move starts from a weak position.
- Does not apply when: the target is already in KO range, paralyzed, unable to
  punish, or the lock sequence is already safely underway.
- Example fixtures:
  - `whitney_miltank_vs_geodude_rollout_temptation`
- Implementation target: lock-move opener scoring.

### Do Not Lock Into A Public Immunity

- Status: stable
- Type: hard rule
- Rule: Do not choose a Choice-locked identity STAB when public typing makes
  the move fail. A live coverage move or preservation switch is better than
  committing to a no-effect move.
- Applies when: the target's public type or revealed mechanic makes the move
  immune/no-effect and the boss item or move lock makes the mistake compound
  across future turns.
- Does not apply when: the target is expected to switch and the chosen move
  covers the switch branch, or a local mechanic has been verified to bypass the
  immunity.
- Example fixtures:
  - `sabrina_alakazam_choice_lock_vs_houndoom`
- Implementation target: `public_type_immunity_risk` should fire from public
  fixture text before generic coverage or identity bonuses can save the move.

### Switch When Preservation Is Worth The Free Hit

- Status: developing
- Type: switch policy
- Rule: Switching is good when preserving the active boss Pokemon is worth more
  than the free turn the player gets, especially if the bench has a clear resist
  or a better threat.
- Applies when: the current active is likely to lose or has high later value.
- Does not apply when: the switch-in is not actually safer, the active can take
  a clean KO now, or the switch gives up too much pressure.
- Example fixtures:
  - `chuck_poliwrath_vs_pidgeotto_ice_punch`
  - `pryce_slowking_vs_ampharos_ground_pivot`
  - `brock_golem_vs_vaporeon_explosion_question`
  - `will_slowbro_vs_houndoom_amnesia_or_surf`
- Implementation target: switch preservation scoring and plan scoring.

### Scout Hidden Coverage Before Committing An Ace

- Status: provisional
- Type: scout policy
- Rule: Hidden coverage suspicion can make probing, attacking once, or switching
  better than greedy setup before committing an ace.
- Applies when: the player staying in only makes sense if they have dangerous
  hidden coverage, the coverage branch is severe, and a public pivot preserves
  the route without handing over a worse position.
- Does not apply when: the threat is already revealed, no longer plausible, too
  weak to change the route, or the boss has a direct winning line.
- Example fixtures:
  - `clair_dragonair_vs_suicune_hidden_ice_beam`
  - `lance_dragonite_vs_suicune_champion_ace`
- Benchmark artifact: `fixture_clair_dragonair_vs_suicune_hidden_ice_001`;
  mutation `mut_clair_hidden_ice_absent_attack_now_001` flips to Thunder when
  the public hidden-Ice punish is no longer plausible.
- Implementation target: public hidden-coverage risk scoring.

### Preserve Variety In Near-Tie Sacrifice Lines

- Status: developing
- Type: personality style
- Rule: If sacrifice, switch, and attack lines are genuinely close, the boss
  should preserve some variety instead of becoming deterministic.
- Applies when: both lines are defensible and source notes call out near-tie
  behavior.
- Does not apply when: one option is clearly forced by KO, public fail gate, or
  survival.
- Example fixtures:
  - `brock_golem_vs_vaporeon_explosion_question`
  - `morty_gengar_vs_kadabra_destiny_bond`
- Implementation target: final tie-break/randomization policy.

## Answered Teaching Notes

### Erika Victreebel vs Snorlax

- Fixture: `erika_victreebel_vs_snorlax_sleep_or_boost`
- Answer: Sleep Powder first. Even though it is inaccurate, landing sleep gives
  Victreebel the turn it needs to Swords Dance. After that, pressure with Sludge
  Bomb. If Snorlax wakes up, use Sleep Powder again only when Sleep Clause is
  legal.
- Extracted rule: Sleep can be the correct first move when it creates a setup
  turn that changes the damage race. The follow-up is bounded: setup once,
  attack, and re-sleep only after a legal wake state.

### Lance Yanma vs Lapras

- Fixture: `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Answer: Same pattern as Erika. Sleep Powder first, then use the sleep turn to
  Quiver Dance, then attack with Giga Drain. Reapply Sleep Powder only after
  Lapras wakes up and only if Sleep Clause is legal.
- Extracted rule: Weak immediate damage plus dangerous hidden coverage can still
  favor sleep-first setup. The setup is not raw greed because sleep creates the
  turn that makes Quiver Dance safe enough to try.
- Implementation follow-up: the first scorer regression miss was not a new
  strategic exception. `Quiver Dance` was missing from the setup taxonomy, so
  the debugger misclassified it as damage-like and awarded a false coverage
  bonus from the phrase "Ice coverage." Classifying `Quiver Dance` as setup now
  makes the debugger rank Sleep Powder first in this fixture.
- Direct-action follow-up: the Erika one-turn scorer now has the same
  sleep-first opener logic as the multi-turn plan. In sleep/setup fixtures with
  an unstatused target, a sleep move can earn `sleep_enables_setup_line` because
  it creates the turn that makes the boost legal. This is intentionally
  narrower than "sleep is always best."
- Plan follow-up: the next gap was sequence-level. Separate cards for
  `Sleep Powder -> Giga Drain` and `Quiver Dance -> Giga Drain` still miss the
  actual taught line. The plan generator now emits a bounded
  `sleep_then_setup_then_attack` card for fixtures tagged both `sleep` and
  `setup`, with branches that stop and re-score after miss, wake, switch, Sleep
  Clause, or lost setup value.

### External GSC Rhydon vs Sleeping Snorlax

- Fixture: `external_gsc_rhydon_vs_sleeping_snorlax_curse_window`
- Source: replay 912130, turn 49.
- Answer: Curse is better than immediate Earthquake, Rock Slide, or switching
  Zapdos in this exact endgame because Snorlax is still publicly asleep and
  Rhydon needs the boost to convert the route before or through the wake branch.
  The line is not "setup because setup is good"; it is setup because the sleep
  window changes the KO math and still leaves a coherent turn after Snorlax
  wakes.
- Extracted rule: a sleeping target can create a real setup window, but the
  explanation must still price wake timing, speed changes, entry damage, and
  the next attack. Preserve the phrase "sleeping win condition is not available
  yet" as a state-tracking warning, not as a reason to ignore the target.
- Implementation follow-up: the scorer now has a narrow
  `sleeping_target_setup_window` contribution for setup moves when the public
  target is asleep in a fixture tagged both `sleep` and `setup`. This fixed the
  new replay-derived fixture without globally rewarding setup.

### Mechanics Drill: Full-HP Rest And Awake Sleep Talk

- Fixture: `mechanics_snorlax_full_hp_rest_status_fail`
- Answer: do not use Rest at full HP to cure paralysis, and do not use Sleep
  Talk while awake. Body Slam or even a phazeable Curse line is better than a
  known failed move.
- Extracted rule: Rest status-cure logic only matters after the move passes the
  full-HP check. If the user is at exactly full HP, status does not rescue the
  move. Sleep Talk similarly requires actual sleep, not merely any status.
- Implementation follow-up: the debugger now applies `full_hp_rest_fails`,
  `healthy_rest_no_status`, and `awake_sleep_talk_fails` contributions, and
  the feature report exposes `rest_at_full_hp`, `rest_high_hp_no_status`, and
  `sleep_talk_while_awake` features.

### Janine Qwilfish Romhack Spikes Layers

- Fixtures: `janine_qwilfish_finish_third_spikes_layer` and
  `janine_qwilfish_spikes_already_maxed`
- Answer: at two local layers, Qwilfish should usually finish the third layer
  over ordinary attack chip or switching when the player is grounded, no player
  spinner is public, and Qwilfish is not under immediate lethal pressure. At
  three layers, another Spikes click is a known failed move and should be
  rejected before style or long-game reasoning.
- Extracted rule: local Spikes decisions require the current layer count. The
  third layer changes future grounded switch-ins from max HP / 6 to max HP / 4;
  a fourth layer is not "more pressure", it is no action. Explosion stays in a
  separate route-trade bucket because removing Snorlax or a wall can be worth
  more than completing the stack in some states.
- Implementation follow-up: the debugger now applies
  `third_spikes_layer_pressure` and `spikes_already_maxed` contributions, and
  the feature report exposes `move_class_hazard`,
  `spikes_third_layer_available`, and `spikes_already_maxed`.

## Current Scorer Gap Audit

Most entries below are notebook interpretations of the existing queue, user
feedback, and local damage debugger. Treat them as review targets until direct
action labels or stronger trajectory rows confirm them; entries marked
resolved have already been promoted into fixtures, labels, or code changes.

Latest local audit status:

- `python -m tools.boss_ai_preference validate` passes and now validates 43
  public state-transition cards and 43 hidden oracles with explicit `seed` /
  `holdout` / `fixture_harvest` splits.
- `python -m tools.boss_ai_preference benchmark-policy` writes
  `audit/boss_ai_preference/state_transition_policy_answers.json` from the
  deterministic `state_transition_baseline_v1` policy. This policy reads
  `state_transition_public_cards.json`, emits `state_hash`,
  `candidate_ranking`, inferred catastrophe branches, answer-changing
  information, and `rules_fired`, and does not read hidden oracle labels.
- `python -m tools.boss_ai_preference benchmark-report --answers
  audit/boss_ai_preference/state_transition_policy_answers.json` writes the
  executable state-transition benchmark report by joining the hidden oracle file
  only inside the evaluator. The current report has
  `benchmark_contract_ready=True`, `policy_evaluated=True`,
  `policy_passes=True`, and
  `split_passes={'fixture_harvest': True, 'holdout': True, 'seed': True}`
  across the 43 current snapshots. This is a baseline gate, not mastery proof.
- `python -m tools.boss_ai_preference benchmark-harvest` writes
  `audit/boss_ai_preference/fixture_benchmark_harvest.md`. The current harvest
  finds 4 complete fixture-derived benchmark candidates:
  `chuck_poliwrath_vs_pidgeotto_ice_punch`,
  `janine_qwilfish_finish_third_spikes_layer`, and
  `mechanics_snorlax_full_hp_rest_status_fail`, and
  `brock_golem_vs_vaporeon_explosion_question`. Those four are now promoted
  into the `fixture_harvest` benchmark split. The Will Slowbro/Houndoom
  fast-threat case is also promoted from high-confidence pairwise feedback as a
  targeted coverage card with a pivot-unavailable mutation. The Koga
  Ariados/Typhlosion case is also promoted to test that Spikes/status lose to a
  revealed lethal Fire punish, the Bugsy Scyther/Geodude case is promoted
  to test that setup can be correct when the public punish is survivable, and
  the Chuck Poliwrath/Alakazam case is promoted to test that a verified Dark
  pivot can dominate an accuracy-dependent sleep line. The Morty
  Haunter/Noctowl case is promoted to test that legal sleep can dominate fixed
  damage and premature ace exposure. The Falkner Pidgeotto/Geodude case is
  promoted to test that a single scout probe can dominate tiny direct chip when
  a public punish branch is live. The other 23 feedback fixtures are partial,
  mostly because they lack an acceptable alternative label.
- `python -m tools.boss_ai_preference benchmark-label-queue` writes
  `audit/boss_ai_preference/benchmark_label_queue.md`. The current queue has
  23 request candidates, returns 20 by default, and has 11 one-label
  completions where an unclassified action can be reviewed as the missing
  acceptable alternative. It prefers plausible probes such as preservation
  switches or sensible coverage over already catastrophic moves, so the queue
  is for evidence collection rather than label invention. The remaining
  partials need either a contextual exception, a new benchmark variant, or a
  resolved single-best / catastrophe label.
- `python -m unittest tools.boss_ai_preference.tests.test_benchmark_positions`
  also checks answer-changing mutations: blocked Sleep Clause changes away from
  sleep, maxed Spikes changes away from Spikes, revealed Protect changes away
  from Explosion, unavailable Piloswine changes away from the preservation
  switch, unavailable Sudowoodo changes from preservation to Ice Punch,
  unavailable Houndoom changes from preservation to Surf, unavailable
  Tentacruel changes the Koga Fire-pressure preservation pivot to Umbreon, and
  a removed safe setup window changes Bugsy Scyther from Swords Dance to Wing
  Attack. Unavailable Umbreon changes Chuck Poliwrath from preservation to
  Hypnosis. Occupied Sleep Clause changes Morty Haunter from Hypnosis to Night
  Shade. Removing the public Rock-risk branch changes Falkner Pidgeotto from
  Sand Attack to Gust. Full-HP Rest / awake Sleep Talk remain failed state
  transitions. It also checks
  replay-derived opening, Explosion, RestTalk, and late Rapid Spin boundaries
  from Showdown GSC logs.
- `python tools/audit/check_boss_ai_preference.py` passes.
- `python tools/audit/check_boss_ai_trace_invariants.py` passes.
- `python tools/audit/check_boss_ai_policy_contract.py` passes.
- `python tools/audit/check_boss_ai_no_cheat.py` passes.
- `python tools/audit/check_boss_ai_gating.py` passes.
- `python tools/audit/check_boss_ai_memory_budget.py` passes.
- `python -m tools.boss_ai_debugger regress --json-out
  audit/boss_ai_preference/regression_report.json` now reports 43 / 43 strict
  pairwise labels agreeing with the scorer after the `Quiver Dance` taxonomy
  fix, the sleeping-target setup-window rule, the Rest/Sleep Talk state gates,
  the local Spikes layer-state rules, and the sleep-first setup opener rule.
- Resolved strict regression:
  `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`. Before the fix, the
  debugger ranked Quiver Dance 59 over Sleep Powder 58 because `Quiver Dance`
  was absent from `SETUP_NAMES` / `SETUP_MOVES`, so the word "coverage" in
  "Ice coverage" triggered the damage coverage bonus. After the fix, the same
  inspection ranks Sleep Powder 58, Giga Drain 57, Switch to Kingdra 56, and
  Quiver Dance 48 with `setup_identity` and `setup_risk` applied.
- Resolved plan-card gap: `audit/boss_ai_preference/plan_queue.md` and
  `audit/boss_ai_preference/coach_report.md` now surface
  `sleep_then_setup_then_attack` for both the Lance Yanma and Erika Victreebel
  sleep/setup demonstrations. This does not prove the plan is always correct;
  it means the review tool can finally show the taught candidate instead of
  forcing reviewers to choose among incomplete fragments.
- Resolved replay-fixture gap:
  `external_gsc_rhydon_vs_sleeping_snorlax_curse_window` converts the 54-turn
  external review into a scored single-position test. The debugger now ranks
  Curse 68, Earthquake 63, Rock Slide 57, and Switch to Zapdos 54, with the
  setup score coming from public sleep state rather than vague setup prose.
- Resolved Rest/Sleep Talk state-gate gap:
  `mechanics_snorlax_full_hp_rest_status_fail` converts the local Rest source
  check into a scored mechanics fixture. The debugger now ranks Curse 56,
  Body Slam 50, Rest 39, and Sleep Talk 38, explicitly penalizing full-HP Rest
  and awake Sleep Talk instead of treating them as generic recovery/control.
- Resolved romhack Spikes layer gap:
  `janine_qwilfish_finish_third_spikes_layer` and
  `janine_qwilfish_spikes_already_maxed` convert the three-layer Spikes source
  check into scored mechanics fixtures. The debugger now ranks third-layer
  Spikes above ordinary chip in the safe Janine Qwilfish fixture, and ranks
  maxed-out Spikes last once the player side already has three layers.
- Resolved Erika direct-action gap:
  `erika_victreebel_vs_snorlax_sleep_or_boost` now has strict pairwise labels
  for Sleep Powder over raw Swords Dance, Sludge Bomb, and switching. The
  debugger ranks Sleep Powder 71 over Swords Dance 68 because the sleep move is
  scored as the opener to a setup line rather than generic status flavor.
- Resolved Will preservation gap:
  `will_slowbro_vs_houndoom_amnesia_or_surf` now has strict pairwise labels
  for switching to Will's Houndoom over Amnesia, Surf, and Psychic. The lesson
  is preservation under a faster public KO branch: boosting the right defense
  and clicking super-effective Surf both lose if Slowbro faints before moving.
- Resolved Koga hazard-passivity gap:
  `koga_ariados_vs_typhlosion_spikes_or_toxic` now has trajectory evidence and
  an executable benchmark showing that Spikes and Toxic are too slow when
  revealed Flamethrower is a guaranteed KO into Ariados. The taught transition
  is Tentacruel first, re-score next; the mutation removes Tentacruel and flips
  the answer to Umbreon rather than pretending hazards are still free.
- Resolved Bugsy safe-setup gap:
  `bugsy_scyther_vs_geodude_safe_swords_dance` now has trajectory evidence and
  an executable benchmark showing the positive side of setup arbitration.
  Swords Dance is preferred because Scyther is faster, direct Wing Attack is
  low-impact, and the public Rock Throw branch does not remove Scyther from
  full HP. The mutation lowers Scyther into a KO branch and flips the answer to
  Wing Attack.
- Resolved Bugsy fire-setup gap:
  `bugsy_scyther_vs_quilava_fire_pressure` now has an executable benchmark
  grounded in saved pairwise and trajectory feedback. Swords Dance is preferred
  because Scyther acts first, survives one Ember, unboosted Wing Attack does
  not KO, and boosted Wing Attack changes the two-turn route. The mutation
  lowers Scyther into an Ember KO branch and flips the answer to Wing Attack.
- Resolved Chuck Psychic-pivot gap:
  `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch` now has trajectory
  evidence and an executable benchmark showing that Hypnosis is a real fallback
  but not the best line while Umbreon is healthy. The romhack type chart keeps
  Psychic at no effect into Dark, so switching to Umbreon preserves Poliwrath
  from faster Psychic/Recover pressure; removing Umbreon flips the mutation to
  Hypnosis.
- Resolved Morty sleep-control gap:
  `morty_haunter_vs_noctowl_sleep_line` now has trajectory evidence and an
  executable benchmark showing the positive sleep-control case. Hypnosis is
  preferred because Sleep Clause is free, Noctowl is unstatused, and the public
  Peck branch is survivable; Night Shade becomes the fallback when Sleep Clause
  is occupied.
- Resolved Falkner scout-probe gap:
  `falkner_pidgeotto_vs_geodude_rock_risk` now has an executable benchmark
  grounded in existing pairwise and trajectory feedback. One Sand Attack is
  preferred because Gust is tiny chip while public Rock Throw is a meaningful
  punish. The benchmark also records the exception: repeated probing is not the
  policy, and if the Rock-risk branch is removed the mutation flips to Gust.
- Resolved Pryce fire-pivot gap:
  `pryce_cloyster_vs_quilava_explosion_line` now has an executable benchmark
  grounded in saved pairwise feedback and Smogon bad-matchup switching /
  Explosion discipline principles. Slowking is preferred because revealed
  Flame Wheel can remove 39% Cloyster before Surf or Explosion makes progress,
  while Cloyster still has future Spikes/Explosion value. The mutation raises
  Cloyster out of the KO branch and flips the answer to Surf.
- Resolved Whitney lock-sequencing gap:
  `whitney_miltank_vs_geodude_rollout_temptation` now has an executable
  benchmark grounded in saved pairwise and trajectory feedback. Body Slam is
  preferred before Rollout because the first Rollout hit is tiny, Geodude is
  not paralyzed yet, and Miltank is healthy enough to pressure before healing.
  The mutation marks Geodude paralyzed and flips the answer to Rollout.
- Resolved Pryce preservation gap:
  `pryce_slowking_vs_ampharos_ground_pivot` now has strict pairwise labels for
  switching to Piloswine over Thunder Wave, Surf, and Rest. The important
  romhack-specific detail is that Dragon's Majesty means Piloswine is not fully
  immune to Ampharos's Electric damage, but it still resists the pressure,
  preserves Slowking, and threatens back with Ground coverage.
- Resolved Bugsy Ariados status-tempo gap:
  `bugsy_ariados_vs_pidgey_toxic_or_attack` now has strict pairwise labels for
  Toxic over Giga Drain, Leech Life, Poison Sting, and switching to Scyther.
  The lesson is not "status because status"; Toxic is preferred because
  Pidgey's Flying pressure is real but not lethal, Ariados's chip is weak, and
  the poison clock changes future turns without exposing the ace early.
- Resolved Sabrina public-immunity gap:
  `sabrina_alakazam_choice_lock_vs_houndoom` now penalizes Psychic with
  `public_type_immunity_risk` when public text says the target is a Dark type,
  and strict labels prefer Hypno, ThunderPunch, and Ice Punch over the failed
  Choice Specs Psychic lock.

### Falkner Pidgeotto vs Geodude

- Fixture: `falkner_pidgeotto_vs_geodude_rock_risk`
- Current lesson: one Sand Attack is a real scout/probe turn because Gust is
  nearly meaningless and public Rock Throw can swing the game immediately.
- Damage evidence:
  - Pidgeotto Gust into 86% Geodude is 2-3 damage, 6-9% of current HP.
  - Geodude Rock Throw into 72% Pidgeotto is 27-32 damage, 96-114% of current
    HP.
  - Geodude Tackle into Pidgeotto is 7-9 damage, 25-32% of current HP.
- Failure signs:
  - repeating Sand Attack several times without a conversion plan;
  - switching only to avoid risk when Noctowl still takes heavy damage;
  - clicking Gust and calling it pressure despite doing under 10%.

### Pryce Cloyster vs Quilava

- Fixture: `pryce_cloyster_vs_quilava_explosion_line`
- Current lesson: low HP does not automatically make Cloyster expendable.
  If the public faster Flame Wheel branch removes Cloyster before Surf or
  Explosion resolves, the right transition is Slowking first, preserving
  Cloyster's later Spikes/Explosion route.
- Boundary mutation:
  - when Cloyster is raised out of the Flame Wheel KO branch, the policy flips
    from `switch_slowking` to `move_surf`;
  - Explosion still needs a named route and speed/survival evidence.
- Failure signs:
  - saying "Surf is super-effective" without checking whether Cloyster moves;
  - saying "Cloyster is low, so boom" without naming the route opened;
  - using Protect as a loop instead of a one-turn scout before re-scoring.

### Bugsy Scyther vs Quilava

- Fixture: `bugsy_scyther_vs_quilava_fire_pressure`
- Current lesson: setup is conditional on speed, survival, and conversion, not
  on the fact that Scyther is an ace. The saved feedback prefers Swords Dance
  over raw Wing Attack when Scyther acts first and survives one Ember, but the
  damage range is close enough that this is now an executable boundary
  benchmark.
- Damage evidence:
  - unboosted Wing Attack into 69% Quilava is 21-25 damage, 49-58% of current
    HP, never a KO;
  - Quilava Ember into 81% Scyther is 32-38 damage, 71-84% of current HP, never
    a non-crit KO;
  - +2 Wing Attack using doubled attack stat is 41-49 damage, 95-114% of
    current HP, a possible but not guaranteed KO.
- Failure signs:
  - treating "setup once then attack" as automatic without checking speed and
    the low-roll branch;
  - cashing weak unboosted damage when it leaves Quilava alive anyway;
  - ignoring that a crit Ember invalidates the line but should be separated as
    a luck branch, not necessarily a strategic error.
- Benchmark artifact: `fixture_bugsy_scyther_vs_quilava_fire_setup_001`;
  mutation `mut_bugsy_fire_setup_window_removed_001` flips to Wing Attack when
  Ember removes the setup route before boosted Wing Attack can convert.

### Whitney Miltank vs Geodude

- Fixture: `whitney_miltank_vs_geodude_rollout_temptation`
- Current lesson: Body Slam is the opener because first-turn Rollout is weak
  by public damage evidence before it ramps. The taught plan is Body Slam
  pressure, heal with Milk Drink around the danger threshold, and only consider
  Rollout after paralysis or a safer setup state.
- Damage evidence:
  - Body Slam into 78% Geodude is 7-9 damage, 15-19% of current HP;
  - first-turn Rollout into 78% Geodude is 2-3 damage, 4-6% of current HP;
  - Geodude Rock Throw into 92% Miltank is 15-18 damage, 21-25% of current HP.
- Failure signs:
  - opening Rollout because it is iconic;
  - using Milk Drink at high HP as a scout when Body Slam has not created
    paralysis or meaningful chip yet;
  - repeating Body Slam forever without noticing when the board becomes safe
    enough to ramp.
- Benchmark artifact: `fixture_whitney_miltank_vs_geodude_rollout_lock_001`;
  mutation `mut_whitney_rollout_after_status_001` flips to Rollout once
  paralysis and board safety make the lock route live.

### Chuck Poliwrath vs Pidgeotto

- Fixture: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Current lesson: Ice Punch is the best listed attack, but the saved feedback
  says the better plan is switching to Sudowoodo because Sudowoodo walls the
  public Flying/Normal pressure and preserves Poliwrath's HP. Focus Punch is
  not reliable into a faster attacker that is likely to hit.
- Damage evidence:
  - Poliwrath Ice Punch into 58% Pidgeotto is 34-40 damage, 52-61% of current
    HP, never a non-crit KO;
  - Poliwrath Focus Punch into 58% Pidgeotto is 58-69 damage, 88-105% of
    current HP if it resolves, but it is vulnerable to interruption;
  - Pidgeotto Wing Attack into 76% Poliwrath is 52-62 damage, 53-63% of
    current HP;
  - Pidgeotto Wing Attack into 58% Sudowoodo is 11-14 damage, 17-22% of
    current HP.
- Failure signs:
  - choosing Focus Punch because its damage is attractive if the opponent does
    not attack;
  - choosing Ice Punch without asking whether Poliwrath's HP is needed later;
  - switching to any resist without naming the preserved job and the next turn.

### Red Snorlax vs Alakazam

- Fixture: `red_snorlax_vs_alakazam_curse_or_body_slam`
- Current lesson: this is unresolved and should stay in the queue. Body Slam
  immediately creates paralysis and chip chances; Curse improves future damage
  but still does not immediately beat Recover/Psychic pressure. Rest at 84%
  with no status is not a serious line.
- Damage evidence:
  - unboosted Body Slam into 62% Alakazam is 43-51 damage, 28-34% of current
    HP;
  - +1 Body Slam into 62% Alakazam is 65-77 damage, 43-51% of current HP;
  - Alakazam Psychic into 84% Snorlax is 133-157 damage, 47-55% of current HP.
- Failure signs:
  - choosing Curse solely because Snorlax is a setup wallbreaker;
  - choosing Rest as a generic recovery move before status or danger threshold;
  - ignoring Recover as the player's likely answer to slow chip.
