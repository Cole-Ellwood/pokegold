# Policy Card: Romhack Mechanics Firewall

Status: active boundary card.

Use when: external GSC knowledge affects a local romhack move, route, damage,
item, type passive, timing, or boss-AI claim.

Trigger:

- A recommendation depends on mechanics that may differ from vanilla GSC.
- The claim touches Spikes/Rapid Spin, sleep, RestTalk, Explosion, phazing,
  type passives, items, AI information, Counter/Mirror Coat, or move timing.
- A source is expert vanilla GSC material rather than local evidence.

Default:

Treat external GSC knowledge as source material, not local truth. If the local
status is unknown or supplied-but-unverified, cap confidence and say what
fixture, source check, debugger output, or emulator trace would settle it.

Opposite boundary:

Do not freeze just because a mechanic is unverified if the recommendation does
not depend on that mechanic. Separate route logic from mechanics claims.

Exceptions:

- Source-visible boss rosters and known boss opener policy are allowed for
  player-side Gym Leader Lab advice.
- Haki/oracle behavior stays quarantined and does not generalize to ordinary
  boss AI.
- Ordinary boss AI must not use unrevealed player team slots, hidden moves,
  hidden items, hidden PP, exact hidden stats, or current-turn player input.

Worst branch:

You import a vanilla mechanic into a local boss route, choose a move that only
works in vanilla, and then count the failure as a planning error instead of a
mechanics error.

Local status:

This card is a process rule. Use `romhack_deltas/mechanics_pending_index.md`
for the current status of individual mechanics.

Evidence:

- `active_goal.md`
- `cross_domain_autonomy_policy.md`
- `boss_ai_re_solve_trigger_audit_2026-05-14.md`
- `romhack_deltas/`
- `mechanics_fixtures/`

Drill:

Before live romhack advice, list every decision-relevant mechanic and mark each
one `runtime_verified`, `source_verified`, `supplied_unverified`, `unknown`, or
`not_decision_relevant`.
