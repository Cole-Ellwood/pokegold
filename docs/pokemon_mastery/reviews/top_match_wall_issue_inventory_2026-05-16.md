# Top-Match Wall Issue Inventory - 2026-05-16

Purpose:
Document the specific issues that are preventing top-match improvement. This is
not a new live card and not a proof claim. It is a detailed inventory for a
future stronger reviewer or new session to diagnose why severe, hidden-info,
state, and mechanics errors have improved faster than exact move prediction.

Evidence base:

- `active_context.md`, measurement snapshot through packet 044.
- `training_method_review_006_2026-05-15.md`.
- `training_method_review_007_2026-05-16.md`.
- `route_budget_tiebreaker_annotation_001_2026-05-16.md`.
- `workspace/quick_tests/side_known_transfer_044_smogtours-gen2ou-821941_p1_2026-05-16.md`.
- `measurement_progress_ledger.csv`.

## Current Pattern

The project has improved at avoiding the obvious ways to be wrong:

- fewer severe blunders;
- fewer hidden-info anchoring errors;
- fewer mechanics errors;
- better no-Team-Preview discipline;
- better role/package update discipline after public reveals;
- better ability to name plausible candidates.

It has not improved much at exact top-match. The relevant recent numbers:

- Packets 038-040: 49/90 top, 78/90 acceptable.
- Packets 041-043: 48/89 top, 72/89 acceptable.
- Packet 044: 15/30 top, 29/30 acceptable, 25/30 actual in top three, 27/30
  actual branch named, 0 severe, 0 hidden-info, 1 state, 0 mechanics.

That means the current failure is usually not "I did not see the move at all."
It is "I saw the actual move or branch, but ranked another plausible move
first."

## Confirmed Central Blocker

The main blocker is top-rank ordering after candidate generation succeeds.

Packet 044 made this unusually clear. The actual move or switch appeared in my
frozen top three 25/30 times, and the actual branch was named before reveal
27/30 times. Exact top was still only 15/30.

This rules out the simplest explanation that the docs are merely missing lots
of facts. Missing facts still happen, but they are no longer the dominant
failure. The dominant failure is deciding which already-named route should be
ranked first.

## Issue 1: Route-Budget Tiebreaking Is Weak

Symptom:
I often choose the move that looks most active - damage, status, phaze, branch
punish, or immediate pressure - when the better move is to preserve the route
piece, Rest, absorb a sleep turn, or make a lower-cost handoff.

Why this blocks top-match:
GSC games often convert through repeated forced entries, Rest clocks, Spikes
tax, and ownership preservation. Once pressure already exists, the best move is
often not the move that adds the most visible progress this turn. It is the move
that keeps the scarce piece alive long enough for the already-created pressure
to matter.

Packet 044 examples:

- Turn 18: I wanted to switch Cloyster into Forretress to contest hazards. The
  replay kept sleeping Skarmory in and preserved Cloyster while Forretress used
  Spikes.
- Turn 24: I wanted Raikou to Thunderbolt. The replay used Rest as Snorlax
  came in, preserving Raikou's Zapdos job.
- Turn 30: I wanted Snorlax to Double-Edge Zapdos/Rhydon. The replay used Rest
  as Rhydon came in, preserving Snorlax before the counter-owner sequence.

Underlying mistake:
I ask "what move converts?" but not consistently "has conversion already been
created, and is the next move mainly about not losing the converter?"

Current repair:
`reset_loop_denial.md` now has a fast tiebreaker: if Spikes, Rest, phaze,
status, or correct-owner handoff already created pressure, chip/status/coverage
is top only when it forces the next choice before the route piece becomes
scarce.

Remaining gap:
That tiebreaker has not been tested on a fresh packet yet. It is a hypothesis,
not proof.

## Issue 2: I Undervalue Future Entry Tax

Symptom:
I correctly notice Spikes are up, but I do not always translate that into a
future-entry budget for each route piece.

Why this blocks top-match:
With p1-side Spikes up, each grounded switch can be a large irreversible cost.
The correct move may be Rest now, stay in now, or use the typed owner now
because switching later will be too expensive.

Packet 044 examples:

- Raikou versus Zapdos: I sometimes treated Raikou as a reusable answer without
  fully pricing that each entry through Spikes plus Thunderbolt/phaze pressure
  could make it fail as the Zapdos owner.
- Snorlax versus Zapdos/Rhydon: I saw Double-Edge as active conversion, but the
  replay preserved Snorlax before Rhydon could force the next HP-budget crisis.
- Cloyster versus Forretress: I wanted to spend Cloyster to contest immediately,
  but keeping it healthy preserved the later spinner/hazard mirror.

Underlying mistake:
I track current HP, but I do not reliably calculate "how many useful future
entries does this piece have after this move?"

Needed improvement:
Before ranking a switch or attack, explicitly price the next forced entry for
the unique job holder: spinner, Electric absorber, special sponge, phazer,
spinblocker, RestTalker, or breaker.

## Issue 3: I Do Not Reliably Know When Pressure Is Already Sufficient

Symptom:
I chase extra chip, extra status, or extra phazing after the route already has
enough pressure to force a useful future choice.

Why this blocks top-match:
Extra progress is not always real progress. If the opponent is already forced
by Spikes, Rest sleep, status, or a bad owner, the best move may be to avoid
letting the opponent trade into the scarce piece.

Packet 044 examples:

- Turn 19: Whirlwind was a plausible route move, but Hidden Power into the
  Snorlax switch converted the already-created Spikes pressure more precisely.
- Turn 30: Double-Edge would add chip, but Rest converted the existing Zapdos
  pressure and incoming Rhydon branch by preserving Snorlax.

Underlying mistake:
I treat "more immediate route action" as better than "maintain the route that
is already winning enough."

Needed improvement:
Add a mental stop check before clicking active pressure: "What happens if I do
nothing aggressive and let the existing pressure continue?"

## Issue 4: I Over-Rank Generic Phazing When No Specific Reset Must Be Denied

Symptom:
I choose Whirlwind/Roar because Spikes are up and phazing looks route-positive,
even when direct damage or preservation is more precise.

Why this blocks top-match:
Phazing is not progress by itself. It is progress when it denies setup, denies
Rest/Recover loops, preserves Spikes damage, or forces a bad entry. If the
opponent is already switching or no reset must be stopped, phazing can be a
generic script.

Packet 044 examples:

- Turn 19: I ranked Whirlwind first into Forretress/Rhydon/Snorlax dynamics.
  The replay used Hidden Power and caught Snorlax switching through Spikes.
- Turn 20: I ranked Whirlwind into RestTalk Snorlax. The replay used Toxic and
  missed as Snorlax Rested. My line may have been more route-logical than the
  actual, but the mismatch still shows phazing was too easy for me to promote.

Underlying mistake:
I sometimes say "Spikes are up, so phaze converts" without naming the exact
setup/reset route that phaze denies this turn.

Needed improvement:
Before ranking phaze first, answer: "What exact thing fails if I do not phaze
now?" If the answer is vague, direct damage, Rest, Toxic, or handoff may be
better.

## Issue 5: I Misprice Correct Owner Versus Active Branch Punish

Symptom:
I sometimes choose a move that punishes a named branch, but the replay chooses
the correct typed owner or defensive owner instead.

Why this blocks top-match:
Branch punish is not automatically better than ownership. In GSC, keeping the
right owner assigned can matter more than punishing one branch, especially when
the branch punish is inaccurate, resisted, low-value, or exposes a future
piece.

Packet 044 example:

- Turn 28: Heracross was in against revealed Whirlwind Zapdos. I wanted
  Megahorn to punish Whirlwind/switch pressure before negative-priority phaze.
  The replay switched to sleeping Raikou, accepting Spikes plus Thunderbolt
  because Raikou was still the typed Zapdos owner.

Underlying mistake:
After learning "named branches must change ranking," I can overcorrect and
rank the branch punish above the owner even when the owner is the route.

Needed improvement:
Branch-punish ranking must be subordinate to owner scarcity: if the typed owner
is still required and the branch punish does not force a clear range, owner
handoff can be first.

## Issue 6: I Do Not Have a Strong Enough Branch Probability Model

Symptom:
I name multiple branches correctly but do not estimate which branch an expert
is most likely to respect or induce.

Why this blocks top-match:
Top-match is not just finding legal good moves. It is predicting the expert's
first-ranked move under realistic opponent incentives. If I name Zapdos,
Rhydon, Forretress, and Snorlax, but cannot weight stay, switch, phaze, Rest,
or hazard action, I will often put the actual second or third.

Packet 044 examples:

- Turn 1: I chose Double-Edge into lead Zapdos. Actual switched Raikou while
  opponent switched Forretress. The branch was plausible, but I weighted active
  damage too high.
- Turn 9: I wanted Skarmory into Snorlax. Actual Cloyster entered as Snorlax
  Rested, turning the Rest branch into Spikes pressure.
- Turn 19: I named Snorlax branch but did not rank Hidden Power first.

Underlying mistake:
The current prompt forces branch naming, but it does not force branch
probability or opponent utility. It asks "what can happen?" more reliably than
"what is the opponent incentivized to do?"

Needed improvement:
For nontrivial turns, add a short branch weighting before final rank:
"active stays because X; receiver enters because Y; reset move happens because
Z." Do this without anchoring possible-only hidden info.

## Issue 7: I Sometimes Obey the Named Branch Too Weakly

Symptom:
I name a branch and still rank a move that does not beat it.

Why this blocks top-match:
This is worse than bad probability weighting. If the actual branch is named and
the top move fails into it, then the issue is not missing information; it is
failure to obey my own reasoning.

Packet 044 example:

- Turn 22: I named sleeping Snorlax as a switch branch but ranked Toxic first
  into Rhydon. Snorlax was already asleep, so Toxic could not convert that
  branch. The actual Whirlwind covered the branch and dragged Zapdos.

Underlying mistake:
The branch list is sometimes treated as commentary rather than a hard filter on
the ranked top move.

Needed improvement:
Before freezing, run a branch legality check: "If each named branch happens,
does my top move still do something useful?" If the answer is no for a likely
branch, the top move needs demotion.

## Issue 8: Public State Obedience Still Has Rare Leaks

Symptom:
Most state/mechanics errors are gone, but one public state contradiction can
still break top-match.

Why this blocks top-match:
Top-match can survive uncertain strategy, but it cannot survive a state
contradiction such as using Toxic into an already sleeping target, assuming a
sleep turn incorrectly, or missing that a phaze move is negative priority.

Packet 044 example:

- Turn 22 was a state error because I ranked Toxic while naming an already
  sleeping Snorlax branch.

Underlying mistake:
The state ledger is present, but the final candidate ranking does not always
re-check it.

Needed improvement:
The final top-three should be filtered by a "dead move against public branch"
check: status into already-statused target, Electric into Ground if the Ground
branch is the main read, phaze after likely KO before move, Rest when already
at full unless tempo reason exists, and so on.

## Issue 9: I Lack a Quantitative Enough Multi-Turn EV Model

Symptom:
My route explanations are verbal, not consistently comparative over two or
three turns.

Why this blocks top-match:
Exact top often depends on a small multi-turn tradeoff: taking chip now versus
Resting now, spending a switch now versus preserving a future entry, phazing
now versus attacking the receiver. A verbal route transaction can name all
pieces but still miss the marginal value.

Packet 044 examples:

- Raikou Rest on Turn 24 only makes sense if future Zapdos entries are priced.
- Snorlax Rest on Turn 30 only makes sense if Rhydon plus Spikes plus future
  Thunderbolt pressure are priced.
- Cloyster preservation on Turn 18 only makes sense if the later hazard mirror
  is worth more than contesting Forretress immediately.

Underlying mistake:
I compare candidate moves by narrative quality more than by "what board exists
after two turns, and which route piece is still usable?"

Needed improvement:
For hard turns, force a minimal two-turn board delta:
"If top succeeds, board after two turns is X with piece Y alive. If second
candidate succeeds, board is Z with piece Y spent."

## Issue 10: Exact-Top Replay Oracle Includes Player Style And Hidden Reads

Symptom:
Some actual moves are not necessarily objectively best from public information.
They may reflect player style, opponent history, risk appetite, tournament
state, or private predictions.

Why this blocks top-match:
If every mismatch is treated as a lesson, the docs will absorb noise. This can
make top-match worse by teaching overfitted replay imitation instead of general
singles advice.

Packet 044 examples:

- Turn 20: I ranked Whirlwind into RestTalk Snorlax. Actual Toxic missed while
  Snorlax Rested. This may be a reasonable expert line, but it is not obviously
  superior to phazing the Rest reset.
- Turn 27: Zapdos revealed Whirlwind. I did not predict it because it was not
  public yet. Scoring the exact miss is fair, but it should not become a
  hidden-info lesson.

Underlying mistake:
Top-match is useful but noisy. It must be interpreted with acceptable-match,
route-conversion, branch-punish, and hidden-info discipline.

Needed improvement:
Keep classifying misses as `oracle_style`, `hidden_package_reveal`, or
`candidate_weighting` instead of promoting every exact mismatch to a rule.

## Issue 11: Hidden Package Reveals Create Unavoidable Exact Misses

Symptom:
A move can be correct under public info and still miss exact top because the
opponent reveals a hidden package move.

Why this blocks top-match:
The no-Team-Preview discipline correctly forbids anchoring on possible-only
hidden moves. That means exact top will sometimes be lower than replay oracle
when a hidden move first appears.

Packet 044 example:

- Turn 27: Zapdos revealed Whirlwind and dragged Raikou. I did not anchor on
  Zapdos Whirlwind before it was public, which was correct. Exact top missed,
  but hidden-info discipline held.

Underlying mistake:
This is not a strategic mistake by itself. The issue is measurement
interpretation: do not let hidden reveal misses look like failure to learn.

Needed improvement:
Keep hidden reveal misses out of policy promotion unless the move was a strong
prior that should have been priced as a high-risk branch with fallback.

## Issue 12: Own-Move Reconstruction Can Be Sparse Or Late

Symptom:
Side-known prompts reconstruct own moves eventually shown in the replay. Before
a move is shown, the side-known helper may list incomplete move information.

Why this blocks top-match:
If an own move is missing from the prompt, the candidate set may be incomplete.
That can create false top-match misses or make the model overuse the visible
moves.

Evidence from prior method reviews:
Packet 040 had sparse side-known reconstruction and caused a method stop. The
completeness prefilter improved this but did not eliminate all uncertainty.

Underlying mistake:
The training method sometimes asks for an expert move with partial own-set
knowledge, while the actual player knows their full set.

Needed improvement:
Continue marking access mode and own-move gaps. Do not promote a lesson from a
turn where the actual move was unavailable in side-known prompt unless the
access-mode limitation is explicit.

## Issue 13: I Overfit Constructed Regression Probes

Symptom:
Constructed probes are often passed after a repair, but fresh replay top-match
does not move much.

Why this blocks top-match:
Constructed probes confirm that a rule can be repeated when the issue is
obvious. They do not prove the rule will be retrieved and weighted correctly in
a noisy board with multiple plausible routes.

Evidence:
Several nonblind drills passed: irreversible converter, resisted Explosion
board delta, stall route budget. Fresh side-known packets after those repairs
remained flat.

Underlying mistake:
The training loop can mistake "I can recite/apply the lesson in a clean probe"
for "I will rank it first under pressure."

Needed improvement:
Use constructed probes only as regression checks. The next proof must be fresh
side-known packets with exact top, acceptable, route-conversion, branch-punish,
and error gates tracked together.

## Issue 14: More Notes Can Make Retrieval Worse

Symptom:
The project contains many repeated versions of the same lesson. Before the
cleanup, reading more docs did not reliably improve fresh move choice.

Why this blocks top-match:
If the live context contains too many overlapping rules, the model can satisfy
one rule while violating another. For example, "punish named branch" can fight
"preserve scarce route piece" unless the current board identifies which rule
dominates.

Evidence:
The simplified system felt easier and produced better acceptable-match, but it
did not lift exact top. This suggests the docs were previously too large, but
size was not the only blocker.

Underlying mistake:
Documentation volume is not skill. The live system needs fewer rules with
clear dominance order, not more repeated reminders.

Needed improvement:
Keep live cards tiny. Move evidence and examples into reviews/workspace. Add
front-door tiebreakers only when repeated fresh misses prove a rule needs
promotion.

## Issue 15: Rule Dominance Is Under-Specified

Symptom:
Several correct heuristics apply at once, but the system does not always say
which one wins.

Why this blocks top-match:
Top-match is often decided by dominance between two good rules:

- branch punish versus owner preservation;
- phaze versus direct receiver damage;
- active chip versus Rest;
- Spikes conversion versus spinner preservation;
- exact removal versus overguard;
- status clock versus immediate damage.

Evidence:
Packet 044 had many acceptable misses where the actual was in top three. Those
are dominance failures more than knowledge failures.

Underlying mistake:
The cards say what matters, but not always the priority order when two things
matter at once.

Needed improvement:
Future repairs should state dominance in if/then form:
"If pressure already exists and the active move does not force the next choice,
preservation beats chip." Avoid adding another broad reminder without a
dominance condition.

## Issue 16: I Still Use Generic "Route Conversion" Too Broadly

Symptom:
I give positive-selection credit to moves that are route-aware, but the exact
top still misses because the chosen route is not the highest-value route.

Why this blocks top-match:
Positive selection is necessary but too broad. A move can be route-oriented and
still be wrong because it converts the wrong branch, spends the wrong piece, or
converts too late.

Packet 044 evidence:
Positive-selection was 28/30 while top-match was 15/30. That gap is huge.

Underlying mistake:
The model has learned to avoid safe/generic non-routes, but it has not learned
to compare two route-positive actions sharply enough.

Needed improvement:
Track "route_converting_move_chosen" and "branch_punish_chosen" separately, but
also require a tiebreaker sentence for why the top route beats the second route
when both are positive.

## Issue 17: I Lack Expert-Style Risk Appetite Calibration

Symptom:
I sometimes choose the safer-looking route when the expert chooses an active
line, and sometimes choose the active line when the expert preserves.

Why this blocks top-match:
Top-match needs calibration to expert risk appetite, not only strategic
legality. Experts often know when a position has enough pressure and when a
seemingly passive Rest is actually the aggressive route because it preserves
the winning owner.

Examples:

- I over-attacked with Double-Edge or Thunderbolt when Rest was the expert
  preservation line.
- I over-preserved or phazed when direct Hidden Power chip was the expert
  precision line.

Underlying mistake:
I do not yet have a stable prior for "expert will accept this much risk for
this much conversion."

Needed improvement:
Expert annotation should focus on tiebreakers, not only actual moves:
"why did the expert accept this risk and reject the other plausible route?"

## Issue 18: Opponent Incentive Modeling Is Too Shallow

Symptom:
I name possible opponent branches but often do not reason from the opponent's
needs: what they must preserve, what they are trying to reset, what they are
happy to trade, and what they are trying to reveal.

Why this blocks top-match:
Exact top depends on predicting which branch is live under both players'
incentives. If I only list branches, my top move may beat a low-value branch
instead of the branch the opponent is actually incentivized to choose.

Packet 044 examples:

- Forretress entering while Skarmory slept was a hazard-control invitation, but
  the actual first action was Spikes rather than immediate Spin.
- Rhydon entering on Snorlax created a preservation window for Rest, not just a
  target for Double-Edge.

Underlying mistake:
The current transaction format says "their package -> our answer -> next owner
-> punish," but it does not force "why would they choose that next owner now?"

Needed improvement:
Add an opponent utility note for hard turns: "Their best branch is likely X
because it preserves Y / resets Z / forces W."

## Issue 19: The Current Metrics Expose The Wall But Do Not Yet Fix It

Symptom:
The added labels are working diagnostically, but they have not produced fresh
improvement yet.

Why this blocks top-match:
Measurement improvements can make the failure clearer without making the model
stronger. Packet 044 diagnosed the problem well, but exact top remained flat.

Evidence:
The new labels showed:

- actual in top three: 25/30;
- actual branch named: 27/30;
- top still only 15/30.

Underlying mistake:
It is easy to mistake better measurement for better play.

Needed improvement:
The next packet must test whether the route-budget tiebreaker changes ranking,
not merely whether the artifact labels are more informative.

## Issue 20: Severe-Blunder Avoidance Can Hide Skill Stagnation

Symptom:
Clean severe/hidden/mechanics gates can make a packet feel better than it is.

Why this blocks top-match:
The user explicitly wants positive move selection, not just error suppression.
If severe errors drop but exact top, route conversion, and branch-punish do not
improve, the advisor is safer but not meaningfully stronger.

Evidence:
Packet 044 had clean severe/hidden/mechanics and excellent acceptable-match,
but exact top was still flat.

Underlying mistake:
The model naturally treats "no big errors" as success. The project target
requires correct first-choice pressure, not merely acceptable lines.

Needed improvement:
Final progress claims must lead with exact top and positive-selection movement,
not with severe-blunder avoidance.

## Issue 21: Fresh Replay Review May Be The Wrong Main Training Tool If This Persists

Symptom:
Repeated replay packets identify similar ranking failures but do not by
themselves correct the tiebreaker.

Why this blocks top-match:
If the method repeatedly says "route-budget/preservation miss" without changing
the next packet, then more replay volume is not training. It is measurement.

Evidence:
The plateau loop has already triggered multiple times. Training method review
006 and 007 both found flat exact top after repairs.

Underlying mistake:
Replay prediction creates many noisy examples but not necessarily enough
deliberate contrast between the top two candidate moves.

Needed improvement:
If the next fresh packet remains flat, switch one block to contrastive expert
annotation or pairwise ranking drills:

- present two plausible moves from a real replay;
- ask which wins and why;
- force the scarce-piece and pressure-already-created tiebreaker;
- then test on fresh replay.

## Issue 22: The "1500 Elo Proxy" May Need A Better Oracle Than Exact Imitation Alone

Symptom:
Exact replay top-match is useful, but some expert actual moves are not clean
public-information proof.

Why this blocks top-match:
A solid singles advisor should sometimes disagree with a replay move if the
replay move depends on private reads, style, or hidden context. Conversely,
always chasing exact top may train imitation over advice quality.

Evidence:
Packet 044 had 29/30 acceptable but 15/30 top. Some misses were real ranking
failures. Others were plausibly oracle style or hidden package reveal.

Underlying mistake:
The current proof gate treats exact top as the main scoreboard, but advice
quality may need a second oracle: expert annotation, multi-turn outcome, or
route-quality review.

Needed improvement:
Keep exact top as a pressure metric, but do not let it be the only target.
Track acceptable, route-conversion, branch-punish, actual-in-top-three,
state/hidden/mechanics, and post-reveal route quality together.

## Issue 23: I Need Better "Do Nothing Active" Discipline

Symptom:
I underselect turns where the right move is basically to stay, Rest, burn a
sleep turn, or let the opponent reveal into an already prepared answer.

Why this blocks top-match:
In long GSC games, the move that looks passive can be the strongest move
because it denies the opponent a profitable trade. This is especially true
after Spikes or status already make switching painful.

Packet 044 examples:

- staying with sleeping Skarmory on Turn 18;
- Resting Raikou on Turn 24;
- Resting Snorlax on Turn 30;
- using the typed owner rather than attacking with Heracross on Turn 28.

Underlying mistake:
The positive-selection objective corrected "safe/generic" passivity, but it
may have made me suspicious of passive-looking moves even when they are the
route-improving choice.

Needed improvement:
Positive selection must include route-preserving passivity when it improves the
multi-turn route. The question is not "is the move active?" but "does the move
improve the realistic win route?"

## Issue 24: I Need Stronger End-Of-Ranking Audit

Symptom:
The answer can contain the right facts but still freeze the wrong top action.

Why this blocks top-match:
The final ranking is where the mistake happens. Reading more docs before the
answer will not fix a weak final audit.

Needed final audit before freezing a hard turn:

1. Did I name the current owner and next owner?
2. Did I price p1-side and p2-side Spikes as future-entry budgets?
3. Did I identify whether pressure already exists?
4. Does my top move force the next choice, or only add chip/status?
5. Which unique route piece becomes scarce if I click my top?
6. If the actual named branch happens, does my top still function?
7. Is a passive-looking Rest/stay/phaze/handoff actually the stronger route?
8. Is my top relying on possible-only hidden information?
9. Is the replay oracle likely noisy because of hidden reveal, style, or own
   move gap?

This audit must stay short enough to use live. If it becomes another long
checklist, it will recreate the context problem.

## What Is Not The Main Problem Anymore

These issues still matter, but they are not the dominant current wall:

- Raw GSC mechanics knowledge. Mechanics errors are now low in recent packets.
- Hidden-info discipline. Hidden errors are now low, and possible-only branches
  are usually labeled instead of anchored.
- Candidate generation. Packet 044 had actual in top three 25/30.
- Branch naming. Packet 044 had actual branch named 27/30.
- Massive doc size. The simplified system felt easier and produced a cleaner
  packet, although exact top stayed flat.

## Most Important Next Test

The next fresh side-known packet should answer one question:

Does the route-budget tiebreaker improve exact first-choice ranking without
reducing acceptable-match, branch-punish, route-conversion, or clean
severe/hidden/state/mechanics gates?

If yes, keep training on route-budget tiebreakers and gather more fresh volume.
If no, stop replay grinding again and change method toward pairwise expert
ranking drills or a stronger outside review of the tiebreaker logic.

## Short Version For Future Reviewer

The advisor is no longer mainly losing because it lacks facts. It is losing
because it misorders good candidates. It sees the branch, usually includes the
actual in top three, then chooses the more visibly active route when the expert
often preserves the scarce route piece, Rests before entry-tax failure, keeps
the typed owner assigned, or lets existing pressure continue. The next repair
must improve that exact tiebreaker, not add more broad notes.
