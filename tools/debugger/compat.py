"""Compatibility bridges between the new debugger kernel and existing tools.

Existing tools (damage_debugger, boss_ai_debugger) continue to use their
own modules unchanged. This module provides adapters for code that wants
to use the new unified service while remaining compatible with the old API.

Usage:
    from tools.debugger.compat import symbol_table_from_service

    svc = SymbolService.from_project()
    old_style = symbol_table_from_service(svc)
    # old_style has the same API as damage_debugger.symbols.SymbolTable
"""

from __future__ import annotations

from tools.damage_debugger.symbols import Symbol, SymbolTable

from .kernel.symbol_service import SymbolEntry, SymbolService


def symbol_table_from_service(svc: SymbolService) -> SymbolTable:
    """Build a legacy SymbolTable from the new SymbolService."""
    symbols = [
        Symbol(bank=e.bank, address=e.address, name=e.name)
        for e in svc._symbols
    ]
    return SymbolTable(symbols)


def symbol_entry_from_legacy(sym: Symbol) -> SymbolEntry:
    return SymbolEntry(bank=sym.bank, address=sym.address, name=sym.name)


def service_from_symbol_table(table: SymbolTable) -> SymbolService:
    """Build a SymbolService from a legacy SymbolTable (sym-only, no .map)."""
    entries = [
        SymbolEntry(bank=sym.bank, address=sym.address, name=sym.name)
        for sym in table._by_name.values()
    ]
    return SymbolService(entries)
