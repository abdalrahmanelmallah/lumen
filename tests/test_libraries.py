"""
Library tests — run small Lumen snippets through `python3 lumen.py` as a
subprocess and check stdout. Subprocess (rather than calling the
interpreter in-process) is used here because some of these libraries
touch the filesystem/environment the way real programs would.

Run with:
    pip install pytest
    pytest tests/
"""
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUMEN_PY = os.path.join(REPO_ROOT, "lumen.py")


def run_lumen(source):
    """Writes `source` to a temp .lu file, runs it, and returns
    (stdout, exit_code)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".lu", delete=False, encoding="utf-8"
    ) as f:
        f.write(source)
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, LUMEN_PY, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        return result.stdout.strip(), result.returncode, result.stderr
    finally:
        os.unlink(path)


def assert_ok(source, expected_lines):
    stdout, code, stderr = run_lumen(source)
    assert code == 0, f"exited {code}, stderr:\n{stderr}"
    assert stdout.splitlines() == expected_lines


def test_json_roundtrip():
    assert_ok(
        """
        import "json"
        let obj = jsonParse("{\\"a\\": 1, \\"b\\": [1, 2, 3]}")
        run(obj["a"])
        run(obj["b"])
        run(jsonStringify({"x": 1}))
        run(jsonIsValid("not json"))
        """,
        ["1", "[1, 2, 3]", '{"x": 1}', "false"],
    )


def test_re_library():
    assert_ok(
        r"""
        import "re"
        run(reTest("\d+", "abc123"))
        run(reFindAll("\d+", "a1 b22 c333"))
        run(reReplace("\s+", "a   b", "_"))
        """,
        ["true", '["1", "22", "333"]', "a_b"],
    )


def test_datetime_library():
    assert_ok(
        """
        import "datetime"
        run(formatTime(0, "%Y-%m-%d"))
        run(weekdayName(0))
        """,
        ["1970-01-01", "Thursday"],
    )


def test_format_library():
    assert_ok(
        """
        import "format"
        run(toFixed(3.14159, 2))
        run(padStart("7", 3, "0"))
        run(withCommas(1234567))
        """,
        ["3.14", "007", "1,234,567"],
    )


def test_collections_library():
    assert_ok(
        """
        import "collections"
        let s = new Stack()
        s.push(1); s.push(2)
        run(s.pop())
        let q = new Queue()
        q.enqueue("a"); q.enqueue("b")
        run(q.dequeue())
        let set = new Set()
        set.add("x"); set.add("x"); set.add("y")
        run(set.size())
        """,
        ["2", "a", "2"],
    )


def test_test_library_passes_and_fails_correctly():
    stdout, code, stderr = run_lumen(
        """
        import "test"
        try {
            assertEqual(1 + 1, 2, "math")
            run("passed")
        } catch err {
            run("unexpected failure")
        }
        """
    )
    assert code == 0
    assert stdout.strip() == "passed"

    stdout, code, stderr = run_lumen(
        """
        import "test"
        try {
            assertEqual(1 + 1, 3, "broken math")
            run("should not print")
        } catch err {
            run("caught failure")
        }
        """
    )
    assert code == 0
    assert "caught failure" in stdout
    assert "should not print" not in stdout


def test_lists_library_additions():
    assert_ok(
        """
        import "lists"
        run(unique([1, 2, 1, 3, 2]))
        run(flatten([[1, 2], [3]]))
        run(chunk([1, 2, 3, 4, 5], 2))
        run(zip([1, 2], ["a", "b"]))
        """,
        ["[1, 2, 3]", "[1, 2, 3]", "[[1, 2], [3, 4], [5]]", '[[1, "a"], [2, "b"]]'],
    )


def test_strings_library_additions():
    assert_ok(
        """
        import "strings"
        run(capitalizeWords("hello there world"))
        run(wordCount("  a b  c "))
        run(isBlank("   "))
        """,
        ["Hello There World", "3", "true"],
    )


def test_file_search():
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "log.txt").replace("\\", "/")
        with open(target, "w", encoding="utf-8") as f:
            f.write("hello\nworld\nhello again\n")
        stdout, code, stderr = run_lumen(
            f"""
            import "file"
            let hits = searchInFile("{target}", "hello")
            run(len(hits))
            run(hits[0]["line"])
            """
        )
        assert code == 0, stderr
        assert stdout.splitlines() == ["2", "1"]


def test_encrypt_roundtrip_with_unicode():
    assert_ok(
        """
        import "encrypt"
        let key = generateKey()
        let cipher = encryptWithKey("café 🎉", key)
        let plain = decryptWithKey(cipher, key)
        run(plain == "café 🎉")
        """,
        ["true"],
    )
