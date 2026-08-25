import io
import os
import re
import sys

from tapify import test
from tapify.supertape import create_test

import formatter_progress_bar as fpb


def _with_env(env, fn):
    saved = {k: os.environ.get(k) for k in env}
    for k, v in env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)
    try:
        return fn()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _run(fn_map, env=None) -> str:
    def _inner():
        buf = io.StringIO()
        t_fn, _, run = create_test(formatter=fpb, stream=buf)
        for msg, fn in fn_map.items():
            t_fn(msg)(fn)
        run()
        return buf.getvalue()[1:]  # strip leading \r

    return _with_env(env or {"CI": "1"}, _inner)


@test("formatter_progress_bar: CI mode shows TAP header")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn}, env={"CI": "1"})
    t.match(result, r"TAP version 13")
    t.end()


@test("formatter_progress_bar: failure shows test name")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    result = _run({"scope: failing": fn}, env={"CI": "1"})
    t.match(result, r"# scope: failing")
    t.end()


@test("formatter_progress_bar: failure line uses emoji prefix")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    result = _run({"scope: x": fn}, env={"CI": "1"})
    t.match(result, r"❌ not ok 1")
    t.end()


@test("formatter_progress_bar: passing tests print no per-test line")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn}, env={"CI": "1"})
    t.not_match(result, r"^ok 1")
    t.end()


@test("formatter_progress_bar: all-pass end shows ok emoji")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn}, env={"CI": "1"})
    t.match(result, r"✅")
    t.end()


@test("formatter_progress_bar: skip shows warning emoji")
def _(t):
    def _inner():
        buf = io.StringIO()
        t_fn, _, run = create_test(formatter=fpb, stream=buf)

        @t_fn.skip("scope: skipped")
        def fn(t2):
            t2.ok(True)
            t2.end()

        run()
        return buf.getvalue()[1:]

    result = _with_env({"CI": "1"}, _inner)
    t.match(result, r"⚠️")
    t.end()


@test("formatter_progress_bar: no-stack omits stack trace")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    result = _run({"scope: x": fn}, env={"CI": "1", "TAPIFY_PROGRESS_BAR_STACK": "0"})
    t.not_match(result, r"stack: \|-")
    t.end()


@test("formatter_progress_bar: _get_stream returns devnull when CI=1")
def _(t):
    def _inner():
        stream = fpb._get_stream(total=200)
        t.not_equal(stream, sys.stderr)

    _with_env({"CI": "1"}, _inner)
    t.end()


@test("formatter_progress_bar: _get_stream returns stderr when forced on")
def _(t):
    def _inner():
        stream = fpb._get_stream(total=1)
        t.equal(stream, sys.stderr)

    _with_env({"TAPIFY_PROGRESS_BAR": "1"}, _inner)
    t.end()


@test("formatter_progress_bar: _get_stream force off wins")
def _(t):
    def _inner():
        stream = fpb._get_stream(total=500)
        t.not_equal(stream, sys.stderr)

    _with_env({"TAPIFY_PROGRESS_BAR": "0", "CI": None}, _inner)
    t.end()


@test("formatter_progress_bar: jetbrains adds a space")
def _(t):
    def _inner():
        t.equal(fpb._format_ok(), "# ✅  ok")

    _with_env({"TERMINAL_EMULATOR": "JetBrains-JediTerm"}, _inner)
    t.end()


@test("formatter_progress_bar: create_formatter protocol works")
def _(t):
    formatter = fpb.create_formatter("#ff0000")
    formatter.start(total=1)
    out = formatter.end(count=1, passed=1, failed=0, skipped=0)
    t.ok(out.startswith("\r") and "TAP version 13" in out)
    t.end()


@test("formatter_progress_bar: non-CI bar renders and buffers")
def _(t):
    saved = {k: os.environ.get(k) for k in ("CI", "TAPIFY_PROGRESS_BAR")}
    os.environ.pop("CI", None)
    os.environ["TAPIFY_PROGRESS_BAR"] = "1"
    captured = io.StringIO()
    orig_stderr = sys.stderr
    sys.stderr = captured
    try:
        fmt = fpb.create_formatter("#f9d472")
        fmt.start(total=1)
        fmt.test(test="scope: bar")

        def bad(t2):
            t2.ok(False)
            t2.end()

        fmt.fail(
            at="at file.py:1",
            count=1,
            message="bad thing",
            operator="ok",
            result=False,
            expected=True,
            output="",
            error_stack="stack here",
        )
        fmt.test_end(count=1, total=1)
        out = fmt.end(count=1, passed=0, failed=1, skipped=1)
        ok = all(
            re.search(p, out) for p in (r"# scope: bar", r"bad thing", r"⚠️ skip 1", r"# ❌ fail 1")
        )
        t.ok(ok and captured.getvalue().startswith("\r") and "█" in captured.getvalue())
    finally:
        sys.stderr = orig_stderr
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    t.end()


@test("formatter_progress_bar: color functions")
def _(t):
    identity = fpb._color_fn("#ff0000")
    named = fpb._color_fn("red")
    unknown = fpb._color_fn("chartreuse")
    results = (identity("x"), named("x"), unknown("x"), fpb._devnull().__class__.__name__)
    # not a tty → no colors
    t.equal(results, ("x", "x", "x", "_Devnull"))
    t.end()


@test("formatter_progress_bar: comment is buffered")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=1)
    result = fmt.comment(message="note")
    out = fmt.end(count=1, passed=1, failed=0, skipped=0)
    t.ok(result is None and "# note" in out)
    t.end()


@test("formatter_progress_bar: devnull swallows writes")
def _(t):
    t.equal(fpb._devnull().write("ignored"), None)
    t.end()


@test("formatter_progress_bar: end does not write to stderr directly")
def _(t):
    captured = io.StringIO()
    orig = sys.stderr
    sys.stderr = captured
    try:
        fmt = fpb.create_formatter("#f9d472")
        fmt.start(total=1)
        out = fmt.end(count=1, passed=1, failed=0, skipped=0)
    finally:
        sys.stderr = orig
    # output is returned for the harness to write — never written twice
    t.ok(out.startswith("\r") and captured.getvalue() == "")
    t.end()
