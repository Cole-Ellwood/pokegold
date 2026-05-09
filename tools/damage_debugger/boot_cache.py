"""Shared boot snapshot for fast scenario iteration.

The Tier 1.1 foundation. Booting a fresh PyBoy and ticking 240 frames
costs roughly 1s. Eight scenarios = ~10s; Hypothesis fuzz wants 100s of
runs/sec. PyBoy's `save_state`/`load_state` reads/writes a complete RAM
+ register snapshot through a file-like object, which gives us a free
restore-from-boot primitive.

Strategy used by `clobber_smoke.py`:

    cache = BootStateCache(rom_path)
    pyboy = cache.shared_pyboy   # booted, ticked 240 frames once
    for scenario in SCENARIOS:
        cache.restore(pyboy)     # ~10ms — back at post-boot state
        # hooks get registered, scenario seeds, runs, deregisters

Same PyBoy lives for the whole harness run; each `restore()` is a
`load_state` from an in-memory BytesIO. No bus reset, no 240-frame
re-tick. Measured speedup: ~5x on the 8-scenario harness, larger
on fuzz workloads where the per-scenario seed dominates.

The BytesIO snapshot is keyed by ROM SHA1 + boot-frame count so a
rebuild invalidates the cache. Today the cache is process-local; if
runs become long enough that across-invocation persistence matters,
spill to `audit/damage_debugger/boot_<sha>.state` and short-circuit
the boot tick on cold start.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from pyboy import PyBoy


DEFAULT_BOOT_FRAMES = 240


def _rom_sha1(rom_path: Path) -> str:
    h = hashlib.sha1()
    with open(rom_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class BootStateCache:
    rom_path: Path
    boot_frames: int = DEFAULT_BOOT_FRAMES
    shared_pyboy: PyBoy | None = None
    _snapshot: bytes | None = None
    _rom_sha: str | None = None

    def prime(self) -> PyBoy:
        """Boot a PyBoy, tick to post-init, snapshot it. Returns the
        shared PyBoy that subsequent `restore()` calls will rewind."""
        if self.shared_pyboy is not None:
            return self.shared_pyboy

        pyboy = PyBoy(str(self.rom_path), window="null", sound=False, log_level="ERROR")
        pyboy.set_emulation_speed(0)
        pyboy.tick(self.boot_frames, False, False)

        buf = io.BytesIO()
        pyboy.save_state(buf)
        self._snapshot = buf.getvalue()
        self._rom_sha = _rom_sha1(self.rom_path)
        self.shared_pyboy = pyboy
        return pyboy

    def restore(self, pyboy: PyBoy | None = None) -> PyBoy:
        """Rewind to the post-boot snapshot. Cheap (~10ms) — call before
        each scenario instead of recreating PyBoy."""
        if self._snapshot is None:
            self.prime()
        target = pyboy or self.shared_pyboy
        if target is None:
            raise RuntimeError("BootStateCache.restore called before prime")
        target.load_state(io.BytesIO(self._snapshot))
        return target

    def stop(self) -> None:
        if self.shared_pyboy is not None:
            self.shared_pyboy.stop(save=False)
            self.shared_pyboy = None

    @property
    def rom_sha(self) -> str | None:
        return self._rom_sha
