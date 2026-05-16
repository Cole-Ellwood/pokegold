# Pokemon Skill Update - Plain Prose Comparison - 2026-05-14

This is a plain-language follow-up to
`pokemon_skill_tracking_report_2026-05-14.pdf`.

The short answer is: yes, the newest numbers look a little better than the
snapshot in the old PDF, especially on "reasonable move" agreement. But the
improvement is not clean enough to call a stable skill jump yet. I am still
making too many route and information mistakes, and one new severe miss
happened after the old report.

## What I Compared

The old PDF's newest fresh replay data ended at
`setup_hidden_role_stop_transfer_001_2026_05_14`.

Since then, the ledger gained 9 more rows. Of those, 7 were fresh replay
transfer rows and 2 were constructed correction probes. The 7 fresh rows added
210 new scored decisions.

The current newest fresh row is
`cashout_immunity_transfer_001_2026_05_14`.

I did not count the constructed probes as proof of live skill. They are useful
for checking whether a correction is written down clearly, but the honest
comparison is the fresh replay work.

## The Old Snapshot Versus Now

In the old PDF, the latest 20 fresh rows were:

37.1 percent exact top-match. That means I chose the same move as the replay
player 202 times out of 544 decisions.

55.9 percent acceptable-match. That means my move was at least reasonable 304
times out of 544 decisions.

There was 1 severe blunder, 3 state errors, 4 hidden-information errors, and 1
mechanics error.

Now, the latest 20 fresh rows are:

39.3 percent exact top-match. That is 244 out of 621 decisions.

60.7 percent acceptable-match. That is 377 out of 621 decisions.

There are 2 severe blunders, 6 state errors, 6 hidden-information errors, and 1
mechanics error.

So the move-choice side is better than it was in the old PDF. The exact-match
number rose a little, and the acceptable-match number rose more clearly.

But the error-control side is worse. The current latest-20 window has more
severe errors, more state errors, and more hidden-information errors than the
old PDF's latest-20 window.

That matters. A better move-match rate is good, but it does not fully count as
progress if I am also making more mistakes that can poison the reasoning.

## What Happened After The Old PDF

Looking only at the 7 fresh transfer rows after the old PDF, the numbers were:

98 exact top matches out of 210 decisions, or 46.7 percent.

159 acceptable matches out of 210 decisions, or 75.7 percent.

1 severe blunder.

4 state errors.

2 hidden-information errors.

0 mechanics errors.

That is the strongest positive sign in this update. The fresh work after the
old report was much better than the old latest-20 window on acceptable move
choice. It also beat the old top-match rate by a noticeable amount.

But this newer slice is small. It is only 7 fresh rows. It also still contains
one severe miss, so it cannot be treated as a clean pass.

## The Whole Ledger Moved Only Slightly

The old PDF had 97 fresh rows and 2,125 fresh decisions. Across all of that,
I was at 40.6 percent top-match and 59.2 percent acceptable-match.

Now there are 104 fresh rows and 2,335 fresh decisions. Across all fresh work,
I am at 41.2 percent top-match and 60.6 percent acceptable-match.

That is a real increase, but it is small.

The overall record also picked up more errors because more fresh work was
added: severe blunders went from 10 to 11, state errors from 8 to 12, and
hidden-information errors from 4 to 6. Mechanics errors stayed at 1.

This means the total project looks a little better at choosing moves, but not
cleaner overall.

## The Most Important Change

The best news is that the last 10 fresh rows now look much stronger than the
last 10 fresh rows in the old PDF.

Old latest 10 fresh rows:

35.3 percent top-match and 53.2 percent acceptable-match.

Current latest 10 fresh rows:

43.8 percent top-match and 69.1 percent acceptable-match.

That is the clearest sign of improvement in the data. It suggests that the
recent training changes are helping.

But it still misses the target. The current working gate is roughly 55 percent
top-match and 70 percent acceptable-match, with no severe blunders. The current
latest 10 is close on acceptable-match but still below the top-match target,
and it still has 1 severe blunder.

## What I Am Better At

I am better than I was in the old PDF at finding moves that are at least
reasonable in fresh replay positions.

The current latest-20 acceptable rate is 60.7 percent, up from 55.9 percent in
the old PDF.

The fresh rows after the old PDF were even better: 75.7 percent acceptable.

That means I am less often completely off-route. I am more often finding a
move that fits the position, even when it is not the exact expert move.

I also had a useful correction on all-in sacrifice moves. After the bad
Explosion mistake, I added a cash-out immunity guard and then tested it in a
fresh transfer. In that limited sample, I did not repeat the exact same kind of
Explosion-into-immunity failure.

## What I Am Not Better Enough At

I am not yet good enough at picking the exact best move.

The current latest-20 top-match rate is 39.3 percent. That is better than the
old 37.1 percent, but it is still far below the working 55 percent target.

I am also still weak at turning a named branch into the move that actually
punishes it.

The newest transfer found this same problem in a different form: when Jynx or
Gengar faced an obvious receiver, I sometimes wanted the generic move into the
active Pokemon instead of the move that improved through the receiver. For
example, I missed lines like Jynx using Thief into a switch and Gengar using
Ice Punch into Raikou.

In simple terms: I am getting better at avoiding nonsense, but I am still not
reliably choosing the sharp move.

## My Honest Grade Right Now

Compared with the old PDF, I would say I am mildly improved.

The strongest evidence is the post-report fresh slice: 46.7 percent top-match
and 75.7 percent acceptable-match over 210 decisions.

The reason I will not call it a major breakthrough is that the bigger rolling
window still has 2 severe blunders, 6 state errors, and 6 hidden-information
errors.

So the honest statement is:

I am making better average move choices than the old report showed, but the
improvement is still uneven and not yet trustworthy.

## What Should Happen Next

The next training block should not be a broad article-reading block.

The next block should test one narrow thing:

When a status-capable Pokemon such as Jynx or Gengar faces an obvious receiver,
I must rank item removal, coverage, switching, setup or phazing, and status
before choosing.

That directly attacks the current weakness: choosing a safe or familiar move
instead of the move that improves through the opponent's likely branch.

The goal for the next fresh block is not "zero severe mistakes" by itself. The
goal is better positive move choice while keeping severe mistakes at zero.

Until that happens across more fresh decisions, I should not claim 1500-Elo
level play. The data says I am improving, but not there.
