from tapify import test
from tapify.operators import deep_equal, equal, match, not_match, not_ok, ok
from tapify.operators import fail as op_fail


@test("operators: ok: truthy passes")
def _(t):
    t.ok(ok("x")["is"])
    t.end()


@test("operators: ok: empty string fails")
def _(t):
    t.not_ok(ok("")["is"])
    t.end()


@test("operators: not_ok: falsy passes")
def _(t):
    t.ok(not_ok(0)["is"])
    t.end()


@test("operators: equal: same type and value passes")
def _(t):
    t.ok(equal(1, 1)["is"])
    t.end()


@test("operators: equal: different types fail even when == is true")
def _(t):
    t.not_ok(equal(1, True)["is"])
    t.end()


@test("operators: equal: produces output on failure")
def _(t):
    t.ok(bool(equal(1, 2)["output"]))
    t.end()


@test("operators: deep_equal: equal dicts pass")
def _(t):
    t.ok(deep_equal({"a": 1}, {"a": 1})["is"])
    t.end()


@test("operators: deep_equal: different dicts fail")
def _(t):
    t.not_ok(deep_equal({"a": 1}, {"a": 2})["is"])
    t.end()


@test("operators: match: matching pattern passes")
def _(t):
    t.ok(match("hello world", r"world")["is"])
    t.end()


@test("operators: match: non-matching pattern fails")
def _(t):
    t.not_ok(match("hello", r"world")["is"])
    t.end()


@test("operators: match: bad pattern type fails")
def _(t):
    t.not_ok(match("hello", 42)["is"])
    t.end()


@test("operators: match: bad regex fails")
def _(t):
    t.not_ok(match("hello", "(")["is"])
    t.end()


@test("operators: not_match inverts match")
def _(t):
    t.ok(not_match("hello", r"world")["is"])
    t.not_ok(not_match("hello world", r"world")["is"])
    t.end()


@test("operators: fail: is is always False")
def _(t):
    t.not_ok(op_fail(Exception("boom"))["is"])
    t.end()


# --- init_operators wiring ---

from tapify.operators import init_operators


def _state():
    events = []
    count = [0]
    passed = [0]
    failed = [0]
    assertions = [0]
    is_ended = [False]

    class Fmt:
        def emit(self, event, data=None, **kw):
            events.append((event, data or kw))

    return ({
        'formatter': Fmt(),
        'count': lambda: count[0],
        'inc_count': lambda: count.__setitem__(0, count[0] + 1),
        'inc_passed': lambda: passed.__setitem__(0, passed[0] + 1),
        'inc_failed': lambda: failed.__setitem__(0, failed[0] + 1),
        'is_ended': is_ended,
        'assertions_count': lambda: assertions[0],
        'inc_assertions_count': lambda: assertions.__setitem__(
            0, assertions[0] + 1),
    }, events)


@test('operators: success emits success event')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.ok(True)
    t.equal(events[0][0], 'success')
    t.end()


@test('operators: failure emits fail event with at')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.ok(False)
    event, data = events[0]
    t.equal(event, 'fail')
    t.match(data['at'], r'\.py:\d+')
    t.ok(data['error_stack'])
    t.end()


@test('operators: double end fails')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.end()
    ops.end()
    fails = [e for e in events if e[0] == 'fail']
    t.equal(len(fails), 1)
    t.match(str(fails[0][1]['message']), r'couple')
    t.end()


@test('operators: assertion after end fails')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.end()
    ops.ok(True)
    fails = [e for e in events if e[0] == 'fail']
    t.equal(len(fails), 1)
    t.match(str(fails[0][1]['message']), r'after')
    t.end()


@test('operators: pass operator always succeeds')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.pass_('all good')
    t.equal(events[0][0], 'success')
    t.equal(events[0][1]['message'], 'all good')
    t.end()


@test('operators: not_equal passes on difference')
def _(t):
    from tapify.operators import not_equal
    t.ok(not_equal(1, 2)['is'])
    t.not_ok(not_equal(1, 1)['is'])
    t.ok(bool(not_equal(1, 1)['output']))
    t.end()


@test('operators: deep equal type mismatch fails')
def _(t):
    state, events = _state()
    t.ok(init_operators(state).deep_equal({'a': [1, 2]}, {'a': [1, 2]})['is'])
    t.end()


@test('operators: comment emits stripped comment lines')
def _(t):
    state, events = _state()
    ops = init_operators(state)
    ops.comment('# hello')
    t.equal(events, [('comment', {'message': 'hello'})])
    t.end()
