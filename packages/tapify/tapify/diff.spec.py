from tapify import test
from tapify.diff import diff


@test("diff: equal values return empty string")
def _(t):
    t.equal(diff(1, 1), "")
    t.end()


@test("diff: unequal values return diff block")
def _(t):
    result = diff(1, 2)
    t.match(result, r"diff: \|-")
    t.end()


@test("diff: minus line contains expected value")
def _(t):
    result = diff("hello", "world")
    t.match(result, r"-.*hello")
    t.end()


@test("diff: plus line contains actual value")
def _(t):
    result = diff("hello", "world")
    t.match(result, r"\+.*world")
    t.end()


@test("diff: colorize adds ansi codes on tty")
def _(t):
    import io
    import sys

    from tapify.diff import _colorize

    fake = io.StringIO()
    fake.isatty = lambda: True
    orig = sys.stdout
    sys.stdout = fake
    try:
        result = (_colorize("- x"), _colorize("+ y"), _colorize("  z"))
    finally:
        sys.stdout = orig
    t.equal(result, ("\x1b[32m- x\x1b[39m", "\x1b[31m+ y\x1b[39m", "  z"))
    t.end()


@test("diff: pad_marker adds space after -/+ but not context")
def _(t):
    from tapify.diff import _pad_marker

    t.equal(
        (_pad_marker("-1"), _pad_marker("+2"), _pad_marker(" 3"), _pad_marker("--- x")),
        ("- 1", "+ 2", " 3", "--- x"),
    )
    t.end()


@test("diff: header-only chunks return empty string")
def _(t):
    import tapify.diff as d

    orig = d.difflib.unified_diff
    d.difflib.unified_diff = lambda *a, **kw: iter(["--- ", "+++ ", "@@ -1 +1 @@"])
    try:
        t.equal(d.diff(1, 2), "")
    finally:
        d.difflib.unified_diff = orig
    t.end()
