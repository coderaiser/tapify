import difflib
import pprint
import sys


def diff(expected, result) -> str:
    """diff(expected, result) — argument order matches supertape."""
    a = pprint.pformat(expected).splitlines()
    b = pprint.pformat(result).splitlines()
    lines = list(difflib.unified_diff(a, b, lineterm=""))
    if not lines:
        return ""
    # drop --- / +++ header (first 2 lines), keep body chunks
    body_lines = lines[2:]
    # strip @@ ... @@ chunk headers — jest-diff doesn't show them
    body_lines = [line for line in body_lines if not line.startswith("@@")]
    if not body_lines:
        return ""
    colored = [_colorize(line) for line in body_lines]
    from tapify.format import add_spaces, format_output

    return add_spaces("diff: |-") + "\n" + format_output("\n".join(colored))


def _colorize(line: str) -> str:
    if not sys.stdout.isatty():
        return line
    if line.startswith("-"):
        return f"\x1b[32m{line}\x1b[39m"  # green — expected
    if line.startswith("+"):
        return f"\x1b[31m{line}\x1b[39m"  # red — result
    return line
