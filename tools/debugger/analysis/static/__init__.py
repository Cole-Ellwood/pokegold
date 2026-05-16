"""Static analysis: register-clobber inference, save-format lock, bank pressure.

Modules:
  clobber_inference — Per-function (uses, defs, preserves) via abstract interp
  save_format_lock  — Save-format drift detection against lockfile
  bank_pressure     — Free-space tracking and threshold enforcement
  stack_depth       — Whole-program stack-depth bounds
  cross_bank        — Plain call to another ROMX bank detection
  macro_safety      — farcall hl/a clobber + c-mirror checks
"""
