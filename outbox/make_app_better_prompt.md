# Spam Prompt: Make The App Better

Paste this into a fresh Codex session when you want it to make the Pokemon Gold
hack better in an important way without needing a narrow task upfront.

```text
We are in C:\Users\lolno\Downloads\pokemon gold hack.

Your job is to make the app/game better in one important way. Do not ask me to
choose a lane unless you truly cannot proceed safely. Start by reading:

1. docs/README.md
2. docs/codex_context.md
3. docs/project_roadmap.md
4. docs/agent_navigation/start_card.md
5. docs/agent_navigation/important_improvement_menu.md

Use the Important Improvement Menu for inspiration, but do not do a little of
everything. Pick one consequential lane and execute it properly. Prefer work
that compounds for future sessions: live boss proof, cheap-difficulty evidence,
release confidence, battle correctness, weak-Pokemon usefulness, QoL with teeth,
player communication, or future-agent leverage.

Default bias: trust before novelty. If a new feature is clearly the best move,
prototype it narrowly and prove it. Otherwise improve the evidence, fairness,
buildability, readability, or playability of what already exists.

While working, take constant notes for future sessions:

- Put exploratory/running notes or handoff thoughts in outbox/.
- Put reproducible trace/check evidence in audit/.
- Update docs/project_roadmap.md when a workstream changes state, gains a
  blocker, gets proof, or has a useful next move.
- Update docs/agent_navigation/ only when future sessions need a faster route.
- Never leave an important finding only in chat.

Respect the dirty worktree. Do not revert unrelated changes. Do not hand-edit
.gbc, .o, .map, .sym, or generated docs. For source changes, use the matching
verification row in docs/agent_navigation/verification_matrix.md and build or
explain exactly why you could not. For docs/navigation-only work, run:

python tools\audit\check_navigation_floor.py

At the end, report:

1. what important lane you chose and why;
2. what files you changed;
3. what evidence or verification exists;
4. what notes you left for the next session;
5. what remains uncertain.
```
