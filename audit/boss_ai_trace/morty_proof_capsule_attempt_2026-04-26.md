# Morty Proof Capsule Attempt - 2026-04-26

Purpose: satisfy `MEGAURGENT-001` from `docs/project_roadmap.md` by trying to
produce the first real boss-position Boss AI trace proof for Morty on the
current trace ROM.

Outcome: blocked. No `audit/boss_ai_trace/morty_live.txt` was produced. The
attempt did improve the preflight tooling: Morty's map object is object index 2
and loaded object structs are `$28` bytes wide, and the probe now also rejects
states whose active player Pokemon has impossible HP.

Why this is blocked:

- `python tools\trace\boss_ai_trace_batch.py` still reports all configured live
  captures as `MISSING_STATE`; the manifest has no boss-position save-state.
- Attempt-time scratch trace ROMs and current root symbols loaded correctly. The
  old scratch ROM hashes are historical; use
  `audit/boss_ai_trace/live_capture_manifest.json` for the accepted trace
  ROM/symbol basis. During this follow-up, the current root trace ROM hash was
  `8936A6D90D98FCDE36CF0F66BA734BA812A057B1668F4B7F82A2831EF488594E` and
  `pokegold_trace.sym` was
  `2042A961ABF381447C69D533C378675EEEBA80970357BEF10F9AF6A893EADC46`.
- Local PyBoy is usable through `.local/pydeps`; `python
  tools\trace\boss_ai_trace_capture.py --symbols-only` prints the trace WRAM
  addresses.
- Reusing `.local/boss_ai_trace_probe/morty_probe.gbc.ram` with the current
  `pokegold_trace.gbc` loads WRAM to Ecruteak Gym at `wMapGroup=4`,
  `wMapNumber=7`, `wYCoord=2`, `wXCoord=5`, but raw boot-continue scratch RAM
  still does not load a usable Morty object/battle context.
- Reusing `.local/boss_ai_trace_probe/morty_warp_probe.gbc.ram` loads Ecruteak
  City near prior scratch setup, but it is not a boss-position state and did not
  produce a Morty battle trace during this attempt.
- A debugger-style script-pointer warp can place the current trace ROM beside
  Morty with `map_object_2=struct=1,sprite=15`, but the stale copied battery RAM
  has an impossible active Totodile value (`player_active=...hp=64000/64000`).
  The battle intro reaches a broken `00/0` HP display and cannot be counted as
  gameplay proof.
- Follow-up probe command:
  `python tools\trace\boss_ai_trace_state_probe.py --rom .local\do_now_morty_current\morty_live_attempt\pokegold_trace.gbc --boot-continue --expect-morty --strict`
  confirms the same failure shape: `map=04:07`, `coords=x=5,y=2`, but
  `morty_candidate=FAIL` with
  `morty_candidate_reasons=morty_map_object_missing:object2_sprite=23`.
- Follow-up debugger-warp probe against the current root ROM rejects the copied
  SRAM basis with
  `player_party_invalid:active_max_hp_implausible=64000|active_hp_implausible=64000`.
- A scratch-only WRAM repair of the active party (`hp=220/220`, plausible stats
  and moves) made the debugger-warp state pass the stricter preflight, but
  driving the battle still stalled in the send-out sequence at `Go! TOTODILE!`
  before any Boss AI trace field became nonzero. This was not added to the
  manifest.

Do not treat existing source-path excerpts in `audit/boss_ai_trace/morty.txt` as
the same thing. They support the design, but `MEGAURGENT-001` requires real
boss-position trace evidence.

Next exact unblock:

1. Create or supply a PyBoy-compatible save-state at a Morty decision point in
   the current `pokegold_trace.gbc` with a sane active player Pokemon.
2. Probe it before trusting it:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

3. Add its path to the `morty` entry in
   `audit/boss_ai_trace/live_capture_manifest.json`.
4. Run:

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
