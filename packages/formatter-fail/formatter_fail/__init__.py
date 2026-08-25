from formatter_tap import comment, end, start  # re-export unchanged

__all__ = ["start", "comment", "end", "test", "success", "test_end", "fail"]


class _Fail:
    """Formatter instance with isolated state (createFormatter protocol)."""

    def __init__(self):
        self.current = ""

    def start(self, **kwargs):
        from formatter_tap import start as tap_start

        return tap_start(**kwargs)

    def comment(self, *, message="", **_):
        from formatter_tap import comment as tap_comment

        return tap_comment(message=message)

    def end(self, **kwargs):
        from formatter_tap import end as tap_end

        return tap_end(**kwargs)

    def test(self, *, test, **_) -> str:
        self.current = test
        return ""

    def success(self, **_) -> None:
        return None

    def test_end(self, **_) -> None:
        return None

    def fail(self, **kwargs) -> str:
        from formatter_tap import fail as tap_fail

        return f"# {self.current}\n{tap_fail(**kwargs)}"


def create_formatter(**_):
    """Returns a fresh formatter instance with isolated state."""
    return _Fail()


_default = _Fail()

test = _default.test
success = _default.success
test_end = _default.test_end
fail = _default.fail
