According to a document from 2026-05-14, yes: that is the most plausible read of the current evidence. The loop is getting better at not doing obviously illegal, hidden-info, or route-losing things, but it is not yet clearly getting better at picking the strongest move.

The evidence is pretty blunt. First 20 fresh rows: 146/405 top-match, 233/405 acceptable, 5 severe blunders. Latest 20 fresh rows: 202/544 top-match, 304/544 acceptable, 1 severe blunder. That means severe blunders improved a lot, but top-match only moved from about 36.0% to 37.1%, and acceptable-match slipped from about 57.5% to 55.9%. The latest 10 fresh rows also show hidden-info errors rising to 4, so the “safety” improvement is not even perfectly stable. 

The qualitative evidence points the same way. The latest focused transfer had 0 severe, 0 mechanics, 0 state, and 0 hidden-info errors, but only 16/39 top and 25/39 acceptable. Its misses were not “obvious blunders”; they were stronger-move-selection misses: failing to make Roar the main line, missing Misdreavus as the third route owner, overcalling Rest/pivot, and missing exact counter-handoffs.  The active context also says the assistant sometimes names likely receivers like Raikou or Skarmory, then still clicks active pressure instead of the move that actually beats that branch. That is exactly “knows the danger, does not choose the converting move.” 

So the next three blocks should be changed in one key way: severe-blunder avoidance becomes a **gate**, not the training objective. A block only “passes” if it increases positive move-selection evidence: top-match, acceptable-match, action quality, route conversion, and correct branch-punish choice. The measurement mini-goal already weights action quality most heavily and says an answer without a single recommended move or ranked move class is capped, so the next cycle should lean into that rather than another error-suppression probe. 

## Changed Three-Block Plan

### Block 1 — Fresh replay transfer with ranked candidate forcing

Timebox: 75–90 minutes.

Objective: train and measure positive move selection, not just safe answers. For every decision, require a ranked top 3: primary move/switch, best alternative, and rejected tempting line. The answer must say: “This move improves the route because ___; it beats the likely branch by ___; I reject the safer/default move because ___.”

Files/artifacts to create or update: one fresh replay-turn-pause artifact; one ledger row. Do not create a policy card.

Score or evidence expected: 30–50 fresh side decisions. Score the normal top/acceptable/severe metrics, but add three extra columns or tags: `ranked_top3_present`, `route_converting_move_chosen`, and `branch_punish_chosen`. A good result is not merely 0 severe. A good result is at least 55% top, 70% acceptable, 0 severe, and at least 60% on “route-converting move chosen” for decisions where an active converter exists. The active context already uses 55% top, 70% acceptable, 0 severe, and no repeated uncorrected error as the provisional gate, but this block adds a positive-selection target. 

Kill condition or stop rule: stop if two answers in a row are “safe but non-converting,” meaning they avoid disaster but fail to punish the named branch. Also stop if the assistant cannot name why the top move is better than the second-best move.

What must not be done: do not reward a move just because it avoids a severe blunder. Do not write “reasonable line” unless it names what the move gains. Do not use the old pattern: identify the branch, then click a generic pressure/status/pivot move anyway.

### Block 2 — Positive-miss review, not error-class review

Timebox: 45 minutes.

Objective: review only the decisions where the answer was safe but weaker than the replay move or a high-EV route. The question is not “what mistake did I avoid?” The question is “what stronger move did I fail to see?”

Files/artifacts to create or update: update the same replay artifact with a compact “positive miss table.” Add at most one short ledger note. Do not touch the cookbook unless the same positive-selection miss repeats twice.

Score or evidence expected: produce a table with five columns: public state, my chosen move, stronger candidate, why stronger candidate improved the route, and what feature I underweighted. The feature labels should be things like “counter-handoff,” “phaze loop conversion,” “active damage before defensive script,” “third-owner job,” “cash-out before status,” or “preserve route piece.” These match the current active error classes and latest transfer misses.  

Kill condition or stop rule: stop if the review becomes a broad GSC lesson. The output must stay tied to actual fresh decisions. If there are fewer than five positive misses, stop after extracting them; do not manufacture a policy card.

What must not be done: do not count “0 severe” as the headline. Do not make another constructed regression probe. The latest constructed probe already passed 4/4 and explicitly says it is regression only, requiring fresh replay transfer before treating the correction as stable. 

### Block 3 — Fresh mini-transfer targeting the strongest-move miss

Timebox: 60–75 minutes.

Objective: run a second fresh segment that targets the single biggest positive-selection weakness from Block 2. Not the biggest “bad blunder” weakness. The biggest “I chose a safe line but missed the route-improving line” weakness.

Files/artifacts to create or update: one mini-transfer artifact and one ledger row. No new policy card unless the same positive-selection miss repeats in both Block 1 and Block 3.

Score or evidence expected: 20–30 fresh decisions, with separate scoring for the chosen target. For example, if the miss is “branch-action after naming,” score how often the assistant names the likely switch/support branch and then actually chooses the counter-switch, coverage, phaze, setup, or utility move that beats it. If the miss is “active damage before defensive script,” score how often it attacks when damage removes or cripples the converter before Rest/pivot/status is needed. The current probe checklist already frames these as positive choices: Reflect+Roar as one package, third-owner job identification, no hidden Rest import, and active damage before Rest or pivot. 

Kill condition or stop rule: stop if the same safe-but-weaker pattern appears twice. At that point, source study is allowed, but only for that exact failure class and only if it produces one decision rule plus another fresh Pokemon check.

What must not be done: do not run another “avoid hidden info / avoid severe blunder” drill. Do not accept a move just because it is defensible. The whole point of this block is to choose the move that wins more board equity.

## The scoring change I would make immediately

Add one small positive-skill score to every fresh replay decision:

`positive_selection = 1` if the answer chooses a move that actively improves the route, punishes the named branch, preserves or spends the correct route piece, or converts pressure into progress.

`positive_selection = 0` if the answer is merely safe, generic, passive, or “acceptable” only because it does not throw.

Then track four numbers separately:

Fresh top-match.

Fresh acceptable-match.

Severe blunders.

Positive-selection rate.

Right now, the loop can look better by driving severe blunders down while top/acceptable stay flat. That is useful, but incomplete. The next loop should only be considered progress if severe stays low **and** positive-selection rises.
