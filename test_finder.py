import subprocess
import sys
import textwrap

from finder import find_709_comps, find_709_comps_in_files


def test_cli(tmp_path):
    file1 = tmp_path / "file1.py"
    file1.write_text(
        textwrap.dedent(
        """
        x = 1
        class C:
            x = 2
            [x for y in [1]]
        """
        )
    )
    file2 = tmp_path / "file2.py"
    file2.write_text("x = 1")
    res = subprocess.run(
        [sys.executable, "-m", "finder", str(tmp_path)],
        capture_output=True,
        check=True,
        text=True,
    )
    assert res.stderr == ""
    assert res.stdout == textwrap.dedent(
        f"""
        {file1}:
            5 - x
    """
    )


def test_in_dir(tmp_path):
    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    sub = tmp_path / "d"
    sub.mkdir()
    file3 = sub / "file3.py"
    txt = tmp_path / "file.txt"
    txt.write_text("This is not Python.")
    file1.write_text(
        textwrap.dedent(
            """
        x1 = 1
        class C:
            x1 = 2
            [x1 for y in [1]]
    """
        )
    )
    file2.write_text(
        textwrap.dedent(
            """
        x2 = 1
        class C:
            x2 = 2
            [x2 for y in [1]]
    """
        )
    )
    file3.write_text(
        textwrap.dedent(
            """
        x3 = 1
        class C:
            x3 = 2
            [x3 for y in [1]]
    """
        )
    )
    assert find_709_comps_in_files(tmp_path) == {
        str(file1): [(5, "x1")],
        str(file2): [(5, "x2")],
        str(file3): [(5, "x3")],
    }


def test_in_file(tmp_path):
    file_path = tmp_path / "code.py"
    file_path.write_text(
        textwrap.dedent(
            """
        incr = 1
        class C:
            incr = 2
            [incr for x in [1]]
    """
        )
    )
    assert find_709_comps_in_files(file_path) == {str(file_path): [(5, "incr")]}


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


def test_bad_syntax():
    codestr = """
    foo = "
    """
    assert run(codestr) == [(0, "Unable to parse file.")]