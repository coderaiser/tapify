import os
import shutil
import sys

_lines_store: list = []
_current = ""
_stream_box: list = [None]
_total_box: list = [0]


def _lines() -> list:
    return _lines_store


class _Devnull:
    def write(self, *_):
        return None


def _devnull() -> object:
    return _Devnull()


def _get_stream(total=None) -> object:
    is_enough = (total or 0) >= int(os.environ.get("TAPIFY_PROGRESS_BAR_MIN", 100))
    force = os.environ.get("TAPIFY_PROGRESS_BAR")
    is_ci = bool(os.environ.get("CI"))

    if force == "0":
        return _devnull()
    if force == "1":
        return sys.stderr
    if is_enough and not is_ci:
        return sys.stderr
    return _devnull()


def _format_ok() -> str:
    emulator = os.environ.get("TERMINAL_EMULATOR", "")
    spaces = " " if "JetBrains" in emulator else ""
    return f"# ✅{spaces} ok"


def _color_fn(color: str):
    if not sys.stderr.isatty():
        return lambda s: s
    if color.startswith("#"):
        r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
        prefix = f"\x1b[38;2;{r};{g};{b}m"
        return lambda s: f"{prefix}{s}\x1b[39m"
    named = {
        "red": "\x1b[31m",
        "green": "\x1b[32m",
        "yellow": "\x1b[33m",
        "blue": "\x1b[34m",
        "magenta": "\x1b[35m",
        "cyan": "\x1b[36m",
    }
    prefix = named.get(color, "")
    return lambda s: f"{prefix}{s}\x1b[39m" if prefix else s


def _render_bar(count, done, color) -> str:
    width = shutil.get_terminal_size().columns
    bar_color = _color_fn(color)
    percent = int(done * 100 / count) if count else 100
    bar_width = max(width - 30, 10)
    filled = int(bar_width * done / count) if count else bar_width
    bar = bar_color("█" * filled) + "░" * (bar_width - filled)
    return f"{bar} {percent}% | {done}/{count}"


def global_current(name):
    global _current
    _current = name


def create_formatter(color=None):
    """createFormatter() protocol — returns an object with formatter hooks."""
    color = color or os.environ.get("TAPIFY_PROGRESS_BAR_COLOR", "#f9d472")
    ci = bool(os.environ.get("CI"))
    stream = sys.stdout if ci else _get_stream()

    class _Formatter:
        @staticmethod
        def start(*, total=0, **_):
            _stream_box[0] = stream
            _total_box[0] = total
            _lines().clear()
            return None

        @staticmethod
        def test(*, test="", **_):
            global_current(test)
            lines = _lines()
            if bool(os.environ.get("CI")):
                lines.append(f"# {test}")
            return None

        @staticmethod
        def test_end(**_):
            return None

        @staticmethod
        def comment(*, message="", **_):
            return f"# {message}\n"

        @staticmethod
        def success(*, count=0, message="", **_):
            line = (
                _format_ok() + f" {count} {message}"
                if not bool(os.environ.get("CI"))
                else f"✅ ok {count} {message}"
            )
            _lines().append(line)
            return None

        @staticmethod
        def fail(
            *,
            at="",
            count=0,
            message="",
            operator="",
            result=None,
            expected=None,
            output="",
            error_stack="",
            test="",
            **_,
        ):
            show_stack = os.environ.get("TAPIFY_PROGRESS_BAR_STACK", "1") != "0"
            name = test or _current
            out = [
                f"# {name}",
                f"❌ not ok {count} {message}",
                "  ---",
                f"    operator: {operator}",
            ]
            if output:
                out.append(output)
            else:
                out += [
                    "    expected: |-",
                    f"      {expected}",
                    "    result: |-",
                    f"      {result}",
                ]
            out += [f"    {at}"]
            if show_stack:
                out += ["    stack: |-", error_stack]
            out += ["  ..."]
            _lines().append("\n".join(out))
            return None

        @staticmethod
        def end(*, count=0, passed=0, failed=0, skipped=0, **_) -> str:
            lines = []
            ci = bool(os.environ.get("CI"))
            if ci:
                lines.append("TAP version 13")
                lines.extend(_lines())
                lines.append(f"1..{count}")
            else:
                lines.append(_render_bar(count, count - failed, color))
                lines.extend(_lines())
            for _ in range(skipped):
                lines.append("# ⚠️ skip")
            if failed:
                lines.append(f"# fail {failed}")
            elif ci:
                lines.append("# ✅ ok")
            else:
                lines.append(_format_ok())
            result = "\r" + "\n".join(lines) + "\n"
            if stream is not None and not ci:
                stream.write(result)
            _lines_store.clear()
            return result

    return _Formatter()
