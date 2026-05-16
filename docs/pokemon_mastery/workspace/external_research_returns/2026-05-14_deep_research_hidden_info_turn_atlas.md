# GSC No-Team-Preview Singles Training Corpus for a GSC-Based Romhack

## Methodology and source list

This corpus follows the user’s constraints closely: no public Team Preview, no later-generation mechanics, no romhack-specific mechanics assumed without evidence, and no future-turn spoilers inside the public state. Every **public_state** below is reconstructed only from what a strong player could know before the decision turn. Every **sealed_hidden_state** is either taken from explicit source commentary, from the source’s matchup analysis, or marked as uncertain where the source does not fully justify the inference. The point of the set is not to restate broad metagame wisdom; it is to isolate **move-changing** decisions under hidden information. The biggest limitation is source shape: some entries come from richly argued articles or forum analyses rather than raw replay logs, so not every replay-derived position has exact HP/PP granularity. I mark those cases plainly instead of inventing precision. citeturn2view0turn22view0turn26view0turn23search0turn37view0turn38view0turn41view0turn40view0turn29view0turn14view0

The source base is concentrated in high-value primary or quasi-primary GSC material: Jorgen’s **Playing with Spikes in GSC** and **Explosion in GSC**, Oglemi/havoc/Earthworm’s **Introduction to Status in GSC**, Borat’s long-form GSC guide, the approved **GSC Mechanics** resource, Siatam’s **GSC OU Sample Teams Breakdown**, high-level tournament discussion threads from SPL, and tournament recap writing that names specific GSC moments and replay URLs. Together they cover the exact skill zones the prompt asked for: Spikes and spin control, sleep discipline, Explosion timing, preservation, phazing, setup denial, Rest cycles, PP, and endgame conversion. citeturn22view0turn26view0turn23search0turn37view0turn38view0turn41view0turn40view3turn40view0turn29view0turn14view0

## Hazard, Rapid Spin, and spinblock positions

**P01**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, rapid-spin, spinblock, preservation`
**public_state:** Your Cloyster has established Spikes and the opponent brings in Starmie, the most common spinner.
**sealed_hidden_state:** The source’s matchup analysis says Cloyster has “almost no way” to keep Spikes against Starmie by itself, and that Misdreavus is the sturdier Starmie spinblocker compared with Gengar.
**candidate_moves_or_switches:** stay in and Surf; Toxic; explode; switch to Gengar; switch to Misdreavus.
**expert_move_or_recommended_line:** Prefer the Misdreavus switch if your plan actually depends on keeping Spikes down.
**why_this_move:** The source is explicit that Cloyster cannot really solo the Starmie war and that Misdreavus, not Gengar, is the safer Starmie spinblocker.
**worst_plausible_branch:** Staying in and playing “honest” leaves you losing the whole Spikes route for negligible progress.
**irreplaceable_piece_or_resource:** Spikes presence plus the only reliable Starmie spinblocker.
**information_that_would_flip_the_answer:** If Starmie is already poisoned and repeatedly forced to recover, or if your own route values immediate Starmie chip over long-term Spikes, the line can flip.
**transfer_to_romhack:** If your hazard plan hinges on one remover matchup, preserve the one answer that actually wins that subgame.
**do_not_transfer:** This lesson assumes vanilla GSC spinblocking and Starmie’s role, not Defog or later hazard stacks.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the opponent reveals the premier remover against your lone hazard setter, prefer the dedicated remover-answer, unless the game is short enough that one immediate trade wins.
**measurement_hook:** Check whether the trainee identifies that “keep Spikes” and “damage Starmie” are not the same objective. citeturn34view1turn25view1

**P02**
`source_url: https://www.smogon.com/forums/threads/gsc-mechanics.3542417/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, rapid-spin, legality, role-compression`
**public_state:** You need one slot to both remove Spikes and threaten a last-ditch Explosion later.
**sealed_hidden_state:** The approved mechanics thread lists **Cloyster Rapid Spin + Explosion** as illegal in vanilla GSC, while the Spikes article highlights that Forretress can combine Rapid Spin and Explosion on one set.
**candidate_moves_or_switches:** route through Cloyster as “spinner + boom”; use Forretress; use Starmie/Tentacruel and outsource boom.
**expert_move_or_recommended_line:** In vanilla assumptions, prefer Forretress or another legal structure; do not train on illegal Cloyster compression.
**why_this_move:** The move-choice lesson changes completely if the advisor imagines a non-existent Cloyster role.
**worst_plausible_branch:** The model learns to preserve or pivot a set that cannot exist on cartridge-accurate or standard-sim vanilla GSC.
**irreplaceable_piece_or_resource:** Correct role identity.
**information_that_would_flip_the_answer:** Local romhack evidence that Cloyster legally can run both moves.
**transfer_to_romhack:** Preserve role compression accuracy before you preserve the Pokémon.
**do_not_transfer:** Vanilla illegality should not be assumed true in a romhack without local movepool proof.
**mechanics_status:** locally_supplied_romhack_evidence_needed
**policy_trigger:** When a line depends on one Pokémon doing two jobs, prefer the legal role-compressor, unless local romhack evidence changes the movepool.
**measurement_hook:** Check whether the trainee rejects illegal Cloyster Spin + Explosion under vanilla status. citeturn34view1turn38view0

**P03**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, preservation, scouting, setup-denial`
**public_state:** Your Forretress gets a seemingly free entry on a mixed attacker or Exeggutor-like target and can Spikes, Spin, attack, or pivot.
**sealed_hidden_state:** The source stresses that Forretress fears surprise Fire moves enough that it must scout before assuming a safe setup turn.
**candidate_moves_or_switches:** click Spikes; click Rapid Spin; attack; scout with a safer pivot.
**expert_move_or_recommended_line:** Scout first when the opponent plausibly carries Fire tech.
**why_this_move:** Forretress wins long hazards games only if it survives; losing it to an unscouted Fire move collapses both your remove and keep-Spikes plan.
**worst_plausible_branch:** Taking the “obvious” Spikes turn and losing your entire hazard structure instantly.
**irreplaceable_piece_or_resource:** Forretress longevity.
**information_that_would_flip_the_answer:** Hard set information that the target lacks Fire coverage.
**transfer_to_romhack:** Hazard setters that also remove hazards are too valuable to gamble away on ambiguous coverage.
**do_not_transfer:** This is not a general anti-setup rule; it is specifically about GSC Forretress risk and hidden coverage.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your hazard controller faces an opponent with meaningful hidden coverage risk, prefer scouting, unless confirmed information makes the greed line clean.
**measurement_hook:** Check whether the trainee values role preservation over one “free-looking” layer. citeturn34view1

**P04**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, status, rapid-spin, patience`
**public_state:** The opponent’s Starmie or Cloyster is trying to control Spikes over repeated switch cycles.
**sealed_hidden_state:** The source argues Toxic is the most reliable status against Starmie, while paralysis and sleep are less dependable because Starmie evades them well and lacks Natural Cure in GSC.
**candidate_moves_or_switches:** fish for paralysis; attempt sleep; Toxic; hard double to punish spin.
**expert_move_or_recommended_line:** Prefer Toxic if your goal is to win the long hazard war.
**why_this_move:** Poison forces recover loops and turns future spin attempts into resource squeezes; flashy para/sleep lines are less reliable against Starmie specifically.
**worst_plausible_branch:** Burning turns on low-probability status plans while Starmie keeps spinning freely.
**irreplaceable_piece_or_resource:** Time and long-run spin pressure.
**information_that_would_flip_the_answer:** If Starmie is already slowed or your team can immediately convert one paralysis into a kill, the answer can flip.
**transfer_to_romhack:** Against the best remover, the right status is the one that changes its future menu, not the one that looks strongest on paper.
**do_not_transfer:** Do not import Natural Cure assumptions or later-gen anti-status expectations.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When trying to beat a durable remover over many turns, prefer the status that constrains recovery timing, unless you can convert a faster status into immediate material.
**measurement_hook:** Check whether the trainee chooses Toxic over prettier but weaker anti-Starmie plans. citeturn34view3turn34view4

**P05**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, rapid-spin, speed-control, pursuit-support`
**public_state:** Your Icy Wind Cloyster expects Starmie to switch in on Spikes and Rapid Spin.
**sealed_hidden_state:** The source gives the exact tactical sequence: set Spikes as Starmie enters, use Icy Wind as it Spins, then exploit the speed drop so Tyranitar or another slower anti-spinner can operate from advantage.
**candidate_moves_or_switches:** raw Explosion; Surf; Toxic; Icy Wind; immediate Tyranitar double.
**expert_move_or_recommended_line:** Use Icy Wind on the spin turn if the route is “keep Spikes and trap later,” not “trade now.”
**why_this_move:** It turns a losing speed matchup into a winning one and makes later Pursuit or Explosion lines far cleaner.
**worst_plausible_branch:** Exploding too early or attacking for chip while Starmie remains structurally in control.
**irreplaceable_piece_or_resource:** Speed control over the spinner.
**information_that_would_flip_the_answer:** If Starmie is already poisoned into Recover range, immediate Explosion can be superior.
**transfer_to_romhack:** Temporary speed manipulation can be a resource bridge that converts a bad remover matchup into a good one.
**do_not_transfer:** This is not a later-gen hazard stack lesson; it is built around one-layer Spikes and GSC speed control.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a bad remover matchup can be converted by tempo and speed, prefer the enabling line, unless an immediate trade is already winning.
**measurement_hook:** Check whether the trainee sees Icy Wind as a route-creating move rather than “weak damage.” citeturn35view0turn35view1

**P06**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, explosion, bait, trade-management`
**public_state:** Your Steelix is in against a target that strongly invites Starmie or Cloyster.
**sealed_hidden_state:** The source explicitly says Steelix often baits those Water-types and can survive Surf from both at full health, so Explosion does not have to be only a blind on-switch gamble.
**candidate_moves_or_switches:** Curse; Earthquake; double switch; Explosion.
**expert_move_or_recommended_line:** If removing the spinner unlocks your broader route, Explosion is the expert default once the bait is set.
**why_this_move:** In GSC, hazard wars often hinge on one remover; deleting it cleanly is worth more than local board prettiness.
**worst_plausible_branch:** Taking a cute noncommittal line and letting the remover live long enough to reset the entire game.
**irreplaceable_piece_or_resource:** The opponent’s spinner.
**information_that_would_flip_the_answer:** If Steelix is still your only crucial Normal resist or Electric pivot, the trade may be too expensive.
**transfer_to_romhack:** When a support mon baits the one piece that invalidates your route, proactive trade conversion is often correct.
**do_not_transfer:** This assumes vanilla Explosion power and Steelix’s GSC role.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your bait piece invites the single best answer to your residual route, prefer the conversion trade, unless that bait piece is still more valuable alive than the target is dead.
**measurement_hook:** Check whether the trainee values the remover kill over incremental Steelix development. citeturn35view0turn26view0

**P07**
`source_url: https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, preservation, role-identity`
**public_state:** Your Cloyster has already set Spikes and now has a chance to take an aggressive trade.
**sealed_hidden_state:** The sample-team writeup says Cloyster’s primary job is not merely to get Spikes up; it is also to stay healthy enough to **keep** them up if the opponent can remove them.
**candidate_moves_or_switches:** explode now; attack; rest; pivot out and preserve.
**expert_move_or_recommended_line:** Preserve Cloyster if the opponent still has real removal.
**why_this_move:** A Spiker that dies before the removal war is over often spent its slot for half a job.
**worst_plausible_branch:** Winning one exchange while quietly losing the whole hazard game.
**irreplaceable_piece_or_resource:** Your only practical “keep Spikes” body.
**information_that_would_flip_the_answer:** If the opponent’s remover is gone or nonfunctional, Cloyster can shift from strategic asset to trade piece.
**transfer_to_romhack:** Do not confuse “hazards established” with “hazards secured.”
**do_not_transfer:** This lesson is about GSC’s sparse removal ecosystem, not modern multi-remover metagames.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your hazard setter is also your path to retaining hazards, prefer preservation, unless removal is already off the board.
**measurement_hook:** Check whether the trainee distinguishes setup completion from hazard-war completion. citeturn41view0

**P08**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: hazard, pursuit, pp, rapid-spin`
**public_state:** You are considering Umbreon as the lone answer to Starmie’s repeated spinning.
**sealed_hidden_state:** The source says Starmie can stall out Umbreon’s Pursuit PP with Recover; Umbreon erodes Ghosts and Cloyster better than it kills Starmie.
**candidate_moves_or_switches:** hard lean on Pursuit Umbreon; pair Umbreon with other spin pressure; abandon the chronic anti-Starmie route.
**expert_move_or_recommended_line:** Do not route the whole spin war through Umbreon alone.
**why_this_move:** The matchup looks cleaner than it actually is; Recover and PP turn it into a grind Umbreon does not reliably win by itself.
**worst_plausible_branch:** The advisor keeps choosing “safe” Pursuit lines and bleeds PP while Starmie preserves the real objective.
**irreplaceable_piece_or_resource:** Pursuit PP and anti-spinner redundancy.
**information_that_would_flip_the_answer:** If Starmie is already Toxiced or already committed to staying low, Umbreon becomes much better.
**transfer_to_romhack:** A piece that is strong in small exchanges may still be bad as the sole long-game answer.
**do_not_transfer:** This is about GSC Pursuit mechanics and Recover loops, not later dark-type or item ecosystems.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your anti-removal line wins only the local exchange but not the long resource fight, prefer redundancy, unless the remover is already on a timer.
**measurement_hook:** Check whether the trainee notices the PP dimension of the Umbreon–Starmie line. citeturn34view3

## Sleep and status discipline positions

**P09**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: sleep, hidden-information, punish-switch, lead-discipline`
**public_state:** Your sleep inducer is in and the opponent is strongly signaling a Sleep Talk pivot.
**sealed_hidden_state:** The source’s rule is explicit: do not waste sleep into obvious Sleep Talk; use the threat of sleep to force the pivot, then attack or reposition.
**candidate_moves_or_switches:** click sleep move; attack the predicted Talker; double switch.
**expert_move_or_recommended_line:** Prefer the punish line over the raw sleep move.
**why_this_move:** The value of a sleep move in GSC is often the threat that shapes the opponent’s reaction, not the status itself.
**worst_plausible_branch:** Burning your once-important sleep turn on a RestTalk body that wanted the sleep anyway.
**irreplaceable_piece_or_resource:** Unspent sleep pressure.
**information_that_would_flip_the_answer:** If you have strong evidence the opponent lacks a Talker or cannot afford to go to it, the direct sleep line improves.
**transfer_to_romhack:** Threatened status can generate stronger lines than landed status.
**do_not_transfer:** Do not import later-gen sleep mechanics where RestTalk behaves differently.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the opponent’s obvious sleep absorber is better for them asleep than awake, prefer punishing the absorber, unless the sleep itself immediately breaks the position.
**measurement_hook:** Check whether the trainee identifies “threat leverage” instead of “status greed.” citeturn25view3turn36view0

**P10**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: sleep, target-selection, route-planning`
**public_state:** You have a clean sleep chance but more than one plausible target may appear.
**sealed_hidden_state:** The article advises aiming sleep at the opponent’s biggest offensive threat or at the defensive counter blocking your route, not at any random non-Talker.
**candidate_moves_or_switches:** sleep the first available body; preserve sleep until the key target appears; use the turn for another advantage play.
**expert_move_or_recommended_line:** Preserve and allocate sleep toward the route-defining target.
**why_this_move:** In GSC, sleep is rare, recoverable, and strategically expensive; wasting it on a low-value mon often changes nothing.
**worst_plausible_branch:** You land sleep, feel ahead, and later realize the actual win-condition blocker stayed untouched.
**irreplaceable_piece_or_resource:** The one meaningful sleep slot.
**information_that_would_flip_the_answer:** If the present target is uniquely vulnerable and the future target is unlikely to be exposed, take the immediate value.
**transfer_to_romhack:** Status allocation should be route-first, not accuracy-first.
**do_not_transfer:** This is not a blanket “greed sleep forever” rule; tempo can still matter more.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When sleep is scarce and restorative tools exist, prefer sleeping the route-critical piece, unless the immediate target creates a decisive tempo break.
**measurement_hook:** Check whether the trainee names the intended route before selecting the sleep target. citeturn36view0

**P11**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: sleep, rest-cycle, endgame`
**public_state:** An opposing RestTalk Pokémon is asleep and looks passive for a turn.
**sealed_hidden_state:** The article’s worked example shows Sleep Talk can call Rest in GSC, successfully reset the sleep counter, and restore HP.
**candidate_moves_or_switches:** assume a free setup turn; make a conservative progress play; force a different exchange.
**expert_move_or_recommended_line:** Respect the possibility that the sleeping Talker is still actively stabilizing.
**why_this_move:** Treating sleeping RestTalkers as dead turns is a classic later-gen mistake that loses GSC positions.
**worst_plausible_branch:** You give a “free” turn to a Talker that simply re-Rests, returns to full, and hands tempo back.
**irreplaceable_piece_or_resource:** Accurate Rest-cycle accounting.
**information_that_would_flip_the_answer:** If the target lacks Sleep Talk or already showed a different status set, the greed line becomes safer.
**transfer_to_romhack:** Sleep-state evaluation must include what the sleeping move menu still threatens.
**do_not_transfer:** Later-generation Sleep Talk standards are non-transferable here.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the sleeping opponent is a likely RestTalk user, prefer lines that still make progress through a Sleep Talk Rest roll, unless the set is already disproven.
**measurement_hook:** Check whether the trainee correctly predicts that Sleep Talk can reset Rest sleep in vanilla GSC. citeturn25view3turn38view0

**P12**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: paralysis, lure, setup-support`
**public_state:** Your attacker can choose a stronger damage move or a paralysis-fishing move into an expected defensive answer like Skarmory.
**sealed_hidden_state:** The article gives the concrete example that Body Slam Snorlax crippling Skarmory can open a later Marowak clean.
**candidate_moves_or_switches:** strongest damage move; Body Slam or Thunder for para support; hard double to the sweeper.
**expert_move_or_recommended_line:** Take the para-support line when the whole team is built to exploit the slowed answer.
**why_this_move:** In GSC, status often matters less for the present exchange than for enabling a later route.
**worst_plausible_branch:** You win one damage race but leave the real defensive hinge fully functional for the endgame.
**irreplaceable_piece_or_resource:** The opponent’s defensive speed tier and setup window.
**information_that_would_flip_the_answer:** If the answer is already chipped enough or Heal Bell is ready to erase the para immediately, raw damage may be better.
**transfer_to_romhack:** The correct move may be the one that changes future initiative rather than present damage totals.
**do_not_transfer:** Do not assume modern knockoff-style item disruption or heavy hazard stacks are there to finish the job.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your win condition is a slow breaker, prefer the line that cripples its answer, unless direct damage already crosses the route threshold.
**measurement_hook:** Check whether the trainee links the current para line to a later sweeper’s board state. citeturn25view4

**P13**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: paralysis, status-discipline, snorlax`
**public_state:** You can click Thunder Wave or Stun Spore freely, but Snorlax is the obvious switch-in.
**sealed_hidden_state:** The source is direct that many paralysis inducers do too little to Snorlax, making it the default sink and leaving your plan stranded.
**candidate_moves_or_switches:** click para blindly; use a move that also damages Snorlax; double to a Snorlax punisher.
**expert_move_or_recommended_line:** Do not route your para plan through a turn that just lets Snorlax absorb it for free.
**why_this_move:** Snorlax shrugs off paralysis better than most of the tier; the status is often effectively wasted.
**worst_plausible_branch:** You reveal your support move, invite Snorlax, and hand the opponent both information and position.
**irreplaceable_piece_or_resource:** Meaningful status distribution.
**information_that_would_flip_the_answer:** If the opponent’s Snorlax is the actual piece you must neutralize and you can pressure it afterward, the line can still be correct.
**transfer_to_romhack:** Status moves need target discipline; “status anything” is not the same as “advance your route.”
**do_not_transfer:** This is specifically about GSC Snorlax’s role and para tolerance.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the obvious status sink is also the tier’s best status absorber, prefer pressure or rerouting, unless that sink is itself the route-critical target.
**measurement_hook:** Check whether the trainee anticipates the Snorlax switch before choosing the status move. citeturn36view1

**P14**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: toxic, spikes, redundancy, phazing`
**public_state:** You are deciding where to place Toxic support on a Spikes team and both Starmie and Raikou could carry it.
**sealed_hidden_state:** The article warns against placing Toxic on pieces that invite the same switch-in, giving the example of Starmie and Raikou both drawing Snorlax; it recommends alternative exploitation like Roar on Raikou.
**candidate_moves_or_switches:** Toxic on both; Toxic on one and Roar on the other; abandon Toxic on one slot for coverage.
**expert_move_or_recommended_line:** Avoid redundant Toxic slots that point at the same answer; diversify the punishment.
**why_this_move:** Good status distribution multiplies switch tax; bad distribution wastes move slots by telegraphing the same target repeatedly.
**worst_plausible_branch:** The advisor keeps selecting Toxic into a board where the same Snorlax line neutralizes both versions.
**irreplaceable_piece_or_resource:** Move-slot leverage.
**information_that_would_flip_the_answer:** If the romhack or local meta makes those switch-ins materially different, redundancy can become less bad.
**transfer_to_romhack:** Status coverage should map to distinct opponent responses.
**do_not_transfer:** Do not assume vanilla switch maps if romhack type charts or movepools differ.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When two status users draw the same answer, prefer diversified punishment, unless local evidence says the answers diverge.
**measurement_hook:** Check whether the trainee notices status redundancy rather than counting Toxic users. citeturn36view3

**P15**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: heal-bell, sleep, preservation, rest-cycle`
**public_state:** Your cleric can cure team status now, but the opponent still has live sleep pressure.
**sealed_hidden_state:** The source warns that once the Heal Bell user is slept, it cannot cure itself and therefore cannot cure the rest of the team either.
**candidate_moves_or_switches:** heal immediately; pivot the cleric out and protect it; accept current status placement; let another mon absorb sleep.
**expert_move_or_recommended_line:** Protect the cleric from being slept if the whole team’s recovery plan depends on it.
**why_this_move:** A slept cleric is not just one disabled mon; it can collapse the entire restorative structure.
**worst_plausible_branch:** Using Heal Bell greedily, then watching the opponent reapply sleep while your cleric is no longer functional.
**irreplaceable_piece_or_resource:** The team’s only status reset.
**information_that_would_flip_the_answer:** If the cleric is expendable or the remaining status matchup is trivial, immediate Bell can still be best.
**transfer_to_romhack:** Preserve the recovery engine, not just the current HP bar.
**do_not_transfer:** This is about vanilla Heal Bell access and sleep interaction, not later cleric ecosystems.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your team’s status resilience is concentrated in one slot, prefer protecting that slot from sleep, unless the immediate cure ends the game faster than the risk matters.
**measurement_hook:** Check whether the trainee counts the cleric as a team resource rather than a single active Pokémon. citeturn25view5turn36view4

**P16**
`source_url: https://www.smogon.com/gs/articles/status` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: heal-bell, status-discipline, sacrifice-management`
**public_state:** One of your Pokémon is asleep, but that Pokémon is low-value into the remaining opposing team.
**sealed_hidden_state:** The article explicitly says there are situations where it is wise **not** to use Heal Bell if the sleep has effectively landed on a piece that no longer matters.
**candidate_moves_or_switches:** Bell immediately; hold Bell; use Bell later after more status accumulates.
**expert_move_or_recommended_line:** Hold Heal Bell when the current sleep allocation is favorable and Bell would only reopen the opponent’s sleep option.
**why_this_move:** Cure timing matters; sometimes the best status is the status you have already “parked” onto a disposable body.
**worst_plausible_branch:** You “fix” the board and hand the opponent a new high-value sleep target.
**irreplaceable_piece_or_resource:** Bell timing and sleep clause positioning.
**information_that_would_flip_the_answer:** If the sleeping mon becomes route-critical later, the answer flips.
**transfer_to_romhack:** Resource recovery should be judged against future exposure, not just current cleanliness.
**do_not_transfer:** This assumes vanilla sleep-clause logic and Heal Bell role concentration.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When sleep is already parked on a low-value piece, prefer holding the cure, unless restoring that piece materially improves your remaining route.
**measurement_hook:** Check whether the trainee asks “who becomes the next sleep target if I Bell now?” citeturn25view5turn36view4

## Explosion, sacrifice, and conversion positions

**P17**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, hazard, wallbreaking, route-conversion`
**public_state:** Cloyster has already created a reason for Starmie to appear and your offense needs Starmie gone to breathe.
**sealed_hidden_state:** Jorgen’s canonical example is exactly this: Cloyster uses Spikes to bait Starmie into attempting removal, then Explodes to remove it and open a later sweep.
**candidate_moves_or_switches:** keep clicking Surf; double to Pursuit; explode.
**expert_move_or_recommended_line:** Explode if Starmie’s removal or defensive role is the real bottleneck.
**why_this_move:** In GSC, Explosion is often best when it deletes the one defensive or utility piece that holds your whole route back.
**worst_plausible_branch:** Getting greedy for extra marginal value and leaving Starmie alive to undo the whole Spikes plan.
**irreplaceable_piece_or_resource:** The Starmie removal choke point.
**information_that_would_flip_the_answer:** If the opponent has already shown no Spin or if Starmie is no longer route-critical, keep Cloyster.
**transfer_to_romhack:** Trade the boom piece for the specific blocker, not for generic damage.
**do_not_transfer:** This lesson assumes vanilla Explosion strength and the one-layer Spikes game.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your Exploder baits the single utility piece invalidating your plan, prefer the immediate conversion, unless that piece has already lost its strategic value.
**measurement_hook:** Check whether the trainee can name the downstream beneficiary of the Explosion before selecting it. citeturn26view0

**P18**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, sleep, lure, wallbreaking`
**public_state:** Exeggutor threatens Sleep Powder and the opponent’s likely response is a Sleep Talk Electric, especially Zapdos.
**sealed_hidden_state:** The article explicitly names Exeggutor as a good bait Exploder because Sleep Powder draws in Sleep Talk Zapdos or Raikou.
**candidate_moves_or_switches:** raw Psychic/Giga Drain; sleep; immediate Explosion; punish after the expected absorber enters.
**expert_move_or_recommended_line:** Use the sleep threat to draw Zapdos, then convert with Explosion when its removal matters more than Exeggutor’s body.
**why_this_move:** The point is not “Egg explodes sometimes”; the point is that sleep pressure manufactures the exact boom target.
**worst_plausible_branch:** Spending Sleep Powder or Psychic on a low-value exchange and never cashing the lure.
**irreplaceable_piece_or_resource:** The opponent’s electric wall and your lure credibility.
**information_that_would_flip_the_answer:** If Skarmory or Tyranitar is the more important defensive hinge and the set threatens them instead, the target changes.
**transfer_to_romhack:** Use one threat to manufacture another resource trade.
**do_not_transfer:** This assumes vanilla Exeggutor role patterns and Explosion mechanics.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a status threat predictably summons the wall you most need removed, prefer the lure-to-trade line, unless keeping your lure alive is worth more than the kill.
**measurement_hook:** Check whether the trainee picks Explosion only after identifying the manufactured switch-in. citeturn26view0

**P19**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, chip-thresholds, electric-matchup`
**public_state:** Gengar can Explode into Raikou, but Raikou is not clearly in guaranteed KO range.
**sealed_hidden_state:** The article is unusually specific here: unchipped Raikou often survives Gengar Explosion, so weak damage or paralysis support should come first.
**candidate_moves_or_switches:** explode immediately; chip with coverage; paralyze first; pivot elsewhere.
**expert_move_or_recommended_line:** Do not boom prematurely; reach the chip threshold first.
**why_this_move:** A failed Explosion into Rest throws away Gengar and often gives Raikou the last word anyway.
**worst_plausible_branch:** You lose Gengar, Raikou survives, Rests, and the whole “lure” line backfires.
**irreplaceable_piece_or_resource:** Gengar’s one-shot trade opportunity.
**information_that_would_flip_the_answer:** If Raikou is paralyzed, lacks Rest, or is already chipped into guaranteed range, boom becomes correct.
**transfer_to_romhack:** High-power sac moves still require threshold discipline.
**do_not_transfer:** Do not import later-gen damage expectations or item boosts.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your sac move only works above a chip threshold, prefer setup toward the threshold, unless confirmed information makes the trade certain now.
**measurement_hook:** Check whether the trainee asks “does this actually KO?” before selecting Explosion. citeturn26view0

**P20**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, anti-setup, emergency-defense`
**public_state:** A boosted Belly Drum Snorlax, Growth Vaporeon, or similar snowball threat has one turn from ending the game.
**sealed_hidden_state:** The article explicitly presents defensive Explosion as the emergency stopgap for exactly these positions, singling out Cloyster and Forretress in that role.
**candidate_moves_or_switches:** bluff and attack; switch to a shaky wall; explode.
**expert_move_or_recommended_line:** Pull the trigger on Explosion when the alternative is losing the game to setup.
**why_this_move:** This is the purest “defensive boom” use case: not profit, survival.
**worst_plausible_branch:** Overvaluing your Exploder’s future and never getting a future because the sweeper ends the game.
**irreplaceable_piece_or_resource:** The emergency stop.
**information_that_would_flip_the_answer:** If another confirmed answer exists and is healthy, preserve the boom.
**transfer_to_romhack:** Some sacrifice routes are simply damage-control routes; train them that way.
**do_not_transfer:** This relies on vanilla Explosion lethality and setup profiles.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a boosted threat wins unless answered immediately, prefer the emergency sacrifice, unless another live answer is actually reliable.
**measurement_hook:** Check whether the trainee distinguishes “favorite long-term line” from “only non-losing line.” citeturn26view0

**P21**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: selfdestruct, surprise, anti-setup, simplification`
**public_state:** Snorlax is facing an opposing CurseLax line and can continue the war or reveal Selfdestruct.
**sealed_hidden_state:** Jorgen notes that Selfdestruct Snorlax is one of the best surprise anti-CurseLax tools because players often do not expect it and +1 opposing Snorlax takes huge damage.
**candidate_moves_or_switches:** continue Curse war; Rest; switch; Selfdestruct.
**expert_move_or_recommended_line:** If removing opposing Snorlax immediately unlocks your route and your own Lax’s glue duty is already replaceable, Selfdestruct is the expert punish.
**why_this_move:** Surprise matters in GSC; the best self-sac trades are often the ones the opponent structurally cannot respect.
**worst_plausible_branch:** You preserve Snorlax as “too important” and let the opposing CurseLax take over first.
**irreplaceable_piece_or_resource:** Surprise value and Snorlax’s walling role.
**information_that_would_flip_the_answer:** If your team still collapses to special pressure without your own Snorlax, preserve it.
**transfer_to_romhack:** Hidden set identity can itself be a resource worth cashing in at the hinge point.
**do_not_transfer:** This assumes vanilla Selfdestruct damage and vanilla Snorlax centrality.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your hidden self-sac line cleanly removes the opposing anchor and your own anchor duty is already covered, prefer revealing it, unless losing your anchor opens a worse route.
**measurement_hook:** Check whether the trainee weighs role loss against route simplification. citeturn26view0

**P22**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, bait, curse, wallbreaking`
**public_state:** Steelix is in a position where Suicune is the natural defensive response and one Curse is plausibly available.
**sealed_hidden_state:** The article names the exact line: Steelix survives one Surf and after one Curse can guarantee the Explosion KO on Suicune.
**candidate_moves_or_switches:** Earthquake; Roar; immediate Explosion; Curse then Explosion.
**expert_move_or_recommended_line:** If the Suicune removal is route-critical and you can safely get the boost, Curse first.
**why_this_move:** One prep turn changes the sacrifice from speculative to guaranteed.
**worst_plausible_branch:** Blowing up for big damage instead of a kill, leaving Suicune alive to continue walling the route.
**irreplaceable_piece_or_resource:** The guaranteed KO threshold.
**information_that_would_flip_the_answer:** If Steelix cannot afford the Surf or if Suicune is already chipped into raw-boom range, skip the Curse.
**transfer_to_romhack:** Some sacrifices are strongest when preconditioned.
**do_not_transfer:** This assumes vanilla damage and the same Steelix–Suicune relationship.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When one setup turn converts a trade from partial to decisive, prefer the prepared trade, unless the setup turn itself is too costly.
**measurement_hook:** Check whether the trainee recognizes the difference between “damage” and “guaranteed removal.” citeturn26view0

**P23**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, bluff, anti-overprediction`
**public_state:** Your Cloyster is threatening Explosion into a boosted or valuable target, and the opponent may overrespect it by pivoting to a Normal-resistant or other “safety” answer.
**sealed_hidden_state:** The article explicitly notes that mispredicting Explosion can be as bad as taking it, and that Cloyster can punish the overrespect with Surf instead.
**candidate_moves_or_switches:** raw Explosion; Surf; preserve.
**expert_move_or_recommended_line:** Bluff Explosion when the opponent’s safe switch is itself punishable and your boom is too valuable to cash now.
**why_this_move:** The threat of Explosion is part of the move’s value; sometimes you monetise the fear instead of the boom.
**worst_plausible_branch:** Exploding into the one class of Pokémon the opponent most wants to feed you.
**irreplaceable_piece_or_resource:** Credible Explosion threat.
**information_that_would_flip_the_answer:** If the active target is already the exact piece you need dead, stop bluffing and boom.
**transfer_to_romhack:** Visible threat can be a stronger resource than immediate execution.
**do_not_transfer:** This is a GSC-specific explosion-bluff lesson, not a modern pivoting rule.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the opponent’s respect for your sac move creates a punishable pivot, prefer cashing the threat, unless the current target is already the route-critical kill.
**measurement_hook:** Check whether the trainee can articulate what the opponent is trying to dodge. citeturn26view0

**P24**
`source_url: https://www.smogon.com/gs/articles/guide_to_explosion` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: explosion, simplification, conversion, endgame`
**public_state:** You are ahead in material or route integrity and can either preserve complexity or use Explosion to simplify.
**sealed_hidden_state:** The article treats “trading down” as a chess-like simplification tool when ahead.
**candidate_moves_or_switches:** keep maneuvering; explode to simplify; pivot and preserve all bodies.
**expert_move_or_recommended_line:** Trade down if the reduced game clearly favors your remaining anchor or endgame.
**why_this_move:** Not every boom is about wallbreaking; some are about removing tactical chaos.
**worst_plausible_branch:** Refusing simplification, reopening hidden-set or crit routes for the opponent.
**irreplaceable_piece_or_resource:** Your route advantage.
**information_that_would_flip_the_answer:** If the simplified endgame actually favors the opponent’s hidden win condition, do not trade down.
**transfer_to_romhack:** Once ahead, the best move may be the one that makes the game smaller.
**do_not_transfer:** This is not a universal “explode when ahead” rule; the simplified game must still be winning.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When you are already ahead and a sacrifice removes tactical volatility, prefer simplification, unless the smaller game secretly improves the opponent’s route.
**measurement_hook:** Check whether the trainee evaluates the post-trade endgame, not just the local exchange. citeturn26view0

## Preservation, leads, setup denial, and endgame positions

**P25**
`source_url: https://www.coupcritique.fr/entity/actualities/136` · `source_type: other` · `battle_format: GSC OU` · `turn_number: uncertain` · `category_tags: explosion, punishment, hidden-information, anti-pivot`
**public_state:** OmBrArch’s Curse Snorlax has been poisoned by Cloyster and must likely preserve itself; Fakes has just brought in Golem into a forced-switch moment.
**sealed_hidden_state:** The recap states OmBrArch chose Gengar and Fakes clicked Earthquake, immediately deleting it; exact prior board texture is recap-level rather than full-log precise.
**candidate_moves_or_switches:** Earthquake; Rock Slide; prediction switch; conservative positioning.
**expert_move_or_recommended_line:** Earthquake is the expert punish because Gengar is a natural poison-preserving pivot off a poisoned CurseLax.
**why_this_move:** The forced-preservation moment narrows the opponent’s switch tree; the best move covers the highest-value pivot.
**worst_plausible_branch:** Overrespecting coverage and giving the opponent a free reset with the one mon that keeps the midgame flexible.
**irreplaceable_piece_or_resource:** Gengar as spinblock/utility pivot on OmBrArch’s side.
**information_that_would_flip_the_answer:** If team reveals had already made Jolteon or a Flying-type pivot overwhelmingly more likely, the answer could change.
**transfer_to_romhack:** When status forces preservation, the pivot tree often contracts enough for a hard punish.
**do_not_transfer:** Exact set assumptions beyond the recap are uncertain.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When your status play forces the opponent to preserve their setup anchor, prefer hitting the most natural preserving pivot, unless stronger public evidence points elsewhere.
**measurement_hook:** Check whether the trainee uses preservation logic to narrow the switch tree. citeturn14view0

**P26**
`source_url: https://www.coupcritique.fr/entity/actualities/136` · `source_type: other` · `battle_format: GSC OU` · `turn_number: uncertain` · `category_tags: sacrifice-route, status, endgame-conversion`
**public_state:** Alice Kazumi’s Snorlax lacks Rest and OmBrArch needs a route for his own Snorlax to close.
**sealed_hidden_state:** The recap says OmBrArch went so far as to sacrifice Alakazam in order to poison the non-Rest Snorlax, after which his own Snorlax found the closing Curse route.
**candidate_moves_or_switches:** preserve Alakazam; chip passively; force poison even at material cost.
**expert_move_or_recommended_line:** Sacrifice the expendable piece if poisoning the opposing non-Rest anchor converts the whole endgame.
**why_this_move:** Trading a smaller piece for permanent timer control over the enemy anchor is classic GSC route conversion.
**worst_plausible_branch:** Preserving everything and never actually creating a closing route for your own win condition.
**irreplaceable_piece_or_resource:** Permanent status on the enemy anchor.
**information_that_would_flip_the_answer:** If Alice’s Snorlax secretly had cleric or Rest support still alive, the poison sacrifice is less decisive.
**transfer_to_romhack:** Sacrifices are strongest when they change the timer on the opponent’s anchor, not just their HP.
**do_not_transfer:** Exact move sequencing is recap-level and therefore medium-confidence.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a permanent timer on the opposing anchor immediately unlocks your own anchor, prefer the status-for-material trade, unless recovery support can erase it cheaply.
**measurement_hook:** Check whether the trainee sees why the sacrificed piece was expendable and the poison was not. citeturn14view0

**P27**
`source_url: https://www.smogon.com/gs/articles/gsc_guide_part1` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: preservation, pivoting, tempo`
**public_state:** You are in a bad matchup on board and can stay in for chip, sack, or switch.
**sealed_hidden_state:** Borat is emphatic: in GSC, if you are in a mismatch, you should usually switch; do not let something die just to get a new mon in.
**candidate_moves_or_switches:** stay and chip; sack; switch to the real answer.
**expert_move_or_recommended_line:** Switch.
**why_this_move:** KOs are worked for in GSC; trading bodies casually for small chip is usually new-gen thinking and loses structural integrity.
**worst_plausible_branch:** Donate a piece, then watch the opponent answer your “free” follow-up anyway.
**irreplaceable_piece_or_resource:** Your full defensive answer tree.
**information_that_would_flip_the_answer:** If the active mon is truly deadweight and the extra attack is guaranteed to convert your route, sacking can become right.
**transfer_to_romhack:** Preserve answer identity unless you are cashing it for a real threshold.
**do_not_transfer:** This is not “never sack”; it is “never sack for foggy reasons.”
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the board is a mismatch and no real threshold is gained by staying, prefer the switch, unless the sacrifice concretely advances a winning route.
**measurement_hook:** Check whether the trainee can explain what the staying line actually accomplishes. citeturn37view0

**P28**
`source_url: https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: preservation, cut-losses, curse-war, endgame`
**public_state:** A CurseLax line has already snowballed through multiple pivots and you can keep trying to preserve everything or cut losses.
**sealed_hidden_state:** The guide says one common mistake is preserving too much; once the pivot chain has already failed, it may be time to cut losses.
**candidate_moves_or_switches:** continue fancy preserving; commit one piece; aggressive check line.
**expert_move_or_recommended_line:** Cut losses before the setup threat reaches the point where no answer is clean.
**why_this_move:** Late preservation can be fake preservation: it saves names on paper while losing their functional value.
**worst_plausible_branch:** You rotate until every answer is weakened and then lose without ever making a stand.
**irreplaceable_piece_or_resource:** Functional, not nominal, defensive integrity.
**information_that_would_flip_the_answer:** If one unrevealed set detail still gives you a reliable reset, the harder preserve line may remain correct.
**transfer_to_romhack:** Resource value decays; a thing preserved too long can become unusable anyway.
**do_not_transfer:** This is contextual, not a blanket anti-pivot rule.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When repeated preserving only worsens every answer’s future utility, prefer cutting losses, unless you still retain a genuine reset line.
**measurement_hook:** Check whether the trainee distinguishes preserved HP from preserved function. citeturn40view2

**P29**
`source_url: https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: lead, no-team-preview, information-management`
**public_state:** You are choosing a lead in no-Team-Preview GSC.
**sealed_hidden_state:** The guide’s lead lesson is that leads matter, but only as a one-turn edge; static leads invite counter-leads and predictable first moves.
**candidate_moves_or_switches:** always lead the same mon; vary leads from viable options; overfit to one expected opponent lead.
**expert_move_or_recommended_line:** Prefer viable lead variety over autopilot lead repetition.
**why_this_move:** In no-preview formats, concealed team identity and first-turn ambiguity are themselves resources.
**worst_plausible_branch:** Your advisor learns one popular lead and becomes free prey for counter-tech.
**irreplaceable_piece_or_resource:** Early-game information asymmetry.
**information_that_would_flip_the_answer:** If one lead is overwhelmingly necessary into a very specific known scout, specialization can be justified.
**transfer_to_romhack:** In no-preview singles, lead choice is part of deception, not just matchup tables.
**do_not_transfer:** Do not import Team Preview assumptions or fixed lead heuristics from later gens.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When multiple viable leads exist and preview is absent, prefer unpredictability, unless opponent-specific evidence makes one lead clearly superior.
**measurement_hook:** Check whether the trainee values hidden team identity in lead selection. citeturn40view2turn39search16

**P30**
`source_url: https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 1` · `category_tags: lead, pivot, hidden-information`
**public_state:** Lead Zapdos faces lead Nidoking, and Hidden Power is the obvious immediate threat.
**sealed_hidden_state:** The guide explicitly says the line can be reversed by switching to Snorlax on the obvious Hidden Power and turning the “bad” lead into an advantage.
**candidate_moves_or_switches:** stay in and attack; go to Snorlax; overpredict elsewhere.
**expert_move_or_recommended_line:** The Snorlax pivot is the high-quality if the HP line is obvious.
**why_this_move:** The best no-preview lead play often weaponizes obviousness.
**worst_plausible_branch:** Playing the lead chart literally and missing the fact that the first-turn move is telegraphed.
**irreplaceable_piece_or_resource:** Snorlax’s ability to absorb the obvious line and flip tempo.
**information_that_would_flip_the_answer:** If Nidoking has already shown or strongly telegraphed Lovely Kiss or another non-HP line, the risk changes.
**transfer_to_romhack:** Predictability is often more important than nominal matchup.
**do_not_transfer:** This assumes vanilla hidden-power and lead dynamics.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the opponent’s first-turn best move is too obvious, prefer the pivot that flips that certainty into your advantage, unless alternate coverage is materially more likely.
**measurement_hook:** Check whether the trainee looks for “obvious move punishment” instead of raw lead charting. citeturn40view2

**P31**
`source_url: https://www.smogon.com/forums/threads/spl-xii-gsc-discussion-thread.3676008/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 1` · `category_tags: lead, counter-tech, uncertainty`
**public_state:** You are considering a Counter lead meant to punish Snorlax.
**sealed_hidden_state:** Mr.E’s tournament discussion view is that Counter leads are very high risk, depend heavily on Lax leads, and really want Double-Edge specifically.
**candidate_moves_or_switches:** bring or click Counter tech; use a broadly stable lead line; hedge for Cloyster/Electrics.
**expert_move_or_recommended_line:** Unless the scout is extremely narrow, do not let the advisor overrate the Counter-lead line.
**why_this_move:** The payoff is flashy, but the range of misses is huge in a no-preview format with diverse viable leads.
**worst_plausible_branch:** Training the model to love “hero” T1 lines that mostly whiff against the real lead field.
**irreplaceable_piece_or_resource:** Reliable opening structure.
**information_that_would_flip_the_answer:** Very strong opponent-specific evidence of Double-Edge Lax lead.
**transfer_to_romhack:** High-payoff lead traps should stay low-prior confidence lines unless public evidence is narrow.
**do_not_transfer:** This is a metagame-risk assessment, not a mechanics statement.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a lead trap only works into a narrow subset of openings, prefer stable play, unless opponent-specific public evidence sharply narrows the lead range.
**measurement_hook:** Check whether the trainee discounts low-frequency trap lines appropriately. citeturn40view3

**P32**
`source_url: https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 1` · `category_tags: lead, preservation, hazard, anti-golem`
**public_state:** You lead Zapdos into a possible Curse Snorlax and are tempted to go immediately to Cloyster.
**sealed_hidden_state:** The SPL XIII review explicitly criticizes this because the line leaves you quite vulnerable to possible Golem teams.
**candidate_moves_or_switches:** immediate Cloyster; safer broad answer; hold Zapdos; a more conservative scout.
**expert_move_or_recommended_line:** Do not autopilot Zapdos → Cloyster just because “Lax means Spikes turn.”
**why_this_move:** The hidden backline matters; converting the first reveal into your own scripted line can walk straight into Ground punish.
**worst_plausible_branch:** You “win” the local matchup table and lose the unseen-team matchup behind it.
**irreplaceable_piece_or_resource:** Early-game flexibility before the backline is known.
**information_that_would_flip_the_answer:** If Golem or equivalent punish is already disproven, the Cloyster route improves.
**transfer_to_romhack:** Early turns should preserve optionality against hidden-team punishers.
**do_not_transfer:** Exact team members in the cited game are replay-analysis specific.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a standard early pivot exposes you to one of the strongest unrevealed punishers, prefer the more flexible line, unless that punisher is already ruled out.
**measurement_hook:** Check whether the trainee reasons about unseen teammates, not just the active matchup. citeturn40view0

**P33**
`source_url: https://www.smogon.com/forums/threads/gsc-mechanics.3542417/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: phazing, anti-setup, move-priority`
**public_state:** Both sides are in a Roar / Whirlwind war or a setup-vs-phaze spot.
**sealed_hidden_state:** The mechanics resource is clear: in GSC, Roar and Whirlwind must go last to work, so the slower phazer wins that exchange.
**candidate_moves_or_switches:** race with the faster phazer; preserve the slower phazer; attack instead.
**expert_move_or_recommended_line:** Value the slower phazer more highly in direct phazing contests.
**why_this_move:** This is one of the most generation-specific ways a later-gen instinct can betray you.
**worst_plausible_branch:** Preserving the “faster” phazer on autopilot and losing the actual phazing war.
**irreplaceable_piece_or_resource:** The slower phazing body.
**information_that_would_flip_the_answer:** If the board is about damage or status and not a direct phaze contest, speed can matter differently.
**transfer_to_romhack:** Priority rules can invert which defensive piece matters most.
**do_not_transfer:** This is explicitly non-transferable to later gens where faster phazing works differently.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the position is a true phazing race, prefer preserving the slower phazer, unless the turn is no longer decided by phazing mechanics.
**measurement_hook:** Check whether the trainee knows that GSC phazing wants to move second. citeturn38view0turn24search3

**P34**
`source_url: https://www.smogon.com/forums/threads/mean-look-spider-web-baton-pass-in-gsc-ou.3696148/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 1` · `category_tags: lead, sleep, baton-pass, phazing, anti-setup`
**public_state:** Lead Smeargle appears and your team has one critical phazer.
**sealed_hidden_state:** The discussion post says you only really “lose T1” to Smeargle if you let your sole phazer get slept; otherwise, giving Spore to a less critical non-Talker is often survivable.
**candidate_moves_or_switches:** let the phazer absorb sleep; sack a lower-value body; respond with a sleep/thief lead; hard attack.
**expert_move_or_recommended_line:** Protect the sole phazer.
**why_this_move:** Against pass chains, phazer value is route value; misallocating sleep there is game-shaping.
**worst_plausible_branch:** You preserve a random body and lose the only structural answer.
**irreplaceable_piece_or_resource:** The only phazer.
**information_that_would_flip_the_answer:** If you have multiple phazers or another hard anti-BP structure, the sleep allocation becomes more flexible.
**transfer_to_romhack:** Against setup chains, sleep allocation should protect the route-denying piece first.
**do_not_transfer:** This assumes vanilla-style phazing and pass interaction, not modern baton-pass clauses or mechanics.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a setup lead threatens sleep and your team has one unique denial piece, prefer protecting that piece, unless redundant denial already exists.
**measurement_hook:** Check whether the trainee can identify the unique denial resource before choosing a sleep absorber. citeturn40view1turn43view0

**P35**
`source_url: https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: baton-pass, anti-setup, preservation`
**public_state:** The opponent got the first Agility pass off.
**sealed_hidden_state:** The sample-team BP section says surviving the first pass chain makes future prevention much easier, and specifically calls for keeping checks to Snorlax/Marowak/Machamp awake and at 100%, especially Cloyster or Skarmory.
**candidate_moves_or_switches:** trade one check loosely; preserve the healthy hard stop; chase greed elsewhere.
**expert_move_or_recommended_line:** Preserve the awake, full check even if that means making a temporarily passive line.
**why_this_move:** The first chain is the hardest; if you stabilize once, the BP team’s best edge is largely spent.
**worst_plausible_branch:** Using your check for short-term utility and discovering you no longer actually survive the first recipient.
**irreplaceable_piece_or_resource:** The full-HP anti-recipient check.
**information_that_would_flip_the_answer:** If Spikes or prior chip make the check no longer sufficient, you may need a different emergency line.
**transfer_to_romhack:** Against once-per-game explosive routes, preservation targets the first collapse point.
**do_not_transfer:** This is about vanilla GSC BP counterplay, not a general anti-setup rule.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a pass chain is likely and one healthy check is your first survival hinge, prefer preserving that check, unless it can no longer survive the chain anyway.
**measurement_hook:** Check whether the trainee values HP and sleep status on anti-setup pieces correctly. citeturn43view0

**P36**
`source_url: https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: baton-pass, spikes, anti-setup, boldness`
**public_state:** You are defending against Baton Pass and can play passively or assertively around Jolteon / Smeargle turns.
**sealed_hidden_state:** Siatam’s anti-BP notes say Spikes matter because pass teams do not run Leftovers everywhere, and “be bold” because BP wants setup turns, not honest attacks.
**candidate_moves_or_switches:** passive, predictable switching; set Spikes; stay in with Skarmory on Jolteon; let Tyranitar take manageable chip to deny free turns.
**expert_move_or_recommended_line:** Use Spikes and deny free setup turns, even if that means taking a respectable hit.
**why_this_move:** Predictable “always respect” lines are exactly what BP farms.
**worst_plausible_branch:** Giving the passer three clean turns because every defensive click was too polite.
**irreplaceable_piece_or_resource:** Free-turn denial.
**information_that_would_flip_the_answer:** If the incoming hit would meaningfully remove your only answer, boldness becomes recklessness.
**transfer_to_romhack:** Against fragile setup structures, the turn economy matters more than surface HP neatness.
**do_not_transfer:** Do not import modern BP bans or mechanics to this exact lesson.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When the opposing strategy needs uncontested setup turns more than clean attacks, prefer denying the free turn, unless the denied hit would destroy your only live answer.
**measurement_hook:** Check whether the trainee can separate “take damage” from “give a setup turn.” citeturn43view0

**P37**
`source_url: https://www.smogon.com/forums/threads/spl-xvi-gsc-discussion.3757711/page-2` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: anti-setup, phazing, preservation`
**public_state:** In builder- or early-game logic, you dropped Machamp and must compensate for CurseLax weakness during play.
**sealed_hidden_state:** Vani’s prep post says exactly why Reflect + Whirlwind Zapdos and Hypnosis Gengar were selected: they were direct responses to CurseLax when Gengar was chosen over Machamp.
**candidate_moves_or_switches:** save Zapdos too greedily for generic special checking; spend Hypnosis elsewhere; keep the anti-CurseLax line intact.
**expert_move_or_recommended_line:** Preserve your specifically designated anti-CurseLax tools for that job.
**why_this_move:** Once role compression shifts, the preservation hierarchy shifts with it.
**worst_plausible_branch:** Using Hypnosis Gengar or Reflect WW Zapdos casually, then facing the exact setup line they were chosen to stop.
**irreplaceable_piece_or_resource:** Your explicit anti-CurseLax assignment.
**information_that_would_flip_the_answer:** If opposing Snorlax is already identified as a passive or non-Curse set, these pieces gain freedom.
**transfer_to_romhack:** Preservation depends on role assignment, not species prestige.
**do_not_transfer:** This is prep-context commentary, not a universal set prescription.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When a piece was selected to patch one specific matchup hole, prefer preserving it for that hole, unless public information has already disproved the threat.
**measurement_hook:** Check whether the trainee preserves by function rather than by famous-name Pokémon. citeturn42view1

**P38**
`source_url: https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 25 and later` · `category_tags: pp, endgame, preservation, mono-lax`
**public_state:** Umbreon is your main line into MonoLax, but it has already spent meaningful Moonlight PP and Smeargle is still a live nuisance.
**sealed_hidden_state:** The SPL XIII commentary stresses Umbreon’s **8 Moonlight PP** timer and how that timer makes later Smeargle entries and Marowak pass lines much harder to contain.
**candidate_moves_or_switches:** overuse Umbreon as the sole stop; preserve Moonlight PP; trade elsewhere sooner.
**expert_move_or_recommended_line:** Preserve Moonlight PP like a hard resource, not as an afterthought.
**why_this_move:** In slow GSC endgames, PP is often the real HP bar.
**worst_plausible_branch:** Stabilizing every turn locally while slowly running out of the only move that actually keeps the matchup alive.
**irreplaceable_piece_or_resource:** Moonlight PP.
**information_that_would_flip_the_answer:** If MonoLax no longer threatens or Umbreon gets outside support, the timer pressure relaxes.
**transfer_to_romhack:** Limited-recovery PP should be modeled as a strategic countdown.
**do_not_transfer:** This position depends on Umbreon’s move economy and the specific matchup texture.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When one recovery move is your only long-game stabilizer, prefer preserving its PP, unless cashing it now prevents immediate collapse.
**measurement_hook:** Check whether the trainee tracks recovery PP as a first-class resource. citeturn42view0

**P39**
`source_url: https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/` · `source_type: forum analysis` · `battle_format: GSC OU` · `turn_number: 25` · `category_tags: rapid-spin, hidden-route, hazards, sacrifice-management`
**public_state:** You can accept Toxic on Golem in exchange for spinning because your unrevealed win condition badly wants no Spikes on your side.
**sealed_hidden_state:** The analysis says that once Toxic on Golem was revealed, taking Toxic in exchange for Spin was reasonable in hindsight because the concealed strategy cared much more about avoiding Spikes than about Golem’s status.
**candidate_moves_or_switches:** refuse Toxic and preserve Golem clean; take the status and spin; pivot elsewhere.
**expert_move_or_recommended_line:** Take the Toxic if removing Spikes is the real route enabler.
**why_this_move:** Not all damage is equal; sometimes status on one role-player is cheaper than one permanent layer on your side.
**worst_plausible_branch:** Preserving the spinner’s cleanliness while suffocating the actual hidden win condition under Spikes.
**irreplaceable_piece_or_resource:** A clean field for the unrevealed route.
**information_that_would_flip_the_answer:** If Golem is also your indispensable late-game pivot or Toxic makes the endgame unwinnable, preserve it instead.
**transfer_to_romhack:** Damage and status valuation should be route-relative.
**do_not_transfer:** This position is specific to hidden-route sequencing from replay analysis.
**mechanics_status:** vanilla_gsc
**policy_trigger:** When one status trade unlocks the field condition your hidden route needs, prefer the trade, unless the status destroys that same route elsewhere.
**measurement_hook:** Check whether the trainee compares field state value against individual mon cleanliness. citeturn42view0

**P40**
`source_url: https://www.smogon.com/gs/articles/gsc_spikes` · `source_type: article` · `battle_format: GSC OU` · `turn_number: null` · `category_tags: pp, heal-bell, status, endgame`
**public_state:** Your long hazard/status route has finally pressured the opponent into leaning on Heal Bell.
**sealed_hidden_state:** The Spikes article says to have a Bell plan: capitalize on the switch-in, waste Bell’s **8 PP**, or deny Bell entry entirely.
**candidate_moves_or_switches:** accept the cleric reset passively; attack the cleric switch-in; route toward Bell PP exhaustion.
**expert_move_or_recommended_line:** Treat the Bell turn as a punishable or exhaustible resource turn, not as an inevitability.
**why_this_move:** If the opponent’s entire status reset is only eight uses, your advisor should see each Bell as part of the endgame economy.
**worst_plausible_branch:** Spending twenty turns spreading status without ever asking whether Bell itself can be constrained or punished.
**irreplaceable_piece_or_resource:** Heal Bell PP and the punishment window on the cleric.
**information_that_would_flip_the_answer:** If Bell is not present or is no longer strategically relevant, other status lines dominate.
**transfer_to_romhack:** Recovery and cleanse buttons should be modeled as finite route resources.
**do_not_transfer:** This assumes vanilla Heal Bell access and PP, which should be locally checked if the romhack edits movesets.
**mechanics_status:** locally_supplied_romhack_evidence_needed
**policy_trigger:** When the opponent relies on finite teamwide status cleansing, prefer punishing or exhausting the cleanse, unless the current board demands a different immediate answer.
**measurement_hook:** Check whether the trainee tracks Bell PP and identifies punish windows on the cleric switch-in. citeturn34view4turn35view0

## JSONL block

```jsonl
{"id":"P01","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","rapid-spin","spinblock","preservation"],"public_state":"Your Cloyster has Spikes up and the opponent reveals Starmie as the likely spinner.","sealed_hidden_state":"Source says Cloyster cannot reliably keep Spikes against Starmie by itself; Misdreavus is the sturdier Starmie spinblocker.","candidate_moves_or_switches":["Surf","Toxic","Explosion","switch to Gengar","switch to Misdreavus"],"expert_move_or_recommended_line":"Prefer Misdreavus if the route depends on keeping Spikes.","why_this_move":"It wins the actual removal subgame instead of merely damaging Starmie.","worst_plausible_branch":"Stay in, get minor chip, and lose the whole Spikes route.","irreplaceable_piece_or_resource":"Reliable Starmie spinblocker.","information_that_would_flip_the_answer":"Starmie already poisoned into forced Recover or immediate Explosion route wins.","transfer_to_romhack":"Preserve the one piece that actually wins the remover matchup.","do_not_transfer":"No Defog, no multi-layer modern hazard assumptions.","mechanics_status":"vanilla_gsc","policy_trigger":"When the premier remover appears against your lone hazard setter, prefer the dedicated remover-answer, unless one immediate trade already wins.","measurement_hook":"Does the trainee separate 'keep Spikes' from 'damage the spinner'?"}
{"id":"P02","source_url":"https://www.smogon.com/forums/threads/gsc-mechanics.3542417/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","rapid-spin","legality","role-compression"],"public_state":"You need a single slot to both remove Spikes and threaten Explosion later.","sealed_hidden_state":"Vanilla legal sets matter: Cloyster Rapid Spin + Explosion is illegal; Forretress can legally combine Spin and Explosion.","candidate_moves_or_switches":["assume Cloyster can do both","use Forretress","separate the roles"],"expert_move_or_recommended_line":"Do not train on illegal Cloyster compression under vanilla assumptions.","why_this_move":"A fake role identity distorts every downstream choice.","worst_plausible_branch":"Advisor preserves or pivots an impossible set.","irreplaceable_piece_or_resource":"Correct role identity.","information_that_would_flip_the_answer":"Local romhack evidence that movepools changed.","transfer_to_romhack":"Check legal role compression before preserving the mon.","do_not_transfer":"Vanilla illegality should not be assumed in the romhack without proof.","mechanics_status":"locally_supplied_romhack_evidence_needed","policy_trigger":"When a line depends on one Pokémon doing two jobs, prefer the legal role-compressor, unless local romhack evidence changes the movepool.","measurement_hook":"Does the trainee reject Spin + Boom Cloyster in vanilla?"}
{"id":"P03","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","preservation","scouting","setup-denial"],"public_state":"Forretress seems to have a free Spikes/Spin turn into an opponent with possible Fire coverage.","sealed_hidden_state":"Source says Forretress must scout surprise Fire moves before assuming a safe setup turn.","candidate_moves_or_switches":["Spikes","Rapid Spin","attack","scout pivot"],"expert_move_or_recommended_line":"Scout first when Fire tech is plausible.","why_this_move":"Losing Forretress can collapse both keep- and remove-Spikes plans.","worst_plausible_branch":"Take the greedy layer and lose your entire hazard controller.","irreplaceable_piece_or_resource":"Forretress longevity.","information_that_would_flip_the_answer":"Hard evidence the target lacks Fire coverage.","transfer_to_romhack":"Do not gamble away the role-compressed hazard controller on ambiguous coverage.","do_not_transfer":"Specific to GSC Forretress risk and hidden coverage.","mechanics_status":"vanilla_gsc","policy_trigger":"When your hazard controller faces meaningful hidden coverage risk, prefer scouting, unless confirmed information makes the greed line clean.","measurement_hook":"Does the trainee value role preservation over one layer?"}
{"id":"P04","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","status","rapid-spin","patience"],"public_state":"Starmie or Cloyster is repeatedly contesting the Spikes war.","sealed_hidden_state":"Source favors Toxic as the most reliable anti-Starmie status and warns not to rely on para/sleep there.","candidate_moves_or_switches":["fish for para","attempt sleep","Toxic","hard double punish"],"expert_move_or_recommended_line":"Prefer Toxic if your goal is to win the long hazard war.","why_this_move":"Poison changes future recovery and spin timing.","worst_plausible_branch":"Spend turns on unreliable status while the spinner keeps control.","irreplaceable_piece_or_resource":"Long-run spin pressure.","information_that_would_flip_the_answer":"Spinner already slowed or easy immediate conversion from para.","transfer_to_romhack":"Choose the status that changes the remover's future menu.","do_not_transfer":"No Natural Cure or later-gen anti-status assumptions.","mechanics_status":"vanilla_gsc","policy_trigger":"When beating a durable remover over many turns, prefer the status that constrains recovery timing, unless a faster status converts immediately.","measurement_hook":"Does the trainee pick Toxic over prettier anti-Starmie lines?"}
{"id":"P05","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","rapid-spin","speed-control","pursuit-support"],"public_state":"Icy Wind Cloyster expects Starmie to enter and Spin.","sealed_hidden_state":"Source gives the sequence: Spikes as Starmie enters, Icy Wind on Spin, then leverage the speed drop for Tyranitar or later Explosion.","candidate_moves_or_switches":["Explosion","Surf","Toxic","Icy Wind","immediate Tyranitar"],"expert_move_or_recommended_line":"Use Icy Wind when the route is keep-Spikes-then-trap.","why_this_move":"It converts a losing speed matchup into a winning one.","worst_plausible_branch":"Explode too early or attack for chip while Starmie stays in control.","irreplaceable_piece_or_resource":"Speed control over the spinner.","information_that_would_flip_the_answer":"Starmie already poisoned into Recover range.","transfer_to_romhack":"Temporary speed control can bridge a bad remover matchup into a good one.","do_not_transfer":"Built around one-layer GSC Spikes, not modern hazard stacks.","mechanics_status":"vanilla_gsc","policy_trigger":"When a bad remover matchup can be converted by tempo and speed, prefer the enabling line, unless an immediate trade is already winning.","measurement_hook":"Does the trainee treat Icy Wind as route creation rather than weak damage?"}
{"id":"P06","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","explosion","bait","trade-management"],"public_state":"Steelix is active in a spot that strongly invites Starmie or Cloyster.","sealed_hidden_state":"Source says Steelix often baits those Water-types and can survive one Surf from them at full.","candidate_moves_or_switches":["Curse","Earthquake","double switch","Explosion"],"expert_move_or_recommended_line":"Explode if removing the spinner unlocks your broader route.","why_this_move":"One remover often gates the whole residual plan.","worst_plausible_branch":"Stay cute and let the remover live long enough to reset the game.","irreplaceable_piece_or_resource":"Opponent's spinner.","information_that_would_flip_the_answer":"Steelix still needed as unique Normal resist or Electric pivot.","transfer_to_romhack":"Use the bait piece to trade for the single invalidator of your route.","do_not_transfer":"Assumes vanilla Explosion and Steelix role.","mechanics_status":"vanilla_gsc","policy_trigger":"When your bait piece invites the single best answer to your residual route, prefer the conversion trade, unless the bait piece is still more valuable alive.","measurement_hook":"Does the trainee see the remover kill as worth more than local development?"}
{"id":"P07","source_url":"https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","preservation","role-identity"],"public_state":"Cloyster has set Spikes and can now trade or preserve.","sealed_hidden_state":"Sample-team notes say Cloyster's job is to get Spikes up and stay healthy enough to keep them up if removal still exists.","candidate_moves_or_switches":["explode now","attack","rest","pivot out"],"expert_move_or_recommended_line":"Preserve Cloyster if real removal is still live.","why_this_move":"A Spiker that dies before the removal war ends only did half its job.","worst_plausible_branch":"Win one exchange and lose the entire hazard game.","irreplaceable_piece_or_resource":"Your only realistic keep-Spikes body.","information_that_would_flip_the_answer":"Opponent's remover already gone or invalidated.","transfer_to_romhack":"Do not confuse hazards established with hazards secured.","do_not_transfer":"Specific to sparse GSC removal ecosystem.","mechanics_status":"vanilla_gsc","policy_trigger":"When your hazard setter is also your path to retaining hazards, prefer preservation, unless removal is already off the board.","measurement_hook":"Does the trainee distinguish setup completion from hazard-war completion?"}
{"id":"P08","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["hazard","pursuit","pp","rapid-spin"],"public_state":"Umbreon is being considered as the lone anti-Starmie plan.","sealed_hidden_state":"Source says Starmie can stall out Umbreon Pursuit PP with Recover; Umbreon is not enough by itself.","candidate_moves_or_switches":["lean on Umbreon alone","pair with other anti-spin tools","abandon long anti-Starmie route"],"expert_move_or_recommended_line":"Do not route the spin war through Umbreon alone.","why_this_move":"Local exchange strength is not the same as long-game control.","worst_plausible_branch":"Bleed Pursuit PP while Starmie preserves the real objective.","irreplaceable_piece_or_resource":"Pursuit PP and anti-spinner redundancy.","information_that_would_flip_the_answer":"Starmie already poisoned or otherwise on a timer.","transfer_to_romhack":"A piece can be good locally and still bad as the sole strategic answer.","do_not_transfer":"Specific to GSC Pursuit and Recover loops.","mechanics_status":"vanilla_gsc","policy_trigger":"When your anti-removal line wins only the local exchange but not the resource fight, prefer redundancy, unless the remover is already on a timer.","measurement_hook":"Does the trainee notice the PP dimension?"}
{"id":"P09","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["sleep","hidden-information","punish-switch","lead-discipline"],"public_state":"Your sleep inducer is in and the opponent is strongly signaling a Sleep Talk pivot.","sealed_hidden_state":"Source says do not waste sleep into obvious Sleep Talk; use the threat to force the switch and punish it.","candidate_moves_or_switches":["sleep move","attack the Talker","double switch"],"expert_move_or_recommended_line":"Prefer the punish line over raw sleep.","why_this_move":"The threat of sleep is often more valuable than landing it on the absorber.","worst_plausible_branch":"Spend a prime sleep turn on something that wanted the sleep.","irreplaceable_piece_or_resource":"Unspent sleep pressure.","information_that_would_flip_the_answer":"Strong evidence the opponent lacks a Talker or cannot afford that pivot.","transfer_to_romhack":"Threatened status can be stronger than landed status.","do_not_transfer":"Later-gen RestTalk instincts are non-transferable.","mechanics_status":"vanilla_gsc","policy_trigger":"When the obvious sleep absorber is better for them asleep than awake, prefer punishing the absorber, unless the sleep itself breaks the position.","measurement_hook":"Does the trainee identify threat leverage rather than status greed?"}
{"id":"P10","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["sleep","target-selection","route-planning"],"public_state":"You have a clean sleep chance but more than one plausible target may appear.","sealed_hidden_state":"Source says sleep the biggest offensive threat or the defensive counter blocking your plan, not a random non-Talker.","candidate_moves_or_switches":["sleep first available target","hold sleep for key target","take another advantage line"],"expert_move_or_recommended_line":"Allocate sleep toward the route-defining target.","why_this_move":"Sleep is scarce, recoverable, and strategically expensive in GSC.","worst_plausible_branch":"Land sleep and realize the real blocker stayed untouched.","irreplaceable_piece_or_resource":"The one meaningful sleep slot.","information_that_would_flip_the_answer":"Future key target unlikely to be exposed.","transfer_to_romhack":"Status allocation should be route-first.","do_not_transfer":"Not a blanket 'hold sleep forever' rule.","mechanics_status":"vanilla_gsc","policy_trigger":"When sleep is scarce and restorative tools exist, prefer sleeping the route-critical piece, unless the immediate target creates decisive tempo.","measurement_hook":"Does the trainee name the intended route before picking the target?"}
{"id":"P11","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["sleep","rest-cycle","endgame"],"public_state":"An opposing RestTalk user is asleep and seems passive.","sealed_hidden_state":"Source example shows Sleep Talk can call Rest successfully in GSC, reset sleep, and heal back to full.","candidate_moves_or_switches":["treat as free setup turn","make conservative progress","force a different exchange"],"expert_move_or_recommended_line":"Respect that the sleeping Talker is still stabilizing.","why_this_move":"Sleeping RestTalkers are not dead turns in vanilla GSC.","worst_plausible_branch":"You gift a free turn to a mon that simply re-Rests.","irreplaceable_piece_or_resource":"Accurate Rest-cycle accounting.","information_that_would_flip_the_answer":"Set already shown to lack Sleep Talk.","transfer_to_romhack":"Sleep-state evaluation must include the sleeping move menu.","do_not_transfer":"Later-gen Sleep Talk standards do not transfer.","mechanics_status":"vanilla_gsc","policy_trigger":"When the sleeping opponent is a likely RestTalk user, prefer lines that still make progress through a Sleep Talk Rest roll, unless the set is disproven.","measurement_hook":"Does the trainee know Sleep Talk can reset Rest sleep in GSC?"}
{"id":"P12","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["paralysis","lure","setup-support"],"public_state":"Your attacker can choose raw damage or a paralysis-fishing line into an expected defensive answer like Skarmory.","sealed_hidden_state":"Article gives Body Slam Snorlax crippling Skarmory to open Marowak as a concrete example.","candidate_moves_or_switches":["strongest damage","Body Slam/Thunder para line","hard double to sweeper"],"expert_move_or_recommended_line":"Take the para-support line when the team is built to exploit the slowed answer.","why_this_move":"Status often matters more for the next route than the current exchange.","worst_plausible_branch":"Win one damage race and leave the actual endgame hinge intact.","irreplaceable_piece_or_resource":"Opponent's defensive speed tier.","information_that_would_flip_the_answer":"Answer already chipped enough or Bell immediately erases para.","transfer_to_romhack":"Current move value may be mostly future initiative value.","do_not_transfer":"No modern hazard-stack cleanup assumptions.","mechanics_status":"vanilla_gsc","policy_trigger":"When your win condition is a slow breaker, prefer the line that cripples its answer, unless direct damage already crosses the route threshold.","measurement_hook":"Does the trainee connect the para line to a later sweeper board?"}
{"id":"P13","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["paralysis","status-discipline","snorlax"],"public_state":"You can click Thunder Wave or Stun Spore freely, but Snorlax is the obvious switch-in.","sealed_hidden_state":"Source says many paralysis inducers do too little to Snorlax, making it the default sink.","candidate_moves_or_switches":["blind para","a move that also pressures Snorlax","double to a Lax punisher"],"expert_move_or_recommended_line":"Do not route your para plan through a free Snorlax absorb.","why_this_move":"Snorlax tolerates paralysis too well for many such lines to count as progress.","worst_plausible_branch":"Reveal support move and hand the opponent both info and position.","irreplaceable_piece_or_resource":"Meaningful status distribution.","information_that_would_flip_the_answer":"Snorlax itself is the route-critical target and you can pressure it after.","transfer_to_romhack":"Status moves need target discipline.","do_not_transfer":"Specific to GSC Snorlax role and para tolerance.","mechanics_status":"vanilla_gsc","policy_trigger":"When the obvious status sink is also the best absorber, prefer pressure or rerouting, unless that sink is itself the critical target.","measurement_hook":"Does the trainee anticipate the Snorlax switch first?"}
{"id":"P14","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["toxic","spikes","redundancy","phazing"],"public_state":"You are deciding where to place Toxic support and both Starmie and Raikou could carry it.","sealed_hidden_state":"Source warns against redundant Toxic users that invite the same answer, using Starmie/Raikou both drawing Snorlax as the example.","candidate_moves_or_switches":["Toxic on both","Toxic on one and Roar on the other","coverage on one"],"expert_move_or_recommended_line":"Diversify the punishment instead of duplicating Toxic into the same switch map.","why_this_move":"Good status spread multiplies switch tax; bad spread wastes slots.","worst_plausible_branch":"Advisor repeatedly Toxics into the same answer from both angles.","irreplaceable_piece_or_resource":"Move-slot leverage.","information_that_would_flip_the_answer":"Local meta or romhack makes the switch-ins diverge.","transfer_to_romhack":"Status coverage should map to distinct opponent responses.","do_not_transfer":"Do not assume vanilla switch maps if local movepools differ.","mechanics_status":"vanilla_gsc","policy_trigger":"When two status users draw the same answer, prefer diversified punishment, unless local evidence says the answers diverge.","measurement_hook":"Does the trainee notice status redundancy?"}
{"id":"P15","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["heal-bell","sleep","preservation","rest-cycle"],"public_state":"Your cleric can cure team status now, but the opponent still has live sleep pressure.","sealed_hidden_state":"Source warns that if the Heal Bell user is slept, it cannot cure itself or the rest of the team.","candidate_moves_or_switches":["Bell now","protect cleric","accept current status placement","sleep with another mon"],"expert_move_or_recommended_line":"Protect the cleric from sleep when the whole recovery plan depends on it.","why_this_move":"A slept cleric can collapse the entire restorative structure.","worst_plausible_branch":"Bell greedily and then lose the whole cure engine.","irreplaceable_piece_or_resource":"Teamwide status cure.","information_that_would_flip_the_answer":"Cleric expendable or immediate Bell ends the game.","transfer_to_romhack":"Preserve the recovery engine, not just a current HP bar.","do_not_transfer":"Specific to vanilla Heal Bell access and sleep interaction.","mechanics_status":"vanilla_gsc","policy_trigger":"When team status resilience is concentrated in one slot, prefer protecting that slot from sleep, unless the immediate cure ends the game faster than the risk matters.","measurement_hook":"Does the trainee treat cleric value as team-level?"}
{"id":"P16","source_url":"https://www.smogon.com/gs/articles/status","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["heal-bell","status-discipline","sacrifice-management"],"public_state":"One of your Pokémon is asleep, but that mon is low-value into the remaining enemy team.","sealed_hidden_state":"Source explicitly says it can be wise not to use Heal Bell if sleep is parked on something not useful.","candidate_moves_or_switches":["Bell immediately","hold Bell","Bell later after more status"],"expert_move_or_recommended_line":"Hold Heal Bell when the current sleep allocation is favorable.","why_this_move":"Curing now may only reopen the opponent's sleep option on a better target.","worst_plausible_branch":"You fix the board and hand over a new high-value sleep target.","irreplaceable_piece_or_resource":"Bell timing and sleep-clause positioning.","information_that_would_flip_the_answer":"Sleeping mon becomes route-critical later.","transfer_to_romhack":"Recovery timing should be judged against future exposure.","do_not_transfer":"Assumes vanilla sleep-clause logic and Heal Bell role concentration.","mechanics_status":"vanilla_gsc","policy_trigger":"When sleep is already parked on a low-value piece, prefer holding the cure, unless restoring that piece materially improves your route.","measurement_hook":"Does the trainee ask who becomes the next sleep target if Bell is used now?"}
{"id":"P17","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","hazard","wallbreaking","route-conversion"],"public_state":"Cloyster has already created a reason for Starmie to appear and your offense needs Starmie gone.","sealed_hidden_state":"Canonical source example is Cloyster baiting Starmie with Spikes and Exploding to remove it.","candidate_moves_or_switches":["keep Surfing","double to Pursuit","Explosion"],"expert_move_or_recommended_line":"Explode if Starmie is the actual bottleneck.","why_this_move":"Delete the single utility piece invalidating your route.","worst_plausible_branch":"Get greedy and let Starmie survive to undo the whole plan.","irreplaceable_piece_or_resource":"The Starmie choke point.","information_that_would_flip_the_answer":"Starmie no longer route-critical or no Spin revealed.","transfer_to_romhack":"Trade the boom piece for the specific blocker.","do_not_transfer":"Assumes vanilla Explosion and one-layer Spikes game.","mechanics_status":"vanilla_gsc","policy_trigger":"When your Exploder baits the one utility piece invalidating your plan, prefer the immediate conversion, unless that piece already lost strategic value.","measurement_hook":"Can the trainee name the downstream beneficiary before booming?"}
{"id":"P18","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","sleep","lure","wallbreaking"],"public_state":"Exeggutor threatens Sleep Powder and likely summons a Sleep Talk Electric.","sealed_hidden_state":"Article names Exeggutor as a good bait Exploder because Sleep Powder draws in Zapdos/Raikou.","candidate_moves_or_switches":["Psychic","Sleep Powder","Explosion","sleep-then-punish"],"expert_move_or_recommended_line":"Use the sleep threat to draw Zapdos, then trade when its removal matters more than Exeggutor.","why_this_move":"Sleep pressure manufactures the boom target.","worst_plausible_branch":"Spend the turn without cashing the lure and never remove the real wall.","irreplaceable_piece_or_resource":"Zapdos/Raikou as the summoned wall.","information_that_would_flip_the_answer":"Another defensive hinge matters more or the lure set differs.","transfer_to_romhack":"Use one threat to manufacture another resource trade.","do_not_transfer":"Assumes vanilla Exeggutor role and Explosion mechanics.","mechanics_status":"vanilla_gsc","policy_trigger":"When a status threat predictably summons the wall you most need removed, prefer the lure-to-trade line, unless keeping your lure alive is worth more.","measurement_hook":"Does the trainee identify the manufactured switch-in?"}
{"id":"P19","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","chip-thresholds","electric-matchup"],"public_state":"Gengar can Explode into Raikou, but guaranteed KO range is unclear.","sealed_hidden_state":"Source says healthy Raikou often survives Gengar Explosion unless chipped or paralyzed.","candidate_moves_or_switches":["boom now","chip first","paralyze first","pivot"],"expert_move_or_recommended_line":"Do not boom prematurely; reach the chip threshold first.","why_this_move":"A failed Explosion into Rest wastes Gengar and gives Raikou the last word.","worst_plausible_branch":"Lose Gengar; Raikou survives and Rests.","irreplaceable_piece_or_resource":"Gengar's one-shot trade window.","information_that_would_flip_the_answer":"Raikou already paralyzed, chipped, or lacks Rest.","transfer_to_romhack":"High-power sac moves still require threshold discipline.","do_not_transfer":"No item-boosted later-gen damage assumptions.","mechanics_status":"vanilla_gsc","policy_trigger":"When your sac move only works above a chip threshold, prefer setup toward the threshold, unless the trade is already certain now.","measurement_hook":"Does the trainee ask whether Explosion actually KOs?"}
{"id":"P20","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","anti-setup","emergency-defense"],"public_state":"A boosted DrumLax or Growth sweeper is one turn from taking over.","sealed_hidden_state":"Article presents defensive Explosion as the emergency stop for exactly these spots, especially via Cloyster/Forretress.","candidate_moves_or_switches":["bluff and attack","shaky wall","Explosion"],"expert_move_or_recommended_line":"Pull the trigger when the alternative is losing instantly to setup.","why_this_move":"This is defensive boom as survival, not profit.","worst_plausible_branch":"Saving the Exploder for later and never getting a later.","irreplaceable_piece_or_resource":"Emergency stop.","information_that_would_flip_the_answer":"Another confirmed reliable answer remains healthy.","transfer_to_romhack":"Some sacrifice lines are simply the only non-losing lines.","do_not_transfer":"Assumes vanilla Explosion lethality and setup profiles.","mechanics_status":"vanilla_gsc","policy_trigger":"When a boosted threat wins unless answered immediately, prefer the emergency sacrifice, unless another live answer is actually reliable.","measurement_hook":"Does the trainee distinguish favorite line from only non-losing line?"}
{"id":"P21","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["selfdestruct","surprise","anti-setup","simplification"],"public_state":"Your Snorlax is in a Curse war and could continue or reveal Selfdestruct.","sealed_hidden_state":"Article says Selfdestruct Snorlax is a top surprise anti-CurseLax tool because players often do not expect it.","candidate_moves_or_switches":["continue Curse war","Rest","switch","Selfdestruct"],"expert_move_or_recommended_line":"Selfdestruct if removing opposing Snorlax unlocks your route and your own glue duty is already replaceable.","why_this_move":"Surprise is part of the value.","worst_plausible_branch":"Preserve too long and let the opposing CurseLax take over first.","irreplaceable_piece_or_resource":"Surprise value vs Snorlax walling role.","information_that_would_flip_the_answer":"Team still collapses to special pressure without your own Lax.","transfer_to_romhack":"Hidden set identity can itself be a spendable resource.","do_not_transfer":"Assumes vanilla Selfdestruct damage and Snorlax centrality.","mechanics_status":"vanilla_gsc","policy_trigger":"When your hidden self-sac line cleanly removes the opposing anchor and your own anchor duty is covered, prefer revealing it, unless losing your anchor opens a worse route.","measurement_hook":"Does the trainee weigh role loss against simplification gain?"}
{"id":"P22","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","bait","curse","wallbreaking"],"public_state":"Steelix can likely get one Curse before Suicune answers.","sealed_hidden_state":"Article names the line: Steelix survives one Surf and after one Curse guarantees the Explosion KO on Suicune.","candidate_moves_or_switches":["Earthquake","Roar","raw Explosion","Curse then Explosion"],"expert_move_or_recommended_line":"If Suicune removal is route-critical and the setup turn is safe, Curse first.","why_this_move":"One prep turn changes the trade from damage to removal.","worst_plausible_branch":"Settle for partial boom and leave Suicune alive.","irreplaceable_piece_or_resource":"Guaranteed KO threshold.","information_that_would_flip_the_answer":"Steelix cannot afford the Surf or Suicune already in raw-boom range.","transfer_to_romhack":"Some sacrifices should be preconditioned.","do_not_transfer":"Assumes vanilla Steelix–Suicune damage profile.","mechanics_status":"vanilla_gsc","policy_trigger":"When one setup turn converts a trade from partial to decisive, prefer the prepared trade, unless the setup turn is too costly.","measurement_hook":"Does the trainee distinguish damage from guaranteed removal?"}
{"id":"P23","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","bluff","anti-overprediction"],"public_state":"Cloyster threatens Explosion and the opponent may overrespect it with a normal-resistant pivot.","sealed_hidden_state":"Article says mispredicting Explosion can be as bad as taking it, and Cloyster can punish the overrespect with Surf.","candidate_moves_or_switches":["Explosion","Surf","preserve"],"expert_move_or_recommended_line":"Bluff Explosion when the safety pivot is itself punishable and the boom is still too valuable.","why_this_move":"Sometimes the fear of boom is worth more than the boom itself.","worst_plausible_branch":"Explode into the class of target the opponent most wants to feed you.","irreplaceable_piece_or_resource":"Credible Explosion threat.","information_that_would_flip_the_answer":"Current target is already the exact route-critical kill.","transfer_to_romhack":"Visible threat can be a stronger resource than immediate execution.","do_not_transfer":"GSC-specific explosion-bluff lesson.","mechanics_status":"vanilla_gsc","policy_trigger":"When the opponent's respect for your sac move creates a punishable pivot, prefer cashing the threat, unless the current target is already the route-critical kill.","measurement_hook":"Does the trainee explain what the opponent is trying to dodge?"}
{"id":"P24","source_url":"https://www.smogon.com/gs/articles/guide_to_explosion","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","simplification","conversion","endgame"],"public_state":"You are ahead and can preserve complexity or explode to simplify.","sealed_hidden_state":"Article treats trading down as a chess-like simplification tool when ahead.","candidate_moves_or_switches":["keep maneuvering","explode to simplify","preserve everything"],"expert_move_or_recommended_line":"Trade down if the reduced game still clearly favors your remaining anchor or endgame.","why_this_move":"The boom removes tactical volatility, not just a mon.","worst_plausible_branch":"Refuse simplification and reopen hidden-set or crit routes.","irreplaceable_piece_or_resource":"Your route advantage.","information_that_would_flip_the_answer":"Smaller game secretly helps the opponent's hidden route.","transfer_to_romhack":"Once ahead, making the game smaller is often strongest.","do_not_transfer":"Not a universal 'explode when ahead' rule.","mechanics_status":"vanilla_gsc","policy_trigger":"When you are already ahead and a sacrifice removes tactical volatility, prefer simplification, unless the smaller game secretly improves the opponent's route.","measurement_hook":"Does the trainee evaluate the post-trade endgame?"}
{"id":"P25","source_url":"https://www.coupcritique.fr/entity/actualities/136","source_type":"other","battle_format":"GSC OU","turn_number":null,"category_tags":["explosion","punishment","hidden-information","anti-pivot"],"public_state":"Poison has forced a CurseLax preserve and Golem is in against the forced-switch moment.","sealed_hidden_state":"Recap says OmBrArch pivoted to Gengar and Fakes clicked Earthquake to remove it; exact full-log details are uncertain.","candidate_moves_or_switches":["Earthquake","Rock Slide","prediction switch","conservative pivot"],"expert_move_or_recommended_line":"Earthquake is the best cover on the natural preserving pivot.","why_this_move":"Status-forced preservation narrows the switch tree enough for a hard punish.","worst_plausible_branch":"Play too safe and let the utility pivot reset the game.","irreplaceable_piece_or_resource":"Gengar as preserving pivot.","information_that_would_flip_the_answer":"Public evidence that Jolteon or a Flying-type pivot is materially more likely.","transfer_to_romhack":"Forced preservation often contracts the pivot tree.","do_not_transfer":"Exact set assumptions are recap-level, not full-log precise.","mechanics_status":"vanilla_gsc","policy_trigger":"When status forces the opponent to preserve their setup anchor, prefer hitting the most natural preserving pivot, unless better public evidence points elsewhere.","measurement_hook":"Does the trainee narrow the switch tree using preservation logic?"}
{"id":"P26","source_url":"https://www.coupcritique.fr/entity/actualities/136","source_type":"other","battle_format":"GSC OU","turn_number":null,"category_tags":["sacrifice-route","status","endgame-conversion"],"public_state":"Opponent's Snorlax lacks Rest and your own Snorlax wants a closing route.","sealed_hidden_state":"Recap says OmBrArch sacrificed Alakazam just to poison the non-Rest Snorlax, then won via his own CurseLax route.","candidate_moves_or_switches":["preserve Alakazam","chip passively","force poison at material cost"],"expert_move_or_recommended_line":"Sacrifice the expendable piece if permanent poison on the opposing anchor converts the endgame.","why_this_move":"Timer control over the anchor matters more than marginal material.","worst_plausible_branch":"Preserve everything and never create a real closing route.","irreplaceable_piece_or_resource":"Permanent poison on the enemy anchor.","information_that_would_flip_the_answer":"Cleric or Rest support still alive.","transfer_to_romhack":"Sacrifices are strongest when they change the enemy anchor's timer.","do_not_transfer":"Exact full sequence is medium-confidence recap, not full-log parsed.","mechanics_status":"vanilla_gsc","policy_trigger":"When permanent timer on the opposing anchor unlocks your own anchor, prefer the status-for-material trade, unless recovery support can erase it cheaply.","measurement_hook":"Does the trainee see why the sacrificed piece was expendable?"}
{"id":"P27","source_url":"https://www.smogon.com/gs/articles/gsc_guide_part1","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["preservation","pivoting","tempo"],"public_state":"You are in a bad on-board matchup and can stay, sack, or switch.","sealed_hidden_state":"Borat states that in GSC if you're in a mismatch you usually should switch instead of letting something die for vague reasons.","candidate_moves_or_switches":["stay and chip","sack","switch to real answer"],"expert_move_or_recommended_line":"Switch.","why_this_move":"KOs are worked for in GSC; casual sacks usually lose structural integrity for too little return.","worst_plausible_branch":"Donate a mon and watch the opponent answer the follow-up anyway.","irreplaceable_piece_or_resource":"Full defensive answer tree.","information_that_would_flip_the_answer":"Extra attack is guaranteed to convert a real winning threshold.","transfer_to_romhack":"Preserve answer identity unless cashing it for a real threshold.","do_not_transfer":"Not 'never sack'; rather 'never sack for foggy reasons'.","mechanics_status":"vanilla_gsc","policy_trigger":"When the board is a mismatch and no real threshold is gained by staying, prefer the switch, unless the sacrifice concretely advances a winning route.","measurement_hook":"Can the trainee explain what staying actually accomplishes?"}
{"id":"P28","source_url":"https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["preservation","cut-losses","curse-war","endgame"],"public_state":"A CurseLax chain has already snowballed through several pivots and you can keep preserving or cut losses.","sealed_hidden_state":"Guide warns that players often preserve too much; once the pivot chain already failed, cutting losses can be correct.","candidate_moves_or_switches":["keep preserving","commit one piece","aggressive reset line"],"expert_move_or_recommended_line":"Cut losses before every answer is functionally ruined.","why_this_move":"Late preservation can save names on paper while losing all future utility.","worst_plausible_branch":"Rotate until every answer is weakened and lose anyway.","irreplaceable_piece_or_resource":"Functional defensive integrity.","information_that_would_flip_the_answer":"An unrevealed set detail still gives a real reset line.","transfer_to_romhack":"Resource value decays with repeated bad preserving.","do_not_transfer":"Contextual, not blanket anti-pivot advice.","mechanics_status":"vanilla_gsc","policy_trigger":"When repeated preserving only worsens every answer's future utility, prefer cutting losses, unless you still retain a genuine reset line.","measurement_hook":"Does the trainee distinguish preserved HP from preserved function?"}
{"id":"P29","source_url":"https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["lead","no-team-preview","information-management"],"public_state":"You are choosing a lead in no-Team-Preview GSC.","sealed_hidden_state":"Guide argues lead advantage is only about one turn and static leads invite counter-leads and predictable first moves.","candidate_moves_or_switches":["always same lead","vary viable leads","overfit to one expected opener"],"expert_move_or_recommended_line":"Prefer viable lead variety over autopilot repetition.","why_this_move":"In no-preview formats, concealed team identity is a resource.","worst_plausible_branch":"Advisor becomes prey for counter-tech because it always leads the same way.","irreplaceable_piece_or_resource":"Early information asymmetry.","information_that_would_flip_the_answer":"Strong opponent-specific public evidence makes one lead clearly best.","transfer_to_romhack":"Lead choice is part of deception, not just matchup tables.","do_not_transfer":"Do not import Team Preview logic.","mechanics_status":"vanilla_gsc","policy_trigger":"When multiple viable leads exist and preview is absent, prefer unpredictability, unless opponent-specific evidence makes one lead clearly superior.","measurement_hook":"Does the trainee value hidden team identity in lead choice?"}
{"id":"P30","source_url":"https://www.smogon.com/forums/threads/part-6-complete-guide-to-battling-and-team-building-idiot-proof.3447576/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":1,"category_tags":["lead","pivot","hidden-information"],"public_state":"Lead Zapdos faces lead Nidoking and Hidden Power is the obvious first move.","sealed_hidden_state":"Guide explicitly says Snorlax can pivot into the obvious Hidden Power and flip the 'bad lead' into advantage.","candidate_moves_or_switches":["stay in and attack","go Snorlax","overpredict elsewhere"],"expert_move_or_recommended_line":"Snorlax pivot is best if the HP line is truly obvious.","why_this_move":"No-preview lead play often weaponizes obviousness.","worst_plausible_branch":"Follow the lead chart literally and miss the telegraphed move punish.","irreplaceable_piece_or_resource":"Snorlax's absorption and tempo flip.","information_that_would_flip_the_answer":"Lovely Kiss or another non-HP line is materially more likely.","transfer_to_romhack":"Predictability can matter more than nominal matchup.","do_not_transfer":"Assumes vanilla HP/lead dynamics.","mechanics_status":"vanilla_gsc","policy_trigger":"When the opponent's best first move is too obvious, prefer the pivot that flips that certainty into your advantage, unless alternate coverage is materially more likely.","measurement_hook":"Does the trainee look for obvious-move punishment?"}
{"id":"P31","source_url":"https://www.smogon.com/forums/threads/spl-xii-gsc-discussion-thread.3676008/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":1,"category_tags":["lead","counter-tech","uncertainty"],"public_state":"You are considering a Counter lead meant to punish Snorlax.","sealed_hidden_state":"Tournament discussion says Counter leads are high risk, need Lax leads, and especially want Double-Edge.","candidate_moves_or_switches":["bring/click Counter tech","use broad stable lead","hedge for Cloyster/Electrics"],"expert_move_or_recommended_line":"Do not overrate the Counter-lead line without a very narrow scout.","why_this_move":"The payoff is real, but the miss range is huge in no-preview lead fields.","worst_plausible_branch":"Model learns flashy T1 traps that mostly whiff.","irreplaceable_piece_or_resource":"Reliable opening structure.","information_that_would_flip_the_answer":"Very strong public evidence of Double-Edge Lax lead.","transfer_to_romhack":"High-payoff lead traps should stay low-confidence without narrow evidence.","do_not_transfer":"Metagame-risk assessment, not general mechanics fact.","mechanics_status":"vanilla_gsc","policy_trigger":"When a lead trap only works into a narrow opening subset, prefer stable play, unless public evidence sharply narrows the lead range.","measurement_hook":"Does the trainee discount low-frequency trap lines?"}
{"id":"P32","source_url":"https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":1,"category_tags":["lead","preservation","hazard","anti-golem"],"public_state":"You led Zapdos into a possible CurseLax and want to go straight to Cloyster.","sealed_hidden_state":"SPL XIII commentary criticizes this because it leaves you exposed to possible Golem teams behind the reveal.","candidate_moves_or_switches":["immediate Cloyster","safer broad answer","hold Zapdos","conservative scout"],"expert_move_or_recommended_line":"Do not autopilot Zapdos to Cloyster before the hidden backline is better mapped.","why_this_move":"The unseen team behind the active pair matters.","worst_plausible_branch":"Win the local matchup table and lose the hidden-team matchup behind it.","irreplaceable_piece_or_resource":"Early flexibility before the backline is known.","information_that_would_flip_the_answer":"Golem punish or similar line already disproven.","transfer_to_romhack":"Early turns should preserve optionality against hidden punishers.","do_not_transfer":"Specific analysis comes from a replay-review context.","mechanics_status":"vanilla_gsc","policy_trigger":"When a standard early pivot exposes you to one of the strongest unrevealed punishers, prefer the more flexible line, unless that punisher is already ruled out.","measurement_hook":"Does the trainee reason about unseen teammates instead of only the active matchup?"}
{"id":"P33","source_url":"https://www.smogon.com/forums/threads/gsc-mechanics.3542417/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["phazing","anti-setup","move-priority"],"public_state":"Both sides are in a Roar/Whirlwind race or setup-vs-phaze spot.","sealed_hidden_state":"Resource states that Roar and Whirlwind must go last to work in GSC, so the slower phazer wins the direct contest.","candidate_moves_or_switches":["race with faster phazer","preserve slower phazer","attack instead"],"expert_move_or_recommended_line":"Value the slower phazer more highly in direct phazing contests.","why_this_move":"Later-gen instincts misfire here.","worst_plausible_branch":"Preserve the faster phazer on autopilot and lose the phazing war.","irreplaceable_piece_or_resource":"The slower phazing body.","information_that_would_flip_the_answer":"Board no longer decided by direct phaze contest.","transfer_to_romhack":"Priority rules can invert which defensive piece matters most.","do_not_transfer":"Explicitly non-transferable to later gens.","mechanics_status":"vanilla_gsc","policy_trigger":"When the position is a true phazing race, prefer preserving the slower phazer, unless the turn is no longer decided by phazing mechanics.","measurement_hook":"Does the trainee know GSC phazing wants to move second?"}
{"id":"P34","source_url":"https://www.smogon.com/forums/threads/mean-look-spider-web-baton-pass-in-gsc-ou.3696148/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":1,"category_tags":["lead","sleep","baton-pass","phazing","anti-setup"],"public_state":"Lead Smeargle appears and your team has one critical phazer.","sealed_hidden_state":"Discussion says you only really lose T1 if your sole phazer gets slept; otherwise other sleep allocations are often survivable.","candidate_moves_or_switches":["let phazer absorb sleep","sack lower-value body","respond with sleep/thief lead","hard attack"],"expert_move_or_recommended_line":"Protect the sole phazer.","why_this_move":"Against pass chains, phazer value is route value.","worst_plausible_branch":"Preserve a random body and lose the only structural answer.","irreplaceable_piece_or_resource":"The only phazer.","information_that_would_flip_the_answer":"Multiple phazers or another hard anti-BP structure exist.","transfer_to_romhack":"Against setup chains, sleep allocation should protect the route-denying piece first.","do_not_transfer":"Assumes vanilla style phazing/pass interaction.","mechanics_status":"vanilla_gsc","policy_trigger":"When a setup lead threatens sleep and your team has one unique denial piece, prefer protecting that piece, unless redundant denial already exists.","measurement_hook":"Can the trainee identify the unique denial resource first?"}
{"id":"P35","source_url":"https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["baton-pass","anti-setup","preservation"],"public_state":"The opponent got the first Agility pass off.","sealed_hidden_state":"Sample-team anti-BP notes say surviving the first pass chain makes future prevention much easier; keep Cloyster/Skarmory awake and full.","candidate_moves_or_switches":["trade one check loosely","preserve the healthy hard stop","chase greed elsewhere"],"expert_move_or_recommended_line":"Preserve the awake full check even if the line is temporarily passive.","why_this_move":"The first chain is the hardest survival hinge.","worst_plausible_branch":"Use your check for short-term utility and no longer survive the first recipient.","irreplaceable_piece_or_resource":"Full-HP anti-recipient check.","information_that_would_flip_the_answer":"Spikes or prior chip already make the check insufficient.","transfer_to_romhack":"Preserve for the first collapse point against once-per-game explosive routes.","do_not_transfer":"Vanilla GSC BP counterplay, not generic anti-setup.","mechanics_status":"vanilla_gsc","policy_trigger":"When a pass chain is likely and one healthy check is your first survival hinge, prefer preserving that check, unless it can no longer survive the chain anyway.","measurement_hook":"Does the trainee value HP and sleep status on anti-setup pieces?"}
{"id":"P36","source_url":"https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["baton-pass","spikes","anti-setup","boldness"],"public_state":"You are defending against Baton Pass and can play passively or assertively around Jolteon/Smeargle turns.","sealed_hidden_state":"Anti-BP notes say Spikes matter because pass teams don't run Leftovers everywhere and that one must often be bold to deny setup turns.","candidate_moves_or_switches":["passive predictable switching","set Spikes","stay in with Skarmory on Jolteon","let Tyranitar take manageable chip"],"expert_move_or_recommended_line":"Use Spikes and deny free setup turns, even if that means taking respectable chip.","why_this_move":"Predictable always-respect lines are exactly what BP farms.","worst_plausible_branch":"Give three clean setup turns because every click was too polite.","irreplaceable_piece_or_resource":"Free-turn denial.","information_that_would_flip_the_answer":"The hit would destroy your only live answer.","transfer_to_romhack":"Against fragile setup structures, turn economy beats surface HP neatness.","do_not_transfer":"Do not import modern BP bans or mechanics.","mechanics_status":"vanilla_gsc","policy_trigger":"When the opposing strategy needs uncontested setup turns more than clean attacks, prefer denying the free turn, unless the denied hit would destroy your only live answer.","measurement_hook":"Does the trainee separate taking damage from giving a setup turn?"}
{"id":"P37","source_url":"https://www.smogon.com/forums/threads/spl-xvi-gsc-discussion.3757711/page-2","source_type":"forum analysis","battle_format":"GSC OU","turn_number":null,"category_tags":["anti-setup","phazing","preservation"],"public_state":"Your structure dropped Machamp and now depends on Reflect + WW Zapdos and Hypnosis Gengar as CurseLax counterplay.","sealed_hidden_state":"Prep post explains those exact set choices were direct responses to CurseLax after choosing Gengar over Machamp.","candidate_moves_or_switches":["use Zapdos/Gengar casually","preserve them for CurseLax","spend Hypnosis elsewhere"],"expert_move_or_recommended_line":"Preserve the pieces assigned to the specific setup hole you created in builder.","why_this_move":"Once role compression shifts, the preservation hierarchy shifts too.","worst_plausible_branch":"Spend those tools casually and face the exact threat they were chosen to stop.","irreplaceable_piece_or_resource":"Explicit anti-CurseLax assignment.","information_that_would_flip_the_answer":"Opposing Snorlax now identified as non-Curse or otherwise passive.","transfer_to_romhack":"Preservation depends on role assignment, not species fame.","do_not_transfer":"Prep-context commentary is not a universal set prescription.","mechanics_status":"vanilla_gsc","policy_trigger":"When a piece was selected to patch one matchup hole, preserve it for that hole, unless public info has already disproved the threat.","measurement_hook":"Does the trainee preserve by function rather than by name?"}
{"id":"P38","source_url":"https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":"25+","category_tags":["pp","endgame","preservation","mono-lax"],"public_state":"Umbreon is the main line into MonoLax, but Moonlight PP is already being taxed and Smeargle remains live.","sealed_hidden_state":"Commentary stresses Umbreon's 8 Moonlight PP timer and how that timer enables later Smeargle/Marowak pressure.","candidate_moves_or_switches":["keep leaning on Umbreon every time","preserve Moonlight PP","trade elsewhere sooner"],"expert_move_or_recommended_line":"Preserve Moonlight PP like a hard resource.","why_this_move":"In long GSC endings, PP is often the real HP bar.","worst_plausible_branch":"Stabilize locally every turn while slowly running out of the only move that keeps the matchup alive.","irreplaceable_piece_or_resource":"Moonlight PP.","information_that_would_flip_the_answer":"MonoLax no longer threatens or Umbreon gets outside support.","transfer_to_romhack":"Limited-recovery PP should be modeled as a strategic countdown.","do_not_transfer":"Depends on Umbreon's move economy and this matchup texture.","mechanics_status":"vanilla_gsc","policy_trigger":"When one recovery move is your only long-game stabilizer, prefer preserving its PP, unless cashing it now prevents immediate collapse.","measurement_hook":"Does the trainee track recovery PP as a first-class resource?"}
{"id":"P39","source_url":"https://www.smogon.com/forums/threads/spl-xiii-gsc-discussion-thread.3695006/","source_type":"forum analysis","battle_format":"GSC OU","turn_number":25,"category_tags":["rapid-spin","hidden-route","hazards","sacrifice-management"],"public_state":"You can accept Toxic on Golem in exchange for Spin because your hidden win condition badly wants a clean field.","sealed_hidden_state":"Replay analysis says taking Toxic for Spin was reasonable because the concealed route cared far more about no Spikes than about Golem staying clean.","candidate_moves_or_switches":["save Golem clean","take Toxic and Spin","pivot elsewhere"],"expert_move_or_recommended_line":"Take the Toxic if removing Spikes is the real route enabler.","why_this_move":"Not all damage is equal; one status can be cheaper than one permanent layer.","worst_plausible_branch":"Preserve the spinner's cleanliness while suffocating the actual route under Spikes.","irreplaceable_piece_or_resource":"A clean field for the hidden route.","information_that_would_flip_the_answer":"Toxic also destroys Golem's indispensable endgame role.","transfer_to_romhack":"Value damage and status relative to the planned route.","do_not_transfer":"Specific hidden-route analysis context.","mechanics_status":"vanilla_gsc","policy_trigger":"When one status trade unlocks the field condition your hidden route needs, prefer the trade, unless the status destroys that same route elsewhere.","measurement_hook":"Does the trainee compare field-state value against individual mon cleanliness?"}
{"id":"P40","source_url":"https://www.smogon.com/gs/articles/gsc_spikes","source_type":"article","battle_format":"GSC OU","turn_number":null,"category_tags":["pp","heal-bell","status","endgame"],"public_state":"Your hazard/status route has finally forced the opponent to lean on Heal Bell.","sealed_hidden_state":"Spikes article says to plan around Bell: punish the switch-in, deny its entry, or exhaust Bell's 8 PP.","candidate_moves_or_switches":["accept Bell passively","attack the cleric switch-in","route toward Bell PP exhaustion"],"expert_move_or_recommended_line":"Treat the Bell turn as a punishable or exhaustible resource turn.","why_this_move":"Bell is part of the endgame economy, not a reset button outside the game.","worst_plausible_branch":"Spread status for twenty turns without ever constraining the status cleanse itself.","irreplaceable_piece_or_resource":"Heal Bell PP and cleric punish windows.","information_that_would_flip_the_answer":"No Bell present or Bell no longer strategically relevant.","transfer_to_romhack":"Cleanses and recovery buttons should be modeled as finite route resources.","do_not_transfer":"Assumes vanilla Bell access and PP unless local movepools changed.","mechanics_status":"locally_supplied_romhack_evidence_needed","policy_trigger":"When the opponent relies on finite teamwide status cleansing, prefer punishing or exhausting the cleanse, unless the board demands a different immediate answer.","measurement_hook":"Does the trainee track Bell PP and the punish window on the cleric?"}
```

## Open questions and limitations

A few entries are deliberately marked medium-confidence rather than overclaimed. The biggest reason is source shape: some tournament positions are preserved in high-quality recap prose or forum review rather than in a directly parsed replay log, so the tactical hinge is clear but the exact HP/PP ledger is not. That especially affects **P25** and **P26**, and to a lesser extent any turn-numbered forum-analysis position where the reviewer emphasizes the decision more than the full board ledger. Those positions are still valuable training material, but they should be labeled as **commentary-grounded** rather than “full-log exact.” citeturn14view0turn40view0

A second limitation is romhack uncertainty. Several excellent vanilla lessons depend on movepool legality, PP, or exact move behavior. The most obvious example is **Cloyster Rapid Spin + Explosion**, illegal in vanilla but possibly changed in a romhack. Heal Bell access and PP, Baton Pass legality, and event-move availability can also matter. Any local content pack for the advisor should therefore include a small verified mechanics appendix so the model knows whether to keep, soften, or discard each `locally_supplied_romhack_evidence_needed` lesson. citeturn38view0turn34view4

## Transfer Rules For A GSC-Based Romhack

**Preserve route-defining answers, not just strong Pokémon.** If one piece uniquely keeps Spikes, denies setup, or resets status, preservation priority should follow that role map, not species prestige. citeturn41view0turn42view1

**Use no-preview lead choice as information warfare.** A good lead is not only the one with the best matchup chart; it is the one that keeps your first move and your team identity hard to read. citeturn40view2turn39search16

**Treat sleep as an allocation problem.** The best sleep target is often the offensive anchor or defensive blocker that matters most for the route, not the first available legal target. citeturn36view0

**Do not waste sleep into obvious RestTalk absorbers.** In GSC, the threat of sleep often generates more value than the landed sleep. citeturn25view3turn36view0

**Respect GSC RestTalk and Rest cycles as active game pieces.** Sleeping Talkers can still advance, and Sleep Talk can hit Rest in vanilla GSC. citeturn25view3turn38view0

**Model Spikes as a full subgame, not a checkbox.** “Spikes are up” is not enough; ask whether they are likely to stay up and what piece secures that. citeturn34view0turn41view0

**Against the best remover, pick the status that constrains its future menu.** In vanilla GSC that often means Toxic against Starmie, not greedier status lines. citeturn34view3turn34view4

**Explosion and Selfdestruct should be trained as route-conversion moves.** The right boom removes the specific wall, remover, or setup threat blocking your win condition. citeturn26view0

**Sometimes the threat of Explosion is worth more than the move.** If the opponent’s anti-boom pivot is punishable, cash the fear and keep the boom. citeturn26view0

**When ahead, simplify ruthlessly if the smaller game is still favorable.** Explosion can be an endgame-conversion tool, not only a wallbreaker. citeturn26view0

**If the board is a mismatch, default to switching, not foggy sacrifice.** GSC generally rewards preserving answer trees over casual chip-sacks. citeturn37view0turn40view2

**But do not preserve too much.** Once preserving only degrades every answer, cutting losses becomes the higher-skill line. citeturn40view2

**In direct phazing contests, slower is better in vanilla GSC.** That is a generation-specific rule and should not be overwritten by later-gen instincts. citeturn38view0turn24search3

**Track PP on clutch recovery and cleanse moves as real strategic resources.** Moonlight, Heal Bell, Pursuit, and Recover loops regularly decide GSC endgames. citeturn34view3turn35view0turn42view0

**Do not transfer vanilla legality into the romhack without proof.** Anything that depends on movepool legality or altered mechanics should be gated behind local evidence rather than assumed. citeturn38view0
