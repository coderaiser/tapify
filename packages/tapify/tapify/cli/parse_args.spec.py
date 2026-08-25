import os

from tapify import test
from tapify.cli.parse_args import parse_args


@test("parse_args: default format is progress-bar outside CI")
def _(t):
    os.environ.pop("CI", None)
    t.equal(parse_args([]).format, "progress-bar")
    t.end()


@test("parse_args: default format is tap inside CI")
def _(t):
    os.environ["CI"] = "1"
    result = parse_args([]).format
    os.environ.pop("CI")
    t.equal(result, "tap")
    t.end()


@test("parse_args: -f overrides default")
def _(t):
    t.equal(parse_args(["-f", "fail"]).format, "fail")
    t.end()


@test("parse_args: --no-worker sets worker to False")
def _(t):
    t.not_ok(parse_args(["--no-worker"]).worker)
    t.end()


@test("parse_args: --dry-run flag")
def _(t):
    t.ok(parse_args(["--dry-run"]).dry_run)
    t.end()


@test("parse_args: validation defaults from env")
def _(t):
    saved = os.environ.get("TAPIFY_CHECK_SCOPES")
    os.environ["TAPIFY_CHECK_SCOPES"] = "0"
    args = parse_args(["-s"])
    if saved is None:
        os.environ.pop("TAPIFY_CHECK_SCOPES", None)
    else:
        os.environ["TAPIFY_CHECK_SCOPES"] = saved
    t.ok(args.check_scopes)
    t.end()


@test("parse_args: require collects modules")
def _(t):
    args = parse_args(["-r", "json", "-r", "os"])
    t.deep_equal(args.require, ["json", "os"])
    t.end()


@test('parse_args: unknown format exits INVALID_OPTION')
def _(t):
    raised = False
    try:
        parse_args(['-f', '__nope__'])
    except SystemExit as e:
        raised = e.code == 4
    t.ok(raised)
    t.end()


@test('parse_args: help and version flags')
def _(t):
    args = parse_args(['-h'])
    t.ok(args.help)
    args = parse_args(['--version'])
    t.ok(args.version)
    t.end()
