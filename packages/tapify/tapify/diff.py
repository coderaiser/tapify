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
    # jest-diff pads -/+ markers with a space: '- 2', '+ 1'
    body_lines = [_pad_marker(line) for line in body_lines]
    colored = [_colorize(line) for line in body_lines]
    from tapify.format import add_spaces, format_output

    return add_spaces("diff: |-") + "\n" + format_output("\n".join(colored))


def _pad_marker(line: str) -> str:
    if line.startswith(("-", "+")) and not line.startswith(("---", "+++")):
        return f"{line[0]} {line[1:]}"
    return line


def _colorize(line: str) -> str:
    if not sys.stdout.isatty():
        return line
    marker = line[:1]
    if marker == "-":
        return f"\x1b[32m{line}\x1b[39m"  # green — expected
    if marker == "+":
        return f"\x1b[31m{line}\x1b[39m"  # red — result
    return line
