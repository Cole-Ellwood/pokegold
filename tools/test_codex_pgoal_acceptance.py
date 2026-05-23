"""Pytest acceptance tests for codex-pgoal-skill-v1.

5 mechanical tests that gate the pgoal completion check.
"""

from __future__ import annotations

import json
import os
import subprocess


SKILL_PATH = os.path.expanduser("~/.claude/skills/codex-pgoal/SKILL.md")
ROADMAP_PATH = "docs/codex_pgoal_skill_codex_task.md"
LOG_PATH = "audit/codex_pgoal_handoff_log.jsonl"


def test_skill_exists() -> None:
    """codex-pgoal SKILL.md exists at the user-level skills path."""
    assert os.path.exists(SKILL_PATH), f"missing {SKILL_PATH}"


def test_skill_frontmatter() -> None:
    """SKILL.md has YAML frontmatter with name + description."""
    text = open(SKILL_PATH, encoding="utf-8").read()
    assert "name: codex-pgoal" in text, "missing 'name: codex-pgoal' in frontmatter"
    assert "description:" in text, "missing 'description:' in frontmatter"


def test_skill_sections() -> None:
    """SKILL.md contains Step 0 through Step 7 section markers."""
    text = open(SKILL_PATH, encoding="utf-8").read()
    needed = [f"Step {i}" for i in range(8)]
    missing = [s for s in needed if s not in text]
    assert not missing, f"missing sections: {missing}"


def test_roadmap_committed() -> None:
    """Roadmap doc has at least one commit in git log.

    Uses stdin=DEVNULL + stderr=DEVNULL to keep subprocess from trying
    to inherit pytest's captured stdin handle on Windows. Without
    stdin=DEVNULL, `subprocess._make_inheritable` can fail with
    `OSError: [WinError 6] The handle is invalid` when pytest has
    captured stdin (which is its default). Confirmed by running this
    test 5x in a row with capture_output=True: ~80%% transient failure
    rate. With explicit stdin redirection: 100%% stable.
    """
    output = subprocess.check_output(
        ["git", "log", "--oneline", "--", ROADMAP_PATH],
        text=True,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert output.strip(), "no commits on roadmap doc"


def test_mutual_done_row_present() -> None:
    """Handoff log has a mutual_done row for codex-pgoal-skill-v1 status=complete."""
    assert os.path.exists(LOG_PATH), f"missing {LOG_PATH}"
    rows = [json.loads(line) for line in open(LOG_PATH, encoding="utf-8")]
    ok = any(
        row.get("event") == "mutual_done"
        and row.get("phase") == "codex-pgoal-skill-v1"
        and row.get("status") == "complete"
        for row in rows
    )
    assert ok, "no mutual_done row found for codex-pgoal-skill-v1"
