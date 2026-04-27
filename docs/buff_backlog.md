# Buff Backlog

Audience: future Codex/helper agents. Purpose: keep weak-Pokemon review findings
out of chat history and in a durable queue.

First-Playthrough Promise lens: backlog entries matter because the player should
not already know which Pokemon are worthless. Resolve weak or strange species by
creating real discovery, role identity, or documented intentional gimmicks, not
by quietly accepting old solved assumptions.

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
| `LEDIAN` | Upgraded into a fast Bug/Flying screen passer with real Bug/Flying attacks; Bugsy now showcases it instead of another early Spikes/Rapid Spin shell. | Watch early Bugsy pacing. |
| `SUDOWOODO` | Upgraded into a slow Rock wall with usable special bulk plus Spikes/Roar role access; Chuck/Brock now use it as non-Onix Rock utility. | Watch whether two boss uses feel distinct enough. |
| `JYNX` | Upgraded into a frail fast Ice/Psychic sleep breaker and assigned to Sabrina as Starmie replacement. | Watch Lovely Kiss swinginess. |
| `LANTURN` | Upgraded into a bulky Water/Electric pivot with real special pressure and Ice Beam access; Misty now uses it instead of Kingdra. | Watch broad Water-type power creep. |
| `MANTINE` | Upgraded into a Water/Flying special wall with Rapid Spin, Haze, and Hydro Pump; Clair now uses it instead of Donphan. | Watch whether Rapid Spin reads naturally enough. |
| `DEWGONG` | Upgraded into an Ice/Water utility spinner with Encore/Haze; Pryce now uses it instead of Starmie. | Watch midgame defensive pacing. |
| `POLITOED` | Upgraded into a rain support Water with better mixed bulk; Misty now uses it instead of Cloyster. | Watch rain-team redundancy with Lapras. |
| `QWILFISH` | Upgraded into a faster Poison/Water Spikes trade piece; Janine now uses it instead of Ariados. | Watch Explosion pressure. |
| `CORSOLA` | Upgraded into a sturdier Rock/Water Recover spinner; Brock now uses it instead of Donphan. | Watch late Rock-team stall pacing. |
| `ELECTRODE` | Added Rapid Spin access so Electric teams can clear hazards without importing Donphan. | Watch if the fastest spinner is too clean. |
| `DELIBIRD` | Upgraded from Present-only into an Ice/Flying utility wall with Icy Wind, Aurora Beam, Agility, Wing Attack, Haze, and late Blizzard. | Watch Silver Ice Path catch feel and Pokefan Colin's level 32 Delibird. |
| `FARFETCH_D` | Moved into a provisional Stick-backed crit attacker role: wild Farfetch'd now commonly carry Stick, learn Wing Attack at level 23, and Stick's item text names its critical-ratio effect. | Playtest Route 38 catch feel and Bird Keeper Jose/Perry trainer showcases. |
| `ARIADOS` | Moved into a provisional slow hazard-trapper role: evolved Ariados now learns Spikes at level 22 and gets Spider Web by level 37, matching Koga's level-40 utility showcase without relying on reminder-only level 1 Spikes. | Playtest evolved Spinarak between level 22 and 37, plus Koga's trap/hazard turn feel. |

## High Priority

_No active high-priority entries after the resolved evolution and gimmick pass._

## Medium Priority

| Pokemon | Why It Is Suspicious | Likely Fix Paths | Status |
| --- | --- | --- | --- |
| `YANMA` | Fast-ish Bug/Flying with questionable STAB quality. | Confirm speed/offense role or improve level-up attack access. | needs review |

## Lower Priority Watchlist

| Pokemon | Watch Reason | Status |
| --- | --- | --- |
| `DUNSPARCE` | Current source is much lower than an earlier rebalance snapshot; may be intentional, but needs confirmation. | needs review |
| `TOGETIC` | Current source differs sharply from earlier high-speed physical concept. | needs review |
| `GLIGAR` | Current source differs from earlier bulky Ground/Flying concept. | needs review |
| `QUAGSIRE` | Current source differs from earlier bulky mixed attacker concept. | needs review |
| `VENOMOTH` | Current source differs from earlier very fast concept. | needs review |

## Frustrated Process Note

This backlog exists because relying on memory or generated change manifests is
not enough. The hack's stated goal is to make weak Pokemon usable, but without a
living backlog and species intent table, it is too easy to ship a low-BST
standalone Pokemon and only discover later that nobody knows whether it was a
design choice. That should not be happening after a broad rebalance pass.
