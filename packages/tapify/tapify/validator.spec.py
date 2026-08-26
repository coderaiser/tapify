import re

from tapify import test
from tapify.validator import (
    create_validator,
    get_at,
    reset_processed,
    reset_validations,
    set_validations,
)


def _tests(*messages):
    return [
        {
            "message": m,
            "at": "file.py:1",
            "validations": {
                "check_duplicates": True,
                "check_scopes": True,
                "check_assertions_count": True,
            },
        }
        for m in messages
    ]


@test("validator: one assertion passes")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    t.equal(v("scope: x", assertions_count=1), [])
    reset_validations()
    t.end()


@test("validator: zero assertions fails")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    msg, at = v("scope: x", assertions_count=0)
    t.match(msg, r"have none")
    reset_validations()
    t.end()


@test("validator: two assertions fails")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    msg, at = v("scope: x", assertions_count=2)
    t.match(msg, r"have more")
    reset_validations()
    t.end()


@test("validator: bad scope fails when check_scopes enabled")
def _(t):
    set_validations(
        {"check_scopes": True, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("no scope here"))
    msg, at = v("no scope here", assertions_count=1)
    t.match(msg, r"Scope should be defined")
    reset_validations()
    t.end()


@test("validator: duplicates detected once")
def _(t):
    set_validations(
        {"check_duplicates": True, "check_scopes": False, "check_assertions_count": False}
    )
    reset_processed()
    v = create_validator(tests=_tests("scope: dup", "scope: dup"))
    result = v("scope: dup", assertions_count=1)
    t.ok(result, "first duplicate reported")
    reset_processed()
    reset_validations()
    t.end()


@test("validator: unknown message raises")
def _(t):
    set_validations(
        {"check_scopes": True, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("scope: known"))
    try:
        v("scope: unknown", assertions_count=1)
        raised = False
    except RuntimeError:
        raised = True
    t.ok(raised)
    reset_validations()
    t.end()


@test("validator: all disabled returns empty")
def _(t):
    set_validations(
        {"check_scopes": False, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("anything"))
    t.equal(v("anything", assertions_count=0), [])
    reset_validations()
    t.end()


@test("validator: get_at returns user frame")
def _(t):
    at = get_at()
    t.match(at, r"\.py:\d+$")
    t.end()


@test("validator: filter_frames keeps deepest user frame onward")
def _(t):
    import traceback

    from tapify.validator import filter_frames

    frames = traceback.extract_stack()
    kept = filter_frames(frames)
    t.not_equal(kept, frames)
    t.end()


@test("validator: filter_frames drops python internals from head")
def _(t):
    import traceback

    from tapify.validator import _is_internal, filter_frames

    kept = filter_frames(traceback.extract_stack())
    names = [frame.filename for frame in kept]
    t.ok(not _is_internal(names[0]) or len(kept) == 1)
    t.end()


@test("validator: get_stack output has no runpy/threading frames")
def _(t):
    from tapify.validator import get_stack

    stack = get_stack()
    t.ok("runpy" not in stack and "threading" not in stack)
    t.end()


@test("validator: get_stack starts at a user file")
def _(t):
    import os

    from tapify.validator import get_stack

    stack = get_stack()
    first_file = [line for line in stack.splitlines() if 'File "' in line][0]
    t.match(first_file, rf"{re.escape(os.path.basename(__file__.removesuffix('.spec.py')))}")
    t.end()


@test("validator: get_at falls back when no user frame exists")
def _(t):
    from unittest import mock

    from tapify.validator import get_at

    frames = [
        mock.Mock(filename="/usr/lib/python3.12/threading.py", lineno=1030),
        mock.Mock(filename="<frozen runpy>", lineno=198),
    ]
    with mock.patch("tapify.validator.traceback.extract_stack", return_value=frames):
        at = get_at()
    t.equal(at, "at <frozen runpy>:198")
    t.end()


@test("validator: _is_user rejects internal and generated filenames")
def _(t):
    from tapify.validator import _is_user

    result = (
        _is_user("<frozen runpy>"),
        _is_user("/x/asyncio/base.py"),
        _is_user("/x/tapify/tapify/operators.py"),
        _is_user("/env/site-packages/pkg/mod.py"),
        _is_user("/w/packages/formatter-tap/formatter_tap/__init__.py"),
        _is_user("/tmp/user_code.spec.py"),
    )
    t.equal(result, (False, False, False, False, False, True))
    t.end()
