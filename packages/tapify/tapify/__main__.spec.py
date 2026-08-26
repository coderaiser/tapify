import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from tapify import test

_PY = sys.executable


def _run(args, env=None) -> int:
    e = {**os.environ, **(env or {})}
    return subprocess.run([_PY, "-m", "tapify", *args], env=e, capture_output=True).returncode


def _write_spec(body) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".spec.py", delete=False) as f:
        f.write(body)
        return f.name


def _cleanup(name):
    pathlib.Path(name).unlink()


@test("cli: no test files exits OK")
def _(t):
    t.equal(_run(["__nonexistent_glob__"]), 0)
    t.end()


@test("cli: all passing tests exits OK")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("scope: pass")\ndef _(t): t.ok(True); t.end()\n'
    )
    code = _run([name, "-f", "tap", "--no-worker"])
    _cleanup(name)
    t.equal(code, 0)
    t.end()


@test("cli: failing test exits FAIL (1)")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("scope: fail")\ndef _(t): t.ok(False); t.end()\n'
    )
    code = _run([name, "-f", "tap", "--no-worker"])
    _cleanup(name)
    t.equal(code, 1)
    t.end()


@test("cli: TAPIFY_CHECK_SKIPPED=1 with skipped exits SKIPPED (5)")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test.skip("scope: skip")\ndef _(t): t.ok(True); t.end()\n'
    )
    code = _run([name, "-f", "tap", "--no-worker"], env={"TAPIFY_CHECK_SKIPPED": "1"})
    _cleanup(name)
    t.equal(code, 5)
    t.end()


@test("cli: TAPIFY_CHECK_SKIPPED=1 with skipped AND failed exits FAIL (1)")
def _(t):
    name = _write_spec(
        "from tapify import test\n"
        '@test.skip("scope: skip")\ndef _(t): t.ok(True); t.end()\n'
        '@test("scope: fail")\ndef _(t): t.ok(False); t.end()\n'
    )
    code = _run([name, "-f", "tap", "--no-worker"], env={"TAPIFY_CHECK_SKIPPED": "1"})
    _cleanup(name)
    t.equal(code, 1)  # fail beats skipped
    t.end()


@test("cli: unknown --format exits INVALID_OPTION (4)")
def _(t):
    code = _run(["-f", "nonexistent"])
    t.equal(code, 4)
    t.end()


@test("cli: worker mode passes too")
def _(t):
    name = _write_spec(
        'from tapify import test\n@test("scope: pass")\ndef _(t): t.ok(True); t.end()\n'
    )
    code = _run([name, "-f", "fail"])
    _cleanup(name)
    t.equal(code, 0)
    t.end()


@test("cli: dry run imports without running")
def _(t):
    name = _write_spec(
        "from tapify import test\n"
        '@test("scope: fail")\ndef _(t): raise RuntimeError("should not run")\n'
    )
    code = _run([name, "-f", "tap", "--no-worker", "--dry-run"])
    _cleanup(name)
    t.equal(code, 0)
    t.end()


@test("cli: bad --require module exits UNHANDLED (3)")
def _(t):
    code = _run(["-r", "__definitely_not_a_module__"])
    t.equal(code, 3)
    t.end()


@test("cli: __main__.py inside glob does not recurse")
def _(t):
    d = tempfile.mkdtemp()
    # "__main__.py" sorts before "z.spec.py": the nested run re-imports
    # __main__.py before finishing → infinite recursion without the fix
    pathlib.Path(d, "__main__.py").write_text("x = 1\n")
    pathlib.Path(d, "z.spec.py").write_text(
        'from tapify import test\n@test("scope: pass")\ndef _(t): t.ok(True); t.end()\n'
    )
    try:
        r = subprocess.run(
            [_PY, "-m", "tapify", "**/*.py", "-f", "tap", "--no-worker"],
            capture_output=True,
            cwd=d,
            timeout=30,
        )
        code = r.returncode
    finally:
        shutil.rmtree(d)
    t.equal(code, 0)
    t.end()


@test("cli: _import_file never loads a file as __main__")
def _(t):
    import tapify.__main__ as m

    d = tempfile.mkdtemp()
    p = pathlib.Path(d, "__main__.py")
    body = "import pathlib\n"
    body += 'pathlib.Path(__file__).with_name("name.txt").write_text(__name__)\n'
    p.write_text(body)
    try:
        m._import_file(p)
        loaded_as = (p.parent / "name.txt").read_text()
    finally:
        shutil.rmtree(d)
    t.not_equal(loaded_as, "__main__")
    t.end()


@test("cli: --help exits OK and prints usage")
def _(t):
    import io

    import tapify.__main__ as m

    orig_argv = sys.argv
    orig_stdout = sys.stdout
    sys.argv = ["tapify", "--help"]
    sys.stdout = io.StringIO()
    code = None
    try:
        m.main()
    except SystemExit as e:
        code = e.code
    out = sys.stdout.getvalue()
    sys.stdout = orig_stdout
    sys.argv = orig_argv
    t.ok("Usage: python -m tapify" in out and code == 0)
    t.end()


@test("cli: --version prints version and exits OK")
def _(t):
    import io
    import re

    import tapify.__main__ as m

    orig_argv = sys.argv
    orig_stdout = sys.stdout
    sys.argv = ["tapify", "--version"]
    sys.stdout = io.StringIO()
    code = None
    try:
        m.main()
    except SystemExit as e:
        code = e.code
    out = sys.stdout.getvalue()
    sys.stdout = orig_stdout
    sys.argv = orig_argv
    t.ok(bool(re.match(r"^v\d+\.\d+", out)) and code == 0)
    t.end()
