from tapify import test
from tapify.emitter import _default_loop, create_emitter
from tapify.maybe_once import disable_once, enable_once


@test("emitter: on/emit dispatch to listeners")
def _(t):
    em = create_emitter(loop_fn=lambda **kw: None)
    got = []
    em.on("hello", lambda *a: got.append(a))
    em.emit("hello", 1, 2)
    t.equal(got, [(1, 2)])
    t.end()


@test("emitter: loop receives emit and tests")
def _(t):
    seen = {}

    def loop_fn(*, emit, tests):
        seen["emit"] = emit
        seen["tests"] = tests

    em = create_emitter(loop_fn=loop_fn)
    em.emit("loop")
    t.ok("emit" in seen)
    t.ok("tests" in seen)
    t.end()


@test("emitter: test event appends to tests")
def _(t):
    em = create_emitter(loop_fn=lambda **kw: None)

    def fn(t):
        pass

    em.emit("test", "msg", fn, {"skip": True})
    em.emit("loop")
    # loop_fn captured above would have been called with the same list;
    # use internal check via a fresh emitter
    seen = {}

    def loop_fn(*, emit, tests):
        seen["tests"] = tests

    em2 = create_emitter(loop_fn=loop_fn)
    em2.emit("test", "msg", fn, {"skip": True})
    em2.emit("loop")
    t.equal(seen["tests"][0]["message"], "msg")
    t.ok(seen["tests"][0]["skip"])
    t.end()


@test("emitter: default loop fires run when stable")
def _(t):
    disable_once()

    def loop_fn(*, emit, tests):
        pass

    em = create_emitter(loop_fn=loop_fn)
    ran = []
    em.on("run", lambda: ran.append(1))
    enable_once()
    # call the default loop directly through the emitter wiring
    from tapify.emitter import _start_run  # noqa: F401

    disable_once()
    _default_loop(emit=em.emit, tests=[])
    enable_once()
    t.equal(ran, [1])
    t.end()


@test('emitter: start_run executes tests and emits done')
def _(t):
    from tapify.emitter import create_emitter
    done = []

    def loop_fn(*, emit, tests):
        pass

    em = create_emitter(loop_fn=loop_fn)
    em.on('done', lambda: done.append(1))

    def fn(t2):
        t2.ok(True)
        t2.end()

    # register through the emitter so the shared list is populated
    seen = {}

    def capture(*, emit, tests):
        seen['tests'] = tests
        emit('run')

    em2 = create_emitter(loop_fn=capture)
    em2.on('done', lambda: done.append(1))
    em2.emit('test', 'scope: x', fn, {})
    em2.emit('loop')
    t.equal(done, [1])
    t.equal(seen['tests'][0]['message'], 'scope: x')
    t.end()
