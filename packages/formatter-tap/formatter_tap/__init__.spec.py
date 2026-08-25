import io

from tapify import test
from tapify.supertape import create_test

import formatter_tap


def _run(fn_map) -> str:
    """fn_map: {message: fn}. Returns full formatter output."""
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_tap, stream=buf)
    for msg, fn in fn_map.items():
        t_fn(msg)(fn)
    run()
    return buf.getvalue()


@test("formatter_tap: success line format")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn})
    t.match(result, r"ok 1 should be truthy")
    t.end()


@test("formatter_tap: fail line format")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    result = _run({"scope: x": fn})
    t.match(result, r"not ok 1 should be truthy")
    t.end()


@test("formatter_tap: end section has plan line")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn})
    t.match(result, r"1\.\.1")
    t.end()


@test("formatter_tap: end section has ok when all pass")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = _run({"scope: x": fn})
    t.match(result, r"# ok")
    t.end()


@test("formatter_tap: skip counted in end")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_tap, stream=buf)

    @t_fn.skip("scope: skipped")
    def fn(t2):
        t2.ok(True)
        t2.end()

    run()
    t.match(buf.getvalue(), r"# skip 1")
    t.not_match(buf.getvalue(), r"# fail")
    t.end()


@test("formatter_tap: comment hook writes comment line")
def _(t):
    result = formatter_tap.comment(message="hello")
    t.equal(result, "# hello\n")
    t.end()


@test("formatter_tap: test_end returns None")
def _(t):
    t.equal(formatter_tap.test_end(count=1), None)
    t.end()
