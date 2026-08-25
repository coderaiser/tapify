from tapify import exit_codes, test


@test("exit_codes: OK is 0")
def _(t):
    t.equal(exit_codes.OK, 0)
    t.end()


@test("exit_codes: FAIL is 1")
def _(t):
    t.equal(exit_codes.FAIL, 1)
    t.end()


@test("exit_codes: WAS_STOP is 2")
def _(t):
    t.equal(exit_codes.WAS_STOP, 2)
    t.end()


@test("exit_codes: UNHANDLED is 3")
def _(t):
    t.equal(exit_codes.UNHANDLED, 3)
    t.end()


@test("exit_codes: INVALID_OPTION is 4")
def _(t):
    t.equal(exit_codes.INVALID_OPTION, 4)
    t.end()


@test("exit_codes: SKIPPED is 5")
def _(t):
    t.equal(exit_codes.SKIPPED, 5)
    t.end()
