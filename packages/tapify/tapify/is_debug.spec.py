import sys

from tapify import test
from tapify.is_debug import is_debug


@test("is_debug: false for regular argv")
def _(t):
    orig = sys.orig_argv
    sys.orig_argv = [_orig for _orig in ["python", "-m", "tapify"]]
    result = is_debug()
    sys.orig_argv = orig
    t.not_ok(result)
    t.end()


@test("is_debug: true when inspect in argv")
def _(t):
    orig = sys.orig_argv
    sys.orig_argv = ["python", "-m", "tapify", "--inspect"]
    result = is_debug()
    sys.orig_argv = orig
    t.ok(result)
    t.end()


@test("is_debug: true when debug in argv")
def _(t):
    orig = sys.orig_argv
    sys.orig_argv = ["python", "debug.py"]
    result = is_debug()
    sys.orig_argv = orig
    t.ok(result)
    t.end()
