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
    **_,
) -> str:
    """Same as formatter_tap.fail but omits the `stack: |-` block."""
    out = [f"not ok {count} {message}", "  ---", f"    operator: {operator}"]
    if output:
        out.append(output)
    else:
        out += ["    expected: |-", f"      {expected}", "    result: |-", f"      {result}"]
    out += [f"    {at}", "  ...", ""]
    return "\n".join(out) + "\n"
