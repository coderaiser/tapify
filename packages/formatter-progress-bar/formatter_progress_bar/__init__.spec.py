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

    _with_env({"CI": "1", "TAPIFY_PROGRESS_BAR": None}, _inner)
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


@test("formatter_progress_bar: payload looks like supertape cliProgress format")
def _(t):
    rendered = fpb._render_bar(10, 4, "#f9d472", "scope: x")
    t.match(rendered, r"40% | 👌 | 4/10 | scope: x")
    t.end()


@test("formatter_progress_bar: payload shows failed count after failure")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=1)
    fmt.test(test="scope: bad")
    fmt.fail(at="", count=1, message="m", operator="ok", result=False, expected=True)
    fmt.test_end(count=1, total=1)
    rendered = fpb._last_render()[0]
    t.match(rendered, r" \| 1 \| 1/1 \| scope: bad")
    t.end()


@test("formatter_progress_bar: no 👌 after failure")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=1)
    fmt.test(test="scope: bad")
    fmt.fail(at="", count=1, message="m", operator="ok", result=False, expected=True)
    fmt.test_end(count=1, total=1)
    rendered = fpb._last_render()[0]
    t.not_match(rendered, r"👌")
    t.end()


@test("formatter_progress_bar: failed count resets on next test")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=2)
    fmt.test(test="a")
    fmt.fail(at="", count=1, message="m", operator="ok", result=False, expected=True)
    fmt.test_end(count=1, total=2)
    fmt.test(test="b")
    fmt.test_end(count=2, total=2)
    first = fpb._last_render()[0]
    t.not_match(first, r"👌")
    t.end()


@test("formatter_progress_bar: 👌 returns on passing test")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=2)
    fmt.test(test="a")
    fmt.fail(at="", count=1, message="m", operator="ok", result=False, expected=True)
    fmt.test_end(count=1, total=2)
    fmt.test(test="b")
    fmt.test_end(count=2, total=2)
    second = fpb._last_render()[1]
    t.match(second, r"\| 👌 \|")
    t.end()


@test("formatter_progress_bar: red count is colored on a tty")
def _(t):
    class _Tty(io.StringIO):
        def isatty(self):
            return True

    orig = sys.stderr
    sys.stderr = _Tty()
    try:
        colored = fpb.bar_color_red(3)
    finally:
        sys.stderr = orig
    t.equal(colored, "\x1b[31m3\x1b[39m")
    t.end()


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


@test("formatter_progress_bar: _visible_len counts wide chars as 2 columns")
def _(t):
    t.equal(fpb._visible_len("a👌b"), 4)
    t.end()


@test("formatter_progress_bar: rendered bar fits in one terminal line")
def _(t):
    import shutil

    columns = shutil.get_terminal_size().columns
    rendered = fpb._render_bar(10, 4, "#f9d472", "scope: x")
    visible = fpb._visible_len(_ANSI_RE.sub("", rendered))
    t.ok(visible < columns)
    t.end()


@test("formatter_progress_bar: consecutive renders stay on one line")
def _(t):
    fmt = fpb.create_formatter()
    fmt.start(total=10)
    writes = []

    class _Stream:
        def write(self, s):
            writes.append(s)

        def isatty(self):
            return False

        def flush(self):
            return None

    import os as _os

    saved = _os.environ.get("TAPIFY_PROGRESS_BAR")
    _os.environ["TAPIFY_PROGRESS_BAR"] = "1"
    orig_stderr = sys.stderr
    sys.stderr = _Stream()
    try:
        for i in range(1, 11):
            fmt.test(test=f"scope: test number {i}")
            fmt.test_end(count=i, total=10)
    finally:
        sys.stderr = orig_stderr
        if saved is None:
            _os.environ.pop("TAPIFY_PROGRESS_BAR", None)
        else:
            _os.environ["TAPIFY_PROGRESS_BAR"] = saved
    # every update must be a carriage-return redraw, never a wrapped newline
    t.ok(all("\n" not in chunk for chunk in writes))
    t.end()
