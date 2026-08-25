def add_spaces(s: str) -> str:
    return f"      {s}"


def format_output(s: str) -> str:
    return "\n".join(add_spaces(line) for line in s.splitlines())


_REASON_USER = 3


def parse_at(stack: str) -> str:
    lines = stack.splitlines()
    if len(lines) == 1:
        return stack
    if len(lines) > 10 and lines[0].startswith("Error: "):
        return lines[_REASON_USER] or lines[0]
    if len(lines) <= _REASON_USER:
        raise RuntimeError(f"☝️ Looks like 'async' operator called without 'await': {stack}")
    return lines[_REASON_USER].strip()
