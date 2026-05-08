"""Boss AI preference-labeling side app."""

from .data import (
    ALLOWED_LABELS,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    TOOL_VERSION,
    append_label,
    build_report,
    load_fixtures,
    load_labels,
    render_markdown_report,
)

__all__ = [
    "ALLOWED_LABELS",
    "DEFAULT_FIXTURES_PATH",
    "DEFAULT_LABELS_PATH",
    "TOOL_VERSION",
    "append_label",
    "build_report",
    "load_fixtures",
    "load_labels",
    "render_markdown_report",
]
