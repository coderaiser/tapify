import queue
import sys

from tapify import test
from tapify.worker.create_console_log import CONSOLE_LOG, SPLITTER, override_stdout


@test("create_console_log: routes writes to queue")
def _(t):
    q = queue.Queue()
    restore = override_stdout(q)
    sys.stdout.write("hello")
    restore()
    event, data = q.get_nowait()
    t.equal(event, "console:log")
    t.equal(data["message"], "hello")
    t.equal(event, CONSOLE_LOG)
    t.end()


@test("create_console_log: restore puts write back")
def _(t):
    q = queue.Queue()
    original = sys.stdout.write
    restore = override_stdout(q)
    restore()
    t.equal(sys.stdout.write, original)
    t.ok(len(SPLITTER) > 0)
    t.end()
