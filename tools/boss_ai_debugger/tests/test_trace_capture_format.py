from __future__ import annotations

import unittest

from tools.trace.boss_ai_trace_capture import format_capture


class TraceCaptureFormatTests(unittest.TestCase):
    def test_format_capture_includes_model_score_snapshot(self) -> None:
        values = {
            "wBossAITraceTopMoves": [1, 2, 0],
            "wBossAITraceTopScores": [14, 20, 255],
            "wBossAITracePreModelScores": [20, 20, 80, 255],
            "wBossAITracePostModelScores": [14, 20, 80, 255],
            "wBossAITraceChosenMove": [1],
            "wBossAITraceSwitchConfidence": [0],
            "wBossAITracePlanId": [0],
            "wBossAITracePlanPhase": [0],
            "wBossAITracePlanConfidence": [0],
            "wBossAITracePlausibleMask": [0, 0, 0, 0],
            "wBossAITraceRiskFlags": [0],
            "wBossAITraceLookaheadBonusTop": [0, 0, 0],
            "wBossAIRevealedMovesBitmap": [0] * 24,
            "wBossAITier": [3],
            "wEnemyMonMoves": [1, 2, 3, 0],
            "wEnemyAIMoveScores": [13, 20, 80, 80],
            "wCurEnemyMoveNum": [0],
            "wCurEnemyMove": [1],
            "wEnemySwitchMonParam": [0],
            "wEnemySwitchMonIndex": [0],
            "wBossAILastSwitchedOut": [0],
            "wBossAISwitchCooldown": [0],
            "wCurOTMon": [0],
        }

        text = format_capture(values, {1: "POUND", 2: "KARATE_CHOP"}, {})

        self.assertIn("pre_model_scores=20,20,80,255", text)
        self.assertIn("post_model_scores=14,20,80,255", text)
        self.assertIn("model_score_deltas=-6,+0,+0,na", text)


if __name__ == "__main__":
    unittest.main()
