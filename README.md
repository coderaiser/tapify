# tapify

TAP-compatible test runner for Python — a faithful port of
[supertape](https://github.com/coderaiser/supertape).

## Install

```sh
uv sync
```

## Usage

Write a spec file:

```py
# math.spec.py
from tapify import test


@test('math: adds numbers')
def _(t):
    t.equal(1 + 1, 2)
    t.end()
```

Run it:

```sh
tapify 'packages/**/*.spec.py'
```

Exit codes follow supertape exactly:

| Code | Meaning |
|------|---------|
| `0` | all passed |
| `1` | failures |
| `2` | stopped by user |
| `3` | unhandled error |
| `4` | invalid CLI option |
| `5` | skipped tests found (`TAPIFY_CHECK_SKIPPED=1`) |

## Formatters

`tap`, `fail`, `short`, `progress-bar` (default), `json-lines`. Select with
`-f/--format`. On CI the default is `tap`.

## Environment variables

| Variable | Default | Controls |
|----------|---------|----------|
| `TAPIFY_TIMEOUT` | `3000` | per-test timeout (ms) |
| `TAPIFY_CHECK_DUPLICATES` | `1` | duplicate test-name validation |
| `TAPIFY_CHECK_SCOPES` | `1` | `scope: subject` name validation |
| `TAPIFY_CHECK_ASSERTIONS_COUNT` | `1` | one assertion per test |
| `TAPIFY_CHECK_SKIPPED` | `0` | non-zero exit on skipped tests |
| `TAPIFY_PROGRESS_BAR` | unset | force bar on (`1`) / off (`0`) |
| `CI` | unset | truthy → tap format, bar disabled |

## Operators

`t.ok`, `t.not_ok`, `t.equal`, `t.not_equal`, `t.deep_equal`,
`t.not_deep_equal`, `t.pass_`, `t.fail`, `t.match`, `t.not_match`,
`t.comment`, `t.end`. Extend with `test.extend({...})`.

## Development

Lint and format with ruff, run the self-hosting suite, check coverage:

```sh
uv run ruff check . && uv run ruff format --check .
uv run python -m tapify 'packages/**/*.spec.py' -f tap --no-worker
uv run coverage run -m tapify 'packages/**/*.spec.py' -f tap --no-worker
uv run coverage report --fail-under=100
```
The test runner is the project itself: the spec files above are executed by
`tapify`.
