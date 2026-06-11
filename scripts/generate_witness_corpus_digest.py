#!/usr/bin/env python3
"""Write the tracked digest for the untracked Boss AI witness proof corpus.

The witness materialization corpus (multi-GB machine-regenerated evidence
JSON under audit/boss_ai_debugger/god_level_benchmark/artifacts/) is NOT
tracked in git: single files exceed GitHub's 100 MB hard limit and the
content is fully regenerable by the debugger pipelines (witness_reexec,
rom-counterfactual-materialize, rom-score-materialize). This script records
per-file sha256 + size + counts in a small tracked JSON so any corpus state
remains verifiable against the commit that used it.

Run after any corpus regeneration:
    python scripts/generate_witness_corpus_digest.py

Note: hashing a file mid-write (e.g. while witness_reexec is running) gives
a digest that won't reproduce — regenerate once the pipeline is idle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "audit/boss_ai_debugger/god_level_benchmark/artifacts"
CORPUS_DIRS = (
    "counterfactual_witness_materializations",
    "score_witness_materializations",
)
OUT = ARTIFACTS / "witness_corpus_digest.json"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    corpus: dict[str, dict] = {}
    total_bytes = 0
    total_files = 0
    for dirname in CORPUS_DIRS:
        base = ARTIFACTS / dirname
        files = {}
        for path in sorted(base.glob("*.json")) if base.is_dir() else []:
            size = path.stat().st_size
            files[path.name] = {"size": size, "sha256": sha256_of(path)}
            total_bytes += size
            total_files += 1
        corpus[dirname] = {"file_count": len(files), "files": files}
    report = {
        "schema_version": 1,
        "kind": "boss_ai_witness_corpus_digest",
        "total_file_count": total_files,
        "total_bytes": total_bytes,
        "corpus": corpus,
    }
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT.relative_to(ROOT)} ({total_files} files, {total_bytes / 1e9:.2f} GB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
