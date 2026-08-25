import importlib
import importlib.util
import os
import sys
import traceback
from pathlib import Path

from tapify import exit_codes
from tapify.cli.parse_args import parse_args


def main():
    # Windows ANSI
    if os.name == "nt":
        try:
            import colorama

            colorama.just_fix_windows_console()
        except ImportError:
            pass

    args = parse_args(sys.argv[1:])

    if args.help:
        _print_help()
        sys.exit(exit_codes.OK)

    if args.version:
        from tapify import __version__

        sys.stdout.write(f"v{__version__}\n")
        sys.exit(exit_codes.OK)

    # Apply validation flags
    from tapify.validator import set_validations

    set_validations(
        {
            "check_duplicates": args.check_duplicates,
            "check_scopes": args.check_scopes,
            "check_assertions_count": args.check_assertions_count,
        }
    )

    # --require
    for module in args.require:
        try:
            importlib.import_module(module)
        except Exception:
            sys.stderr.write(traceback.format_exc())
            sys.exit(exit_codes.UNHANDLED)

    # Glob test files
    files: list[Path] = []
    for pattern in args.patterns:
        candidate = Path(pattern)
        if candidate.is_absolute():
            if candidate.is_file() and candidate not in files:
                files.append(candidate)
            continue
        for p in sorted(Path(".").glob(pattern)):
            if p not in files and "node_modules" not in p.parts:
                files.append(p)

    # init supertape
    from tapify.supertape import init

    init(
        {
            "run": False,
            "quiet": True,
            "format": args.format,
            "stream": sys.stdout,
            "check_duplicates": args.check_duplicates,
            "check_scopes": args.check_scopes,
            "check_assertions_count": args.check_assertions_count,
        }
    )

    if not files:
        sys.exit(exit_codes.OK)  # no files is not an error

    if not args.dry_run:
        for f in files:
            _import_file(f)

    # Run — with or without worker
    try:
        from tapify.supertape import _tests

        if args.worker:
            from tapify.worker import run_with_worker

            code = run_with_worker(_tests, format_name=args.format)
        else:
            from tapify.worker import run_without_worker

            code = run_without_worker(_tests, format_name=args.format)
    except Exception:
        sys.stderr.write(traceback.format_exc())
        sys.exit(exit_codes.UNHANDLED)

    sys.exit(code)  # _exit_code() already applied in worker._exit_code()


def _import_file(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


def _print_help():
    sys.stdout.write("""\
Usage: python -m tapify [options] [glob ...]

Options:
  -h, --help                       display help
  -v, --version                    output version
  -f, --format FORMAT              tap | fail | short | progress-bar | json-lines
                                   default: progress-bar (tap on CI)
  -r, --require MODULE             import module before test files (repeatable)
  -d, --check-duplicates           check duplicate test names (default: on)
  -s, --check-scopes               enforce 'scope: subject' format (default: on)
  -a, --check-assertions-count     enforce one assertion per test (default: on)
      --no-worker                  disable worker thread
      --dry-run                    import files, do not run
""")


if __name__ == "__main__":
    main()
