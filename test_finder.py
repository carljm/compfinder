import textwrap

from finder import find_709_comps


def run(codestr: str) -> list[tuple[int, str]]:
    return find_709_comps(textwrap.dedent(codestr))


def test_no_comps():
    assert run("") == []


def test_non_class_comp():
    codestr = """
        [x for x in [1]]
    """
    assert run(codestr) == []


def test_no_class_scope_name_used():
    codestr = """
        class C:
            incr = 2
            [x for x in [1]]
    """
    assert run(codestr) == []


def test_ok_name_error_pre_709():
    codestr = """
        class C:
            incr = 2
            [incr for x in [1]]
    """
    assert run(codestr) == []


def test_ok_name_deleted():
    codestr = """
        incr = 1
        class C:
            incr = 2
            del incr
            [incr for x in [1]]
    """
    assert run(codestr) == []


def test_found():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [incr for x in [1]]
    """
    assert run(codestr) == [(5, "incr")]


def test_found_nested():
    codestr = """
        def f():
            incr = 1
            class C:
                incr = 2
                [incr for x in [1]]
    """
    assert run(codestr) == [(6, "incr")]


def test_found_async_nested():
    codestr = """
        async def f():
            incr = 1
            class C:
                incr = 2
                [incr for x in [1]]
    """
    assert run(codestr) == [(6, "incr")]


def test_found_conflicts_with_method():
    codestr = """
        incr = 1
        class C:
            def incr(self): pass
            [incr for x in [1]] 
    """
    assert run(codestr) == [(5, "incr")]


def test_found_conflicts_with_async_method():
    codestr = """
        incr = 1
        class C:
            async def incr(self): pass
            [incr for x in [1]] 
    """
    assert run(codestr) == [(5, "incr")]


def test_found_conflicts_with_nested_class():
    codestr = """
        incr = 1
        class C:
            class incr: pass
            [incr for x in [1]] 
    """
    assert run(codestr) == [(5, "incr")]


def test_found_inside_expr():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [x+incr for x in [1]]
    """
    assert run(codestr) == [(5, "incr")]


def test_found_conflicts_with_builtin():
    codestr = """
        class C:
            def set(self): pass
            [set() for x in [1]]
    """
    assert run(codestr) == [(4, "set")]


def test_found_class_resolve_skips_to_globals():
    codestr = """
        def f():
            incr = 1
            class C:
                [incr for x in [1]]
    """
    assert run(codestr) == [(5, "incr")]


def test_found_in_if_clause():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [x for x in [1] if x == incr]
    """
    assert run(codestr) == [(5, "incr")]


def test_ok_bound_by_target():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [incr for incr in [1]]
    """
    assert run(codestr) == []


def test_found_in_nested_iter():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [x for x in [1] for y in [incr]]
    """
    assert run(codestr) == [(5, "incr")]


def test_ok_in_outer_iter():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [x for x in [incr]]
    """
    assert run(codestr) == []


def test_explicit_global():
    codestr = """
        incr = 1
        class C:
            global incr
            incr = 2
            [incr for x in [1]]
    """
    assert run(codestr) == []


def test_global_jumps_over_enclosing_scope():
    codestr = """
        def f():
            incr = 1
            def g():
                global incr
                def h():
                    class C:
                        incr = 2
                        [incr for x in [1]]
    """
    assert run(codestr) == []


def test_setcomp():
    codestr = """
        incr = 1
        class C:
            incr = 2
            {incr for x in [1]}
    """
    assert run(codestr) == [(5, "incr")]


def test_dictcomp_key():
    codestr = """
        incr = 1
        class C:
            incr = 2
            {incr: 3 for x in [1]}
    """
    assert run(codestr) == [(5, "incr")]


def test_dictcomp_val():
    codestr = """
        incr = 1
        class C:
            incr = 2
            {3: incr for x in [1]}
    """
    assert run(codestr) == [(5, "incr")]


def test_nested():
    codestr = """
        incr = 1
        class C:
            incr = 2
            [[incr for y in [2]] for x in [1]]
    """
    assert run(codestr) == [(5, "incr")]
