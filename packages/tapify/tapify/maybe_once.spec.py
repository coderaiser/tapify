from tapify import test
from tapify.maybe_once import disable_once, enable_once, maybe_once


@test("maybe_once: first call executes fn")
def _(t):
    calls = []
    f = maybe_once(lambda: calls.append(1))
    f()
    t.equal(calls, [1])
    t.end()


@test("maybe_once: second call is no-op")
def _(t):
    calls = []
    f = maybe_once(lambda: calls.append(1))
    f()
    f()
    t.equal(calls, [1])
    t.end()


@test("maybe_once: disable_once allows every call")
def _(t):
    calls = []
    f = maybe_once(lambda: calls.append(1))
    disable_once()
    f()
    f()
    enable_once()
    t.equal(calls, [1, 1])
    t.end()
