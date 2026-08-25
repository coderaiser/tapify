import json


def _j(obj) -> str:
    return json.dumps(obj, default=str) + "\n"


class _JsonLines:
    """Formatter instance with isolated state (createFormatter protocol)."""

    def __init__(self):
        self._lines: list = []
        self._current = ""

    def start(self, **_):
        return None

    def success(self, **_):
        return None

    def comment(self, **_):
        return None

    def test(self, *, test, **_) -> None:
        self._current = test
        return None

    def test_end(self, *, count, total, failed, test, **_) -> None:
        self._lines.append(_j({"count": count, "total": total, "failed": failed, "test": test}))
        return None

    def fail(
        self,
        *,
        at="",
        count=0,
        message="",
        operator="",
        result=None,
        expected=None,
        output="",
        error_stack="",
        **_,
    ) -> None:
        self._lines.append(
            _j(
                {
                    "test": self._current,
                    "at": at,
                    "count": count,
                    "message": message,
                    "operator": operator,
                    "result": result,
                    "expected": expected,
                    "errorStack": error_stack,
                    "output": output,
                }
            )
        )
        return None

    def end(self, *, count=0, passed=0, failed=0, skipped=0, **_) -> str:
        summary = {"count": count, "passed": passed, "failed": failed, "skipped": skipped}
        self._lines.append(_j(summary))
        result = "".join(self._lines)
        self._lines.clear()
        return result


def create_formatter(**_):
    """Returns a fresh formatter instance with isolated state."""
    return _JsonLines()


_default = _JsonLines()

start = _default.start
success = _default.success
comment = _default.comment
test = _default.test
test_end = _default.test_end
fail = _default.fail
end = _default.end
