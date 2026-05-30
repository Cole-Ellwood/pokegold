import io
import unittest
from contextlib import redirect_stdout

from tools.debugger.type_matchup import build_type_matchup_report, main


class TypeMatchupTests(unittest.TestCase):
    def test_retyped_species_reports_hack_types(self) -> None:
        report = build_type_matchup_report(species="GYARADOS")
        self.assertTrue(report["valid"], report)
        # This hack re-types Gyarados to Water/Dragon (not vanilla Water/Flying).
        self.assertIn("DRAGON", report["types"])

    def test_unknown_species_is_invalid(self) -> None:
        self.assertFalse(build_type_matchup_report(species="NOTAMON")["valid"])

    def test_main_returns_status_codes(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--species", "GYARADOS"]), 0)
            self.assertEqual(main(["--species", "NOTAMON"]), 1)


if __name__ == "__main__":
    unittest.main()
