import os
from threading import Timer

from tapify.maybe_once import maybe_once


def create_emitter(*, loop_fn, **kwargs):
    listeners: dict[str, list] = {}

    def on(event, fn):
        listeners.setdefault(event, []).append(fn)

    def emit(event, *args, **kw):
        for fn in list(listeners.get(event, [])):
            fn(*args, **kw)

    tests: list = []

    def _on_test(msg, fn, opts):
        tests.append({"message": msg, "fn": fn, **opts})

    def _on_loop():
        loop_fn(emit=emit, tests=tests)

    def _on_run():
        _start_run(emit, tests, **kwargs)

    on("test", _on_test)
    on("loop", _on_loop)
    on("run", _on_run)

    class _Emitter:
        def on(self, e, f):
            return on(e, f)

        def emit(self, e, *a, **kw):
            return emit(e, *a, **kw)

    return _Emitter()


@maybe_once
def _default_loop(*, emit, tests):
    previous = [0]
    ms = int(os.environ.get("TAPIFY_LOAD_LOOP_TIMEOUT", 5)) / 1000

    def check():
        if previous[0] == len(tests):
            emit("run")
            return
        previous[0] = len(tests)
        Timer(ms, check).start()

    check()


def _start_run(emit, tests, **_kwargs) -> None:
    import asyncio

    from tapify.run_tests import run_tests

    async def _run():
        return await run_tests(tests, formatter=_NullFormatter())

    asyncio.run(_run())
    emit("done")


class _NullFormatter:
    def emit(self, event, data=None, **kwargs):
        pass
