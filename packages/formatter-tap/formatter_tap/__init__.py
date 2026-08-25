def start(*, total, **_) -> str:
    return "TAP version 13\n"


def test(*, test, **_) -> str:
    return f"# {test}\n"


def comment(*, message, **_) -> str:
    return f"# {message}\n"


def success(*, count, message, **_) -> str:
    return f"ok {count} {message}\n"


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
    out = [f"not ok {count} {message}", "  ---", f"    operator: {operator}"]
    if output:
        out.append(output)
    else:
        out += ["    expected: |-", f"      {expected}", "    result: |-", f"      {result}"]
    out += [f"    {at}", "    stack: |-", error_stack, "  ...", ""]
    return "\n".join(out) + "\n"


def test_end(**_) -> None:
    return None


def end(*, count=0, passed=0, failed=0, skipped=0, **_) -> str:
    out = ["", f"1..{count}", f"# tests {count}", f"# pass {passed}"]
    if skipped:
        out.append(f"# skip {skipped}")
    if failed:
        out.append(f"# fail {failed}")
    out.append("")
    if not failed:
        out += ["# ok", ""]
    out.append("")
    return "\n".join(out)
