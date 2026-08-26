import os
import shutil
import sys

_total_box: list = [0]
_last_render_box: list = []

OK = "👌"


def _last_render() -> list:
    return list(_last_render_box)


def bar_color_red(count: int) -> str:
    """red(failed) like chalk.red in supertape's formatErrorsCount."""
    if sys.stderr.isatty():
        return f"\x1b[31m{count}\x1b[39m"
    return str(count)


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


def _visible_len(s: str) -> int:
    """Display width of s — wide/emoji chars take 2 terminal columns."""
    import unicodedata

    return sum(2 if unicodedata.east_asian_width(c) in "WF" or ord(c) > 0xFFFF else 1 for c in s)


def _render_bar(count, done, color, test="", failed=0) -> str:
    width = shutil.get_terminal_size().columns
    bar_color = _color_fn(color)
    count = max(int(count or 0), 1)
    done = min(max(int(done or 0), 0), count)
    percent = int(done * 100 / count)
    # cliProgress: bar fills the terminal minus the rendered payload;
    # failed shows a red error count, 👌 when the current test passes
    failed_part = bar_color_red(failed) if failed else OK
    payload = f"{percent}% | {failed_part} | {done}/{count} | {test}"
    bar_width = max(width - _visible_len(payload) - 2, 10)
    filled = int(bar_width * done / count)
    bar = bar_color("█" * filled) + "░" * (bar_width - filled)
    return f"{bar} {payload}"


def create_formatter(color=None):
    """createFormatter() protocol — returns an object with formatter hooks."""
    color = color or os.environ.get("TAPIFY_PROGRESS_BAR_COLOR", "#f9d472")
    store: list = [""]
    lines: list = []
    current_test: list = [""]
    done: list = [0]
    fails: list = [0]

    class _Formatter:
        @staticmethod
        def start(*, total=0, **_):
            _total_box[0] = total
            done[0] = 0
            fails[0] = 0
            lines.clear()
            _last_render_box.clear()
            lines.append("TAP version 13")
            return None

        @staticmethod
        def test(*, test="", **_):
            store[0] = f"# {test}"
            current_test[0] = test
            fails[0] = 0
            return None

        @staticmethod
        def test_end(*, count=0, total=0, **_):
            del count
            done[0] += 1
            total = total or _total_box[0]
            stream = _get_stream(total)
            rendered = _render_bar(total, done[0], color, current_test[0], fails[0])
            _last_render_box.append(rendered)
            stream.write("\r" + rendered)
            return None

        @staticmethod
        def comment(*, message="", **_):
            lines.append(f"# {message}")
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
            **_,
        ):
            show_stack = os.environ.get("TAPIFY_PROGRESS_BAR_STACK", "1") != "0"
            out = [
                "",
                store[0],
                f"❌ not ok {count} {message}",
                "  ---",
                f"    operator: {operator}",
            ]
            fails[0] += 1
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
            out += ["  ...", ""]
            lines.append("\n".join(out))
            return None

        @staticmethod
        def end(*, count=0, passed=0, failed=0, skipped=0, **_) -> str:
            lines.append("")
            lines.append(f"1..{count}")
            lines.append(f"# tests {count}")
            lines.append(f"# pass {passed}")
            if skipped:
                lines.append(f"# ⚠️ skip {skipped}")
            lines.append("")
            if failed:
                lines.append(f"# ❌ fail {failed}")
            else:
                lines.append(_format_ok())
            lines.extend(["", ""])
            result = "\r" + "\n".join(lines)
            lines.clear()
            return result

    return _Formatter()
