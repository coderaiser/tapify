import importlib
import importlib.metadata

_BUILTIN = {
    "tap": "formatter_tap",
    "fail": "formatter_fail",
    "short": "formatter_short",
    "progress-bar": "formatter_progress_bar",
    "json-lines": "formatter_json_lines",
}


def create_formatter(name):
    """Returns (harness, facade). The facade has .emit(event, data).

    name may be a str (builtin name or entry-point name) or a module object.
    """
    from tapify.formatter.harness import Harness

    if isinstance(name, str):
        pkg = _BUILTIN.get(name)
        if pkg:
            module = importlib.import_module(pkg)
        else:
            eps = importlib.metadata.entry_points(group="tapify.formatter")
            found = [ep for ep in eps if ep.name == name]
            if not found:
                raise ValueError(f"Unknown formatter: {name!r}")
            module = found[0].load()
    else:
        module = name

    harness = Harness(module)

    class _Facade:
        def emit(self, event: str, data: dict | None = None, **kwargs):
            harness.write(event, data or kwargs)

    return harness, _Facade()
