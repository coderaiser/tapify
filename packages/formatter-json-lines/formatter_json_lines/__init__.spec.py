import io
import json

from tapify import test
from tapify.supertape import create_test

import formatter_json_lines


def _run_and_parse(fn_map) -> list[dict]:
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_json_lines, stream=buf)
    for msg, fn in fn_map.items():
        t_fn(msg)(fn)
    run()
    return [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]


@test("formatter_json_lines: test_end line has count total failed test")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    lines = _run_and_parse({"scope: x": fn})
    end_line = lines[-1]
    t.deep_equal(
        set(end_line.keys()) & {"count", "passed", "failed", "skipped"},
        {"count", "passed", "failed", "skipped"},
    )
    t.end()


@test("formatter_json_lines: skip produces end line with skipped count")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_json_lines, stream=buf)

    @t_fn.skip("scope: skipped")
    def fn(t2):
        t2.ok(True)
        t2.end()

    run()
    lines = [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]
    t.equal(lines[-1]["skipped"], 1)
    t.end()


@test("formatter_json_lines: comment produces no output")
def _(t):
    def fn(t2):
        t2.comment("hi")
        t2.ok(True)
        t2.end()

    lines = _run_and_parse({"scope: x": fn})
    # only test_end line + end line
    t.equal(len(lines), 2)
    t.end()


@test("formatter_json_lines: fail line contains test name")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    lines = _run_and_parse({"scope: failing": fn})
    fail_lines = [line for line in lines if "operator" in line]
    t.equal(fail_lines[0]["test"], "scope: failing")
    t.end()


@test("formatter_json_lines: start and success produce nothing")
def _(t):
    t.equal(formatter_json_lines.start(total=1), None)
    t.equal(formatter_json_lines.success(count=1, message="x"), None)
    t.equal(formatter_json_lines.comment(message="hi"), None)
    t.end()
