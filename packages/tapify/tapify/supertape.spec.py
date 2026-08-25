import io

from tapify import supertape, test
from tapify.supertape import create_stream, create_test, init, stub


@test("supertape: init stores options")
def _(t):
    init({"format": "fail"})
    t.equal(supertape.get_options()["format"], "fail")
    init({"format": "tap"})
    t.end()


@test("supertape: create_test isolates tests")
def _(t):
    t_fn, buf, run = create_test(format="tap", stream=io.StringIO())
    t.equal((callable(t_fn), callable(run)), (True, True))
    t.end()


@test("supertape: create_test runs and reports")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(format="tap", stream=buf)

    @t_fn("scope: passing")
    def fn(t2):
        t2.ok(True)
        t2.end()

    run()
    t.match(buf.getvalue(), r"ok 1")
    t.end()


@test("supertape: skip decorator marks skipped")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(format="tap", stream=buf)

    @t_fn.skip("scope: skipped")
    def fn(t2):
        t2.ok(True)
        t2.end()

    run()
    t.match(buf.getvalue(), r"# skip 1")
    t.end()


@test("supertape: only decorator filters")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(format="tap", stream=buf)

    @t_fn("scope: one")
    def a(t2):
        t2.ok(True)
        t2.end()

    @t_fn.only("scope: two")
    def b(t2):
        t2.ok(True)
        t2.end()

    run()
    out = buf.getvalue()
    t.match(out, r"# skip 1")
    t.end()


@test("supertape: extend adds operators")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(format="tap", stream=buf)
    is_even = t_fn.extend(
        {
            "even": lambda ops: lambda x: ops["ok"](x % 2 == 0),
        }
    )

    @is_even("math: even number")
    def fn(t2):
        t2.even(4)
        t2.end()

    run()
    t.match(buf.getvalue(), r"ok 1")
    t.end()


@test("supertape: stub proxies operators")
def _(t):
    calls = []

    @stub({"ok": lambda ok, value: calls.append(value)})
    def fn(t):
        t.ok("x")
        return t

    fake_t = type("T", (), {"ok": staticmethod(lambda v: None)})()
    result = fn(fake_t)
    t.equal(
        (calls, result is not None, fn.__tapify_stub__["ok"].__name__),
        (["x"], True, "<lambda>"),
    )
    t.end()


@test("supertape: stub returns wrapped function result")
def _(t):
    @stub({"ok": lambda ok, value: None})
    def fn(t):
        t.ok("x")
        return "done"

    fake_t = type("T", (), {"ok": staticmethod(lambda v: None)})()
    t.equal(fn(fake_t), "done")
    t.end()


@test("supertape: create_stream returns harness for current format")
def _(t):
    init({"format": "tap"})
    harness = create_stream()
    t.ok(hasattr(harness, "write"))
    t.end()


@test("supertape: test.skip/only register globally")
def _(t):
    from tapify import supertape

    def fn(t2):
        t2.ok(True)
        t2.end()

    supertape.test.skip("scope: skipped-global")(fn)
    supertape.test.only("scope: only-global")(fn)
    messages = [entry["message"] for entry in supertape._tests]
    only_entry = [e for e in supertape._tests if e["message"] == "scope: only-global"][0]
    t.equal(
        ("scope: skipped-global" in messages, only_entry["only"]),
        (True, True),
    )
    supertape.reset()
    t.end()


@test("supertape: reset clears registered tests")
def _(t):
    from tapify import supertape

    def fn(t2):
        t2.ok(True)
        t2.end()

    supertape.test.skip("scope: skipped-global")(fn)
    supertape.reset()
    t.equal(supertape._tests, [])
    t.end()


@test("supertape: run executes registered tests into stream")
def _(t):
    from tapify import supertape

    buf = io.StringIO()
    supertape.reset()
    supertape.init({"format": "tap", "stream": buf})

    @test("scope: global-pass")
    def fn(t2):
        t2.ok(True)
        t2.end()

    result = supertape.run()
    t.equal((result["failed"], "ok 1" in buf.getvalue()), (0, True))
    supertape.reset()
    t.end()


@test("supertape: nested extend chains")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(format="tap", stream=buf)
    base = t_fn.extend({"pos": lambda ops: lambda x: ops["ok"](x > 0)})
    nested = base.extend({"small": lambda ops: lambda x: ops["ok"](x < 10)})

    @nested("math: pos small")
    def fn(t2):
        t2.pos(5)
        t2.small(5)
        t2.end()

    run()
    t.match(buf.getvalue(), r"ok 1")
    t.end()
