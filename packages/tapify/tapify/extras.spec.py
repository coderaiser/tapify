"""Coverage-completion tests: CLI in-process, validator edge cases,
extension/stub edge cases, progress-bar color paths, emitter timer."""

import io
import os
import pathlib
import sys
import tempfile
import time
from unittest import mock

from tapify import supertape, test
from tapify.emitter import _default_loop
from tapify.formatter.harness import Harness
from tapify.maybe_once import disable_once, enable_once
from tapify.operators import _OPERATORS, deep_equal, init_operators, not_deep_equal
from tapify.operators import end as op_end
from tapify.validator import create_validator, reset_processed, set_validations


def _write_spec(body) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".spec.py", delete=False) as f:
        f.write(body)
        return f.name


def _main_run(args):
    import tapify.__main__ as m
    import tapify.supertape as st

    orig_argv, orig_stdout, orig_stderr = sys.argv, sys.stdout, sys.stderr
    saved_tests = st._tests
    st._tests = []  # isolate: only files imported by main() register
    sys.argv = ["tapify", *args]
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    code = None
    try:
        m.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = orig_argv
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        st._tests = saved_tests
    return code


@test("extras: main runs a passing file and exits OK")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("extras: pass")\ndef _(t): t.ok(True); t.end()\n'
    )
    code = _main_run([name, "-f", "tap", "--no-worker"])
    os.unlink(name)
    t.equal(code, 0)
    t.end()


@test("extras: main exits FAIL for failing file")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("extras: fail")\ndef _(t): t.ok(False); t.end()\n'
    )
    code = _main_run([name, "-f", "tap", "--no-worker"])
    os.unlink(name)
    t.equal(code, 1)
    t.end()


@test("extras: main exits SKIPPED when check skipped enabled")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test.skip("extras: skip")\ndef _(t): t.ok(True); t.end()\n'
    )
    saved = os.environ.get("TAPIFY_CHECK_SKIPPED")
    os.environ["TAPIFY_CHECK_SKIPPED"] = "1"
    code = _main_run([name, "-f", "tap", "--no-worker"])
    if saved is None:
        os.environ.pop("TAPIFY_CHECK_SKIPPED", None)
    else:
        os.environ["TAPIFY_CHECK_SKIPPED"] = saved
    os.unlink(name)
    t.equal(code, 5)
    t.end()


@test("extras: main exits INVALID_OPTION for unknown format")
def _(t):
    t.equal(_main_run(["-f", "__nope__"]), 4)
    t.end()


@test("extras: main exits UNHANDLED for bad require module")
def _(t):
    t.equal(_main_run(["-r", "__not_a_module__"]), 3)
    t.end()


@test("extras: main dry-run does not execute tests")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("extras: never")\ndef _(t): raise RuntimeError()\n'
    )
    code = _main_run([name, "-f", "tap", "--no-worker", "--dry-run"])
    os.unlink(name)
    t.equal(code, 0)
    t.end()


@test("extras: get_at skips site-packages and falls back")
def _(t):
    from tapify.validator import get_at

    frames = [
        mock.Mock(filename="/env/site-packages/x.py", lineno=1),
        mock.Mock(filename="user.py", lineno=42),
    ]
    with mock.patch("tapify.validator.traceback.extract_stack", return_value=frames):
        at = get_at()
    t.equal(at, "at user.py:42")
    t.end()


@test("extras: get_at skips frozen frames")
def _(t):
    from tapify.validator import get_at

    frames = [
        mock.Mock(filename="<frozen importlib._bootstrap>", lineno=488),
        mock.Mock(filename="user.py", lineno=42),
    ]
    with mock.patch("tapify.validator.traceback.extract_stack", return_value=frames):
        at = get_at()
    t.equal(at, "at user.py:42")
    t.end()


@test("extras: get_at skips threading internals")
def _(t):
    from tapify.validator import get_at

    frames = [
        mock.Mock(filename="/usr/lib/python3.12/threading.py", lineno=1030),
        mock.Mock(
            filename="/usr/lib/python3.12/concurrent/futures/thread.py",
            lineno=92,
        ),
        mock.Mock(filename="user.py", lineno=42),
    ]
    with mock.patch("tapify.validator.traceback.extract_stack", return_value=frames):
        at = get_at()
    t.equal(at, "at user.py:42")
    t.end()


@test("extras: get_at falls back when only tapify frames")
def _(t):
    from tapify.validator import get_at

    only_tapify = [mock.Mock(filename="x/tapify/y.py", lineno=7)]
    with mock.patch("tapify.validator.traceback.extract_stack", return_value=only_tapify):
        at = get_at()
    t.match(at, r"at x/tapify/y\.py:7$")
    t.end()


@test("extras: per-entry validation opt-out respected")
def _(t):
    set_validations(
        {"check_duplicates": True, "check_scopes": False, "check_assertions_count": False}
    )
    reset_processed()
    tests = [
        {"message": "scope: d", "at": "a.py:1", "validations": {"check_duplicates": False}},
        {"message": "scope: d", "at": "a.py:2", "validations": {"check_duplicates": False}},
    ]
    v = create_validator(tests=tests)
    t.equal(v("scope: d", assertions_count=1), [])
    set_validations({"check_duplicates": False})
    t.end()


@test("extras: operator wrapper handles None return")
def _(t):
    events = []

    class Fmt:
        def emit(self, event, data=None, **kw):
            events.append((event, data or kw))

    state = {
        "formatter": Fmt(),
        "count": lambda: 0,
        "inc_count": lambda: None,
        "inc_passed": lambda: None,
        "inc_failed": lambda: None,
        "is_ended": [False],
        "assertions_count": lambda: 0,
        "inc_assertions_count": lambda: None,
    }
    orig = _OPERATORS["ok"]
    _OPERATORS["ok"] = lambda *a, **kw: None
    try:
        ops = init_operators(state)
        ops.ok(True)
    finally:
        _OPERATORS["ok"] = orig
    event, data = events[0]
    t.equal(event, "fail")
    t.match(str(data["message"]), r"returns nothing")
    t.end()


@test("extras: pure operators edge cases")
def _(t):
    t.not_ok(deep_equal(1, True)["is"])
    t.ok(not_deep_equal(1, True)["is"])
    t.ok(not_deep_equal({"a": 1}, {"a": 2})["is"])
    t.not_ok(not_deep_equal({"a": 1}, {"a": 1})["is"])
    t.equal(op_end(), {})
    t.end()


@test("extras: extension returning nothing is ignored")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = supertape.create_test(format="tap", stream=buf)
    ext = t_fn.extend({"noop": lambda ops: lambda x: None})

    @ext("scope: noop")
    def fn(t2):
        t2.noop(1)
        t2.end()

    run()
    t.match(buf.getvalue(), r"1\.\.0")  # noop extension emits nothing
    t.match(buf.getvalue(), r"# ok")
    t.end()


@test("extras: extended skip/only work on chains")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = supertape.create_test(format="tap", stream=buf)
    base = t_fn.extend({"pos": lambda ops: lambda x: ops["ok"](x > 0)})

    @base.skip("scope: s1")
    def a(t2):
        t2.pos(-1)
        t2.end()

    @base.only("scope: o1")
    def b(t2):
        t2.pos(1)
        t2.end()

    run()
    out = buf.getvalue()
    t.match(out, r"# skip 1")
    t.match(out, r"ok 1")
    t.end()


@test("extras: global extend supports skip/only and merge")
def _(t):
    supertape.reset()
    ext = supertape.test.extend({"pos": lambda ops: lambda x: ops["ok"](x > 0)})

    @ext.skip("scope: gs")
    def a(t2):
        t2.pos(-5)
        t2.end()

    @ext.only("scope: go")
    def b(t2):
        t2.pos(5)
        t2.end()

    messages = {e["message"]: e for e in supertape._tests}
    t.ok(messages["scope: gs"]["skip"])
    t.ok(messages["scope: go"]["only"])
    t.ok(messages["scope: go"]["extensions"])
    supertape.reset()
    t.end()


@test("extras: stub proxy passes through non-overridden attrs")
def _(t):
    from tapify import stub

    seen = []

    @stub({"ok": lambda ok, v: seen.append(v)})
    def fn(t):
        t.ok("x")
        t.mystery()
        return "done"

    fake_t = type(
        "T", (), {"ok": staticmethod(lambda v: None), "mystery": lambda self: seen.append("myst")}
    )()
    result = fn(fake_t)
    t.equal(seen, ["x", "myst"])
    t.equal(result, "done")
    t.end()


@test("extras: direct registration forms")
def _(t):
    supertape.reset()

    def fn(t2):
        t2.ok(True)
        t2.end()

    supertape.test("scope: direct", fn)
    t.equal(supertape._tests[-1]["message"], "scope: direct")
    supertape.reset()

    buf = io.StringIO()
    t_fn, _, run = supertape.create_test(format="tap", stream=buf)
    t_fn("scope: positional", fn)
    run()
    t.match(buf.getvalue(), r"ok 1")
    t.end()


@test("extras: default loop reschedules while tests load")
def _(t):
    saved = os.environ.get("TAPIFY_LOAD_LOOP_TIMEOUT")
    os.environ["TAPIFY_LOAD_LOOP_TIMEOUT"] = "10"
    ran = []

    class EM:
        def emit(self, event, *a, **kw):
            if event == "run":
                ran.append(1)

    em = EM()
    holder = [object()]
    disable_once()
    _default_loop(emit=em.emit, tests=holder)
    time.sleep(0.4)
    enable_once()
    if saved is None:
        os.environ.pop("TAPIFY_LOAD_LOOP_TIMEOUT", None)
    else:
        os.environ["TAPIFY_LOAD_LOOP_TIMEOUT"] = saved
    t.equal(ran, [1])
    t.end()


@test("extras: harness tolerates null stream")
def _(t):
    class M:
        @staticmethod
        def start(*, total, **_):
            return f"total={total}"

    h = Harness(M())
    h.pipe(None)
    h.write("start", {"total": 1})  # must not raise
    t.ok(True)
    t.end()


@test("extras: worker streams print through queue")
def _(t):
    from tapify.worker import run_with_worker

    def talks(t2):
        print("hello-from-test")
        t2.ok(True)
        t2.end()

    buf = io.StringIO()
    code = run_with_worker(
        [
            {
                "message": "scope: talk",
                "fn": talks,
                "at": "file.py:1",
                "skip": False,
                "only": False,
                "extensions": {},
                "timeout": 3000,
            }
        ],
        format_name="tap",
        stream=buf,
    )
    t.equal(code, 0)
    t.match(buf.getvalue(), r"hello-from-test")
    t.end()


@test("extras: progress bar color functions on tty")
def _(t):
    import formatter_progress_bar as fpb

    class FakeErr:
        def isatty(self):
            return True

    orig = sys.stderr
    sys.stderr = FakeErr()
    try:
        colored = fpb._color_fn("#ff0000")("x")
        t.match(colored, r"\x1b\[38;2;255;0;0m")
        t.match(fpb._color_fn("red")("y"), r"\x1b\[31my")
        t.equal(fpb._color_fn("chartreuse")("z"), "z")
    finally:
        sys.stderr = orig
    t.end()


@test("extras: formatter_tap fail without diff output")
def _(t):
    import formatter_tap

    out = formatter_tap.fail(
        count=3, message="m", operator="equal", expected=1, result=2, output=""
    )
    t.match(out, r"expected: \|-")
    t.match(out, r"      1")
    t.end()


@test("extras: formatter_tap fail with diff output")
def _(t):
    import formatter_tap

    out = formatter_tap.fail(
        count=3, message="m", operator="equal", output="      diff: |-\n        - 1"
    )
    t.match(out, r"diff: \|-")
    t.not_match(out, r"expected: \|-")
    t.end()


@test("extras: main ignores absolute non-file pattern")
def _(t):
    t.equal(_main_run(["/definitely/__missing__.spec.py", "-f", "tap"]), 0)
    t.end()


@test("extras: main deduplicates files across patterns")
def _(t):
    directory = tempfile.mkdtemp()
    target = pathlib.Path(directory) / "dedup.spec.py"
    target.write_text(
        'from tapify import test\n@test("extras: dedup")\ndef _(t): t.ok(True); t.end()\n',
        encoding="utf-8",
    )
    old_cwd = os.getcwd()
    os.chdir(directory)
    try:
        code = _main_run(["*.spec.py", "./*.spec.py", "-f", "tap", "--no-worker"])
    finally:
        os.chdir(old_cwd)
    t.equal(code, 0)
    t.end()


@test("extras: main exits OK with no matched files")
def _(t):
    t.equal(_main_run(["__no_files_glob__"]), 0)
    t.end()


@test("extras: main runs with worker enabled")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("extras: worker")\ndef _(t): t.ok(True); t.end()\n'
    )
    code = _main_run([name, "-f", "fail"])
    os.unlink(name)
    t.equal(code, 0)
    t.end()


@test("extras: main exits UNHANDLED when runner raises")
def _(t):
    from unittest import mock as _mock

    name = _write_spec(
        'from tapify import test\n@test("extras: boom")\ndef _(t): t.ok(True); t.end()\n'
    )
    import tapify.worker

    with _mock.patch.object(tapify.worker, "run_with_worker", side_effect=RuntimeError("boom")):
        code = _main_run([name, "-f", "tap"])
    os.unlink(name)
    t.equal(code, 3)
    t.end()


@test("extras: assertions-count opt-out per entry")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    tests = [
        {
            "message": "scope: many",
            "at": "a.py:1",
            "validations": {"check_assertions_count": False},
        },
    ]
    v = create_validator(tests=tests)
    t.equal(v("scope: many", assertions_count=5), [])
    set_validations({"check_assertions_count": False})
    t.end()


@test("extras: progress bar stream selection matrix")
def _(t):
    import formatter_progress_bar as fpb

    def stream_for(env):
        saved = {k: os.environ.get(k) for k in env}
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        try:
            return fpb._get_stream(total=500)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    s = stream_for({"TAPIFY_PROGRESS_BAR": "0"})
    t.not_equal(s, sys.stderr)
    s = stream_for({"TAPIFY_PROGRESS_BAR": "1"})
    t.equal(s, sys.stderr)
    t.end()


@test("extras: progress bar non-CI all-pass end")
def _(t):
    import formatter_progress_bar as fpb

    saved = os.environ.pop("CI", None)
    try:
        fmt = fpb.create_formatter()
        fmt.start(total=1)
        out = fmt.end(count=1, passed=1, failed=0, skipped=0)
        t.ok("# ✅ ok" in out and "# fail" not in out)
    finally:
        if saved is not None:
            os.environ["CI"] = saved
    t.end()


@test("extras: global extend direct call merges")
def _(t):
    supertape.reset()

    def fn(t2):
        t2.ok(True)
        t2.end()

    ext = supertape.test.extend({"pos": lambda ops: lambda x: ops["ok"](x > 0)})
    ext("scope: gdirect", fn)
    messages = [e["message"] for e in supertape._tests]
    t.ok("scope: gdirect" in messages)
    t.ok(supertape._tests[-1]["extensions"])
    supertape.reset()
    t.end()


@test("extras: get_stream enough tests no ci")
def _(t):
    import formatter_progress_bar as fpb

    saved = {k: os.environ.get(k) for k in ("CI", "TAPIFY_PROGRESS_BAR")}
    os.environ.pop("CI", None)
    os.environ.pop("TAPIFY_PROGRESS_BAR", None)
    os.environ["TAPIFY_PROGRESS_BAR_MIN"] = "10"
    try:
        t.equal(fpb._get_stream(total=50), sys.stderr)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        os.environ.pop("TAPIFY_PROGRESS_BAR_MIN", None)
    t.end()


@test("extras: progress bar create_formatter ci end")
def _(t):
    import formatter_progress_bar as fpb

    saved = os.environ.get("CI")
    os.environ["CI"] = "1"
    try:
        fmt = fpb.create_formatter()
        fmt.start(total=1)
        out = fmt.end(count=1, passed=1, failed=0, skipped=0)
        t.ok("# ✅ ok" in out)
    finally:
        if saved is None:
            os.environ.pop("CI", None)
        else:
            os.environ["CI"] = saved
    t.end()


@test("extras: create_test extended registers through merge")
def _(t):
    buf = io.StringIO()
    t_fn, _, run = supertape.create_test(format="tap", stream=buf)
    base = t_fn.extend({"pos": lambda ops: lambda x: ops["ok"](x > 0)})

    def fn(t2):
        t2.pos(3)
        t2.end()

    base("scope: merged", fn)
    run()
    t.match(buf.getvalue(), r"ok 1")
    t.end()


@test("extras: harness flush skipped for streams without flush")
def _(t):
    class NoFlush:
        def __init__(self):
            self.data = []

        def write(self, text):
            self.data.append(text)

    class M:
        @staticmethod
        def start(*, total, **_):
            return f"total={total}"

    sink = NoFlush()
    h = Harness(M(), sink)
    h.write("start", {"total": 2})
    t.equal(sink.data, ["total=2"])
    t.end()


@test("extras: progress bar fail with diff output")
def _(t):
    import formatter_progress_bar as fpb

    fmt = fpb.create_formatter()
    fmt.start(total=1)
    fmt.test(test="scope: diff")
    fmt.fail(
        at="a.py:1", count=1, message="m", operator="equal", output="      diff: |-\n        - 1"
    )
    out = fmt.end(count=1, passed=0, failed=1, skipped=0)
    t.match(out, r"diff: \|-")
    t.end()
