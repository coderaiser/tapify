import io
import json
import os

from tapify import test

import formatter_json_lines_fail


def _run_and_parse(fn_map) -> list[dict]:
    from tapify.supertape import create_test

    buf = io.StringIO()
    t_fn, _, run = create_test(formatter=formatter_json_lines_fail, stream=buf)
    for msg, fn in fn_map.items():
        t_fn(msg)(fn)
    run()
    return [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]


@test("formatter_json_lines_fail: successful test_end produces no line")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    lines = _run_and_parse({"scope: ok": fn})
    # only the summary end line remains
    t.equal(len(lines), 1)
    t.end()


@test("formatter_json_lines_fail: summary line reports passed count")
def _(t):
    def fn(t2):
        t2.ok(True)
        t2.end()

    lines = _run_and_parse({"scope: ok": fn})
    t.equal(lines[0]["passed"], 1)
    t.end()


@test("formatter_json_lines_fail: fail lines are kept")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    lines = _run_and_parse({"scope: failing": fn})
    fail_lines = [line for line in lines if "operator" in line]
    t.equal(fail_lines[0]["test"], "scope: failing")
    t.end()


@test("formatter_json_lines_fail: summary reports failed count")
def _(t):
    def fn(t2):
        t2.ok(False)
        t2.end()

    lines = _run_and_parse({"scope: failing": fn})
    t.equal(lines[-1]["failed"], 1)
    t.end()


@test("formatter_json_lines_fail: create_formatter returns isolated instance")
def _(t):
    a = formatter_json_lines_fail.create_formatter()
    b = formatter_json_lines_fail.create_formatter()
    t.not_equal(a, b)
    t.end()


@test("formatter_json_lines_fail: no-op hooks return None")
def _(t):
    fmt = formatter_json_lines_fail.create_formatter()
    results = (
        fmt.start(total=1),
        fmt.success(count=1),
        fmt.comment(message="hi"),
        fmt.test_end(count=1, total=1, failed=0, test="x"),
    )
    t.equal(results, (None, None, None, None))
    t.end()


@test("formatter_json_lines_fail: registered as valid CLI format")
def _(t):
    from tapify.cli.parse_args import _VALID_FORMATS

    t.ok("json-lines-fail" in _VALID_FORMATS)
    t.end()


@test("formatter_json_lines_fail: registered as builtin formatter")
def _(t):
    from tapify.formatter import _BUILTIN

    t.equal(_BUILTIN.get("json-lines-fail"), "formatter_json_lines_fail")
    t.end()


@test("formatter_json_lines_fail: unknown formatter still raises")
def _(t):
    from tapify.formatter import create_formatter

    raised = False
    try:
        create_formatter("nope-nope")
    except ValueError:
        raised = True
    t.ok(raised)
    t.end()


@test("formatter_json_lines_fail: env var does not affect module-level hooks")
def _(t):
    os.environ["TAPIFY_JSON_LINES_FAIL"] = "1"
    try:
        out = formatter_json_lines_fail.test_end(count=1, total=1, failed=0, test="x")
    finally:
        os.environ.pop("TAPIFY_JSON_LINES_FAIL", None)
    t.equal(out, None)
    t.end()
