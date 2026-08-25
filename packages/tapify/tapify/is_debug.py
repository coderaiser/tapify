import sys


def is_debug() -> bool:
    argv = " ".join(sys.orig_argv)
    return "inspect" in argv or "debug" in argv
