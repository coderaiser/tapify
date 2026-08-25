import asyncio
import os
import queue
import sys
import threading

from tapify import exit_codes
from tapify.formatter import create_formatter
from tapify.run_tests import run_tests


class _QueueFormatter:
    def __init__(self, q: queue.Queue):
        self._q = q

    def emit(self, event: str, data: dict | None = None, **kwargs):
        self._q.put((event, data or kwargs))


def run_with_worker(tests, *, format_name, stream=None, is_stop=None) -> int:
    stream = stream or sys.stdout
    q: queue.Queue = queue.Queue()
    result_box = [None]

    def _worker():
        try:

            async def _run():
                result_box[0] = await run_tests(
                    tests, formatter=_QueueFormatter(q), is_stop=is_stop
                )

            asyncio.run(_run())
        finally:
            q.put(("__done__", {}))

    # Capture the raw write before override_stdout replaces it, so formatter
    # output bypasses the console-log redirection.
    thread = threading.Thread(target=_worker, daemon=True)
    raw_write = stream.write

    class _RawStream:
        @staticmethod
        def write(text):
            raw_write(text)

        @staticmethod
        def flush():
            pass

    harness, _ = create_formatter(format_name)
    harness.pipe(_RawStream())

    # Install the console-log redirect before the worker starts, so print()
    # inside test functions is captured from the very first event.
    restore = _override_stdout(q)
    thread.start()

    try:
        while True:
            event, data = q.get()
            if event == "__done__":
                break
            if event == "console:log":
                raw_write(data["message"])
                continue
            harness.write(event, data)
    finally:
        restore()

    thread.join()
    return _exit_code(result_box[0] or {}, is_stop)


def run_without_worker(tests, *, format_name, stream=None, is_stop=None) -> int:
    stream = stream or sys.stdout

    async def _run():
        harness, formatter = create_formatter(format_name)
        harness.pipe(stream)
        return await run_tests(tests, formatter=formatter, is_stop=is_stop)

    result = asyncio.run(_run())
    return _exit_code(result, is_stop)


def _override_stdout(q):
    from tapify.worker.create_console_log import override_stdout

    return override_stdout(q)


def _exit_code(result: dict, is_stop) -> int:
    if is_stop and is_stop():
        return exit_codes.WAS_STOP
    if result.get("failed"):
        return exit_codes.FAIL
    check_skipped = os.environ.get("TAPIFY_CHECK_SKIPPED", "0") != "0"
    if check_skipped and result.get("skipped"):
        return exit_codes.SKIPPED
    return exit_codes.OK
