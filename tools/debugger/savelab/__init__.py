"""Save-state laboratory: VBA .sgm decode, PyBoy .state conversion, field-level diff.

Modules:
  sgm_decoder  — VBA-M .sgm save-state parser
  state_conv   — Cross-format state conversion (VBA ↔ PyBoy)
  state_diff   — Field-by-field state comparison
"""

__all__ = ["sgm_decoder", "state_conv", "state_diff"]
