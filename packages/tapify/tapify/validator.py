import re
import traceback

_SCOPE_RE = re.compile(r"^[\w\-/\d\s]+:.*")

_processed: set[str] = set()

_validations: dict = {
    "check_duplicates": True,
    "check_scopes": True,
    "check_assertions_count": True,
}


def set_validations(v: dict):
    """Called from __main__ after parsing CLI args."""
    _validations.update(v)


def get_at() -> str:
    """Walk the Python call stack, skip tapify frames,
    return 'filename:lineno' of the first user frame."""
    frames = traceback.extract_stack()
    for frame in reversed(frames[:-1]):
        if frame.filename.startswith("<"):
            continue
        if "tapify" in frame.filename:
            continue
        if "site-packages" in frame.filename:
            continue
        return f"{frame.filename}:{frame.lineno}"
    return frames[-1].filename + ":" + str(frames[-1].lineno)


def create_validator(*, tests: list):
    """Returns validate(msg, *, assertions_count) -> [message, at] | []"""

    def validate(msg: str, *, assertions_count: int) -> list:
        if not any(_validations.values()):
            return []
        entries = [t for t in tests if t["message"] == msg]
        if not entries:
            raise RuntimeError(f"☝️ Looks like message cannot be found in tests: {msg!r}")
        for name, enabled in _validations.items():
            if not enabled:
                continue
            result = _VALIDATORS[name](msg, entries, assertions_count)
            if result:
                return result
        return []

    return validate


def reset_processed() -> None:
    _processed.clear()


def _check_duplicates(msg, entries, _assertions_count) -> list:
    if len(entries) < 2:
        return []
    if not _is_enabled(entries, "check_duplicates"):
        return []
    at = entries[1]["at"]
    if msg in _processed:
        return []
    _processed.add(msg)
    return [f"Duplicate {at}", at]


def _check_scopes(msg, entries, _assertions_count) -> list:
    at = entries[0]["at"]
    if not _SCOPE_RE.match(msg):
        return [
            f"Scope should be defined before first colon: 'scope: subject', received: {msg!r}",
            at,
        ]
    return []


def _check_assertions_count(msg, entries, assertions_count) -> list:
    at = entries[0]["at"]
    if not _is_enabled(entries, "check_assertions_count"):
        return []
    if assertions_count > 1:
        return ["Only one assertion per test allowed, looks like you have more", at]
    if assertions_count == 0:
        return ["Only one assertion per test allowed, looks like you have none", at]
    return []


def _is_enabled(entries, name) -> bool:
    return all(e.get("validations", {}).get(name, True) for e in entries)


_VALIDATORS = {
    "check_duplicates": _check_duplicates,
    "check_scopes": _check_scopes,
    "check_assertions_count": _check_assertions_count,
}
