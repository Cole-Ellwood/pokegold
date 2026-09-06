"""CLI regressions; run in WSL: python3 -m unittest discover -s tools/tests.
Binaries and outputs are temporary. Optional CFLAGS supports sanitizer runs.
"""

import os
from pathlib import Path
import random
import shlex
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name == "posix" and shutil.which("gcc"), "requires POSIX gcc")
class CTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix="gold-c-tools-")
        cls.bin = Path(cls.build.name)
        for name, sources in [
            ("gfx", [ROOT / "tools/gfx.c"]),
            ("make_patch", [ROOT / "tools/make_patch.c"]),
            ("lzcomp", sorted((ROOT / "tools/lz").glob("*.c"))),
        ]:
            subprocess.run(
                [
                    "gcc",
                    "-std=c11",
                    "-g",
                    *shlex.split(os.environ.get("CFLAGS", "-O1")),
                    "-o",
                    str(cls.bin / name),
                    *map(str, sources),
                ],
                check=True,
            )

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gold-c-case-")
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.output = self.put("output", b"unchanged")

    def run_tool(self, tool, *args):
        result = subprocess.run(
            [str(self.bin / tool), *map(str, args)],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=30,
        )
        self.assertNotIn(b"AddressSanitizer", result.stderr)
        self.assertNotIn(b"runtime error:", result.stderr)
        return result

    def put(self, name, data):
        p = self.dir / name
        p.write_bytes(data)
        return p

    def png(self, width, height):
        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data))
            )

        data = b"\x89PNG\r\n\x1a\n" + chunk(
            b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
        )
        return self.put(
            "input.png",
            data
            + chunk(b"IDAT", zlib.compress(bytes((width + 1) * height)))
            + chunk(b"IEND", b""),
        )

    def rejected(self, r):
        self.assertGreater(r.returncode, 0)
        self.assertEqual(self.output.read_bytes(), b"unchanged")

    def test_buffered_output_failure(self):
        src = self.put("tiles", bytes(range(16)))
        self.assertEqual(self.run_tool("gfx", "-o", self.output, src).returncode, 0)
        self.assertEqual(self.output.read_bytes(), src.read_bytes())
        self.assertNotEqual(self.run_tool("gfx", "-o", "/dev/full", src).returncode, 0)

    def test_lz_buffered_output_failures(self):
        for mode, data in [
            ([], b"x"),
            (["-t"], b"x"),
            (["-u"], b"\x00x\xff"),
            (["-d"], b"\x00x\xff"),
        ]:
            src = self.put("input", data)
            for dest in ["/dev/full", "-"]:
                with self.subTest(mode=mode, dest=dest):
                    if dest == "-":
                        with open("/dev/full", "wb") as sink:
                            r = subprocess.run(
                                [str(self.bin / "lzcomp"), *mode, str(src), "-"],
                                stdout=sink,
                                stderr=subprocess.PIPE,
                            )
                    else:
                        r = self.run_tool("lzcomp", *mode, src, dest)
                    self.assertNotEqual(r.returncode, 0)

    def test_patch_buffered_output_failure(self):
        self.output = Path("/dev/full")
        self.assertNotEqual(self.patch([(0, 1)], [0]).returncode, 0)

    def test_invalid_depth_preserves_output(self):
        for depth in [0, -1, 3]:
            self.rejected(
                self.run_tool(
                    "gfx",
                    "-d",
                    depth,
                    "--interleave",
                    "-p",
                    self.png(16, 16),
                    "-o",
                    self.output,
                    self.put("tiles", bytes(64)),
                )
            )

    def test_interleave_geometry(self):
        for depth in [1, 2]:
            for width, rows, length in [
                (16, 1, 16 * depth),
                (16, 3, 48 * depth),
                (0, 2, 32 * depth),
                (7, 2, 32 * depth),
                (9, 2, 32 * depth),
                (16, 2, 32 * depth - 1),
            ]:
                with self.subTest(depth=depth, width=width, rows=rows):
                    self.rejected(
                        self.run_tool(
                            "gfx",
                            "-d",
                            depth,
                            "--interleave",
                            "-p",
                            self.png(width, rows * 8),
                            "-o",
                            self.output,
                            self.put("tiles", bytes(length)),
                        )
                    )
            for rows in [2, 4]:
                tiles = [bytes([i + 1]) * (depth * 8) for i in range(2 * rows)]
                r = self.run_tool(
                    "gfx",
                    "-d",
                    depth,
                    "--interleave",
                    "-p",
                    self.png(16, rows * 8),
                    "-o",
                    self.output,
                    self.put("tiles", b"".join(tiles)),
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                order = [
                    base + i for base in range(0, 2 * rows, 4) for i in [0, 2, 1, 3]
                ]
                self.assertEqual(
                    self.output.read_bytes(), b"".join(tiles[i] for i in order)
                )
                self.output.write_bytes(b"unchanged")

    def test_vertical_flip_both_depths_and_layouts(self):
        for depth in [1, 2]:
            for interleave in [False, True]:
                with self.subTest(depth=depth, interleave=interleave):
                    rows = [
                        bytes(range(i * depth + 1, (i + 1) * depth + 1))
                        for i in range(16 if interleave else 8)
                    ]
                    a, b = b"".join(rows), b"".join(reversed(rows))
                    data = (
                        a[: 8 * depth]
                        + b[: 8 * depth]
                        + a[8 * depth :]
                        + b[8 * depth :]
                        if interleave
                        else a + b
                    )
                    opts = (
                        ["--interleave", "-p", self.png(16, 16)] if interleave else []
                    )
                    src = self.put("tiles", data)
                    r = self.run_tool("gfx", "-d", depth, *opts, "-o", self.output, src)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(self.output.read_bytes(), a + b)
                    r = self.run_tool(
                        "gfx",
                        "-d",
                        depth,
                        *opts,
                        "--remove-yflip",
                        "-o",
                        self.output,
                        src,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(self.output.read_bytes(), a)

    def patch(self, spans, differences, new_size=512):
        new = bytearray(new_size)
        for i in differences:
            new[i] = 0x5A
        symbols = []
        template = []
        for i, (start, length) in enumerate(spans):
            symbols.extend(
                [
                    f"00:{start:04x} .VC_Test{i}",
                    f"00:{start + length:04x} .VC_Test{i}_End",
                ]
            )
            template.append(f"[Test{i}]\n{{patch}}\n")
        return self.run_tool(
            "make_patch",
            self.put("values.sym", ("\n".join(symbols) + "\n").encode()),
            self.put("new.gbc", new),
            self.put("old.gbc", bytes(512)),
            self.put("template", "".join(template).encode()),
            self.output,
        )

    def test_patch_completeness_boundaries(self):
        for spans, diff, warning in [
            ([(0, 1)], [0, 1], 1),
            ([], [0x14E, 0x14F, 0x150], 0x150),
            ([(0, 1), (1, 1)], [0, 1], None),
            ([(0, 3), (1, 3)], [0, 1, 2, 3], None),
            ([(0, 0), (0, 1)], [0], None),
            ([(0, 1)], [0], None),
        ]:
            with self.subTest(spans=spans, diff=diff):
                r = self.patch(spans, diff)
                self.assertEqual(r.returncode, 0, r.stderr)
                if warning is None:
                    self.assertNotIn(b"Unpatched difference", r.stderr)
                else:
                    self.assertIn(
                        f"Unpatched difference at offset: 0x{warning:x}".encode(),
                        r.stderr,
                    )

    def test_patch_invalid_spans_preserve_output(self):
        for start, length, new_size in [
            (512, 1, 512),
            (511, 2, 512),
            (3, -1, 512),
            (511, 1, 511),
            (512, 1, 513),
        ]:
            with self.subTest(start=start, length=length, new_size=new_size):
                self.output.write_bytes(b"unchanged")
                self.rejected(self.patch([(start, length)], [], new_size))
        self.output.write_bytes(b"unchanged")
        self.rejected(self.patch([(0, 1), (512, 1)], [0]))
        r = self.patch([(511, 1)], [511])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"0x5a", self.output.read_bytes())
        r = self.patch([(512, 0)], [])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_lz_invalid_references_preserve_output(self):
        for data in [
            b"\x80\xff\xff",
            b"\x80\x00\x00\xff",
            b"\x00a\x80\x00\x01\xff",
            b"\x00a\xc1\x80\xff",
            b"\x00a\xa0\x81\xff",
        ]:
            with self.subTest(data=data):
                self.rejected(
                    self.run_tool("lzcomp", "-u", self.put("input", data), self.output)
                )

    def test_lz_valid_overlapping_and_reverse_copies(self):
        for data, expected in [
            (b"\x00a\x83\x80\xff", b"aaaaa"),
            (b"\x00\x01\xa3\x80\xff", b"\x01\x80\x01\x80\x01"),
            (b"\x02abc\xc2\x80\xff", b"abccba"),
        ]:
            r = self.run_tool("lzcomp", "-u", self.put("input", data), self.output)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self.output.read_bytes(), expected)

    def test_lz_size_boundaries(self):
        data = random.Random(42).randbytes(32768)
        src = self.put("raw", data)
        for method in [72, 73]:
            for align in [0, 12]:
                with self.subTest(method=method, align=align):
                    packed = self.dir / "packed"
                    r = self.run_tool(
                        "lzcomp", "--method", method, "--align", align, src, packed
                    )
                    self.assertEqual(r.returncode, 0, r.stderr)
                    r = self.run_tool("lzcomp", "-u", packed, self.output)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(self.output.read_bytes(), data)
        r = self.run_tool(
            "lzcomp", "-u", self.put("packed", b"\x00a" * 32767 + b"\xff"), self.output
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.output.read_bytes(), b"a" * 32767)
        self.output.write_bytes(b"unchanged")
        self.rejected(
            self.run_tool(
                "lzcomp", "--method", "72", self.put("raw", bytes(32769)), self.output
            )
        )
        self.rejected(
            self.run_tool(
                "lzcomp",
                "-u",
                self.put("packed", b"\xef\xff" * 32 + b"\x60\xff"),
                self.output,
            )
        )
        self.rejected(
            self.run_tool("lzcomp", "-u", self.put("packed", bytes(65536)), self.output)
        )

    def test_lz_read_failure_and_empty_input(self):
        self.rejected(self.run_tool("lzcomp", "--method", "72", self.dir, self.output))
        r = self.run_tool(
            "lzcomp", "--method", "72", self.put("empty", b""), self.output
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.output.read_bytes(), b"\xff")
        packed = self.put("packed", self.output.read_bytes())
        r = self.run_tool("lzcomp", "-u", packed, self.output)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.output.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
