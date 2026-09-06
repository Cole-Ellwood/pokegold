# PyBoy frame-boundary hook correction

The root-cause debugger's dense instruction hooks exposed a PyBoy 2.7.0 stall.
When a single instruction step completes a frame, the outer tick loop can keep
dispatching the same hook without advancing CPU cycles. A one-frame trace then
never returns. A trace-record limit does not stop that emulator loop.

`pyboy-2.7.0-frame-boundary.patch` exits that dispatch loop after handling the
frame-boundary hook. The pending instruction continues on the next frame. It
changes the emulator, not the ROM, recorded inputs, or game state.

## Build and install

Use the PyBoy 2.7.0 source archive from PyPI. The archive used here has SHA256
`B97DB94C366F5E54AF04F94641C6107454821543015716B7182DF29684AD9180`.
Extract it into a new build directory, apply the patch to that source tree,
and build a wheel with the Python interpreter used by the debugger. For example,
with the extracted source in `.local/tmp/pyboy-build/pyboy-2.7.0`:

```powershell
git apply --check --directory=.local/tmp/pyboy-build/pyboy-2.7.0 tools/trace/patches/pyboy-2.7.0-frame-boundary.patch
git apply --directory=.local/tmp/pyboy-build/pyboy-2.7.0 tools/trace/patches/pyboy-2.7.0-frame-boundary.patch
python -m pip wheel --no-deps .local/tmp/pyboy-build/pyboy-2.7.0 --wheel-dir .local/tmp/pyboy-wheels
```

Test the wheel in a separate `pip install --no-deps --target` directory first:

```powershell
python -m tools.trace.tests.test_pyboy_frame_boundary --probe PATH_TO_TEST_INSTALL
```

After that passes, preserve the previous `pyboy` package and its distribution
metadata if existing evidence refers to it, then install the built wheel with
`python -m pip install --no-deps --upgrade --target .local/pydeps PATH_TO_WHEEL`.
Run `python -m unittest tools.trace.tests.test_pyboy_frame_boundary -q` against
the selected workspace backend. The test uses a bounded child process, so the
unfixed backend produces a timeout failure instead of hanging the test suite.

This is a local source patch, not a published upstream release. The version
string remains 2.7.0; distinguish builds using recorded binary hashes. Existing
evidence with the old backend hash must retain that basis and use the archived
backend for replay, or be recaptured and independently verified with the new
backend. Do not rewrite old report hashes to make them appear compatible.

## Verification and limits

The synthetic ROM test exercises LCD off/on and 1, 2, and 10 frames. Dense hooks
must return the requested frame count and preserve CPU registers, VRAM, WRAM,
OAM, I/O, and HRAM compared with unhooked execution. The original native backend
failed by timing out; the patched native backend passed all six cases.

This does not establish bit-identical save-state files or audio fidelity. A
separate comparison found different internal audio scheduling counters between
dense-hook and unhooked execution, even when CPU state and visible memory match.
Audio-sensitive proof still needs its own verification. A Python-source probe
also confirmed that the stalled hook repeats with unchanged CPU cycles and
`lcd.frame_done` already true; the corrected source advances frames normally.

On this workspace, the original native package is archived at
`.local/tmp/root_cause_oracle/development/pyboy_2.7.0_original_native`. Build
artifacts and hashes are in `pyboy_source`, `pyboy_wheels`, and
`pyboy_frame_build_identity.json` beside that archive. The installed corrected
`pyboy.cp314-win_amd64.pyd` has SHA256
`CE23D5C2D3EB2176E70AC940522E34EED52CB9C91CF01E0990317A2187596B4C`.
