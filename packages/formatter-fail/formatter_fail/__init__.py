from formatter_tap import comment, end, start  # re-export unchanged

__all__ = ["start", "comment", "end", "test", "success", "test_end", "fail"]


def test(*, test, **_) -> str:
    global current
    current = test
    return ""


def success(**_) -> None:
    return None


def test_end(**_) -> None:
    return None


def fail(**kwargs) -> str:
    from formatter_tap import fail as tap_fail

    name = globals().get("current", "")
    return f"# {name}\n{tap_fail(**kwargs)}"
