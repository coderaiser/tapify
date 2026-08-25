import sys

SPLITTER = ">[tapify-splitter]<"
CONSOLE_LOG = "console:log"


def override_stdout(q):
    original = sys.stdout.write

    def _write(text):
        q.put((CONSOLE_LOG, {"message": text}))

    sys.stdout.write = _write
    return lambda: setattr(sys.stdout, "write", original)
