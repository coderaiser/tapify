import io

from tapify import test
from tapify.formatter.harness import Harness, create_harness


class _Mod:
    @staticmethod
    def start(*, total, **_):
        return f"start {total}\n"

    @staticmethod
    def end(**_):
        return "end\n"


@test("harness: routes events to hooks and writes result")
def _(t):
    buf = io.StringIO()
    h = create_harness(_Mod(), buf)
    h.write("start", {"total": 3})
    t.equal(buf.getvalue(), "start 3\n")
    t.end()


@test("harness: missing hooks are no-ops")
def _(t):
    buf = io.StringIO()
    h = Harness(_Mod(), buf)
    h.write("success", {"count": 1, "message": "x"})
    t.equal(buf.getvalue(), "")
    t.end()


@test("harness: unknown event ignored")
def _(t):
    buf = io.StringIO()
    h = Harness(_Mod(), buf)
    h.write("nope", {})
    t.equal(buf.getvalue(), "")
    t.end()


@test("harness: write after end raises")
def _(t):
    buf = io.StringIO()
    h = Harness(_Mod(), buf)
    h.write("end", {})
    raised = False
    try:
        h.write("test", {"test": "x"})
    except RuntimeError:
        raised = True
    t.ok(raised)
    t.end()


@test("harness: pipe changes stream")
def _(t):
    buf1 = io.StringIO()
    buf2 = io.StringIO()
    h = Harness(_Mod(), buf1)
    h.pipe(buf2)
    h.write("start", {"total": 1})
    t.equal(buf1.getvalue(), "")
    t.equal(buf2.getvalue(), "start 1\n")
    t.end()
