"""Real Makefile/RGBDS flag-cache regression with temporary, two-byte ROMs."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(
    os.name == "posix"
    and all(shutil.which(t) for t in ["make", "gcc", "rgbasm", "rgblink"]),
    "requires WSL/POSIX build tools and RGBDS",
)
class MakeFlags(unittest.TestCase):
    def test_normal_trace_normal_and_incremental(self):
        with tempfile.TemporaryDirectory(prefix="gold-make-flags-") as name:
            work = Path(name)
            shutil.copyfile(ROOT / "Makefile", work / "Makefile")
            shutil.copyfile(ROOT / "rgbdscheck.asm", work / "rgbdscheck.asm")
            (work / "tools/audit").mkdir(parents=True)
            (work / "gfx").mkdir()
            (work / "includes.asm").write_text("")
            (work / "gfx/lz.mk").write_text("")
            (work / "tools/Makefile").write_text("all:\n\t@:\n")
            (work / "tools/audit/check_branch_currency.py").write_text("")
            subprocess.run(
                [
                    "gcc",
                    "-o",
                    str(work / "tools/scan_includes"),
                    str(ROOT / "tools/scan_includes.c"),
                ],
                check=True,
            )
            (work / "fixture.asm").write_text("""SECTION "Flags", ROM0[0]
IF DEF(BOSS_AI_TRACE)
    db $77
ELSE
    db $11
ENDC
IF DEF(_SILVER)
    db $22
ELIF DEF(_DEBUG)
    db $33
ELSE
    db $44
ENDC
""")
            objects = ["fixture_gold.o", "fixture_silver.o", "fixture_gold_debug.o"]
            command = [
                "make",
                "-j3",
                "rom_obj=fixture.o",
                "gs_excl_asm=",
                "PYTHON=python3",
                *objects,
            ]
            previous = None
            for defines, should_change, expected in [
                ("", True, 0x11),
                ("", False, 0x11),
                ("-D BOSS_AI_TRACE", True, 0x77),
                ("-D BOSS_AI_TRACE", False, 0x77),
                ("", True, 0x11),
                ("", False, 0x11),
            ]:
                with self.subTest(defines=defines, rebuild=should_change):
                    result = subprocess.run(
                        [*command, "DEFINES=" + defines],
                        cwd=work,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    times = [(work / p).stat().st_mtime_ns for p in objects]
                    if previous is not None:
                        if should_change:
                            self.assertTrue(
                                all(a != b for a, b in zip(times, previous)),
                                result.stdout,
                            )
                        else:
                            self.assertEqual(times, previous, result.stdout)
                    previous = times
                    for obj, variant in zip(objects, [0x44, 0x22, 0x33]):
                        # Link actual assembled bytes, without touching any working-tree ROM.
                        subprocess.run(
                            [
                                "rgblink",
                                "-o",
                                str(work / "fixture.gb"),
                                str(work / obj),
                            ],
                            check=True,
                        )
                        self.assertEqual(
                            (work / "fixture.gb").read_bytes()[:2],
                            bytes([expected, variant]),
                        )


if __name__ == "__main__":
    unittest.main()
