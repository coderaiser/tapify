import re
import traceback

_SCOPE_RE = re.compile(r"^[\w\-/\d\s]+:.*")

_processed: set[str] = set()

_VALIDATIONS_DEFAULTS: dict = {
    "check_duplicates": True,
    "check_scopes": True,
    "check_assertions_count": True,
}

_validations: dict = dict(_VALIDATIONS_DEFAULTS)


def set_validations(v: dict):
    """Called from __main__ after parsing CLI args."""
    _validations.update(v)


def reset_validations():
    """Restore default validations (used between spec tests)."""
    _validations.clear()
    _validations.update(_VALIDATIONS_DEFAULTS)


def _is_user(filename: str) -> bool:
    if filename.startswith("<"):
        return False
    if "site-packages" in filename:
        return False
    if "/tapify/tapify/" in filename and not filename.endswith(".spec.py"):
        return False
    if "/packages/formatter-" in filename and filename.endswith("__init__.py"):
        return False
    return not _is_internal(filename)


def filter_frames(frames: list) -> list:
    """Return only user-code frames, in stack order (Python internals dropped).
    Falls back to the original frames when no user frame is found."""
    kept = [frame for frame in frames if _is_user(frame.filename)]
    return kept or list(frames)


def get_stack() -> str:
    """Formatted call stack starting from user code, no Python internals."""
    return "".join(traceback.format_list(filter_frames(traceback.extract_stack())))


def get_at() -> str:
    """Walk the Python call stack, skip runner/internal frames,
    return 'at filename:lineno' of the deepest user frame."""
    all_frames = list(traceback.extract_stack())
    frames = all_frames
    if frames and not _is_user(frames[-1].filename):
        frames = frames[:-1]
    kept = [frame for frame in frames if _is_user(frame.filename)]
    if kept:
        frame = kept[-1]
        return f"at {frame.filename}:{frame.lineno}"
    last = all_frames[-1]
    return f"at {last.filename}:{last.lineno}"


_INTERNAL_DIRS = (
    "threading.py",
    "concurrent/",
    "asyncio/",
    "multiprocessing/",
    "queue.py",
    "runpy.py",
    "importlib/",
)


def _is_internal(filename: str) -> bool:
    return any(part in filename for part in _INTERNAL_DIRS)


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
    at = entries[1].get("at", "")
    if msg in _processed:
        return []
    _processed.add(msg)
    return [f"Duplicate {at}", at]


def _check_scopes(msg, entries, _assertions_count) -> list:
    at = entries[0].get("at", "")
    if not _SCOPE_RE.match(msg):
        return [
            f"Scope should be defined before first colon: 'scope: subject', received: {msg!r}",
            at,
        ]
    return []


def _check_assertions_count(msg, entries, assertions_count) -> list:
    at = entries[0].get("at", "")
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
