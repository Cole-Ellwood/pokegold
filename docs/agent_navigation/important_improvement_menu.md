# Important Improvement Menu

Use this when the user says something broad like "make the app better in an
important way", "make the game better", "do whatever matters most", or "keep
improving this." This is an inspiration and routing surface, not source truth.

The best default is trust before novelty: prove the game is fair, buildable,
understandable, and worth playing before adding a new clever feature. If a new
feature is clearly the most important move, prototype it narrowly and leave
evidence.

## Operating Rule

Pick one consequential lane, do real work in that lane, and leave notes that a
future session can build from. Do not turn this menu into a grab bag.

If several lanes look tempting, prefer the one that most protects the
First-Playthrough Promise: Pokemon Gold should feel unknown and dangerous again
for a veteran player, without cheating the player or dissolving the journey.

## Productive Lanes

| Lane | What to look at | First routing surface |
| --- | --- | --- |
| Boss AI feel | Does a boss feel prepared, legal, non-scripted, and explainable after the fact? | `docs/agent_navigation/subsystems/trainer_boss_roster.md`, `docs/boss_ai_spec.md` |
| Live proof and trace evidence | Can a current trace ROM prove a real boss decision, not just static correctness? | `docs/agent_navigation/subsystems/boss_ai_trace.md` |
| Cheap difficulty audit | Do losses feel deserved, or did the designer punish trust in the game? | `docs/review_playbook.md`, `docs/project_roadmap.md` |
| Weak Pokemon usefulness | Did weak Pokemon become real team choices with distinct roles and timing? | `docs/agent_navigation/subsystems/pokemon_balance.md` |
| Boss rosters and itemization | Does each major trainer create memorable pressure without fake unfairness? | `docs/agent_navigation/subsystems/trainer_boss_roster.md` |
| QoL with teeth | Does a convenience remove clerical pain while preserving preparation pressure? | `docs/agent_navigation/subsystems/qol_map_scripts.md`, `docs/qol_handoff.md` |
| Player communication | Do descriptions, NPCs, signs, and service text explain the changed game enough? | `docs/project_map.md`, `docs/qol_handoff.md` |
| Battle-system correctness | Are custom mechanics symmetric, timed correctly, and free of stale state bugs? | `docs/review_playbook.md`, `docs/mechanics_changes_from_base.md` |
| Memory and bank pressure | Are scarce banks protected before adding optional code or data? | `docs/generated/dev_index.md`, `docs/project_context.md` |
| Release confidence | Can the current checkout pass source-relevant audits and build Gold/Silver? | `docs/agent_navigation/verification_matrix.md`, `docs/build.md` |
| Regression traps | Can a small audit catch the kind of bug that would quietly come back later? | `tools/audit/`, `docs/review_playbook.md` |
| Progression and pacing | Where does the hack first become exciting, unfair, too easy, or tedious? | `docs/project_context.md`, `docs/project_map.md` |
| World texture | Does a change preserve old-game Johto texture while making the world feel alive? | `docs/project_context.md`, `docs/mechanics_changes_from_base.md` |
| Docs and future-agent leverage | Does the next session find the right surface fast and avoid stale assumptions? | `docs/agent_navigation/README.md` |
| Repo hygiene | Is clutter explained before it is moved, deleted, or hidden? | `docs/agent_navigation/source_output_ownership.md` |
| Playtest artifact design | Can a future session reproduce a tiny scenario instead of trusting a diary? | `docs/agent_navigation/artifact_catalog.md` |
| One bold new idea | Is there one narrow prototype that could make the game scarier and clearer? | `docs/project_roadmap.md`, then the matching subsystem doc |

## Note Discipline

Leave notes while working, but put each note at the right durability level:

- `docs/project_roadmap.md`: status changes, blockers, proof gaps, and next
  moves for live workstreams.
- `decisions/`: dated reversible-judgment notes a future helper might revisit.
- `journal/`: per-session diary observations and rough findings.
- `audit/`: evidence from checks, traces, captures, ledgers, and reproducible
  investigation artifacts.
- subsystem docs under `docs/agent_navigation/subsystems/`: routing facts that
  should be found in constant time next session.

Do not bury source-truth claims in a chat transcript alone. If a finding
changes what future sessions should do, route it into docs, roadmap, audit
evidence, a decision note, or a journal entry before stopping.

## Safe Stop

Before finalizing any lane, name what kind of evidence exists:

- source inspection;
- generated index or linker output;
- audit result;
- build result;
- live emulator/trace proof;
- manual playtest;
- scratch or hypothesis only.

Then run the verification row for the touched subsystem in
`docs/agent_navigation/verification_matrix.md`. If the work was navigation-only,
run:

```powershell
python tools\audit\check_navigation_floor.py
```
