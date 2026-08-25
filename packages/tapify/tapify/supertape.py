import asyncio
import io
import os

_tests: list = []
_inited: dict = {"format": "tap"}


def init(options: dict):
    _inited.update(options)


def get_options() -> dict:
    return dict(_inited)


def reset() -> None:
    """Clear registered tests and options (used between spec runs)."""
    _tests.clear()
    _inited.clear()
    _inited.update({"format": "tap"})


def test(message: str, fn=None, **options):
    def _reg(fn):
        from tapify.validator import get_at

        _tests.append(
            {
                "message": message,
                "fn": fn,
                "skip": options.get("skip", False),
                "only": options.get("only", False),
                "extensions": options.get("extensions", {}),
                "at": get_at(),
                "validations": {
                    "check_duplicates": options.get("check_duplicates", True),
                    "check_scopes": options.get("check_scopes", True),
                    "check_assertions_count": options.get("check_assertions_count", True),
                },
                "timeout": options.get("timeout", int(os.environ.get("TAPIFY_TIMEOUT", 3000))),
            }
        )
        return fn

    if fn is not None:
        return _reg(fn)
    return _reg


test.only = lambda msg, fn=None, **o: test(msg, fn, only=True, **o)
test.skip = lambda msg, fn=None, **o: test(msg, fn, skip=True, **o)


def stub(overrides: dict):
    """Decorator. The decorated fn receives a proxy of `t` whose operators
    named in `overrides` are replaced. Each override receives the original
    bound operator as its first argument.

    Usage:

        @test.stub({'ok': lambda ok: ok(True)})
        def _(t):
            t.ok('ignored')
            t.end()
    """
    from functools import wraps

    def decorator(fn):
        @wraps(fn)
        def proxy(t, *args, **kwargs):
            class _Stub:
                def __getattr__(self, name):
                    if name in overrides:
                        base = getattr(t, name)
                        return lambda *a, **kw: overrides[name](base, *a, **kw)
                    return getattr(t, name)

            return fn(_Stub(), *args, **kwargs)

        proxy.__tapify_stub__ = overrides
        return proxy

    return decorator


def _create_extend(base_test):
    def extend(extensions: dict):
        def extended(msg, fn=None, **o):
            return base_test(msg, fn, extensions=extensions, **o)

        extended.only = lambda msg, fn=None, **o: base_test(
            msg, fn, only=True, extensions=extensions, **o
        )
        extended.skip = lambda msg, fn=None, **o: base_test(
            msg, fn, skip=True, extensions=extensions, **o
        )
        extended.extend = _create_extend(extended)
        return extended

    return extend


test.extend = _create_extend(test)


def create_test(*, format="tap", formatter=None, stream=None, **options):
    """
    Returns (test_fn, stream, run).
    Isolated: does not touch global _tests or _inited.
    Used by formatter spec tests.
    stream is io.StringIO; run() is synchronous (calls asyncio.run).
    """
    from tapify.formatter import create_formatter
    from tapify.run_tests import run_tests

    local_tests = []
    buf = stream or io.StringIO()
    fmt_module = formatter or format
    harness, facade = create_formatter(fmt_module)
    harness.pipe(buf)

    def local_test(message, fn=None, **opts):
        def _reg(fn):
            from tapify.validator import get_at

            local_tests.append(
                {
                    "message": message,
                    "fn": fn,
                    "skip": opts.get("skip", False),
                    "only": opts.get("only", False),
                    "extensions": opts.get("extensions", {}),
                    "at": get_at(),
                    "validations": opts.get(
                        "validations",
                        {
                            "check_duplicates": True,
                            "check_scopes": True,
                            "check_assertions_count": True,
                        },
                    ),
                    "timeout": opts.get("timeout", int(os.environ.get("TAPIFY_TIMEOUT", 3000))),
                }
            )
            return fn

        if fn is not None:
            return _reg(fn)
        return _reg

    local_test.skip = lambda msg, fn=None, **o: local_test(msg, fn, skip=True, **o)
    local_test.only = lambda msg, fn=None, **o: local_test(msg, fn, only=True, **o)

    def _extend(base):
        def extend(extensions: dict):
            def extended(msg, fn=None, **o):
                return base(msg, fn, extensions=extensions, **o)

            extended.skip = lambda msg, fn=None, **o: base(
                msg, fn, skip=True, extensions=extensions, **o
            )
            extended.only = lambda msg, fn=None, **o: base(
                msg, fn, only=True, extensions=extensions, **o
            )
            extended.extend = _extend(extended)
            return extended

        return extend

    local_test.extend = _extend(local_test)

    def run():
        asyncio.run(run_tests(local_tests, formatter=facade))

    return local_test, buf, run


def create_stream():
    """Returns the harness for the current format (for CLI to pipe to stdout)."""
    from tapify.formatter import create_formatter

    harness, _ = create_formatter(_inited.get("format", "tap"))
    return harness


def run():
    """Run all globally registered tests. Returns the result dict."""
    import sys

    from tapify.formatter import create_formatter
    from tapify.run_tests import run_tests

    harness, facade = create_formatter(_inited.get("format", "tap"))
    quiet = _inited.get("quiet", False)
    stream = io.StringIO() if quiet else (_inited.get("stream") or sys.stdout)
    harness.pipe(stream)
    return asyncio.run(run_tests(_tests, formatter=facade))
