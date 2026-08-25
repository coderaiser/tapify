from tapify import test
from tapify.validator import (
    create_validator,
    get_at,
    reset_processed,
    reset_validations,
    set_validations,
)


def _tests(*messages):
    return [
        {
            "message": m,
            "at": "file.py:1",
            "validations": {
                "check_duplicates": True,
                "check_scopes": True,
                "check_assertions_count": True,
            },
        }
        for m in messages
    ]


@test("validator: one assertion passes")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    t.equal(v("scope: x", assertions_count=1), [])
    reset_validations()
    t.end()


@test("validator: zero assertions fails")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    msg, at = v("scope: x", assertions_count=0)
    t.match(msg, r"have none")
    reset_validations()
    t.end()


@test("validator: two assertions fails")
def _(t):
    set_validations(
        {"check_assertions_count": True, "check_duplicates": False, "check_scopes": False}
    )
    v = create_validator(tests=_tests("scope: x"))
    msg, at = v("scope: x", assertions_count=2)
    t.match(msg, r"have more")
    reset_validations()
    t.end()


@test("validator: bad scope fails when check_scopes enabled")
def _(t):
    set_validations(
        {"check_scopes": True, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("no scope here"))
    msg, at = v("no scope here", assertions_count=1)
    t.match(msg, r"Scope should be defined")
    reset_validations()
    t.end()


@test("validator: duplicates detected once")
def _(t):
    set_validations(
        {"check_duplicates": True, "check_scopes": False, "check_assertions_count": False}
    )
    reset_processed()
    v = create_validator(tests=_tests("scope: dup", "scope: dup"))
    result = v("scope: dup", assertions_count=1)
    t.ok(result, "first duplicate reported")
    reset_processed()
    reset_validations()
    t.end()


@test("validator: unknown message raises")
def _(t):
    set_validations(
        {"check_scopes": True, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("scope: known"))
    try:
        v("scope: unknown", assertions_count=1)
        raised = False
    except RuntimeError:
        raised = True
    t.ok(raised)
    reset_validations()
    t.end()


@test("validator: all disabled returns empty")
def _(t):
    set_validations(
        {"check_scopes": False, "check_duplicates": False, "check_assertions_count": False}
    )
    v = create_validator(tests=_tests("anything"))
    t.equal(v("anything", assertions_count=0), [])
    reset_validations()
    t.end()


@test("validator: get_at returns user frame")
def _(t):
    at = get_at()
    t.match(at, r"\.py:\d+$")
    t.end()
