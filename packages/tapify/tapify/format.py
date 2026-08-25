import re

_FILE_RE = re.compile(r'File "([^"]+)", line (\d+)')

_REASON_USER = 3


def add_spaces(s: str) -> str:
    return f"      {s}"


def format_output(s: str) -> str:
    return "\n".join(add_spaces(line) for line in s.splitlines())


def parse_at(stack: str) -> str:
    lines = stack.splitlines()
    if len(lines) == 1:
        return stack
    from tapify.validator import _is_internal

    for line in lines:
        found = _FILE_RE.search(line)
        if not found:
            continue
        filename, lineno = found.groups()
        if filename.startswith("<"):
            continue
        if "tapify" in filename or "site-packages" in filename:
            continue
        if _is_internal(filename):
            continue
        return f"at {filename}:{lineno}"
    if len(lines) <= _REASON_USER:
        raise RuntimeError(f"☝️ Looks like 'async' operator called without 'await': {stack}")
    return lines[_REASON_USER].strip()
