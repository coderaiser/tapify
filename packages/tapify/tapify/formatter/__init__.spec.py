import io

from tapify import test
from tapify.formatter import create_formatter


def _mod():
    class M:
        @staticmethod
        def start(*, total, **_):
            return f"total={total}"

    return M()


@test("formatter: builtin name resolves")
def _(t):
    harness, facade = create_formatter("tap")
    t.ok(hasattr(harness, "write"))
    t.ok(hasattr(facade, "emit"))
    t.end()


@test("formatter: module object accepted")
def _(t):
    buf = io.StringIO()
    harness, facade = create_formatter(_mod())
    harness.pipe(buf)
    facade.emit("start", {"total": 5})
    t.equal(buf.getvalue(), "total=5")
    t.end()


@test("formatter: unknown name raises ValueError")
def _(t):
    raised = False
    try:
        create_formatter("__nope__")
    except ValueError:
        raised = True
    t.ok(raised)
    t.end()


@test("formatter: emit with kwargs only")
def _(t):
    buf = io.StringIO()
    import formatter_tap

    harness, facade = create_formatter(formatter_tap)
    harness.pipe(buf)
    facade.emit("success", count=1, message="hi")
    t.equal(buf.getvalue(), "ok 1 hi\n")
    t.end()


@test('formatter: entry-point lookup resolves custom name')
def _(t):
    import importlib.metadata

    from tapify.formatter import create_formatter as cf

    class FakeEP:
        name = 'custom-fmt'

        def load(self):
            return _mod()

    orig = importlib.metadata.entry_points
    importlib.metadata.entry_points = lambda group=None: [FakeEP()]
    try:
        harness, facade = cf('custom-fmt')
    finally:
        importlib.metadata.entry_points = orig
    t.ok(hasattr(harness, 'write'))
    t.end()
