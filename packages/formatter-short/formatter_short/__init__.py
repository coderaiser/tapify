from formatter_tap import comment, end, start, success, test, test_end  # noqa: F401

__all__ = ["start", "comment", "end", "test", "success", "test_end", "fail"]


def fail(
    *,
    at="",
    count=0,
    message="",
    operator="",
    result=None,
    expected=None,
    output="",
    error_stack="",
    **_,
) -> str:
    """Same as formatter_tap.fail but omits the `stack: |-` block."""
    from formatter_tap import fail as tap_fail

    full = tap_fail(
        at=at,
        count=count,
        message=message,
        operator=operator,
        result=result,
        expected=expected,
        output=output,
        error_stack=error_stack,
    )
    lines = [
        line
        for line in full.splitlines()
        if line != "    stack: |-" and not line.startswith("      ")
    ]
    # drop the stack body lines but keep the indented yaml block content
    lines = []
    skipping = False
    for line in full.splitlines():
        if line == "    stack: |-":
            skipping = True
            continue
        if skipping:
            if not line.strip():
                skipping = False
                continue
            continue
        lines.append(line)
    return "\n".join(lines)
