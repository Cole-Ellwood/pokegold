# Commit checkpoint, 2026-09-06

This checkpoint preserves the assisted root-cause development work described in
the roadmap and case records. It does not complete autonomous diagnosis, the
20-case blind pilot, or the release corpus. The link-mail public investigation
still lacks a watchable replay target and an accepted causal diagnosis.

## Validation performed for the checkpoint

- 184 focused debugger tests passed in 110.540 seconds with `PYTHONUTF8=1`.
  These cover command dispatch, review regressions, instruction capture, taint,
  effects, investigation, root-cause evaluators/fixtures/verifiers, runtime
  experiments, reporting, source mapping, localization, and runtime watches.
- 39 register-flow and front-door speedup-dispatch tests passed in 0.257 seconds.
- 26 runtime, PyBoy frame-boundary, and build/report regression tests passed.
- 13 C-tool and Makefile regression tests passed under WSL.
- Gold, Silver, and debug Gold rebuilt successfully with native WSL RGBDS.
  All three menu-click ROM tests then passed. The previous debug ROM contained
  the old menu instruction and failed six flag/input subcases before rebuilding.
- Documentation navigation passed against the rebuilt linker outputs. A fresh
  dev index differed only in its generated date, so no date-only update was kept.
- The packaged PyBoy patch passed `git apply --check` against the archived
  upstream 2.7.0 source. Installed backend behavior is covered by the bounded
  frame-boundary test; this does not extend its documented audio guarantees.

The full debugger discovery run is **not a passing gate** for this checkpoint.
The initial default-encoding attempt emitted Windows CP1252 decoding errors and
was stopped. A UTF-8 retry remained active after 15 minutes and was stopped
without a unittest summary or verdict. The focused results above are the actual
completed debugger validation; no full-suite, deity, or blind-diagnosis success
is inferred from them.

ROMs, object/linker outputs, installed dependencies, and local replay/build
artifacts remain outside these source commits. Historical case evidence keeps
its original ROM, source, state, and backend identities; committing the tools
does not revalidate an old capture against a different basis.
