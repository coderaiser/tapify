import os

import formatter_progress_bar as fpb
from tapify import test


@test('formatter_progress_bar: non-CI bar renders and buffers')
def _(t):
    saved = {k: os.environ.get(k) for k in ('CI',)}
    os.environ.pop('CI', None)
    try:
        fmt = fpb.create_formatter('#f9d472')
        fmt.start(total=3)
        fmt.test(test='scope: bar')
        fmt.success(count=1, message='good thing')
        fmt.fail(at='file.py:1', count=2, message='bad thing', operator='ok',
                 result=False, expected=True, output='', error_stack='stack here')
        out = fmt.end(count=3, passed=2, failed=1, skipped=1)
        t.ok(out.startswith('\r'))
        t.match(out, r'█')
        t.match(out, r'good thing')
        t.match(out, r'bad thing')
        t.match(out, r'⚠️ skip')
        t.match(out, r'# fail 1')
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    t.end()


@test('formatter_progress_bar: color functions')
def _(t):
    identity = fpb._color_fn('#ff0000')
    t.equal(identity('x'), 'x')   # not a tty → no colors
    named = fpb._color_fn('red')
    t.equal(named('x'), 'x')
    unknown = fpb._color_fn('chartreuse')
    t.equal(unknown('x'), 'x')
    t.equal(fpb._devnull().__class__.__name__, '_Devnull')
    t.end()


@test('formatter_progress_bar: comment returns text')
def _(t):
    t.equal(fpb.create_formatter().comment(message='note'), '# note\n')
    t.end()
