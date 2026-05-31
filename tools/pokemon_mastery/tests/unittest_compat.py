from __future__ import annotations

from contextlib import contextmanager
import inspect
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


@contextmanager
def raises(exc_type: type[BaseException], match: str | None = None):
    try:
        yield
    except exc_type as exc:
        if match is not None and re.search(match, str(exc)) is None:
            raise AssertionError(
                f"exception message {str(exc)!r} did not match {match!r}"
            ) from exc
    else:
        raise AssertionError(f"{exc_type.__name__} was not raised")


class MonkeyPatch:
    def __init__(self) -> None:
        self._patchers: list[object] = []

    def setattr(self, target: object, name: str, value: object) -> None:
        patcher = patch.object(target, name, value)
        patcher.start()
        self._patchers.append(patcher)

    def undo(self) -> None:
        while self._patchers:
            patcher = self._patchers.pop()
            patcher.stop()


class FixtureContext:
    def __init__(self, factories: dict[str, object] | None = None) -> None:
        self._factories = factories or {}
        self._values: dict[str, object] = {}
        self._tmp_dirs: list[TemporaryDirectory[str]] = []
        self._monkeypatch = MonkeyPatch()

    def get(self, name: str) -> object:
        if name in self._values:
            return self._values[name]
        if name == "tmp_path":
            tmp = TemporaryDirectory()
            self._tmp_dirs.append(tmp)
            value = Path(tmp.name)
        elif name == "monkeypatch":
            value = self._monkeypatch
        elif name in self._factories:
            factory = self._factories[name]
            value = factory(self)  # type: ignore[operator]
        else:
            raise TypeError(f"unsupported test fixture {name!r}")
        self._values[name] = value
        return value

    def close(self) -> None:
        self._monkeypatch.undo()
        while self._tmp_dirs:
            self._tmp_dirs.pop().cleanup()


def make_load_tests(
    globals_dict: dict[str, object],
    fixture_factories: dict[str, object] | None = None,
):
    def load_tests(loader, tests, pattern):  # noqa: ANN001
        suite = unittest.TestSuite()
        for name, obj in sorted(globals_dict.items()):
            if name.startswith("test_") and inspect.isfunction(obj):
                suite.addTest(_function_case(obj, fixture_factories))
        return suite

    return load_tests


def _function_case(fn, fixture_factories: dict[str, object] | None):  # noqa: ANN001
    signature = inspect.signature(fn)

    def run() -> None:
        ctx = FixtureContext(fixture_factories)
        try:
            kwargs = {
                name: ctx.get(name)
                for name in signature.parameters
            }
            fn(**kwargs)
        finally:
            ctx.close()

    run.__name__ = fn.__name__
    return unittest.FunctionTestCase(run)
