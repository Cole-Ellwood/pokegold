"""Pokemon Gold romhack debugger front door.

The heavy debugging logic still lives in focused subsystem packages. This
package inventories those tools, routes common symptoms to them, and tracks
the remaining gaps against this romhack's whole-ROM debugger goal.
"""

from .catalog import build_capability_report, build_inventory, triage_request
from .content_mirror import build_content_mirror_report
from .content_scenarios import build_content_scenario_report
from .coverage import build_coverage_report
from .dynamic_taint import build_dynamic_taint_report
from .expect import build_expectation_report
from .fuzz import build_fuzz_plan
from .generate import build_generation_plan
from .ingest import ingest_artifacts
from .instruction_trace import build_instruction_trace_report
from .investigate import build_investigation_run
from .localize import build_localization_plan
from .minimize import build_minimization_plan
from .mirrors import build_compare_plan
from .provenance import build_provenance_report
from .ranking import rank_findings
from .reporting import build_static_report
from .runtime_watch import build_watch_report
from .slicing import build_slice_report
from .setup_plan import build_setup_plan
from .taint import build_taint_report
from .testgen import suggest_tests
from .trace_index import build_trace_index_report
from .workflow import build_gate_plan

__all__ = [
    "build_capability_report",
    "build_content_mirror_report",
    "build_content_scenario_report",
    "build_inventory",
    "build_coverage_report",
    "build_dynamic_taint_report",
    "build_expectation_report",
    "build_fuzz_plan",
    "build_generation_plan",
    "build_gate_plan",
    "build_instruction_trace_report",
    "build_investigation_run",
    "build_localization_plan",
    "build_minimization_plan",
    "build_compare_plan",
    "build_provenance_report",
    "build_slice_report",
    "build_setup_plan",
    "build_static_report",
    "build_taint_report",
    "build_trace_index_report",
    "build_watch_report",
    "ingest_artifacts",
    "rank_findings",
    "suggest_tests",
    "triage_request",
]
