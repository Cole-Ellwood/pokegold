"""Debug Adapter Protocol (DAP) server for VS Code.

Pure-Python DAP implementation over stdio transport. Provides
breakpoint, step, step-back, watch-expression, and variable
inspection for SM83 assembly using RGBDS source maps.

Usage:
    python -m tools.debugger.presentation.dap

VS Code launch.json:
    {
        "type": "gbc-debug",
        "request": "launch",
        "name": "Debug Pokemon Gold",
        "program": "${workspaceFolder}/pokegold.gbc",
        "args": ["--variant", "pokegold"]
    }
"""

__all__ = ["DapServer", "DapSession"]

from .server import DapServer, DapSession
