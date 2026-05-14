# Boss Live-Turn Practice Run: 2026-05-13

Source: `boss_live_turn_prompt_cards.md`

Status: self-training run. This is not a sealed benchmark and not final advice
for a real user battle. The player team layer is abstract, so recommendations
are move classes rather than exact moves.

Scoring posture: grade against public state only. Missing player moves, HP, and
damage evidence must be named instead of guessed.

## Card 001: Misty Adaptive Opening

Recommendation: lead or pivot with the flexible bulky/control piece that does
not consume the only Starmie/Lapras answer. Confidence: medium.

Plan: cover Politoed sleep/rain, Starmie Recover pressure, and Quagsire Curse
without letting one opener spend the only later answer.

State read: Misty can open Politoed, Starmie, or Quagsire. The single reliable
Starmie answer is the resource under pressure because Politoed can sleep it and
Quagsire can lure the team into spending a different answer too early.

Win condition: keep a verified answer to Starmie/Lapras while using the opener
to deny rain/sleep, Recover, or Curse from becoming the whole fight.

Candidate ranking:

1. Flexible bulky/control lead: best if it can act into all three openers and
   stay useful after sleep, rain, or Curse pressure.
2. Strong Water answer: acceptable only if duplicated or protected from sleep.
3. Fast cleaner: risky if Thunder Wave later removes the endgame or if Politoed
   can sleep it before it converts.

Worst plausible branch: Politoed sleeps the only Starmie answer, or Misty opens
Starmie/Quagsire while the lead was chosen only to beat Politoed.

What changes the answer: duplicated Starmie answer, Haze/Encore, confirmed
sleep absorber, exact Starmie damage, rain already active, or Sleep Clause used.

Next turn if it works: identify the opened route immediately: Politoed means
sleep/rain ledger, Starmie means Recover threshold, Quagsire means Curse denial.

Self-audit: good route framing, but exact move confidence cannot rise without
player team, damage, and speed evidence.

## Card 002: Misty Starmie Recover Turn

Recommendation: choose the action that makes Recover non-free: threshold
damage, status/control, or a verified answer entry. Confidence: medium-low.

Plan: turn Starmie's recovery into a punishable timing window instead of
trading chip that Leftovers and Recover erase.

State read: Starmie at mid HP can Recover. Rain and Thunder pressure may make
some pivots fake. The active may also be needed for Quagsire or Lapras.

Win condition: either cross a real Starmie threshold or preserve the piece that
beats the next Misty route after Starmie resets.

Candidate ranking:

1. Damage/status/control that forces Recover and creates entry, setup, or KO
   pressure: best if the follow-up is named.
2. Switch to stronger answer: acceptable only if entry survives rain/Psychic/
   Thunder and does not uncover Quagsire or Lapras.
3. Generic chip: bad if Starmie Recovers and the team loses tempo.

Worst plausible branch: the player attacks for harmless chip, Starmie Recovers,
and the active is now too low or statused to cover Quagsire/Lapras.

What changes the answer: Starmie in KO range, rain expiration, paralysis or
status available, a safe pivot, Quagsire still unhandled, or exact damage rolls.

Next turn if it works: if Starmie Recovers, use the forced recovery turn to
enter the real breaker or set the route condition; if it attacks, re-score
entry safety and rain turns.

Self-audit: this answer avoids shallow damage thinking, but exact ranking needs
the active Pokemon's moves and Starmie's HP in real values.

## Card 003: Blue Adaptive Opening

Recommendation: lead with the piece that can contest Pidgeot/Porygon2/Gyarados
without spending the only Gyarados or Arcanine answer. Confidence: medium.

Plan: use source-known boss roster and opening policy to start the answer map
before turn 1, then re-score after Blue reveals the opener. This is not
symmetrical Team Preview.

State read: Blue can open a Choice Band lock, a Recover bridge, or immediate
Dragon Dance. The fast cleaner is not automatically safe because priority range
matters later.

Win condition: preserve anti-Gyarados and anti-Arcanine resources while forcing
Pidgeot lock information, Porygon2 threshold pressure, or Gyarados setup denial.

Candidate ranking:

1. Flexible lead that can deny Dragon Dance and survive or punish Pidgeot/
   Porygon2: best.
2. Dedicated Pidgeot punish: acceptable only if it does not lose to opening
   Porygon2/Gyarados.
3. Fragile fast cleaner: bad if Pidgeot/Arcanine priority later removes its
   route.

Worst plausible branch: lead choice beats Pidgeot but Blue opens Gyarados, gets
Dragon Dance, and the only answer has already been chipped or exposed.

What changes the answer: duplicated Gyarados answer, phazing/Haze, confirmed
priority ranges, Porygon2 damage threshold, or Pidgeot lock after turn 1.

Next turn if it works: if Pidgeot attacks, record the lock; if Porygon2 opens,
deny Recover stabilization; if Gyarados opens, treat setup denial as immediate.

Self-audit: good adaptive-opener discipline. Needs exact user roster to decide
whether "flexible lead" is a wall, breaker, status user, or phazer.

## Card 004: Blue Gyarados After Dragon Dance

Recommendation: deny Gyarados now with the least expensive effective route:
healthy control, immediate KO/revenge, or controlled sacrifice into the answer.
Confidence: medium.

Plan: stop the boosted route before it converts while preserving enough map for
Tauros, Rhydon, and Arcanine.

State read: Gyarados already boosted, so slow value falls. The answer's label
depends on whether it survives entry and boosted damage now, not whether it
answered Gyarados before the boost.

Win condition: prevent Gyarados from taking multiple KOs while keeping at least
one later physical/priority answer alive.

Candidate ranking:

1. Healthy phaze/Haze/status or guaranteed revenge/KO: best if legal and
   survivable.
2. Controlled sacrifice into clean answer entry: acceptable if it does not
   spend the Tauros/Rhydon/Arcanine answer.
3. Hard switch to a chipped "answer": catastrophic if it dies on entry or loses
   to boosted coverage.

Worst plausible branch: the player preserves material with a slow move while
Gyarados takes the next KO and Blue's remaining breakers inherit a broken map.

What changes the answer: exact +1 damage, hazards, available priority, phazing
legality, Gyarados HP, and whether Hyper Beam recharge can be converted.

Next turn if it works: after denial, rebuild around the next Blue route rather
than spending the same answer again by habit.

Self-audit: strongest of the run because the board already defines urgency.
Remaining gap is exact local damage.

## Card 005: Lance Serial Setup Budget

Recommendation: pressure Steelix while preserving the final Dragonite/Kingdra
answer unless Steelix's boost creates immediate irreversibility. Confidence:
medium.

Plan: treat Lance as six setup waves, not as one Steelix matchup.

State read: Steelix can boost now, but Gyarados, Ampharos, Yanma, Kingdra, and
Dragonite still demand anti-setup coverage. One answer also handles Kingdra, so
spending it early may collapse the later route map.

Win condition: remove or contain Steelix with the cheaper anti-setup tool while
preserving a route against the final boosted threats.

Candidate ranking:

1. Damage/control/status from the tool that is not the final Dragonite/Kingdra
   answer: best if it prevents Steelix from snowballing.
2. Spend the shared anti-setup tool: acceptable only if Steelix otherwise
   becomes irreversible.
3. Use the final Dragonite answer as a type-based Steelix check: bad unless the
   remaining roster has redundant Dragonite coverage.

Worst plausible branch: Steelix chips or removes the final setup answer, then
Gyarados/Kingdra/Dragonite asks the same piece to act again.

What changes the answer: Steelix in KO range, redundant Dragonite answer, exact
boosted Speed/damage, phazing/Haze availability, or status accuracy.

Next turn if it works: re-label remaining anti-setup tools before the next
Lance Pokemon enters; do not autopilot from Steelix to the next Dragon Dance.

Self-audit: good preservation framing. Needs exact player tool list and local
Dragon Dance damage evidence for a real move.

## Card 006: Lance Yanma Focus Band / Sleep Branch

Recommendation: deny Yanma with a line that prices Focus Band and Sleep Powder;
do not assign sleep to the final Dragonite answer unless forced. Confidence:
medium.

Plan: prevent Yanma from turning one survival or sleep turn into Quiver Dance
tempo while preserving the final setup answer.

State read: Yanma can Sleep Powder, Quiver Dance, attack, or survive one KO
through Focus Band. A single-hit KO line is not automatically stable if one
extra Yanma action changes the route.

Win condition: either remove Yanma through a line that tolerates Focus Band, or
route sleep into a piece whose future job remains functional.

Candidate ranking:

1. Multi-hit, phaze/Haze, priority follow-up, or status/control that covers the
   Focus Band branch: best if available.
2. Direct KO attempt: acceptable if Focus Band survival does not expose an
   irreplaceable piece to sleep or boost.
3. Sleep absorption by the only Dragonite answer: catastrophic unless every
   other route is already losing.

Worst plausible branch: Focus Band triggers, Yanma sleeps the only remaining
anti-setup answer, and Dragonite inherits a board with no clean denial.

What changes the answer: Sleep Clause used, multi-hit or priority available,
Yanma HP, phazing/Haze legality, the absorber's later job, or Focus Band already
spent.

Next turn if it works: after Yanma is removed or controlled, immediately update
which answer remains for Kingdra/Dragonite rather than spending it on the next
visible threat.

Self-audit: good branch pricing. Needs exact sleep mechanics and Focus Band
evidence only if a real battle line depends on them.

## Card 007: Red Pikachu Answer Reservation

Recommendation: use the lead or first move that handles Pikachu while keeping
the Snorlax/Espeon/sun/Blastoise answer map intact. Confidence: medium-low.

Plan: treat Pikachu as the first stress test, not the whole fight.

State read: Pikachu has Light Ball special coverage, high-crit Razor Leaf,
Surf for Ground/Rock answers, Thunderbolt pressure, and ExtremeSpeed as a
priority range check. ExtremeSpeed is not Light Ball-boosted locally, but it
still matters for later cleanup.

Win condition: remove or contain Pikachu without spending the only answer to
Red's later RestTalk Snorlax, screen/Calm Mind Espeon, sun starters, or
Blastoise Mirror Coat route.

Candidate ranking:

1. Flexible answer that survives Pikachu's special coverage and still preserves
   the later route map: best.
2. Aggressive KO/status line: acceptable if the lead's later jobs are
   redundant or the KO prevents ExtremeSpeed revenge.
3. Pure type-answer lead: bad if it loses to Surf, Razor Leaf, or critical-hit
   volatility and was needed later.

Worst plausible branch: the player wins the Pikachu exchange but chips,
paralyzes, or exposes the only Snorlax or Espeon answer; Red then pivots into
the real long-game route with the answer already damaged.

What changes the answer: duplicated Snorlax/Espeon answers, exact Pikachu
damage ranges, speed, whether the lead survives high-crit Razor Leaf, and
whether the lead remains outside ExtremeSpeed range after acting.

Next turn if it works: identify which Red route enters next and start that
ledger immediately: Reflect/Calm Mind, Curse/RestTalk, Sunny Day, or Mirror
Coat.

Self-audit: correct reservation framing, but exact advice requires the user's
team and damage evidence. Do not call a Ground or Rock answer safe from type
intuition alone.

## Card 008: Red Blastoise Mirror Coat Arbitration

Recommendation: do not fire the special attack by default. Choose special
damage only if it KOs, forces a decisive state, or Mirror Coat is tolerable;
otherwise use physical pressure, status/control, pivoting, or a controlled
sack. Confidence: medium-low.

Plan: make Blastoise's Mirror Coat branch part of the route score instead of
an afterthought.

State read: Blastoise has Surf, Earthquake, Blizzard, and Mirror Coat. It can
punish special attackers, but physical or pivot lines still have to respect its
coverage.

Win condition: deny Blastoise without losing the special attacker or pivot
needed for Espeon, Venusaur, Charizard, or Snorlax.

Candidate ranking:

1. Guaranteed special KO or special hit where Mirror Coat cannot decide the
   game: best if verified.
2. Physical/status/control line: best when it avoids Mirror Coat and still
   changes Blastoise's route.
3. Blind special nuke: bad if Mirror Coat removes an irreplaceable piece.
4. Passive switch: bad if the switch-in loses to Surf/Blizzard/Earthquake and
   gives Blastoise free progress.

Worst plausible branch: the user clicks the obvious special damage, Blastoise
uses Mirror Coat, and the piece needed for the remaining Red route is removed.

What changes the answer: exact Blastoise HP, Mirror Coat execution evidence,
boss AI trace/source likelihood, special KO range, whether the special attacker
is replaceable, and whether a physical/status line actually forces progress.

Next turn if it works: if Blastoise is forced or weakened, preserve the piece
needed for the route Red can still bring in. If Mirror Coat was scouted or
spent, re-rank special damage from the new state.

Self-audit: good branch separation. Needs local trace evidence before treating
Mirror Coat as likely rather than merely severe.

## Card 009: Pryce Dewgong Encore / Spin Turn

Recommendation: attack Dewgong or pivot to the verified spin punisher rather
than clicking a passive hazard/setup/recovery move. Confidence: medium-low
without the user's actual team.

Plan: convert the hazard plan from "layers exist" into "Dewgong cannot erase or
Encore them for free," while preserving answers to Sneasel, Piloswine, and
Slowking.

State read: Dewgong has Rapid Spin and Encore, so a support move can fail in two
ways: the hazards disappear, or the last executed move becomes a forced 3-6
turn sequence that gives Pryce a receiver or stabilization turn. Dewgong's Surf
and Ice Beam also mean a pivot must be a real entry, not just a type slogan.

Win condition: keep or regain hazard pressure only if spin is punished, or
shorten the game by damaging Dewgong before Pryce's later cleaners inherit the
hazard/Encore tempo.

Candidate ranking:

1. Attack Dewgong or use the move that forces its spin/Encore turn to cost HP,
   status, or position: best when it crosses a KO, Rest, or switch threshold.
2. Pivot to a spin punisher or route piece: acceptable if the entry survives
   Surf/Ice Beam and is not the only later Sneasel/Piloswine answer.
3. Set another hazard layer: acceptable only with a named spin punish or if the
   layer immediately changes a KO/Rest/phaze route before spin.
4. Passive setup/recovery/support: bad if Encore locks it and Pryce gets free
   spin, receiver entry, or Slowking stabilization.

Opponent's best route: remove hazards with Rapid Spin or lock a passive last
move with Encore, then hand the improved board to Sneasel/Piloswine cleanup or
Slowking stabilization.

Worst plausible branch: the player sets or repeats a support move, Dewgong
Encores it, spins the hazard plan away or forces the player to switch through
Pryce's pressure, and the preserved answer map is now worse for the later route.

What changes the answer: exact Dewgong HP, whether the current layer already
creates a route threshold, a healthy spinblocker/punisher, current active's
later job, speed order, last executed move and PP, and whether switching costs
more than spending Encore turns.

Next turn if it works: if Dewgong is damaged or forced, immediately choose
between rebuilding hazard pressure and preserving the specific answer to the
next Pryce route. If Dewgong spins or Encores anyway, re-score from that board
instead of continuing the hazard script.

Self-audit: this answer finally applies the Encore recipe to a local boss
state. Exact move confidence still needs the user team, Dewgong HP, current last
move, and local damage evidence.

## Card 010: Blaine Ninetales Weather / Safeguard Posture

Recommendation: if Ninetales can be forced or heavily damaged now, pressure it
before Sunny Day or Safeguard owns the next five turns; if that pressure does
not change the route, pivot or stall the clock while preserving the real Fire
answer. Confidence: medium-low without team and damage evidence.

Plan: keep Blaine from turning one Ninetales turn into a shared weather/status
window for Rapidash, Arcanine, and Magmar.

State read: Ninetales threatens Sunny Day, Fire Blast, Psychic, and Safeguard.
The dangerous part is not only this matchup; it is what happens after sun
boosts Fire pressure, Safeguard blocks status, hazards add entry tax, and
priority users inherit chipped targets.

Win condition: either deny the field clock before it starts, or make Blaine
spend the sun/Safeguard turns without losing the piece that answers the later
Fire attacker.

Candidate ranking:

1. Direct pressure that forces Ninetales out, KOs, or prevents the field-clock
   payoff: best if it changes the next board and does not spend the only Fire
   answer.
2. Weather/status denial or immediate status before Safeguard: good if it
   interrupts Blaine's route and the miss/fail branch is tolerable.
3. Pivot to the Fire answer: acceptable only if the answer remains above
   hazard, Fire Blast, Quick Attack, ExtremeSpeed, and Magmar coverage ranges.
4. Stall or wait: acceptable only when the clock is contained and Ninetales
   cannot hand a clean turn to Rapidash, Arcanine, or Magmar.
5. Water/status autopilot: bad if Sunny Day or Safeguard has already made that
   route weaker or unavailable.

Opponent's best route: use Ninetales to create sun or Safeguard, then let a
later Fire attacker convert while the player's old Water/status plan is
outdated.

Worst plausible branch: the player makes the clear-weather safe play, Ninetales
sets Sunny Day or Safeguard, Magcargo's Spikes or Blaine's priority puts the
Fire answer into range, and the team is forced to take a risky line one turn
later from a worse position.

What changes the answer: current sun/Safeguard turns, Magcargo Spikes layers,
Ninetales HP, exact Fire answer HP, whether Water damage still crosses a route
threshold under sun, weather replacement, safe Protect/recovery, phazing/Haze,
priority ranges, and Magmar Hidden Power evidence.

Next turn if it works: if Ninetales is denied, re-score which later Fire route
is most urgent. If sun or Safeguard goes up, start the five-turn ledger and
choose whether to burn turns, pivot, or take a forced conversion risk.

Self-audit: this answer uses Smogon risk posture correctly: conservative play
is best only if it preserves a winning route; if the "safe" pivot only lets the
weather clock become decisive, it is not actually safe. Exact confidence needs
damage and user-team evidence.

## Card 011: Janine Explosion Trade Into Breaker Route

Recommendation: keep the Nidoking/Venomoth answer out of the Explosion line
unless trading it immediately wins a stronger route; attack, pivot to a
lower-value absorber, or sacrifice for clean entry based on which post-boom map
is best. Confidence: medium-low without the user's actual team.

Plan: prevent Janine from using Qwilfish or Weezing as a one-time converter that
removes the exact piece needed for Nidoking or Venomoth.

State read: Qwilfish and Weezing are not isolated threats. Their Explosion
value depends on whether the player has already identified the true Nidoking and
Venomoth answers, whether Tentacruel can erase hazards or boosts afterward, and
whether Muk can turn weak chip into a RestTalk reset.

Win condition: either remove or force the exploder before it trades into the
critical answer, or let an expendable piece absorb the trade so the real answer
enters the remaining route map intact.

Candidate ranking:

1. Attack or status/control the exploder if it prevents Spikes/coverage/boom
   from opening the backline route: best when it changes the next board.
2. Pivot to a lower-value boom absorber: good if that piece has no live job
   against Nidoking, Venomoth, Muk, or Tentacruel.
3. Controlled sacrifice for clean entry: acceptable if the next Pokemon forces
   progress and the sacrificed role is accounted for.
4. Hard switch the only Nidoking/Venomoth answer into the exploder:
   catastrophic unless the trade itself creates an immediate win.
5. Set hazards or setup: bad if Tentacruel resets the state or Explosion removes
   the piece that was supposed to convert it.

Opponent's best route: trade Explosion into the player's specific answer, then
let Nidoking coverage or Venomoth sleep/setup inherit a team with no clean
denial.

Worst plausible branch: the player chooses the sturdy answer because it
survives the current hit, Janine explodes, and the answer that mattered for the
remaining boss route is now gone or too low; the next turn is spent reacting to
Nidoking or Venomoth from a broken map.

What changes the answer: whether the current active is truly irreplaceable,
which backup answers remain for Nidoking and Venomoth, exact Explosion and
coverage damage, hazard layers, Tentacruel spin/Haze status, Muk's Rest cycle,
and any local immunity/resistance/protection evidence.

Next turn if it works: after the trade is denied or absorbed, rebuild the route
map immediately. If Nidoking enters, verify local type/passive/damage evidence
for the pivot. If Venomoth enters, price Sleep Powder and Quiver Dance before
any passive move.

Self-audit: this applies the GSC Explosion lesson as role accounting, not as a
species slogan. Exact move confidence needs current HP, damage, and the user
team's real Nidoking/Venomoth answer map.

## Card 012: Morty Destiny Bond / Temporary Control Turn

Recommendation: do not automatically take the Gengar KO. If Destiny Bond is
active or highly incentivized and the attacker is still needed, use a non-KO
move, switch, status/control, or lower-value sacrifice that keeps the remaining
Ghost route covered. Confidence: medium-low without exact state evidence.

Plan: remove or contain Gengar without letting Destiny Bond turn the only clean
Ghost answer into a trade, while keeping enough material for the second Haunter
or any active sleep/Curse clock.

State read: Morty wins by turning temporary control into route value: Hypnosis
into Dream Eater or Curse, Misdreavus into Toxic/Pain Split turns, and Gengar
into Destiny Bond timing. Low HP on Gengar is bait if the KO removes the answer
that still has to handle the rest of the fight.

Win condition: preserve one awake, healthy Ghost answer and cash out any sleep,
confusion, or Curse state before it resets or trades into a worse map.

Candidate ranking:

1. Non-KO control or switch that burns/clears Destiny Bond while preserving the
   main Ghost answer: best if Gengar cannot punish it with coverage into the
   same loss.
2. Take the KO: best only if Destiny Bond is inactive/cleared, the attacker is
   expendable after the KO, or the trade gives a forced win.
3. Lower-value sacrifice: acceptable if it absorbs the trade and gives clean
   entry to the real Gengar/Haunter answer.
4. Passive setup or status: bad if it lets Gengar attack, or if Curse/Toxic/
   Pain Split clocks are already beating the player.

Opponent's best route: invite the obvious KO into Destiny Bond, or use the
player's hesitation to attack with Shadow Ball / Thunderbolt / Psychic while
the earlier temporary-control clocks keep ticking.

Worst plausible branch: the player KOs Gengar with the only clean Ghost answer,
Destiny Bond trades it, and the remaining Haunter or active Curse/sleep state
forces the damaged backup into a losing route.

What changes the answer: whether Destiny Bond is currently active, speed/order,
Gengar's PP and HP, exact KO range, whether the attacker is needed afterward,
backup Ghost answer status/HP, active Curse or sleep state, and Focus Band
availability on the remaining Haunter.

Next turn if it works: if Gengar is removed without losing the clean answer,
immediately re-score the second Haunter and any active control clocks. If the
trade happens, rebuild the route map before spending the next sacrifice.

Self-audit: this is the same temporary-control principle as sleep setup, but
applied to the opposite temptation: the board looks solved by a KO, yet the
trade state can make the KO strategically wrong.

## Card 013: Koga Poison / Trap Clock Ownership

Recommendation: if the current active is the Nidoking or Crobat answer, pivot
or force immediate progress before Ariados/Umbreon turns it into a poisoned or
trapped timer; if the current active is expendable, spend its remaining turns
to damage, deny Tentacruel, or create clean entry. Confidence: medium-low
without the user's team.

Plan: make Koga's early clock land on a piece whose job can be spent, while
preserving the real answers to Nidoking and Crobat.

State read: Koga's slow moves are not passive. Spikes, Toxic, Spider Web,
Confuse Ray, Pursuit, Moonlight, Curse, Rest, Rapid Spin, and Haze all decide
whether the next three turns belong to the player or to Koga. A poisoned or
trapped answer may still look alive while its future role is already gone.

Win condition: either short-circuit the clock with direct pressure, or convert
the poisoned/trapped piece before Nidoking or Crobat inherits the damaged map.

Candidate ranking:

1. Direct pressure or control that prevents the clock from landing on an
   irreplaceable answer: best if it forces Ariados/Umbreon/Tentacruel to spend
   a losing turn.
2. Pivot before Toxic/Spider Web/Pursuit locks the wrong piece: best when the
   current active is needed later.
3. Use an expendable poisoned/trapped active to force damage, hazards, status,
   or clean entry: good when its future job is already gone.
4. Wait or low-effect move: acceptable only if the current clock is already
   winning and Koga cannot spin, Haze, Rest, Moonlight, trap, or enter a
   cleaner.
5. Generic Toxic/hazard/setup: bad if Tentacruel resets it or if Muk/Umbreon
   recover while Crobat/Nidoking become easier to finish.

Opponent's best route: land poison, trap, hazards, or confusion on the piece
that must answer Nidoking/Crobat, then use Tentacruel, Muk, or Umbreon to keep
the clock favorable until Crobat can clean.

Worst plausible branch: the player treats Toxic or Spider Web as minor because
the current matchup is still playable, but the trapped/poisoned Pokemon was the
only real answer to Crobat or Nidoking; by the time the cleaner enters, that
answer has no safe entry or HP budget left.

What changes the answer: current active's later job, hazard layers, poison
state, Spider Web state, Tentacruel HP and spin/Haze access, Muk Curse/Rest
state, Umbreon Moonlight/Pursuit pressure, Crobat damage range, and local
type/passive evidence for Nidoking coverage.

Next turn if it works: if the clock is denied, re-score whether Tentacruel,
Muk, Nidoking, or Crobat is the live route. If the clock lands, schedule the
remaining entries for the affected Pokemon instead of pretending it remains a
full-strength answer.

Self-audit: this answers the Koga route sheet's central question: who owns the
next three turns? It still needs exact user roster and damage data before an
exact move can be named.

## Card 014: Jasmine Set-Retain-Convert Hazard War

Recommendation: do not choose a hazard move until the retain and convert steps
are named. If Forretress can spin for free or the Scizor answer is being chipped
into cleanup range, attack, spin, pivot, or preserve the answer instead.
Confidence: medium-low without the user's actual team and layer state.

Plan: stop Jasmine from turning a small hazard exchange into phaze cycles,
Explosion value, or Scizor cleanup.

State read: Jasmine's hazard game is two-sided. Magneton and Skarmory can set
layers, Forretress can remove the player's layers while threatening Toxic,
Protect, and Explosion, and Steelix/Skarmory can convert layers through forced
switches. Scizor punishes any line that chips or statuses its answer.

Win condition: either keep hazards only long enough to create a real threshold,
or remove/deny Jasmine's layers before Roar, Whirlwind, and Scizor turn them
into a route.

Candidate ranking:

1. Pressure the setter/spinner/phazer directly: best if it prevents the hazard
   route from compounding or forces Forretress to spin/protect/trade at a cost.
2. Spin or remove Jasmine's hazards: best when Roar/Whirlwind or Scizor cleanup
   makes every grounded entry worse.
3. Set or preserve our hazards: good only if there is a retention plan and a
   conversion target before Forretress spins.
4. Pivot to preserve the Scizor/Steelix answer: good if staying in invites
   Toxic, Thunder Wave, Explosion, Rocky Helmet recoil, or phaze chip on that
   answer.
5. Passive setup or extra layer: bad if Forretress resets the route or Scizor
   uses the turn to become live.

Opponent's best route: get a layer down, keep Forretress healthy enough to deny
the player's hazards, then use Steelix/Skarmory phazing or Scizor Swords Dance
after the player's answer has been chipped.

Worst plausible branch: the player wins a visible hazard turn but loses the
Scizor answer to Toxic, paralysis, Explosion, contact recoil, or repeated
phazing; Jasmine then needs only one Swords Dance or Roar cycle to convert.

What changes the answer: current layer count on both sides, grounded teammates,
Forretress HP and Explosion threat, whether our hazards create an immediate
threshold, Scizor answer HP/status, Steelix/Skarmory phazing access, contact
flags for Rocky Helmet, and local type/passive evidence for the intended pivot.

Next turn if it works: if hazards are retained, cash them out immediately with
damage, phazing, forced switch, or KO threshold. If hazards are removed, re-rank
the next live Jasmine route instead of continuing a hazard script.

Self-audit: this applies the hazard article lesson in local form: hazard value
is not the layer itself; it is the set-retain-convert chain and the piece that
survives to use or deny it.

## Card 015: Bugsy Support Chain Into Scyther

Recommendation: deny Ledian's pass or preserve the supported-Scyther answer;
do not spend that answer winning the visible Ledian/Ariados exchange unless the
support chain is broken immediately. Confidence: medium-low without the user's
team and damage data.

Plan: stop Bugsy from turning low-damage support into a Scyther board where the
player's only answer is poisoned, chipped, or absent.

State read: Ledian's damage is not the threat. Reflect, Quiver Dance, and Baton
Pass can change Scyther's entry and survival math, while Ariados Toxic can tax
the exact answer that is supposed to stop Scyther later.

Win condition: either remove the support path before Scyther receives it, or
keep the Scyther answer healthy enough to handle the supported state.

Candidate ranking:

1. Attack or control Ledian before Baton Pass matters: best if it prevents the
   supported Scyther state or forces Scyther in unsupported.
2. Pivot or preserve the Scyther answer: best when the current active is the
   only piece that can survive supported Scyther.
3. Haze/phaze/status: strong if legal, timely, and it actually disrupts the
   pass or receiver before conversion; it still needs a named endpoint.
4. Set up or use hazards: bad if the pass reaches Scyther first and the answer
   map is not preserved.
5. Trade the Scyther answer for Ariados/Ledian chip: catastrophic unless the
   resulting Scyther state is already covered by another piece.

Opponent's best route: use Ledian or Ariados to deliver Reflect, Speed/special
bulk, poison, or chip, then enter Scyther with enough support to set up or
clean with priority.

Worst plausible branch: the player treats Ledian as harmless, sets up or
attacks for chip, Baton Pass delivers support, and Scyther enters while the only
answer has already been poisoned or spent.

What changes the answer: whether Baton Pass can occur before Ledian is removed,
active Reflect turns, Quiver Dance boosts, Scyther HP/item/damage ranges,
whether phazing/Haze is legal and fast enough, Ariados poison state, and whether
the player has a second Scyther answer.

Next turn if it works: if the chain is broken, re-score whether Scyther enters
unsupported and can be removed directly. If support lands, abandon the old
one-on-one plan and evaluate the supported Scyther state from scratch.

Self-audit: this trains receiver-first thinking. The move is not selected by
"who wins the current matchup"; it is selected by whether Scyther receives a
board it can convert. After the `STP-048` update, the control line also needs
an endpoint: reset is only good if the next turn removes Ledian, damages
Scyther, preserves the answer, or otherwise stops the chain from restarting.

## Card 016: Will Slowbro Rest / Amnesia Anchor

Recommendation: force Slowbro's Rest only if the sleep turns are convertible;
otherwise deny Amnesia, pivot to the real breaker, or preserve the special
answer for Will's next route. Confidence: medium-low without the user's team
and damage evidence.

Plan: stop Slowbro from turning weak chip into an Amnesia/Rest reset while
keeping the Alakazam, Houndoom, and Xatu answer map intact.

State read: Slowbro is a Rest anchor, not a RestTalk anchor. In this local
moveset it has Amnesia, Surf, Psychic, and Rest, so the sleep turns are more
punishable than Red Snorlax's Sleep Talk turns, but only if the player has a
real conversion move ready.

Win condition: create a Rest turn that gives safe entry, phazing/Haze, setup,
hazards, status timing, or a KO threshold; if that cannot happen, avoid feeding
Slowbro a reset while Will's special attackers inherit the damaged board.

Candidate ranking:

1. Physical pressure, phazing/Haze, status timing, or breaker entry that forces
   or punishes Rest: best when the follow-up is named.
2. Attack to force Rest: good only if the Rest turn creates a concrete next
   action before Slowbro wakes.
3. Pivot or preserve the special answer: good when damage into Slowbro is
   erased and Alakazam/Houndoom/Xatu remain unsolved.
4. Set hazards: good only if they convert through forced entries and Starmie
   cannot spin them for free.
5. Special chip after Amnesia: bad unless it still crosses a KO, Rest, PP, or
   safe-entry threshold.

Opponent's best route: boost with Amnesia, absorb weak chip, Rest at the right
time, then leave the player with a poisoned/chipped answer for Alakazam,
Houndoom, or Xatu.

Worst plausible branch: the player forces Rest with no punish, Slowbro resets
the damage race, and the turns spent attacking leave the actual special answer
too damaged or poisoned for Will's next route.

What changes the answer: Slowbro boosts, HP and Rest PP, whether Starmie can
spin hazards, current hazards, available Haze/phazing, physical breaker entry,
status timing before Rest, Forretress Toxic/Explosion damage, and which
Alakazam/Houndoom/Xatu answer remains healthy.

Next turn if it works: if Slowbro Rests and no Sleep Talk exists, use the first
sleep turn immediately: enter the breaker, phaze/Haze, set the converting
hazard, or force the KO route. If there is no converting action, rebuild around
preservation instead of repeating chip.

Self-audit: this is the Rest-cycle distinction the notebook needs. Sleeping is
not automatically free, but Rest-only and RestTalk anchors have different
branch trees and must not be conflated.

## Card 017: Will Future Sight / Pursuit Resolution Turn

Recommendation: if Xatu can be denied before Future Sight starts, pressure or
control it now. If Future Sight is already active, schedule the landing turn
first: keep the Houndoom/Alakazam/Slowbro answer off the bad resolution turn,
and do not switch into Houndoom's Pursuit unless that branch is already priced.
Confidence: medium-low without exact HP, speed, damage, and remaining roster.

Plan: turn Future Sight from an unmanaged delayed hit into a ledger entry with
a named absorber, while preventing Houndoom from punishing the escape route.

State read: Xatu's Future Sight is not just delayed Psychic flavor in this
hack. The local move table lists it as 120 BP, 90 accuracy, Psychic, special,
and non-contact, while the delayed-resolution source stores damage and later
sets the type modifier to effective. That means the important question is not
"which type resists Psychic?" It is "which Pokemon is active when the stored
damage lands, and what can Will stack on that turn?"

Win condition: either prevent Future Sight from entering the ledger, or make
the landing turn hit a Pokemon whose job can be spent without opening
Houndoom, Alakazam, Slowbro, Starmie, or Forretress.

Candidate ranking:

1. Immediate pressure or control on Xatu before Future Sight starts: best when
   it removes Xatu, prevents the ledger, or forces a clean non-Future Sight
   exchange despite Focus Band risk.
2. Stay or spend an expendable active through the landing turn: best when a
   switch would expose the real Houndoom/Alakazam/Slowbro answer to Pursuit or
   stacked damage.
3. Scheduled pivot to the chosen absorber: good only when the absorber survives
   the stored hit plus the current threat and still preserves the remaining
   Will route map.
4. Heal, status, phaze, or Haze: useful if it changes the resolution turn or
   prevents Xatu/Houndoom from converting; bad if it only spends time while the
   wrong Pokemon remains scheduled to take Future Sight.
5. Blind switch to the apparent Psychic answer: bad when local Future Sight
   behavior, Pursuit, Sunny Day / Flamethrower, or a Focus Band survival makes
   that switch the route Will wants.

Opponent's best route: start Future Sight, then use Xatu's current attacks or
Houndoom's Crunch / Flamethrower / Sunny Day / Pursuit to force the player into
choosing between taking stacked damage and fleeing into Pursuit.

Worst plausible branch: the player KOs or damages Xatu and treats the exchange
as solved, but Future Sight was already stored; on the landing turn the only
Houndoom or Alakazam answer is active, switches out, and gets punished by
Pursuit or leaves the next Will attacker a clean entry.

What changes the answer: whether Future Sight has already been used, its
countdown, Xatu HP and Focus Band status, Houndoom availability, current switch
flags, the player's expendable pieces, hazards, weather, exact damage on
Future Sight / Psychic / Drill Peck / Night Shade / Pursuit, and whether the
intended absorber is still needed for another Will route.

Next turn if it works: after the landing turn is scheduled, play the current
turn normally against Xatu or Houndoom. If Xatu survives through Focus Band or
Houndoom enters, rebuild the ledger immediately instead of following the old
attack-or-switch script.

Self-audit: this applies the delayed-effect lesson without importing generic
Future Sight mechanics. Smogon Future Sight / Doom Desire material supplies the
two-attacks-one-turn pressure idea, and GSC Houndoom material supplies the
Pursuit incentive model; local source decides the actual Future Sight and
Pursuit behavior.

## Card 018: Brock Golem Explosion Execution Gate

Recommendation: do not call Explosion a live trade until the execution gate is
clear. If the active player Water/Grass attack is faster and KOs, attack Golem
now. If Golem can move first, the attack does not KO, or the player is likely
to switch/heal/setup, price Explosion as a route trade and preserve the
Kabutops/Aerodactyl answer. Confidence: medium without exact Speed and damage.

Plan: remove Golem before it converts Rocky Helmet chip, Curse pressure, or
Explosion into Brock's later route, while avoiding a trade that deletes the
only remaining answer to Kabutops, Onix, or Aerodactyl.

State read: Brock's Golem has `Curse / Earthquake / Rock Slide / Explosion`
and Rocky Helmet. Local Explosion is `EFFECT_SELFDESTRUCT`, 250 BP, 100
accuracy, base priority, and halves target Defense during damage calculation.
It does not interrupt a faster KO. Local Protect/Endure are priority 3, but
Protect has consecutive-use failure odds and only matters if it changes the
trade branch.

Win condition: either KO Golem before Explosion can execute, or make Explosion
hit an expendable target while preserving the piece that handles Brock's
remaining setup, hazard, and cleaner routes.

Candidate ranking:

1. Faster confirmed KO into Golem: best when the damage removes Golem before it
   moves and the next Brock send-out is covered.
2. Protect or scout: good when Explosion is incentive-compatible, Golem can act
   before the player's KO, or the player needs one turn of information; bad if
   attacking already prevents the trade.
3. Pivot to an expendable or resistant piece: good when the active is the only
   Kabutops/Aerodactyl answer and cannot afford Explosion.
4. Status, setup, weak chip, or recovery: poor if it lets Golem Curse or
   Explode before the player has named the post-trade board.
5. Blind preserve-everything switch: poor if it gives Brock a free Curse,
   Spikes/Roar handoff, or Aerodactyl cleanup route.

Opponent's best route: force the player to respect Explosion long enough to
gain Curse damage, Rocky Helmet contact value, or a one-for-one into the only
piece that stops Kabutops, Onix, or Aerodactyl.

Worst plausible branch: the player treats "Golem is low" as solved, uses a
non-KO or contact move, and Golem trades Explosion into the only remaining
Rock-team answer; or the player over-scouts with Protect while a clean faster
KO was available and Brock uses the turn to Curse or switch.

What changes the answer: exact Speed, paralysis, Quick Claw-like effects,
damage range, whether Protect/Detect is revealed and usable, consecutive
Protect count, Golem HP, whether the active move makes contact into Rocky
Helmet, remaining Brock roster, and whether the player has another Kabutops or
Aerodactyl answer.

Next turn if it works: if Golem is removed without a trade, immediately
re-score Brock's likely send-out: Kabutops setup, Onix Spikes/Roar, Aerodactyl
cleanup, Corsola spin/recovery, or Omastar hazards. If Explosion resolves,
rebuild from final material before spending the next one-time resource.

Self-audit: this card prevents a common bad shortcut in boss advice. Explosion
is a route trade only after priority, Speed, KO range, Protect, target choice,
and remaining material have all been priced.

## Card 019: Phazing Target-Pool Gate

Recommendation: count target pool first, then timing, then route value.
Confidence: medium with public bench evidence; low if the player bench state is
hidden or inferred.

Plan: prevent hazard-plus-phaze advice from continuing after the forced-switch
mechanic no longer has a legal target, while still recognizing that a real
bench plus Spikes can make Roar / Whirlwind decisive.

State read: Jasmine, Pryce, Bruno, and Chuck all have local phazing routes that
combine Roar / Whirlwind with Spikes, setup denial, and answer-map disruption.
The local command fails if there is no living non-active target, and Gen 2
timing still matters.

Win condition: use phazing only while it creates a better next board: hazard
damage on a real switch-in, reset of a live setup route, forced reveal, or a
preserved answer map. Once the opponent is last Pokemon, hand off to direct
damage, status timing, recovery, setup, PP, Focus Punch denial, or a trade.

Candidate ranking:

1. Phaze: best if a public living bench target exists, the phazer acts last,
   hazards or setup pressure make the drag valuable, and the post-drag target
   map is acceptable.
2. Attack or coverage pressure: best if the target is last Pokemon, phazing
   would fail, or the active is already in KO / Rest / Focus Punch denial range.
3. Status: good only if it beats the target's reset map; bad if Rest, cure, or
   immediate KO erases it before it changes the route.
4. Recover, preserve, or pivot: good if the phazer is still needed later and
   the current phaze is not legal or not valuable.
5. Blind Roar / Whirlwind: bad when it relies on hidden bench knowledge, acts
   too early, or has no legal target.

Opponent's best route: exploit the advisor's stale hazard script. If the player
is last Pokemon, every failed Roar / Whirlwind gives a free attack, Rest,
status reset, or setup turn. If the player still has a bench, every valid phaze
can convert Spikes into lost answers.

Worst plausible branch: the boss or player spends a critical turn on Roar /
Whirlwind after the target pool is gone, then loses to the active Pokemon's
damage or recovery loop; or refuses to phaze with Spikes up while a legal bench
target and live setup route are both public.

What changes the answer: confirmed living non-active targets, revealed switch
history, observed faints, current hazard layers, Speed/order, paralysis,
Quick Claw-like effects, Sleep Talk calls, setup stages, phaze PP, and whether
the AI would be relying on hidden player-team knowledge.

Next turn if it works: if Roar / Whirlwind succeeds, immediately score the
dragged target's entry damage, revealed set, and answer-map change. If it
fails, stop treating phazing as the route and choose the active-board line.

Self-audit: this card is useful because it turns "phaze setup through Spikes"
into a mechanics-gated recommendation. It still needs a real player-team state
to become exact move advice.

## Card 020: Post-Converter Handoff After Breakthrough

Recommendation: rebuild the blocker map before choosing the next move.
Confidence: medium without exact player bench, HP, PP, and speed. If the old
converter removed the route blocker and a new closer is live, choose the move
that delivers that closer. If no closer remains, abandon the handoff and move
to emergency denial.

Plan: convert the first breakthrough into the next route instead of mourning
the fainted piece or continuing a stale script.

State read: the relevant fact is not "the converter died." It is what changed
before it died: spinner gone, phazer gone, Explosion spent, screen setter gone,
hazard layer retained, Rest forced, ace answer weakened, or speed-control
piece removed. The next move should preserve the piece that now wins, or remove
the last blocker to that piece.

Win condition: identify the new closer and make its entry/action realistic.
Examples: after Jasmine's Steelix falls, preserve the Scizor answer; after
Brock's Golem falls, check Kabutops/Aerodactyl before spending the Water
answer; after Janine's Qwilfish or Tentacruel is gone, preserve the
Nidoking/Venomoth answer; after Will's Forretress or Starmie is gone, avoid
poisoning or exploding the only special anchor; after Surge's support piece is
gone, cover Raichu/Electabuzz rather than chasing the old Magneton exchange.

Candidate ranking:

1. Deliver the new closer: best if its blockers are removed and it has the HP,
   PP, status state, speed, and entry path to act.
2. Preserve or recover the new closer: best if hazards, poison, weather,
   screens, or chip would otherwise make the route collapse.
3. Utility that serves the new closer: Rapid Spin, phazing, Haze, status,
   screen counting, or pivoting is good only when it changes the inherited
   route.
4. One-time trade or controlled sack: good when it removes the final blocker
   and leaves winning material; bad if it spends the closer or the only answer
   to the next boss ace.
5. Continue old converter script: bad if that piece is gone, paused, too low,
   or no longer the route owner.

Opponent's best route: punish stale planning. The boss can hand the board to
the surviving ace, spinner, phazer, screen user, Rest anchor, or Explosion
piece while the player keeps trying to revive the old plan.

Worst plausible branch: the player removes the opening blocker, then spends
the new closer into poison, Spikes, Explosion, Rocky Helmet contact, phazing,
or a coverage hit because the advice never rebuilt the route map.

What changes the answer: exact remaining boss roster, player bench, HP, PP,
status, hazard layers, screen turns, weather, speed/order, one-time resources,
and whether the perspective is player coaching or boss AI. Boss AI must not use
hidden player-team data to prove the handoff.

Next turn if it works: after the closer enters or the final blocker is removed,
stop and re-score the boss's best remaining route. A handoff is not permission
to autopilot the next three turns.

Self-audit: this card transfers the Vaporeon/Golem/Snorlax replay lesson into
boss-battle advice without importing vanilla mechanics as facts. Exact advice
still needs local damage, item, status, hazard, phazing, spin, Explosion, and
AI information-model evidence.

## Card 021: Whitney Rollout Reclassification Gate

Recommendation: Body Slam. Confidence: high for this public state.

Plan: use flexible pressure first, then consider Rollout only after paralysis,
HP, or answer removal makes the lock route favorable.

State read: Whitney's Miltank is active at 92% into a healthy, unstatused
Geodude. Public damage anchors say first Rollout is only 2-3 damage, while Body
Slam is 7-9 damage and can create the paralysis branch that makes later Rollout
safe. Geodude has Rock Throw revealed and Magnitude plausible, so locking early
gives up too much control before reducing the punish.

Win condition: keep Miltank as the route owner. Body Slam pressures Geodude,
preserves Milk Drink around the real danger threshold, and keeps Rollout for
the conversion state rather than the opener.

Candidate ranking:

1. Body Slam: best. It creates chip and paralysis pressure while preserving
   every future Miltank option.
2. Milk Drink: acceptable only if Miltank is near a real danger threshold. At
   92%, it delays the route.
3. Attract: state-dependent. It can be strong if gender applies and the route
   needs action denial, but it does not address the current Rock/Ground punish
   as directly as Body Slam.
4. Rollout: bad now. The first hit is tiny and the lock removes flexible
   recovery/status/switch timing before Geodude is paralyzed or low.
5. Switch: bad without a concrete reason; it gives up Miltank's pressure.

Opponent's best route: keep Geodude unstatused, attack with Magnitude if
available or Rock Throw otherwise, and punish any early lock before Whitney has
created paralysis or forced recovery.

Worst plausible branch: Body Slam does not paralyze, Magnitude is present and
rolls high, and Miltank falls near a real Milk Drink threshold. That branch
asks for recovery next, not turn-1 Rollout.

What changes the answer: Geodude already paralyzed, Geodude lower, Miltank
lower, confirmed no Magnitude, confirmed anti-lock move, gender/Attract
legality, or another player piece becoming public through a real switch.
Hidden player bench data does not change boss AI advice.

Next turn if it works: if Body Slam paralyzes or Geodude damage is shallow,
consider whether Rollout now has a safe conversion path. If Geodude deals
large damage, Milk Drink may become the route-preserving move before more
pressure.

Self-audit: this is a concrete local boss-turn answer. It uses the expert
reclassification lesson without importing Showdown Present damage and keeps
the no-Team-Preview boundary explicit.

## Run Findings

What improved:

- The answers stayed in move-class arbitration instead of species slogans.
- The best recommendations all named the resource being preserved: Starmie
  answer, anti-Gyarados route, Dragonite/Kingdra answer, sleep absorber, or
  Red's later-route answers.
- The strongest pattern was "answer labels change after entry, hazards, status,
  boosts, and route pressure."
- The Dewgong card added a concrete local case where a normally useful hazard
  or support move loses to spin/Encore unless the follow-up is already named.
- The Ninetales card added a local forced-risk posture case: weather and
  Safeguard can turn a clear-weather safe move into a losing line.
- The Janine card added a local Explosion/sacrifice test: a trade is good or
  bad by the remaining route map, not by the current active's HP.
- The Morty card added a local "obvious KO" trap: temporary control and Destiny
  Bond must be priced before trading the clean answer.
- The Koga card added a clock-ownership case: poison/trap/hazard progress is
  good only for the side that converts the next three turns.
- The Jasmine card added a two-sided hazard-war case: setting, spinning,
  protecting, or phazing is only good relative to the route it retains or
  converts.
- The Bugsy card added a receiver-first support-chain case: Ledian and Ariados
  are judged by what they deliver to Scyther, not by their damage.
- The Will card added a Rest-cycle distinction: Rest-only anchors and RestTalk
  anchors have different punish windows, and forcing Rest is only useful with a
  concrete conversion.
- The Xatu/Houndoom card added a delayed-pressure case: Future Sight is judged
  by the resolution turn and by whether Pursuit punishes the scheduled escape.
- The Brock Golem card added an execution-gate case: Explosion is a route trade
  only if it can actually move before a faster KO, Protect, switch, or other
  block invalidates it.
- The phazing target-pool card added a local force-switch gate: Roar and
  Whirlwind need both act-last timing and a living non-active target before
  they count as route control.
- The post-converter card added plan-revision practice: after the original
  route piece dies, list what it removed and deliver the next closer instead of
  continuing the old script.
- The Whitney card added exact boss-move advice: Body Slam first because
  Rollout is a conversion lock after status/HP changes, not a species slogan.

What remains weak:

- Exact confidence stays capped without player HP, moves, speed, and damage.
- These prompts still need real user-team variants so the recommendation can be
  an exact move, not a class.
- The drill does not yet punish bad candidate rankings automatically.

Next concrete training step:

- Convert one card into a full player-team drill using an actual available team
  or a recorded attempt, then score the move recommendation against the route
  map and observed outcome.
