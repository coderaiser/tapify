from tapify import test
from tapify.format import add_spaces, format_output


@test("format: add_spaces prepends six spaces")
def _(t):
    t.equal(add_spaces("ok"), "      ok")
    t.end()


@test("format: format_output indents every line")
def _(t):
    t.equal(format_output("a\nb"), "      a\n      b")
    t.end()


@test("format: parse_at returns single-line stack unchanged")
def _(t):
    from tapify.format import parse_at

    t.equal(parse_at("file.py:1"), "file.py:1")
    t.end()


@test("format: parse_at picks user frame for long error stacks")
def _(t):
    from tapify.format import parse_at

    stack = "\n".join(
        ["Error: boom", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "user.py:42"]
    )
    t.equal(parse_at(stack), "c")
    t.end()


@test("format: parse_at picks first user frame in python stack")
def _(t):
    from tapify.format import parse_at

    stack = "\n".join(
        [
            '  File "/usr/lib/python3.12/threading.py", line 1030, in _bootstrap',
            "    self._bootstrap_inner()",
            '  File "/usr/lib/python3.12/concurrent/futures/thread.py", line 92, in run',
            "    work_item.run()",
            '  File "/tmp/st/demo.spec.py", line 12, in _',
            "    t.equal(1, 2)",
        ]
    )
    t.equal(parse_at(stack), "at /tmp/st/demo.spec.py:12")
    t.end()


@test("format: parse_at skips frozen frames")
def _(t):
    from tapify.format import parse_at

    stack = "\n".join(
        [
            '  File "<frozen importlib._bootstrap>", line 488, in _gcd_import',
            '  File "/tmp/st/user.spec.py", line 7, in _',
        ]
    )
    t.equal(parse_at(stack), "at /tmp/st/user.spec.py:7")
    t.end()


@test("format: parse_at raises for short multi-line stacks")
def _(t):
    from tapify.format import parse_at

    raised = False
    try:
        parse_at("a\nb\nc")
    except RuntimeError:
        raised = True
    t.ok(raised)
    t.end()
