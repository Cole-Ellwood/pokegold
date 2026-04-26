# Buff Backlog

Audience: future Codex/helper agents. Purpose: keep weak-Pokemon review findings
out of chat history and in a durable queue.

## How To Use

1. Regenerate `docs/generated/balance_audit.md`.
2. Move high-signal findings here if they need human balance judgment.
3. When a decision is made, update `docs/balance_intent.md` and, if relevant,
   `docs/evolution_policy.md`.
4. Remove or demote entries only after source changes or explicit design intent
   explain why the Pokemon is fine.

## Priority Discipline

It is valid for a priority section to be empty. Do not promote medium-priority
items just to avoid an empty High Priority table. Priority should reflect current
risk: broken evolution paths, undocumented standalone low-BST finals, or gimmicks
without explicit intent outrank ordinary weak-mon tuning questions.

When moving an item out of this backlog, leave either a resolved row in this file
or a locked/provisional row in `docs/balance_intent.md` so the decision is not
only visible in generated audit output.

## Resolved In Current Pass

| Pokemon | Resolution | Follow-Up |
| --- | --- | --- |
| `SEEL` | Restored `EVOLVE_LEVEL, 34, DEWGONG`; not a standalone final. | None. |
| `CHINCHOU` | Restored `EVOLVE_LEVEL, 27, LANTURN`; not a standalone final. | None. |
| `SMOOCHUM` | Restored `EVOLVE_LEVEL, 30, JYNX`; not a standalone final. | None. |
| `PONYTA` | Restored `EVOLVE_LEVEL, 40, RAPIDASH`; not a standalone final. | None. |
| `RHYHORN` | Restored `EVOLVE_LEVEL, 42, RHYDON`; not a standalone final. | None. |
| `DRAGONAIR` | Restored `EVOLVE_LEVEL, 55, DRAGONITE`; not a standalone final. | None. |
| `UNOWN` | Locked as a Hidden Power gimmick with `148/102/48/48/102/48` stats. | Playtest Hidden Power variance and Ruins timing. |
| `DITTO` | Locked as an Imposter-style gimmick with `100/48/48/48/48/48` stats. | Playtest switch-in reliability and boss abuse risk. |
| `SMEARGLE` | Locked as a fast Sketch toolkit with `90/45/75/110/45/75` stats. | Audit practical move acquisition. |
| `WOBBUFFET` | Locked as a high-HP reactive trap with `220/33/65/33/33/65` stats. | Playtest AI/player fairness. |

## High Priority

_No active high-priority entries after the resolved evolution and gimmick pass._

## Medium Priority

| Pokemon | Why It Is Suspicious | Likely Fix Paths | Status |
| --- | --- | --- | --- |
| `FARFETCH_D` | Buffed Attack helps, but reliable STAB is still modest for a standalone final. | Confirm Stick availability or improve Flying/Normal access. | needs review |
| `ARIADOS` | Bulky enough to have a role, but low speed and modest attack can still feel flat. | Add stronger Bug/Poison identity or document as bulky status utility. | needs review |
| `LEDIAN` | Has stats, but Bug/Flying attacking value can lag without strong reliable STAB. | Confirm support role or improve Bug/Fighting-style coverage. | needs review |
| `YANMA` | Fast-ish Bug/Flying with questionable STAB quality. | Confirm speed/offense role or improve level-up attack access. | needs review |
| `DELIBIRD` | Present-only identity historically weak; current stats are better but role still unclear. | Decide whether it is a special tank, utility pick, or joke mon. | needs review |

## Lower Priority Watchlist

| Pokemon | Watch Reason | Status |
| --- | --- | --- |
| `DUNSPARCE` | Current source is much lower than an earlier rebalance snapshot; may be intentional, but needs confirmation. | needs review |
| `SUDOWOODO` | Current source is much lower than an earlier rebalance snapshot; slow Rock roles are easy to over- or under-tune. | needs review |
| `TOGETIC` | Current source differs sharply from earlier high-speed physical concept. | needs review |
| `JYNX` | Current source differs sharply from earlier mixed/specially bulky concept. | needs review |
| `LANTURN` | Current source differs from earlier bulky special attacker concept. | needs review |
| `GLIGAR` | Current source differs from earlier bulky Ground/Flying concept. | needs review |
| `MANTINE` | Current source differs from earlier faster mixed concept. | needs review |
| `QUAGSIRE` | Current source differs from earlier bulky mixed attacker concept. | needs review |
| `VENOMOTH` | Current source differs from earlier very fast concept. | needs review |

## Frustrated Process Note

This backlog exists because relying on memory or generated change manifests is
not enough. The hack's stated goal is to make weak Pokemon usable, but without a
living backlog and species intent table, it is too easy to ship a low-BST
standalone Pokemon and only discover later that nobody knows whether it was a
design choice. That should not be happening after a broad rebalance pass.
