import sys

_NOOP = lambda **_: None  # noqa: E731


class Harness:
    _HOOK_MAP = {
        "start": "start",
        "test": "test",
        "test:end": "test_end",  # colon → underscore
        "success": "success",
        "fail": "fail",
        "comment": "comment",
        "end": "end",
    }

    def __init__(self, module, stream=None):
        self._hooks = self._prepare(module)
        self._stream = stream or sys.stdout
        self._ended = False

    def _prepare(self, module):
        """Fill missing hooks with no-ops. Support createFormatter() protocol."""
        base = {
            k: _NOOP for k in ("start", "test", "test_end", "success", "fail", "comment", "end")
        }
        provider = module.create_formatter() if hasattr(module, "create_formatter") else module
        for name in base:
            hook = getattr(provider, name, None)
            if hook:
                base[name] = hook
        return base

    def write(self, event: str, data: dict):
        if self._ended:
            raise RuntimeError("☝️ Looks like 'async' operator called without 'await'")
        hook_name = self._HOOK_MAP.get(event)
        if not hook_name:
            return
        result = self._hooks[hook_name](**data)
        if result and self._stream:
            self._stream.write(result)
            if hasattr(self._stream, "flush"):
                self._stream.flush()
        if event == "end":
            self._ended = True

    def pipe(self, stream):
        self._stream = stream


def create_harness(module, stream=None) -> Harness:
    return Harness(module, stream)
