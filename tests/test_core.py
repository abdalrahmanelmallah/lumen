"""
Core language tests — exercise the interpreter directly (no subprocess)
so failures point straight at a line in lumen.py.

Run with:
    pip install pytest
    pytest tests/
"""
import io
import os
import sys
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lumen  # noqa: E402


def run(source):
    """Runs a Lumen source string and returns whatever it printed via run(),
    as a list of lines."""
    interp = lumen.Interpreter()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(source, filename="<test>")
    return buf.getvalue().splitlines()


def test_arithmetic():
    assert run("run(2 + 3 * 4)") == ["14"]
    assert run("run(2 ** 10)") == ["1024"]
    assert run("run(7 % 3)") == ["1"]


def test_variables_and_assignment():
    assert run("let x = 5\nx = x + 1\nrun(x)") == ["6"]


def test_if_elif_else():
    src = """
    let x = 5
    if x > 10 { run("big") } elif x > 3 { run("medium") } else { run("small") }
    """
    assert run(src) == ["medium"]


def test_while_and_break_continue():
    src = """
    let i = 0
    let total = 0
    while i < 10 {
        i = i + 1
        if i == 3 { continue }
        if i == 6 { break }
        total = total + i
    }
    run(total)
    """
    # 1 + 2 + 4 + 5 = 12 (3 skipped via continue, loop stops before adding 6)
    assert run(src) == ["12"]


def test_for_c_style_and_for_in():
    assert run("for let i = 0; i < 3; i = i + 1 { run(i) }") == ["0", "1", "2"]
    assert run('for item in ["a", "b"] { run(item) }') == ["a", "b"]


def test_functions_and_recursion():
    src = """
    fn fact(n) {
        if n <= 1 { return 1 }
        return n * fact(n - 1)
    }
    run(fact(6))
    """
    assert run(src) == ["720"]


def test_closures():
    src = """
    fn makeCounter() {
        let count = 0
        fn increment() {
            count = count + 1
            return count
        }
        return increment
    }
    let counter = makeCounter()
    run(counter())
    run(counter())
    run(counter())
    """
    assert run(src) == ["1", "2", "3"]


def test_lists_and_indexing():
    src = """
    let xs = [10, 20, 30]
    xs[1] = 99
    run(xs)
    run(len(xs))
    run(xs[0] + xs[2])
    """
    assert run(src) == ['[10, 99, 30]', "3", "40"]


def test_dicts():
    src = """
    let d = {"a": 1, "b": 2}
    run(d["a"])
    d["c"] = 3
    run(keys(d))
    run(hasKey(d, "c"))
    """
    assert run(src) == ["1", '["a", "b", "c"]', "true"]


def test_classes_and_methods():
    src = """
    class Point {
        fn init(self, x, y) { self.x = x; self.y = y }
        fn sum(self) { return self.x + self.y }
    }
    let p = new Point(3, 4)
    run(p.sum())
    """
    assert run(src) == ["7"]


def test_try_catch_catches_runtime_errors():
    src = """
    try {
        let boom = [1, 2][99]
        run("unreachable")
    } catch err {
        run("caught")
    }
    """
    assert run(src) == ["caught"]


def test_string_interpolation():
    src = 'let name = "world"\nrun(f"hello, {name}! {2 + 2}")'
    assert run(src) == ["hello, world! 4"]


def test_string_escapes():
    assert run(r'run("a\nb")') == ["a", "b"]
    assert run(r'run("tab:\tend")') == ["tab:\tend"]
    assert run(r'run("quote:\"end")') == ['quote:"end']


def test_unicode_string_literals_are_not_corrupted():
    """Regression test: string literals used to be run through
    str.encode().decode('unicode_escape') to process backslash escapes,
    which silently mangled any non-ASCII character (each UTF-8 byte
    got reinterpreted as a separate Latin-1 character). Any Unicode
    character in a literal must come out exactly as written."""
    assert run('run("café")') == ["café"]
    assert run('run("naïve, Vigenère, 🎉")') == ["naïve, Vigenère, 🎉"]
    assert run('let x = "y"\nrun(f"emoji: 🎉 and {x}")') == ["emoji: 🎉 and y"]


def test_bitwise_operators():
    assert run("run(6 & 3)") == ["2"]
    assert run("run(6 | 1)") == ["7"]
    assert run("run(5 ^ 1)") == ["4"]
    assert run("run(1 << 4)") == ["16"]


def test_builtins():
    assert run('run(typeOf(1), typeOf("a"), typeOf([1]), typeOf({"a": 1}))') == [
        "number string list dict"
    ]
    assert run('run(str(42))') == ["42"]
    assert run('run(num("3.5"))') == ["3.5"]
