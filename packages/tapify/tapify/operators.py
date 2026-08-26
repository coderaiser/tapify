import re
import traceback

from deepdiff import DeepDiff


def _deep_is(result, expected) -> bool:
    """Structural equality: same types recursively, same values."""
    if type(result) is not type(expected):
        return False
    return not DeepDiff(result, expected, ignore_nan_inequality=True)


def ok(result, message="should be truthy") -> dict:
    return {"is": bool(result), "expected": True, "result": result, "message": message}


def not_ok(result, message="should be falsy") -> dict:
    return {"is": not result, "expected": False, "result": result, "message": message}


def equal(result, expected, message="should equal") -> dict:
    from tapify.diff import diff as _diff

    is_eq = result == expected and type(result) is type(expected)
    output = (
        "" if is_eq else (_diff(expected, result) or "    result: values not equal, but deepEqual")
    )
    return {
        "is": is_eq,
        "result": result,
        "expected": expected,
        "message": message,
        "output": output,
    }


def not_equal(result, expected, message="should not equal") -> dict:
    from tapify.diff import diff as _diff

    is_eq = result == expected and type(result) is type(expected)
    output = (
        ""
        if not is_eq
        else (_diff(expected, result) or "    result: values are equal, but deepEqual")
    )
    return {
        "is": not is_eq,
        "result": result,
        "expected": expected,
        "message": message,
        "output": output,
    }


def deep_equal(result, expected, message="should deep equal") -> dict:
    from tapify.diff import diff as _diff

    is_eq = _deep_is(result, expected)
    output = "" if is_eq else _diff(expected, result)
    return {
        "is": is_eq,
        "result": result,
        "expected": expected,
        "message": message,
        "output": output,
    }


def not_deep_equal(result, expected, message="should not deep equal") -> dict:
    from tapify.diff import diff as _diff

    is_eq = _deep_is(result, expected)
    output = "" if not is_eq else _diff(expected, result)
    return {
        "is": not is_eq,
        "result": result,
        "expected": expected,
        "message": message,
        "output": output,
    }


def pass_(message="(unnamed assert)") -> dict:
    return {"is": True, "output": "", "message": message}


def fail(error, at="") -> dict:

    from tapify.validator import _is_internal, filter_frames

    frames = traceback.extract_tb(getattr(error, "__traceback__", None))
    kept = [frame for frame in frames if not _is_internal(frame.filename)]
    stack = "".join(traceback.format_list(filter_frames(kept))) if kept else ""
    return {"is": False, "stack": stack, "output": "", "message": error, "at": at}


def match(result, pattern, message="should match") -> dict:
    if not pattern or (not isinstance(pattern, (str, re.Pattern))):
        return fail(TypeError("pattern should be a str or re.Pattern"))
    try:
        rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    except re.error as e:
        return fail(e)
    return {
        "is": bool(rx.search(result)),
        "result": result,
        "expected": pattern,
        "message": message,
    }


def not_match(result, pattern, message="should not match") -> dict:
    state = match(result, pattern, message)
    return {**state, "is": not state["is"]}


def end() -> dict:
    return {}  # special-cased; never reaches _run()


_OPERATORS = {
    "ok": ok,
    "not_ok": not_ok,
    "equal": equal,
    "not_equal": not_equal,
    "deep_equal": deep_equal,
    "not_deep_equal": not_deep_equal,
    "pass": pass_,
    "pass_": pass_,
    "fail": fail,
    "match": match,
    "not_match": not_match,
    "end": end,
}


def _run(name, runner_state, test_state):

    from tapify.format import format_output

    runner_state["inc_count"]()
    count = runner_state["count"]()
    fmt = runner_state["formatter"]

    if test_state.get("is"):
        runner_state["inc_passed"]()
        fmt.emit("success", {"count": count, "message": test_state["message"]})
        return

    runner_state["inc_failed"]()
    from tapify.validator import get_at, get_stack

    error_stack = test_state.get("stack") or get_stack()
    fmt.emit(
        "fail",
        {
            "count": count,
            "message": str(test_state["message"]),
            "operator": name,
            "result": test_state.get("result"),
            "expected": test_state.get("expected"),
            "output": test_state.get("output", ""),
            "error_stack": format_output(error_stack),
            "at": test_state.get("at") or get_at(),
        },
    )


class _Operators:
    def __init__(self, runner_state, extensions):
        self._state = runner_state
        self.comment = self._make_comment()
        for name, pure_fn in _OPERATORS.items():
            setattr(self, name, _make_operator(name, pure_fn, runner_state))
        for name, factory in (extensions or {}).items():
            ext_fn = factory(_OPERATORS)
            setattr(self, name, _make_operator(name, ext_fn, runner_state, external=True))

    def _make_comment(self):
        state = self._state

        def comment(message: str) -> None:
            for line in message.splitlines():
                stripped = line.strip().lstrip("#").strip()
                state["formatter"].emit("comment", {"message": stripped})

        return comment


def _make_operator(name, pure_fn, runner_state, external=False):
    def wrapper(*args, **kwargs):
        is_ended = runner_state["is_ended"]

        if name == "end":
            if is_ended[0]:
                _run(
                    "fail",
                    runner_state,
                    fail(Exception("Cannot use a couple 't.end()' operators in one test")),
                )
                return
            is_ended[0] = True
            return  # end() does NOT count as an assertion

        runner_state["inc_assertions_count"]()

        if is_ended[0]:
            _run(
                "fail",
                runner_state,
                fail(Exception("Cannot run assertions after 't.end()' called")),
            )
            return

        if external:
            test_state = pure_fn(*args, **kwargs)
            if isinstance(test_state, dict) and "is" in test_state:
                _run(name, runner_state, test_state)
            return

        test_state = pure_fn(*args, **kwargs)

        if test_state is None:
            _run("fail", runner_state, fail(Exception("☝️ Looks like operator returns nothing")))
            return

        _run(name, runner_state, test_state)

    return wrapper


def init_operators(runner_state, extensions=None) -> _Operators:
    return _Operators(runner_state, extensions)
