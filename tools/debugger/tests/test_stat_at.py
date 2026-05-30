import io
import unittest
from contextlib import redirect_stdout

from tools.debugger.stat_at import build_stat_at_report, main


class StatAtTests(unittest.TestCase):
    def test_known_species_reports_base_stat(self) -> None:
        report = build_stat_at_report(
            species="PINSIR", stat="atk", level=50, modifier=0, iv=15, ev=65535
        )
        self.assertTrue(report["valid"], report)
        self.assertEqual(report["base"], 140)

    def test_unknown_species_is_invalid(self) -> None:
        report = build_stat_at_report(
            species="NOTAMON", stat="atk", level=50, modifier=0, iv=15, ev=65535
        )
        self.assertFalse(report["valid"])

    def test_main_returns_status_codes(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--species", "PINSIR", "--stat", "atk"]), 0)
            self.assertEqual(main(["--species", "NOTAMON", "--stat", "atk"]), 1)


if __name__ == "__main__":
    unittest.main()
