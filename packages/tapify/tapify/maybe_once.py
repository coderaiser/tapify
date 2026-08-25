import threading

_disabled_lock = threading.Lock()
_disabled = False


def enable_once() -> None:
    global _disabled
    _disabled = False


def disable_once() -> None:
    global _disabled
    _disabled = True


def maybe_once(fn):
    """Decorator. Wrapped fn runs once; subsequent calls are no-ops.

    When disable_once() is active, the fn runs every time.
    """
    called = set()
    called_lock = threading.Lock()

    def wrapper(*args, **kwargs):
        global _disabled
        if _disabled:
            return fn(*args, **kwargs)
        with called_lock:
            if fn in called:
                return None
            called.add(fn)
        return fn(*args, **kwargs)

    wrapper.enable_once = enable_once
    wrapper.disable_once = disable_once
    return wrapper
