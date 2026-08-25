import json

_lines: list = []
_current = ""


def _buf() -> list:
    return _lines


def _j(obj) -> str:
    return json.dumps(obj, default=str) + "\n"


def start(**_):
    return None


def success(**_):
    return None


def comment(**_):
    return None


def test(*, test, **_) -> None:
    global _current
    _current = test
    return None


def test_end(*, count, total, failed, test, **_) -> None:
    _buf().append(_j({"count": count, "total": total, "failed": failed, "test": test}))
    return None


def fail(
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
    _buf().append(
        _j(
            {
                "test": _current,
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


def end(*, count=0, passed=0, failed=0, skipped=0, **_) -> str:
    _buf().append(_j({"count": count, "passed": passed, "failed": failed, "skipped": skipped}))
    result = "".join(_buf())
    _lines.clear()
    return result
