import io

from tapify import test
from tapify.supertape import create_test

import formatter_short


def _run(fn_map) -> str:
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_short, stream=buf)
    for msg, fn in fn_map.items():
        t_fn(msg)(fn)
    run()
    return buf.getvalue()


@test("formatter_short: fail omits stack block")
def _(t):
    def bad(t2):
        t2.ok(False)
        t2.end()

    out = _run({"scope: bad": bad})
    t.match(out, r"not ok 1 should be truthy")
    t.not_match(out, r"stack: \|-")
    t.end()


@test("formatter_short: passes look like tap")
def _(t):
    def good(t2):
        t2.ok(True)
        t2.end()

    out = _run({"scope: good": good})
    t.match(out, r"ok 1 should be truthy")
    t.end()
