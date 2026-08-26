import io
import re

from tapify import test
from tapify.supertape import create_test

import formatter_fail


def _run(fn_map) -> str:
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_fail, stream=buf)
    for msg, fn in fn_map.items():
        t_fn(msg)(fn)
    run()
    return buf.getvalue()


@test("formatter_fail: passing tests produce no output before fail block")
def _(t):
    def good(t2):
        t2.ok(True)
        t2.end()

    def bad(t2):
        t2.ok(False)
        t2.end()

    out = _run({"scope: good": good, "scope: bad": bad})
    lines = out.splitlines()
    ok = lines[0] == "TAP version 13" and lines[1] == "# scope: bad"
    t.ok(ok and bool(re.search(r"not ok 2 should be truthy", out)))
    t.end()


@test("formatter_fail: success and test_end produce nothing")
def _(t):
    results = (formatter_fail.success(count=1, message="x"), formatter_fail.test_end(count=1))
    t.equal(results, (None, None))
    t.end()


@test("formatter_fail: comment is forwarded to tap formatter")
def _(t):
    def fn(t2):
        t2.comment("hello")
        t2.ok(True)
        t2.end()

    out = _run({"scope: c": fn})
    t.match(out, r"# hello")
    t.end()
