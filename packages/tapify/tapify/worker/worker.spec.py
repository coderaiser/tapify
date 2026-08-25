import io
import os
import re

from tapify import test
from tapify.worker import _exit_code, run_with_worker, run_without_worker


def _mk(fn):
    return {
        "message": fn.__doc__ or "scope: t",
        "fn": fn,
        "skip": False,
        "only": False,
        "extensions": {},
        "timeout": 3000,
    }


def _pass(t):
    t.ok(True)
    t.end()


def _fail(t):
    t.ok(False)
    t.end()


def _named(fn, name):
    d = _mk(fn)
    d["message"] = name
    return d


@test("worker: run_without_worker passes")
def _(t):
    buf = io.StringIO()
    code = run_without_worker([_named(_pass, "scope: ok")], format_name="tap", stream=buf)
    t.ok(code == 0 and bool(re.search(r"ok 1", buf.getvalue())))
    t.end()


@test("worker: run_without_worker fails with FAIL code")
def _(t):
    buf = io.StringIO()
    code = run_without_worker([_named(_fail, "scope: bad")], format_name="tap", stream=buf)
    t.equal(code, 1)
    t.end()


@test("worker: run_with_worker passes")
def _(t):
    buf = io.StringIO()
    code = run_with_worker([_named(_pass, "scope: ok")], format_name="tap", stream=buf)
    value = buf.getvalue()
    t.equal(
        (code, "TAP version 13" in value, "# ok" in value),
        (0, True, True),
    )
    t.end()


@test("worker: run_with_worker reports failures")
def _(t):
    buf = io.StringIO()
    code = run_with_worker([_named(_fail, "scope: bad")], format_name="tap", stream=buf)
    t.equal((code, "not ok 1" in buf.getvalue()), (1, True))
    t.end()


@test("worker: _exit_code stop beats fail")
def _(t):
    t.equal(_exit_code({"failed": 3}, lambda: True), 2)
    t.end()


@test("worker: _exit_code fail when no stop")
def _(t):
    t.equal(_exit_code({"failed": 3}, None), 1)
    t.end()


@test("worker: _exit_code skipped when check enabled")
def _(t):
    saved = os.environ.get("TAPIFY_CHECK_SKIPPED")
    os.environ["TAPIFY_CHECK_SKIPPED"] = "1"
    try:
        code = _exit_code({"failed": 0, "skipped": 2}, None)
    finally:
        if saved is None:
            os.environ.pop("TAPIFY_CHECK_SKIPPED", None)
        else:
            os.environ["TAPIFY_CHECK_SKIPPED"] = saved
    t.equal(code, 5)
    t.end()


@test("worker: _exit_code ok otherwise")
def _(t):
    t.equal(_exit_code({"failed": 0, "skipped": 0}, None), 0)
    t.end()
