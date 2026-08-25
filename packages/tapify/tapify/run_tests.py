import asyncio
import os


async def run_tests(tests: list, *, formatter, is_stop=None) -> dict:

    is_stop = is_stop or (lambda: False)
    only = [t for t in tests if t.get("only")]
    if only:
        skipped = len(tests) - len(only)
        return await _run_list(only, skipped=skipped, formatter=formatter, is_stop=is_stop)
    active = [t for t in tests if not t.get("skip")]
    skipped = len([t for t in tests if t.get("skip")])
    return await _run_list(active, skipped=skipped, formatter=formatter, is_stop=is_stop)


async def _run_list(tests, *, skipped, formatter, is_stop):
    from tapify.validator import create_validator

    count = [0]
    failed = [0]
    passed = [0]
    total = len(tests)

    formatter.emit("start", {"total": total})
    validate = create_validator(tests=tests)

    for test_def in tests:
        if is_stop():
            count[0] = total - 1
            break
        await _run_one(
            test_def,
            formatter=formatter,
            count=count,
            total=total,
            failed=failed,
            passed=passed,
            validate=validate,
        )

    formatter.emit(
        "end",
        {
            "count": count[0],
            "failed": failed[0],
            "passed": passed[0],
            "skipped": skipped,
        },
    )
    return {"count": count[0], "failed": failed[0], "passed": passed[0], "skipped": skipped}


async def _run_one(test_def, *, formatter, count, total, failed, passed, validate):
    from tapify.is_debug import is_debug
    from tapify.operators import init_operators

    message = test_def["message"]
    fn = test_def["fn"]
    timeout_ms = int(test_def.get("timeout") or os.environ.get("TAPIFY_TIMEOUT", 3000))
    timeout_s = 3_000 if is_debug() else timeout_ms / 1000

    formatter.emit("test", {"test": message})

    assertions_count = [0]
    is_ended = [False]

    runner_state = {
        "formatter": formatter,
        "count": lambda: count[0],
        "inc_count": lambda: count.__setitem__(0, count[0] + 1),
        "inc_passed": lambda: passed.__setitem__(0, passed[0] + 1),
        "inc_failed": lambda: failed.__setitem__(0, failed[0] + 1),
        "is_ended": is_ended,
        "assertions_count": lambda: assertions_count[0],
        "inc_assertions_count": lambda: assertions_count.__setitem__(0, assertions_count[0] + 1),
    }

    t = init_operators(runner_state, extensions=test_def.get("extensions", {}))

    is_return = [False]
    try:
        coro = fn(t) if asyncio.iscoroutinefunction(fn) else asyncio.to_thread(fn, t)
        await asyncio.wait_for(coro, timeout=timeout_s)
    except TimeoutError:
        t.fail(Exception(f"Timed out after {timeout_ms}ms"))
        t.end()
        is_return[0] = True
    except Exception as e:
        t.fail(e)
        t.end()
        is_return[0] = True

    is_ended[0] = False  # reset — validator runs after

    if not is_return[0]:
        result = validate(message, assertions_count=assertions_count[0])
        if result:
            msg, at = result
            t.fail(Exception(msg), at)
            t.end()

    formatter.emit(
        "test:end",
        {
            "count": count[0],
            "total": total,
            "test": message,
            "failed": failed[0],
        },
    )
