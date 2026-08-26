import argparse
import os
import sys

from tapify import exit_codes

_VALID_FORMATS = ("tap", "fail", "short", "progress-bar", "json-lines", "json-lines-fail")


def _default_format() -> str:
    return "tap" if os.environ.get("CI") else "progress-bar"


def _env_bool(name, default=True) -> bool:
    v = os.environ.get(name)
    return default if v is None else v != "0"


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="tapify", add_help=False)
    p.add_argument("-h", "--help", action="store_true")
    p.add_argument("-v", "--version", action="store_true")
    p.add_argument("-f", "--format", default=_default_format())
    p.add_argument("-r", "--require", action="append", default=[], metavar="MODULE")
    p.add_argument(
        "-d",
        "--check-duplicates",
        action="store_true",
        default=_env_bool("TAPIFY_CHECK_DUPLICATES"),
    )
    p.add_argument(
        "-s", "--check-scopes", action="store_true", default=_env_bool("TAPIFY_CHECK_SCOPES")
    )
    p.add_argument(
        "-a",
        "--check-assertions-count",
        action="store_true",
        default=_env_bool("TAPIFY_CHECK_ASSERTIONS_COUNT"),
    )
    p.add_argument("--worker", action="store_true", default=True)
    p.add_argument("--no-worker", action="store_false", dest="worker")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("patterns", nargs="*")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if args.format not in _VALID_FORMATS:
        sys.stderr.write(f"tapify: unknown format {args.format!r}\n")
        sys.exit(exit_codes.INVALID_OPTION)

    return args
