import asyncio

from tapify import test
from tapify.run_tests import run_tests


def _collect(tests):
    events = []

    class Fmt:
        def emit(self, event, data=None, **kw):
            events.append((event, data or kw))

    result = asyncio.run(run_tests(tests, formatter=Fmt()))
    return result, events


@test("run_tests: counts passes and failures")
def _(t):
    def good(t2):
        t2.ok(True)
        t2.end()

    def bad(t2):
        t2.ok(False)
        t2.end()

    tests = [
        {
            "message": "scope: good",
            "fn": good,
            "skip": False,
            "only": False,
            "extensions": {},
            "timeout": 3000,
            "validations": {
                "check_duplicates": False,
                "check_scopes": False,
                "check_assertions_count": False,
            },
        },
        {
            "message": "scope: bad",
            "fn": bad,
            "skip": False,
            "only": False,
            "extensions": {},
            "timeout": 3000,
            "validations": {
                "check_duplicates": False,
                "check_scopes": False,
                "check_assertions_count": False,
            },
        },
    ]
    result, events = _collect(tests)
    t.equal(result["failed"], 1)
    t.equal(result["passed"], 1)
    t.end()


@test("run_tests: skips are counted not run")
def _(t):
    ran = []

    def fn(t2):
        ran.append(1)
        t2.end()

    tests = [
        {
            "message": "scope: s",
            "fn": fn,
            "skip": True,
            "only": False,
            "extensions": {},
            "timeout": 3000,
        }
    ]
    result, _ = _collect(tests)
    t.equal(result["skipped"], 1)
    t.equal(ran, [])
    t.end()


@test("run_tests: only filters others into skipped")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    tests = [
        {
            "message": "scope: a",
            "fn": fn,
            "only": True,
            "skip": False,
            "extensions": {},
            "timeout": 3000,
        },
        {
            "message": "scope: b",
            "fn": fn,
            "only": False,
            "skip": False,
            "extensions": {},
            "timeout": 3000,
        },
    ]
    result, _ = _collect(tests)
    t.equal(result["passed"], 1)
    t.equal(result["skipped"], 1)
    t.end()


@test("run_tests: async test functions run")
def _(t):
    async def fn(t2):
        t2.ok(True)
        t2.end()

    tests = [
        {
            "message": "scope: async",
            "fn": fn,
            "skip": False,
            "only": False,
            "extensions": {},
            "timeout": 3000,
        }
    ]
    result, _ = _collect(tests)
    t.equal(result["passed"], 1)
    t.end()


@test("run_tests: exception in test fails it")
def _(t):
    def fn(t2):
        raise RuntimeError("boom")

    tests = [
        {
            "message": "scope: boom",
            "fn": fn,
            "skip": False,
            "only": False,
            "extensions": {},
            "timeout": 3000,
        }
    ]
    result, _ = _collect(tests)
    t.equal(result["failed"], 1)
    t.end()


@test("run_tests: timeout fails the test")
def _(t):
    import time

    def fn(t2):
        time.sleep(0.3)
        t2.ok(True)
        t2.end()

    tests = [
        {
            "message": "scope: slow",
            "fn": fn,
            "skip": False,
            "only": False,
            "extensions": {},
            "timeout": 50,
        }
    ]
    result, _ = _collect(tests)
    t.equal(result["failed"], 1)
    t.end()


@test('run_tests: is_stop aborts remaining tests')
def _(t):
    ran = []

    def fn(t2):
        ran.append(1)
        t2.ok(True)
        t2.end()

    tests = [
        {'message': 'scope: a', 'fn': fn, 'skip': False, 'only': False,
         'extensions': {}, 'timeout': 3000},
        {'message': 'scope: b', 'fn': fn, 'skip': False, 'only': False,
         'extensions': {}, 'timeout': 3000},
    ]
    import asyncio

    class Fmt:
        def emit(self, event, data=None, **kw):
            pass

    stops = [0]

    def is_stop():
        stops[0] += 1
        return True

    result = asyncio.run(run_tests(tests, formatter=Fmt(), is_stop=is_stop))
    t.equal(ran, [])
    t.equal(result['passed'], 0)
    t.end()


@test('run_tests: duplicate validation fails the test')
def _(t):
    from tapify.validator import reset_processed, set_validations

    def fn(t2):
        t2.ok(True)
        t2.end()

    set_validations({'check_duplicates': True, 'check_scopes': False,
                     'check_assertions_count': False})
    reset_processed()
    tests = [
        {'message': 'scope: dup', 'fn': fn, 'skip': False, 'only': False,
         'extensions': {}, 'timeout': 3000,
         'validations': {'check_duplicates': True, 'check_scopes': False,
                         'check_assertions_count': False}},
        {'message': 'scope: dup', 'fn': fn, 'skip': False, 'only': False,
         'extensions': {}, 'timeout': 3000,
         'validations': {'check_duplicates': True, 'check_scopes': False,
                         'check_assertions_count': False}},
    ]
    import asyncio

    class Fmt:
        def emit(self, event, data=None, **kw):
            pass

    result = asyncio.run(run_tests(tests, formatter=Fmt()))
    reset_processed()
    set_validations({'check_duplicates': False})
    t.equal(result['failed'], 1)
    t.end()
