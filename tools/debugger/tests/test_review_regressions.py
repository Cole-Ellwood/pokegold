"""Public regressions for the exhaustive review's debugger findings."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.debugger import consequence, dap_server, register_flow
from tools.debugger.bisect import BisectError, run_bisect
from tools.debugger.clobber_chain import build_clobber_chain_report
from tools.debugger.clobber_graph import build_static_call_graph
from tools.debugger.effect_trace import build_effect_trace_report
from tools.debugger.tdb import run_tdb


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'home').mkdir()

    def source(self, body):
        (self.root / 'home/unit.asm').write_text(body, encoding='utf-8')

    def test_load_macros_match_load_instructions(self):
        for pair in ('bc', 'de', 'hl'):
            with self.subTest(pair=pair):
                self.source(f'Macro:\n\tlb {pair}, 1, 2\n\tret\nLoad:\n\tld {pair}, $102\n\tret\n')
                macro = register_flow.analyze_function('Macro', root=self.root)
                load = register_flow.analyze_function('Load', root=self.root)
                self.assertEqual(macro['clobber_set'], load['clobber_set'])
        report = register_flow.analyze_function('HPBarAnim_UpdateHPRemaining')
        self.assertTrue({'b', 'c'} <= set(report['clobber_set']))
        self.source('Root:\n\tln b, 1, 2\n\tret\n')
        self.assertEqual(register_flow.analyze_function('Root', root=self.root)['clobber_set'], ['b'])

    def test_auto_update_source_and_destination(self):
        for operand in ('[hli]', '[hld]', '[hl+]', '[hl-]', '[hl]'):
            for instruction in (f'ld a, {operand}', f'ld {operand}, a'):
                with self.subTest(instruction=instruction):
                    self.source(f'Root:\n\t{instruction}\n\tret\n')
                    report = build_clobber_chain_report(function='Root', register='hl', root=self.root)
                    self.assertEqual(report['query_clobbered'], operand != '[hl]')

    def test_stack_transfer_and_matching_preservation(self):
        cases = (
            ('push bc\n\tpop de', 'de', True),
            ('pop de', 'de', True),
            ('push bc\n\tld b, 1\n\tpop bc', 'bc', False),
            ('push bc\n\tpush de\n\tld b, 1\n\tld d, 2\n\tpop de\n\tpop bc', 'bc', False),
            ('push bc\n\tld b, 1\n\tpop de', 'bc', True),
            ('push de\n\tpush bc\n\tpop de\n\tpop de', 'de', False),
            ('push bc\n\tpush de\n\tpop bc\n\tpop de', 'bc', True),
        )
        for body, register, expected in cases:
            with self.subTest(body=body, register=register):
                self.source(f'Root:\n\t{body}\n\tret\n')
                report = build_clobber_chain_report(function='Root', register=register, root=self.root)
                self.assertEqual(report['query_clobbered'], expected)

    def test_relative_jump_edges_and_local_branches(self):
        for jump in ('jr Target', 'jr nz, Target', 'jp Target'):
            with self.subTest(jump=jump):
                self.source(f'Root:\n\t{jump}\n\tret\nTarget:\n\tld b, 1\n\tret\n')
                graph = build_static_call_graph(root=self.root)
                self.assertTrue(any(edge.callee == 'Target' for edge in graph.edges))
                report = build_clobber_chain_report(function='Root', register='b', root=self.root)
                self.assertTrue(report['query_clobbered'])
        self.source('Root:\n\tjr nz, .done\n\tld b, 1\n.done\n\tret\n')
        report = build_clobber_chain_report(function='Root', register='b', root=self.root)
        self.assertTrue(report['query_clobbered'])
        self.assertEqual(report['indirect_call_warnings'], [])

    def test_consequence_retains_callee_clobbers_and_warnings(self):
        self.source('Root:\n\tcall Target\n\tcall Missing\n\tmystery\n\tret\nTarget:\n\tld b, 1\n\tret\n')
        report = consequence.build_consequence_report(symbol='Root', root=self.root)
        chain = report['transitive_clobber']
        self.assertEqual(chain['clobbered_registers'], ['b'])
        self.assertEqual(chain['callees_analyzed'], 2)
        self.assertTrue(chain['warnings'])
        rendered = consequence.render_text(report)
        self.assertIn("transitive callee clobber: ['b']", rendered)
        self.assertIn('Missing', rendered)
        self.assertIn('mystery', rendered)
        self.source('Root:\n\tret\n')
        report = consequence.build_consequence_report(symbol='Root', root=self.root)
        self.assertEqual(report['transitive_clobber']['clobbered_registers'], [])
        self.assertEqual(report['transitive_clobber']['callees_analyzed'], 0)
        self.assertEqual(report['transitive_clobber']['warnings'], [])

    def test_tdb_consumes_actual_register_sources(self):
        sym = self.root / 'unit.sym'
        sym.write_text('00:1000 Root\n01:d141 Target\n')
        # Memory store, register transfer, arithmetic, and immediate-only controls.
        cases = ((0xEA, [0x41, 0xD1], True), (0x47, [], True),
                 (0x80, [], True), (0x41, [], False), (0x06, [9], False))
        for opcode, operand, expected in cases:
            with self.subTest(opcode=opcode):
                trace = self.root / 'trace.json'
                trace.write_text(json.dumps([{'seq': 0, 'bank': 0, 'pc': 0x1000,
                    'opcode': opcode, 'operand': operand, 'A': 42, 'B': 3, 'C': 4, 'F': 0,
                    'bank_state': {'wram': 1}}]))
                effect = build_effect_trace_report(traces=(str(trace),), symbols_path=str(sym), root=self.root)
                path = self.root / 'effects.json'
                path.write_text(json.dumps(effect))
                result = run_tdb(query='reads(reg=A)', reports=(str(path),), root=self.root)
                self.assertEqual(result['match_count'] > 0, expected)
                if opcode == 0xEA:
                    for bank, matches in ((1, 1), (2, 0)):
                        result = run_tdb(query=f'reads(reg=A) and writes(addr=$D141, bank={bank})', reports=(str(path),), root=self.root)
                        self.assertEqual(result['match_count'], matches)

    def test_dap_short_and_full_writes(self):
        class Writer(io.BytesIO):
            def __init__(self, limit):
                super().__init__()
                self.limit = limit
            def write(self, data):
                return super().write(data[:self.limit])
        request = dap_server.encode_frame({'seq': 1, 'type': 'request', 'command': 'initialize', 'arguments': {}})
        for limit in (1, 7, 100000):
            with self.subTest(limit=limit):
                output = Writer(limit)
                dap_server.serve_stream(dap_server.DapServer(), io.BytesIO(request), output)
                output.seek(0)
                self.assertEqual(dap_server.read_frame(output)['type'], 'response')
                self.assertEqual(dap_server.read_frame(output)['type'], 'event')
                self.assertIsNone(dap_server.read_frame(output))

    def test_dap_no_progress_fails_explicitly(self):
        class Writer(io.BytesIO):
            def write(self, data):
                return progress
        request = dap_server.encode_frame({'seq': 1, 'type': 'request', 'command': 'initialize'})
        for progress in (0, None):
            with self.subTest(progress=progress), self.assertRaises(OSError):
                dap_server.serve_stream(dap_server.DapServer(), io.BytesIO(request), Writer())

    def test_dap_fragmented_reads_and_write_errors(self):
        class Reader(io.BytesIO):
            def read(self, size=-1):
                return super().read(min(size, 3))
        class Writer(io.BytesIO):
            def write(self, data):
                raise BrokenPipeError('closed')
        request = dap_server.encode_frame({'seq': 1, 'type': 'request', 'command': 'initialize'})
        output = io.BytesIO()
        dap_server.serve_stream(dap_server.DapServer(), Reader(request), output)
        output.seek(0)
        self.assertEqual(dap_server.read_frame(output)['type'], 'response')
        self.assertEqual(dap_server.read_frame(output)['type'], 'event')
        with self.assertRaises(BrokenPipeError):
            dap_server.serve_stream(dap_server.DapServer(), io.BytesIO(request), Writer())

    def test_read_only_rejects_output_abbreviations_before_writing(self):
        for flag in ('--json-out', '--json-o', '--json-out=', '--json-o='):
            with self.subTest(flag=flag):
                dest = self.root / 'report.json'
                args = [flag + str(dest)] if flag.endswith('=') else [flag, str(dest)]
                result = subprocess.run([sys.executable, '-m', 'tools.debugger', '--read-only', 'inventory', *args], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(dest.exists())
                dest.write_bytes(b'keep existing report')
                result = subprocess.run([sys.executable, '-m', 'tools.debugger', '--read-only', 'inventory', *args], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(dest.read_bytes(), b'keep existing report')
                dest.unlink()
        dest = self.root / 'ordinary.json'
        result = subprocess.run([sys.executable, '-m', 'tools.debugger', 'inventory', '--json-o', str(dest)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(dest.exists())
        result = subprocess.run([sys.executable, '-m', 'tools.debugger', '--read-only', 'clobbers', '--symbol', 'MenuClickSound', '--json'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_active_bisect_survives_in_repository_and_worktree(self):
        def git(repo, *args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()
        repo = self.root / 'repo'
        repo.mkdir()
        git(repo, 'init')
        git(repo, 'config', 'user.name', 'Regression Test')
        git(repo, 'config', 'user.email', 'test@example.invalid')
        git(repo, 'config', 'commit.gpgsign', 'false')
        commits = []
        for index in range(4):
            (repo / 'value').write_text(str(index))
            git(repo, 'add', 'value')
            git(repo, 'commit', '-m', str(index))
            commits.append(git(repo, 'rev-parse', 'HEAD'))
        linked = self.root / 'linked'
        git(repo, 'worktree', 'add', '--detach', str(linked))
        for work in (repo, linked):
            with self.subTest(work=work):
                git(work, 'bisect', 'start', commits[-1], commits[0])
                head = git(work, 'rev-parse', 'HEAD')
                log = git(work, 'bisect', 'log')
                marker = self.root / 'scenario-ran'
                with self.assertRaisesRegex(BisectError, 'already in a bisect'):
                    run_bisect(good_ref=commits[0], bad_ref=commits[-1], scenario_argv=[sys.executable, '-c', 'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("ran")', str(marker)], repo=work)
                self.assertEqual(git(work, 'rev-parse', 'HEAD'), head)
                self.assertEqual(git(work, 'bisect', 'log'), log)
                self.assertFalse(marker.exists())
                git(work, 'bisect', 'reset')


if __name__ == '__main__':
    unittest.main()
