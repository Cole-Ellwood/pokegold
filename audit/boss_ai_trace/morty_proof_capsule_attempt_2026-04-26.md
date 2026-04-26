# Morty Proof Capsule Attempt - 2026-04-26

Purpose: satisfy `MEGAURGENT-001` from `docs/project_roadmap.md` by trying to
produce the first real boss-position Boss AI trace proof for Morty on the
current trace ROM.

Outcome: blocked. No `audit/boss_ai_trace/morty_live.txt` was produced.

Why this is blocked:

- `python tools\trace\boss_ai_trace_batch.py` still reports all configured live
  captures as `MISSING_STATE`; the manifest has no boss-position save-state.
- Current trace ROM and symbols load correctly:
  - `pokegold_trace.gbc` SHA256:
    `72FAA870B744F506B9E21C17852C8659F86DF93092D2964BE2DF8B90140EDD37`
  - `pokegold_trace.sym` SHA256:
    `A911C70DDA67A7C871626EBA0F177F67AD188B8D6D1199AD83522F64D00108B0`
- Local PyBoy is usable through `.local/pydeps`; `python
  tools\trace\boss_ai_trace_capture.py --symbols-only` prints the trace WRAM
  addresses.
- Reusing `.local/boss_ai_trace_probe/morty_probe.gbc.ram` with the current
  `pokegold_trace.gbc` loads WRAM to Ecruteak Gym at `wMapGroup=4`,
  `wMapNumber=7`, `wYCoord=2`, `wXCoord=5`, but the NPC object table contains
  no usable Morty object. Talking cannot start the battle, so this is not valid
  live proof.
- Reusing `.local/boss_ai_trace_probe/morty_warp_probe.gbc.ram` loads Ecruteak
  City near prior scratch setup, but it is not a boss-position state and did not
  produce a Morty battle trace during this attempt.
- A debugger-style script-pointer attempt was tried only as a fallback idea and
  abandoned when it did not reach a Boss AI trace promptly. Do not count that as
  gameplay proof.

Do not treat existing source-path excerpts in `audit/boss_ai_trace/morty.txt` as
the same thing. They support the design, but `MEGAURGENT-001` requires real
boss-position trace evidence.

Next exact unblock:

1. Create or supply a PyBoy-compatible save-state at a Morty decision point in
   the current `pokegold_trace.gbc`.
2. Add its path to the `morty` entry in
   `audit/boss_ai_trace/live_capture_manifest.json`.
3. Run:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only morty
python tools\audit\check_boss_ai_live_capture_ledger.py
```

Minimum acceptable `morty_live.txt` content:

- ROM or build basis.
- Save-state path or manual debugger position.
- Public player information at the decision.
- Enemy active Pokemon and turn context.
- Nonzero Boss AI trace fields from `wBossAITraceTopMoves`,
  `wBossAITraceTopScores`, `wBossAITraceChosenMove`,
  `wBossAITracePlausibleMask`, and `wBossAIRevealedMovesBitmap`.
- One short fairness read explaining why the chosen action follows public
  information rather than hidden-information cheating.
